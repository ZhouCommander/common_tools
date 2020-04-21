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

import time
import socket
import threading
import traceback

import conf
import etcd_util
import queue_conf
import worker as workermodule
# from log import worker_logger as logger
from log import reports_to_etcd_logger as logger

algo_statis = {}
host_statis = {}
algo_alloc = {}
host_throughput = []
algo_throughput = {}


def init(host):
    logger.debug('call reports.init ...')
    init_host_statistics(host.total_gpus)
    init_algo_statistics()
    init_allocation(algo_statis)
    init_algo_throughput()


def init_algo_statistics():
    hostname = socket.gethostname()
    queues = queue_conf.QueueConf()
    queue_list = queues.get_queue_list()
    for queue in queue_list:
        pending_msg_number = queue.get_pending_msg_number()
        algo_statis[queue.name] = {
            'pending': pending_msg_number,
            'error': 0,
            'finished': 0,
        }

        dir_name = etcd_util.ALGO_STATISTICS_PATH + queue.name + '/' + hostname
        etcd_util.create_dir(dir_name)

    return algo_statis


def init_algo_throughput():
    queues = queue_conf.QueueConf()
    queue_list = queues.get_queue_list()
    for queue in queue_list:
        algo_throughput[queue.name] = []


def init_host_statistics(total_gpus):
    host_statis['hostname'] = socket.gethostname()
    for gpu_id in range(total_gpus):
        host_statis['gpu_' + str(gpu_id)] = {
            'running': 0,
            'error': 0,
            'finished': 0,
        }
    return host_statis


def init_allocation(algo_statis):
    hostname = socket.gethostname()
    for queue_name in algo_statis:
        algo_alloc[queue_name] = {hostname: {'running': 0}}

        dir_name = etcd_util.ALLOCATION_PATH + queue_name + '/' + hostname
        etcd_util.create_dir(dir_name)


def reset_running_statistics():
    for key in host_statis:
        if key == 'hostname':
            continue
        host_statis[key]['running'] = 0


def reset_running_allocation():
    for queue_name in algo_alloc:
        for hostname in algo_alloc[queue_name]:
            algo_alloc[queue_name][hostname]['running'] = 0


def increase_running(worker):
    host_statis['gpu_' + str(worker.gpu_id)]['running'] += 1


def update_algo_statistics_cnt(worker):

    queue_list = None
    queues = queue_conf.QueueConf()

    if queues:
        queue_list = queues.get_queue_list()

    if queues and queue_list:
        for queue in queue_list:
            pending_msg_number = queue.get_pending_msg_number()
            if queue.name not in algo_statis:
                algo_statis[queue.name] = {
                    'pending': pending_msg_number,
                    'error': 0,
                    'finished': 0,
                }

            else:
                algo_statis[queue.name]['pending'] = pending_msg_number

    if algo_statis and worker:
        logger.debug('worker id is {}'.format(worker.id))
        queue_name = worker.decision.queue.name
        if worker.status == workermodule.WORKER_STATUS_DONE:
            algo_statis[queue_name]['finished'] += 1
            host_statis['gpu_' + str(worker.gpu_id)]['finished'] += 1

        elif worker.status == workermodule.WORKER_STATUS_RUN:
            host_statis['gpu_' + str(worker.gpu_id)]['running'] += 1

        else:
            algo_statis[queue_name]['error'] += 1
            host_statis['gpu_' + str(worker.gpu_id)]['error'] += 1


def update_algo_alloc_cnt(worker):
    queue_name = worker.decision.queue.name
    hostname = worker.decision.hostname
    logger.debug('queue_name is {}'.format(queue_name))
    logger.debug('hostname is {}'.format(hostname))

    if queue_name not in algo_alloc:
        algo_alloc[queue_name] = {hostname: {'running': 0}}
        dir_name = etcd_util.ALLOCATION_PATH + queue_name + '/' + hostname
        etcd_util.create_dir(dir_name)

    if hostname in algo_alloc[queue_name]:
        algo_alloc[queue_name][hostname]['running'] += 1


def get_total_finished(host_statis):
    total_finished = 0
    for key, value in host_statis.items():
        if key == 'hostname':
            continue

        total_finished += value['finished']

    return total_finished


# throughput
"""    ____________________
      |                    |
[2, 3,|3, 2, 4, 5, 6, 7, 3,|2, 1, 4]
      |____________________|
"""


def update_host_throughput(host_statis):
    last_total_finished = 0
    while True:
        logger.debug('call update_host_throughput ...')
        logger.debug('parameter host_statis is {}'.format(host_statis))
        total_finished = get_total_finished(host_statis)
        if total_finished == 0:
            time.sleep(1)
            continue

        diff = total_finished - last_total_finished
        if diff > 0:
            host_throughput.insert(0, diff)
        else:
            host_throughput.insert(0, 0)

        last_total_finished = total_finished
        throughput_size = conf.sched_conf.throughput_interval_sec
        if len(host_throughput) == throughput_size + 1:
            host_throughput.pop()

        time.sleep(1)


def update_algo_throughput(algo_statis):

    algo_last_finished = {}
    for queue_name in algo_statis:
        algo_last_finished[queue_name] = 0

    while True:
        logger.debug('call update_algo_throughput ...')
        logger.debug('parameter algo_statis is {}'.format(algo_statis))

        for queue_name in algo_statis:
            total_finished = algo_statis[queue_name]['finished']
            if total_finished != 0:
                diff = total_finished - algo_last_finished[queue_name]
                if diff > 0:
                    algo_throughput[queue_name].insert(0, diff)
                else:
                    algo_throughput[queue_name].insert(0, 0)

            algo_last_finished[queue_name] = total_finished
            throughput_size = conf.sched_conf.throughput_interval_sec
            if len(algo_throughput[queue_name]) == throughput_size + 1:
                algo_throughput[queue_name].pop()

        time.sleep(1)


def update_reports_to_etcd():
    logger.debug('call update_reports_to_etcd ...')

    host_throughput_thread = threading.Thread(target=update_host_throughput,
                                              args=(host_statis,),
                                              name='update_host_throughput')
    host_throughput_thread.daemon = True
    host_throughput_thread.start()

    algo_throughput_thread = threading.Thread(target=update_algo_throughput,
                                              args=(algo_statis,),
                                              name='update_algo_throughput')
    algo_throughput_thread.daemon = True
    algo_throughput_thread.start()

    while True:
        time.sleep(conf.sched_conf.reports_upload_period_sec)
        # for update queue pending msg number
        update_algo_statistics_cnt(None)

        logger.debug('call update_reports ...')
        try:
            update_host_statis_to_etcd(host_statis)
            update_algo_statis_to_etcd(algo_statis)
            update_algo_alloc_to_etcd(algo_alloc)
            update_host_throughput_to_etcd(host_throughput)
            update_algo_throughput_to_etcd(algo_throughput)

        except Exception as e:
            logger.error('update report to etcd error: <{}>'.format(e))
            logger.error(traceback.format_exc())


def update_host_statis_to_etcd(host_statis):
    logger.debug('call update_host_statis_to_etcd ...')
    logger.debug('parameter host_statis is {}'.format(host_statis))

    hostname = host_statis.get('hostname')
    if hostname is None:
        return

    for key, value in host_statis.items():
        if key == 'hostname':
            continue

        gpu_idx = key[-1]
        key = etcd_util.HOST_STATISTICS_PATH + hostname + '/' + gpu_idx + '/'
        etcd_util.create_dir(key)

        for status, cnt in value.items():
            etcd_util.write_ext(key + status, cnt)
            logger.info('write to etcd, key is {}, value is {}'.format(key + status, cnt))


def update_host_throughput_to_etcd(host_throughput):
    logger.debug('call update_host_throughput_to_etcd ...')

    key = etcd_util.HOST_THROUGHPUT_PATH + socket.gethostname()
    etcd_util.write_ext(key, sum(host_throughput))
    logger.info('write to etcd, key is {}, value is {}'.format(key, sum(host_throughput)))


def update_algo_throughput_to_etcd(algo_throughput):
    logger.debug('call update_algo_throughput_to_etcd ...')
    logger.debug('parameter algo_throughput is {}'.format(algo_throughput))

    for queue_name, throughput in algo_throughput.items():
        key = etcd_util.ALGO_THROUGHPUT_PATH + queue_name + '/' \
            + socket.gethostname()

        etcd_util.write_ext(key, sum(throughput))
        logger.info('write to etcd, key is {}, value is {}'.format(key, sum(throughput)))


def update_algo_alloc_to_etcd(algo_alloc):
    logger.debug('call update_algo_alloc_to_etcd ...')
    logger.debug('parameter algo_alloc is {}'.format(algo_alloc))

    hostname = socket.gethostname()
    for queue_name, alloc_value in algo_alloc.items():
        key = etcd_util.ALLOCATION_PATH + queue_name + '/' + hostname \
            + '/' + 'workers'
        value = alloc_value[hostname]['running']
        etcd_util.write_ext(key, value)
        logger.info('write to etcd, key is {}, value is {}'.format(key, value))


def update_algo_statis_to_etcd(algo_statis):
    logger.debug('call update_algo_statis_to_etcd ...')
    logger.debug('parameter algo_statis is {}'.format(algo_statis))

    hostname = socket.gethostname()
    for queue_name, value in algo_statis.items():
        for status, cnt in value.items():
            key = etcd_util.ALGO_STATISTICS_PATH + queue_name + '/' + \
                hostname + '/' + status
            etcd_util.write_ext(key, cnt)
            logger.info('write to etcd, key is {}, value is {}'.format(key, cnt))