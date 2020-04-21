#!/usr/bin/python
# coding=utf-8
"""
/*******************************************************************************
 * Deep North Confidential
 * Copyright (C) 2018 Deep North Inc. All rights reserved.
 * The source code for this program is not published
 * and protected by copyright controlled
 *******************************************************************************/
"""

import gc
import os
import sys
import etcd
import time
import json
import socket
import logging
import traceback
import threading
import subprocess
import setproctitle
import multiprocessing

import log
import host
import conf
import reports
import etcd_util
import scheduler
import queue_conf
import camera_status
import algo_data_conf
from log import worker_logger as logger


sys.path.append('../algo_framework/src')
from AlgoInterface import AlgoInterface


g_worker_log_idx = {}
g_worker_dict = {}
g_worker_id = 0


WORKER_STATUS_RUN = 0
WORKER_STATUS_DONE = 1
WORKER_STATUS_EXIT = 2
WORKER_STATUS_TIMEOUT = 3
WORKER_STATUS_UNKNOWN = 4

WORK_RETRY_TIMES = 3

# lock = multiprocessing.RLock()
lock = multiprocessing.Lock()


def get_all_workers():
    with lock:
        return g_worker_dict


def get_worker_id():
    global g_worker_id
    g_worker_id = g_worker_id + 1
    if g_worker_id % 20 == 0:
        logger.debug('had process 20 worker, run gc')
        gc.collect()
    return g_worker_id


def add_work_to_dict(worker):
    all_worker_dict = get_all_workers()
    with lock:
        logger.debug('add new worker{} to dict'.format(worker.id))
        all_worker_dict[worker.id] = worker
        logger.info('all_worker_dict is {}'.format(all_worker_dict))


def clean_worker(worker_id, release_res=True):
    all_worker_dict = get_all_workers()
    with lock:
        logger.debug('clean worker{} ...'.format(worker_id))
        worker = all_worker_dict[worker_id]
        worker.finish_time = time.time()

        camera_status.collect_camera_status(worker)

        if release_res:
            reports.update_algo_statistics_cnt(worker)

        logger.debug('del worker{} from dict'.format(worker.id))
        del all_worker_dict[worker_id]

        if release_res:
            logger.debug('release host<{}> resource for worker{}'.format(
                host.HOST_NAME,
                worker_id))

            host.release_host_res(worker)

        if worker.is_alive():
            logger.debug('terminate worker{} and join'.format(worker_id))
            worker.terminate()
            worker.join()

        free_worker_logger_idx(worker)
        worker_release(worker)


class Worker(multiprocessing.Process):

    def __init__(self, worker_id=None, logger_index=None):
        super(Worker, self).__init__()

        if worker_id is not None:
            self.id = worker_id
        else:
            self.id = get_worker_id()

        logger.debug('call worker{} __init__'.format(self.id))
        self.decision = None

        self.msg_que = None
        self.msg_status_que = None

        self.has_msg = False
        self.msg = None
        self.algo = None

        self.interprocess_dict = multiprocessing.Manager().dict()

        self.total_tasks = 0
        self.total_run_tasks = 0
        self.total_done_tasks = 0
        self.total_exit_tasks = 0
        self.total_timeout_tasks = 0

        self.name = 'worker' + str(self.id)

        self.start_time = None
        self.finish_time = None
        self.run_timeout = conf.sched_conf.worker_run_timeout
        self.status = WORKER_STATUS_RUN
        self.retry_times = 0
        self.gpu_id = None
        self.logger = None
        self.logger_index = logger_index

    def watch_parent_process(self):
        self.logger.debug('call watch_parent_process')
        while True:
            ppid = os.getppid()
            if ppid == 1:
                self.logger.info('worker{} exit because the scheduler process exit'.format(self.id))
                os._exit(0)

            time.sleep(3)

    def _init_logger(self, pid):
        self.logger = logging.getLogger('worker' + str(pid))
        self.logger.setLevel(logging.DEBUG)

        log_dir = './log/worker/'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        hostname = socket.gethostname()

        worker_log_name = 'worker' + '_' + hostname + '_' + str(self.logger_index) + '.log'
        worker_log_path = log_dir + worker_log_name
        worker_file_handler = log.get_file_handler(worker_log_path)

        formatter = logging.Formatter(
            "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s - [pid:%(process)d] - %(message)s")
        worker_file_handler.setFormatter(formatter)
        self.logger.addHandler(worker_file_handler)

    def run(self):
        self._init_logger(str(os.getpid()))
        self.logger.info('run worker{} ...'.format(self.id))

        start_run_time = time.time()
        self.logger.debug('create AlgoInterface for worker{}'.format(self.id))
        algo_conf = self.decision.queue.algo_conf
        self.algo = AlgoInterface(
            self.gpu_id, algo_conf,
            log_file_name='AlgoInterface_' + socket.gethostname() + '_' + str(self.logger_index) + '.log')

        self.logger.debug('algo_conf = <{}>'.format(algo_conf))

        # change worker process name
        queue_name = self.decision.queue.name
        process_name = queue_name + '_worker_' + 'gpu' + str(self.gpu_id)
        setproctitle.setproctitle(process_name)

        watch_parent_process_thread = threading.Thread(
            target=self.watch_parent_process,
            name='watch_parent_process_thread')
        watch_parent_process_thread.daemon = True
        watch_parent_process_thread.start()
        self.logger.debug('run watch_parent_process_thread done')

        max_tasks = self.decision.queue.max_tasks_per_worker
        self.logger.debug('max_tasks_per_worker = {}'.format(max_tasks))
        total_tasks = 0

        while True:
            try:
                self.logger.debug('worker{} get msg'.format(self.id))
                timeout = conf.sched_conf.fetch_mq_msg_timeout
                if self.msg_que.full():
                    self.logger.warn('worker{} msg_que is full'.format(self.id))
                if self.msg_que.empty():
                    self.logger.warn('worker{} msg_que is empty, so get msg will failed !!!'.format(self.id))

                msg = self.msg_que.get(block=True, timeout=timeout)
                self.logger.debug('worker{} get msg done'.format(self.id))
                self.logger.debug('worker{} msg: <{}>'.format(self.id, msg))

            except Exception as e:
                self.logger.error('worker{} get msg timeout: {}'.format(self.id, e))
                self.logger.error('failed reason is {}'.format(traceback.format_exc()))
                # self.algo.release()
                os._exit(21)

            file_path = msg.get('file_path', None)
            self.logger.debug('worker{} video file path <{}>'.format(self.id, file_path))

            algo_data = algo_data_conf.get_algo_data(msg, self.logger)
            if algo_data is None:
                self.logger.error('worker{} failed to get algo data, exit'.format(self.id))
                self.algo.release()
                os._exit(22)

            try:
                self.logger.debug('worker{} process_data, algo_data = <{}>'.format(self.id, algo_data))
                start_time = time.time()
                ret = self.algo.process_data(str(file_path), algo_data)
                time_cost = time.time() - start_time

                self.interprocess_dict['schedule_seconds'] = time_cost
                self.interprocess_dict['return_code'] = ret

                self.logger.info('worker{} process_data done, return<{}>, time cost<{:.2f}s>, algo name<{}>,'
                                 ' file path<{}>'.format(self.id, ret, time_cost, self.decision.queue.name, file_path))
            except Exception as e:
                # ret = 127
                self.logger.error('process_data error: {}'.format(e))
                self.algo.release()
                os._exit(127)

            self.msg_status_que.put(ret)
            # self.logger.debug('put worker{} status msg done'.format(self.id))

            total_tasks += 1
            if total_tasks == max_tasks:
                self.logger.info('<worker{}> had process <{}> msgs, exit, total time cost is <{:.2f}s>'.format(
                                 self.id, max_tasks, time.time() - start_run_time))
                self.algo.release()
                self.logger.info('worker{} release success\n\n\n\n'.format(self.id))
                os._exit(ret)


def worker_release(worker):
    if worker:
        free_worker_logger_idx(worker)
        logger.debug('close worker{} queue'.format(worker.id))
        worker.msg_que.close()
        worker.msg_status_que.close()
        if worker.algo:
            worker.algo.release()
            del worker.algo
        del worker


def watch_all_works():
    no_worker_num = 0
    while True:
        time.sleep(1)
        # check_host_block()

        try:
            reports.reset_running_statistics()
            reports.reset_running_allocation()

            all_worker_dict = get_all_workers()
            logger.debug('all_worker_dict is {}'.format(all_worker_dict))
            if not all_worker_dict:
                no_worker_num += 1
                if no_worker_num % 60 == 0:
                    logger.warn('Found no work for {} sec, update host info to etcd'.format(no_worker_num))
                    host.collect_host_static_info(host.TOTAL_GPUS)
            else:
                no_worker_num = 0

            keys = all_worker_dict.keys()
            for worker_id in keys:
                worker = all_worker_dict[worker_id]

                logger.debug('enter update_algo_statistics_cnt')
                reports.update_algo_statistics_cnt(worker)

                logger.debug('enter update_algo_alloc_cnt')
                reports.update_algo_alloc_cnt(worker)

                logger.debug('found worker{} in current host'.format(worker_id))
                logger.debug('worker.retry_times<{}> run_timeout<{}> is_alive<{}> exitcode<{}> has_msg<{}>'.format(
                             worker.retry_times, worker.run_timeout, worker.is_alive(),
                             worker.exitcode, worker.has_msg))

                if worker.retry_times >= WORK_RETRY_TIMES:
                    logger.error('restart worker{} failed, worker{} exit'.format(worker_id, worker_id))
                    worker.status = WORKER_STATUS_TIMEOUT
                    clean_worker(worker.id)
                    continue

                run_time = time.time() - worker.start_time
                if run_time > worker.run_timeout and \
                        worker.retry_times < WORK_RETRY_TIMES and \
                        worker.is_alive():

                    logger.warn('run worker{} timeout, worker{} exit'.format(worker_id, worker_id))

                    logger.warn('worker{} run_time = <{}>, run_timeout = <{}> retry_times = <{}>'.format(
                        worker_id, run_time, worker.run_timeout, worker.retry_times))

                    clean_worker(worker.id, release_res=False)
                    worker.retry_times += 1
                    restart_worker(worker)
                    continue

                if not worker.is_alive() and worker.exitcode is None:
                    logger.warn('failed to start <worker{}>'.format(worker.id))
                    worker.status = WORKER_STATUS_EXIT
                    clean_worker(worker.id)
                    continue

                if worker.is_alive():
                    send_msg_to_work(worker)
                    worker.status = WORKER_STATUS_RUN
                    continue

                if worker.exitcode == 0:
                    worker.status = WORKER_STATUS_DONE
                    logger.info('<worker{}> done'.format(worker.id))
                    clean_worker(worker.id)
                    continue

                if worker.exitcode != 0 and \
                        not worker.is_alive() and \
                        worker.exitcode != -15:
                    logger.info('<worker{}> exit, exitcode <{}>'.format(worker.id, worker.exitcode))

                    if (worker.exitcode is 21 or worker.exitcode is 22) and worker.has_msg:
                        logger.warn('<worker{}> exit,exitcode <{}> but still has message.msg <{}>'.format(
                            worker.id, worker.exitcode, worker.msg))

                        clean_worker(worker.id, release_res=False)
                        worker.retry_times += 1
                        restart_worker(worker)
                        logger.warn('worker still has message restart done.')
                    else:
                        worker.status = WORKER_STATUS_EXIT
                        clean_worker(worker.id)

        except Exception as e:
            logger.error('watch_all_works error: {}'.format(e))
            logger.error(traceback.format_exc())


def check_host_block():
    logger.debug('call check_host_block ...')

    hosts_key_lock = etcd_util.get_etcd_lock('hosts_key_lock', logger)
    if hosts_key_lock is None:
        logger.warn('Failed to get hosts_key_lock from ETCD')
        return

    try:
        host_obj = None
        while True:
            host_obj = host.get_cur_host_from_etcd()
            if host_obj:
                break
            logger.warn('check_host_block get_cur_host_from_etcd() failed')
            time.sleep(3)

        if host_obj.status == host.HOST_STATUS_BLOCK:
            time.sleep(conf.sched_conf.schedule_period_sec)
            all_works = get_all_workers()
            if len(all_works) == 0:
                logger.warn('host <{}> is blocked, scheduler exit'.format(host_obj.name))
                try:
                    # run app-manager cmd to stop scheduler, otherwise
                    # app-manger will restart scheduler when scheduler exit
                    subprocess.call(
                        ['appmgc', 'stop', '-f', '-n', 'scheduler'])
                except Exception as e:
                    logger.error('failed to stop scheduler by app-manger, reason is {}'.format(e))
                os._exit(0)
    except Exception as e:
        logger.error('check_host_block error: {}'.format(e))
        logger.error(traceback.format_exc())
    finally:
        hosts_key_lock.release()


def send_msg_to_work(worker):
    if worker is None or not worker.is_alive():
        return

    queue_obj = worker.decision.queue
    logger.debug('worker is {}'.format(vars(worker)))

    try:
        if not worker.has_msg and worker.is_alive():
            if worker.status != WORKER_STATUS_TIMEOUT:
                logger.debug('worker{} fetch msg from message queue'.format(worker.id))
                msg_json = queue_obj.get_a_msg()
                if msg_json is None:
                    return

                msg = json.loads(msg_json)
                worker.msg_que.put(msg)
                logger.debug('worker{} put msg to msg_que {}'.format(worker.id, msg))
            else:
                msg = worker.msg
                worker.msg_que.put(worker.msg)
                logger.debug('worker{} process old msg when run timeout {}'.format(worker.id, msg))

            defult_timeout = conf.sched_conf.worker_run_timeout
            timeout = msg.get('capture_duration_seconds', defult_timeout)
            worker.run_timeout = timeout * conf.sched_conf.worker_timeout_mulitiple
            worker.has_msg = True
            worker.msg = msg
            logger.debug('send first msg to worker{}'.format(worker.id))

    except Exception as e:
        logger.error('send msg to worker{0} error: {1}'.format(worker.id, e))
        logger.error(traceback.format_exc())


def fetch_sched_decisions():
    logger.debug('fetch_sched_decisions')

    decision_info = None
    deci_key = etcd_util.HOSTS_PATH + host.HOST_NAME + '/decisions'

    client = etcd_util.new_client()
    if client is None:
        logger.warn('fetch_sched_decisions Create new_client failed')
        return None

    dec_lock = etcd_util.get_etcd_lock('decision_lock_' + host.HOST_NAME, logger, client=client)
    if dec_lock is None:
        logger.error('failed to get decision_lock')
        return None

    try:
        decision_info = client.read(deci_key)
        client.delete(deci_key)
    except etcd.EtcdKeyNotFound:
        pass
    except Exception as e:
        logger.error('Read host decisions failed, host<{}>, msg:{}'.format(host.HOST_NAME, e))
    finally:
        dec_lock.release()

    # no decison to read
    if decision_info is None or decision_info.value is None:
        return None

    try:
        decision_str_list = json.loads(decision_info.value)
    except Exception:
        logger.error('bad schedule decision: {}'.format(decision_info.value))
        return None

    decisions = []
    for dec_str in decision_str_list:
        dec_dict = json.loads(dec_str)
        dc = scheduler.SchedDecision()
        dc.__dict__.update(dec_dict)
        que_dict = dc.queue
        dc.queue = queue_conf.Queue()
        dc.queue.__dict__.update(que_dict)
        decisions.append(dc)
        logger.debug('hostname = {} id = {} gpus = {}'.format(dc.hostname, dc.id, dc.alloc_gpu_ids))

    return decisions


def new_worker(decision, gpu_id, worker_id=None):
    queue_name = decision.queue.name
    worker = None
    try:
        logger_index = get_worker_logger_idx()
        worker = Worker(worker_id, logger_index)
        worker.decision = decision
        worker.decision.alloc_workers = 1
        worker_name = queue_name + '_worker' + str(worker.id)
        worker.name = worker_name
        worker.gpu_id = gpu_id
        logger.info('new worker: <{}> alloc GPU <{}>'.format(
            worker.name,
            gpu_id))

        return worker
    except Exception as e:
        free_worker_logger_idx(worker)
        worker_release(worker)
        logger.error('new_worker error: {}'.format(e))
        logger.error(traceback.format_exc())


def restart_worker(worker):
    logger.debug('restart worker{} ...'.format(worker.id))
    decision = worker.decision
    new_wk = new_worker(decision, worker.gpu_id, worker.id)
    if new_wk is None:
        logger.error('failed to create new worker by decision{}'.
                     format(decision.id))

        w = Worker()
        w.decision = decision
        host.release_host_res(w)
        return

    new_wk.retry_times += worker.retry_times
    new_wk.msg = worker.msg
    new_wk.status = WORKER_STATUS_TIMEOUT

    run_work_thread = threading.Thread(
        target=run_worker,
        args=(new_wk, True,),
        name='run_work_thread')
    run_work_thread.daemon = True
    run_work_thread.start()


def run_worker(worker, is_restart=False):
    logger.debug('call run_worker')
    logger.info('worker is {}'.format(vars(worker)))

    # if message queue have not msg, release host res and return
    if not is_restart:
        queue_obj = worker.decision.queue
        total_pend_msg = queue_obj.get_pending_msg_number()
        if total_pend_msg == 0:
            logger.debug(
                'worker{} have not msg, release host res'.format(worker.id))
            free_worker_logger_idx(worker)
            host.release_host_res(worker)
            return

    worker.start_time = time.time()
    worker.msg_que = multiprocessing.Queue()
    worker.msg_status_que = multiprocessing.Queue()

    worker.start()

    logger.debug('run <{0}> <worker{1}> ... '.format(worker.decision.queue.name, worker.id))
    add_work_to_dict(worker)
    worker.join()


def start_worker(decision):
    logger.info('call start_worker')
    logger.info('parameter decision is {}'.format(vars(decision)))

    total_works = decision.alloc_workers
    logger.info('total_works is {}'.format(total_works))

    for i in xrange(total_works):
        gpu_id = decision.alloc_gpu_ids[i]
        worker = new_worker(decision, gpu_id)
        if worker is None:
            logger.error('failed to create new worker by decision{}'.format(decision.id))

            w = Worker()
            w.decision = decision
            host.release_host_res(w)
            return

        worker.status = WORKER_STATUS_RUN

        run_work_thread = threading.Thread(target=run_worker, args=(worker,), name='run_work_thread')
        run_work_thread.daemon = True
        run_work_thread.start()


def launcher():
    logger.debug('call worker.launcher ...')

    init_worker_logger()

    watch_work_thread = threading.Thread(target=watch_all_works, name='watch_work_thread')
    watch_work_thread.daemon = True
    watch_work_thread.start()

    logger.debug('start worker launcher')
    schedule_period_sec = conf.sched_conf.schedule_period_sec
    logger.debug('schedule_period_sec is {}'.format(schedule_period_sec))

    while True:
        try:
            decisions = fetch_sched_decisions()
            if decisions is not None:
                for decision in decisions:
                    start_worker(decision)

            time.sleep(schedule_period_sec)
        except Exception as e:
            logger.error("launcher find except, msg: %s, exit" % (str(e)))
            break


def init_worker_logger():
    # cur_host = host.get_cur_host_from_etcd()
    # logger.debug('cur_host is {}'.format(cur_host))

    min_gpu_cost = queue_conf.get_min_gpu_cost()
    logger.debug('min_gpu_cost is {}'.format(min_gpu_cost))

    global g_worker_log_idx
    # logger_index = int(cur_host.total_gpus / min_gpu_cost) + 1
    logger_index = int(host.TOTAL_GPUS / min_gpu_cost) + 1
    for idx in range(logger_index):
        g_worker_log_idx[idx] = False


def get_worker_logger_idx():
    global g_worker_log_idx
    for idx, used in g_worker_log_idx.items():
        if not used:
            g_worker_log_idx[idx] = True
            return idx

    g_worker_log_idx[idx + 1] = True
    return idx + 1


def free_worker_logger_idx(worker):
    global g_worker_log_idx
    g_worker_log_idx[worker.logger_index] = False
