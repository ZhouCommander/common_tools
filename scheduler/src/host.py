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

import os
import json
import time
import etcd
import GPUtil
import socket
import psutil
import traceback

import conf
import etcd_util
from log import worker_logger as logger
from log import update_host_status_logger as host_status_logger


DATA_UNIT_MB = 1024 * 1024


HOST_STATUS_OK = 0
HOST_STATUS_BUSY = 1
HOST_STATUS_UNAVAIL = 2
HOST_STATUS_BLOCK = 3


HOST_NAME = socket.gethostname()
TOTAL_GPUS = 1


class GPU:
    def __init__(self, gpu_id):
        self.id = gpu_id
        self.total = 1
        self.used = 0
        self.free = self.total


class Host:
    def __init__(self):
        self.name = HOST_NAME
        self.status = HOST_STATUS_OK

        self.total_gpus = 0
        self.total_cpu_cores = 0
        self.total_mem = 0

        self.used_gpus = 0
        self.used_cpu_cores = 0
        self.used_mem = 0

        self.free_gpus = self.total_gpus
        self.free_cpu_cores = self.total_cpu_cores
        self.free_mem = self.total_mem

        self.gpu_list = []

    def to_json(self):
        gpus = []
        for idx, gpu in enumerate(self.gpu_list):
            gpus.append(gpu.__dict__)
        self.gpu_list = gpus

        return json.dumps(self.__dict__, sort_keys=True, indent=4)

    def json_to_obj(self, host_json):
        host_dict = json.loads(host_json)
        self.__dict__.update(host_dict)
        gpu_list = []
        for idx, gpu_dict in enumerate(self.gpu_list):
            gpu = GPU(idx)
            gpu.__dict__.update(gpu_dict)
            gpu_list.append(gpu)
        self.gpu_list = gpu_list

        return self

    def display(self, logger, worker):
        logger.debug('{}-worker{}: free_gpus = {} free_cpu_cores = {} free_mem = {}'.format(
            self.name,
            worker.id,
            self.free_gpus,
            self.free_cpu_cores,
            self.free_mem))

    def calc_gpu_usage(self):
        logger.info('calc_gpu_usage')
        free_gpus = 0
        for gpu in self.gpu_list:
            free_gpus += gpu.free

        self.free_gpus = free_gpus
        self.used_gpus = self.total_gpus - free_gpus
        logger.info('total_gpus is {}, used_gpus {}, free_gpus {}'.format(self.total_gpus, self.used_gpus, free_gpus))

    def set_status(self, status):
        self.status = status

    def get_status_str(self):
        if self.status == HOST_STATUS_OK:
            return 'ok'

        if self.status == HOST_STATUS_BUSY:
            return 'busy'

        if self.status == HOST_STATUS_UNAVAIL:
            return 'unavail'

        if self.status == HOST_STATUS_BLOCK:
            return 'block'

        return 'unknown'


def collect_host_static_info(total_gpus=None):
    host = Host()
    host.total_mem = psutil.virtual_memory().total / DATA_UNIT_MB
    host.total_cpu_cores = psutil.cpu_count()

    logger.debug('init total_gpus = {}'.format(total_gpus))
    logger.debug('host.total_mem = {}'.format(host.total_mem))
    logger.debug('host.total_cpu_cores = {}'.format(host.total_cpu_cores))

    if total_gpus:
        for gpu_id in range(total_gpus):
            new_gpu = GPU(gpu_id)
            host.gpu_list.append(new_gpu)
        host.total_gpus = total_gpus
    else:
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                new_gpu = GPU(gpu.id)
                host.gpu_list.append(new_gpu)
            host.total_gpus = len(host.gpu_list)
        except OSError:
            logger.error('failed to collect host <{}> gpu info'.format(host.name))

    global TOTAL_GPUS
    TOTAL_GPUS = host.total_gpus

    logger.debug('host.total_gpus = {}'.format(host.total_gpus))
    host.free_mem = host.total_mem - host.used_mem
    host.free_cpu_cores = host.total_cpu_cores - host.used_cpu_cores
    host.calc_gpu_usage()

    logger.debug('host.free_mem = {}'.format(host.free_mem))
    logger.debug('host.free_cpu_cores = {}'.format(host.free_cpu_cores))
    logger.debug('host total_mem = {}'.format(host.total_mem))

    host_info = host.to_json()
    client = etcd_util.new_client()
    try:
        client.write(etcd_util.HOSTS_PATH + host.name, None, dir=True, ttl=conf.sched_conf.host_info_ttl)

    except (etcd.EtcdAlreadyExist, etcd.EtcdNotFile):
        pass

    client.write(etcd_util.HOSTS_PATH + host.name + '/host_data', host_info)

    logger.info('write to etcd, key<{}>, value<{}>'.format(etcd_util.HOSTS_PATH + host.name + '/host_data', host_info))
    return host


def update_host_status(gpus):
    host_status_logger.debug('call update_host_status')
    host_key = etcd_util.HOSTS_PATH + HOST_NAME

    while True:
        host_info_ttl = conf.sched_conf.host_info_ttl
        try:
            host_status_logger.debug('start update host <{}> status'.format(HOST_NAME))
            client = etcd_util.new_client(caller='update_host_status')
            client.write(host_key, None, dir=True, ttl=host_info_ttl)
            if etcd_util.read_ext(host_key + '/host_data') is None:
                collect_host_static_info(gpus)
        except etcd.EtcdNotFile:
            try:
                client.write(host_key, None, dir=True, ttl=host_info_ttl, prevExist=True, refresh=True)
            except Exception as e:
                host_status_logger.error('update host <{}> status error: <{}>'.format(HOST_NAME, e))
                host_status_logger.error(traceback.format_exc())
                time.sleep(3)
                continue
        except Exception as e:
            host_status_logger.error('update host <{}> status error: <{}>'.format(HOST_NAME, e))
            host_status_logger.error(traceback.format_exc())
            # os._exit(-1)
            time.sleep(3)
            continue

        host_status_logger.debug('etcd_util.update_master_ttl() start')

        try:
            etcd_util.update_master_ttl()
        except Exception as e:
            host_status_logger.error('update_master_ttl error: <{}>'.format(e))

        host_status_logger.info('update_master_ttl() done, host<{}>, ttl<{}>'.format(host_key, host_info_ttl))
        time.sleep(3)


def get_cur_host_from_etcd(client=None, logger=logger):
    if client is None:
        client = etcd_util.new_client()
    try:
        host_key = etcd_util.HOSTS_PATH + HOST_NAME + '/host_data'
        host_json = client.read(host_key)
        cur_host_json = Host().json_to_obj(host_json.value)

        logger.info("get cur_host_json from etcd is {}, path<{}>".format(cur_host_json, host_key))
        return cur_host_json

    except Exception as e:
        logger.error('failed to get current host from etcd: {}'.format(e))
        logger.error(traceback.format_exc())
        return None


def get_all_hosts_from_etcd(client=None, logger=logger):
    if client is None:
        client = etcd_util.new_client()

    host_list = []
    try:
        hosts_info = client.read(etcd_util.HOSTS_PATH, recursive=True)
        for host_json in hosts_info.children:
            # filter decision key
            _, key = os.path.split(host_json.key)
            if key == 'host_data':
                host_list.append(Host().json_to_obj(host_json.value))
    except Exception as e:
        logger.error('failed to get all hosts from etcd: {}'.format(e))
        logger.error(traceback.format_exc())

    if len(host_list) == 0:
        logger.error('failed to get all hosts data from etcd')

    logger.info("get all_hosts_json from etcd is {}".format(host_list))
    return host_list


def release_host_res(worker, retry_times=10):
    client = etcd_util.new_client()
    decision = worker.decision
    logger.debug('worker{} start release host <{}> resource ... '.format(worker.id, HOST_NAME))

    hosts_key_lock = etcd_util.get_etcd_lock('hosts_key_lock', logger)
    if hosts_key_lock is None:
        logger.error('Failed to get hosts_key_lock from ETCD, forced continue')

    try:
        for i in range(retry_times):
            cur_host = get_cur_host_from_etcd()
            if cur_host is None:
                logger.error('failed to get current host, exit')
                # sys.exit(-1)
                time.sleep(3)
                continue

            cur_host.display(logger, worker)
            cur_host = update_host_by_decision(cur_host, decision, increase=False)
            host_json = cur_host.to_json()
            host_key = etcd_util.HOSTS_PATH + cur_host.name + '/host_data'
            client.write(host_key, host_json)
            logger.info('write to etcd, host_key is {}, value is {}'.format(host_key, host_json))

            # to check host update info
            cur_host = get_cur_host_from_etcd()
            cur_host.display(logger, worker)
            break

    except Exception as e:
        logger.error('release_host_res error: {}'.format(e))
        logger.error(traceback.format_exc())

    finally:
        if hosts_key_lock:
            hosts_key_lock.release()

    logger.debug('worker{} release host <{}> resource done'.format(worker.id, HOST_NAME))


def update_all_hosts_to_etcd(decisions):
    client = etcd_util.new_client()
    logger.debug('start update all hosts resource to etcd ...')
    hosts_key_lock = etcd_util.get_etcd_lock('hosts_key_lock', logger)
    if hosts_key_lock is None:
        logger.warn('Failed to get hosts_key_lock from ETCD')
        return

    try:
        host_list = get_all_hosts_from_etcd()
        for decision in decisions:
            for host in host_list:
                if decision.hostname == host.name:
                    update_host_by_decision(host, decision)

        for host in host_list:
            host_json = host.to_json()
            host_key = etcd_util.HOSTS_PATH + host.name + '/host_data'
            client.write(host_key, host_json)

            logger.info('write to etcd, host_key is {}, value is {}'.format(host_key, host_json))

    except Exception as e:
        logger.error('update_all_hosts_to_etcd error: {}'.format(e))
        logger.error(traceback.format_exc())

    finally:
        hosts_key_lock.release()

    logger.debug('update all hosts resource to etcd done')


def update_host_by_decision(host, decision, increase=True):
    logger.info('host{}: used_mem= {} used_cpu= {} used_gpus= {} increase= {}'.format(
        host.name, host.used_mem, host.used_cpu_cores, host.used_gpus, increase))

    increase_flag = 1
    if not increase:
        increase_flag = -1

    que = decision.queue
    works = decision.alloc_workers
    logger.info('works is {}'.format(works))

    host.used_cpu_cores += que.cpu_cores * works * increase_flag
    host.used_mem += que.mem * works * increase_flag

    host.free_mem = host.total_mem - host.used_mem
    host.free_cpu_cores = host.total_cpu_cores - host.used_cpu_cores

    logger.info('decision.alloc_gpu_ids is {}'.format(decision.alloc_gpu_ids))
    logger.info('host.gpu_list is {}'.format(host.gpu_list))

    for gpu_id in decision.alloc_gpu_ids:
        for gpu in host.gpu_list:
            if gpu.id == gpu_id:
                gpu.used += que.gpu * increase_flag
                gpu.free = gpu.total - gpu.used

                if gpu.used < 0.0:
                    logger.warn('update_host_by_decision find gpu<{}>.used= {}, change to 0'.format(gpu_id, gpu.used))
                    gpu.used = 0.0
                if gpu.used > 1.0:
                    logger.warn('update_host_by_decision find gpu<{}>.used= {}, change to 1'.format(gpu_id, gpu.used))
                    gpu.used = 1.0
                if gpu.free < 0.0:
                    logger.warn('update_host_by_decision find gpu<{}>.free= {}, change to 0'.format(gpu_id, gpu.free))
                    gpu.free = 0.0
                if gpu.free > 1.0:
                    logger.warn('update_host_by_decision find gpu<{}>.free= {}, change to 1'.format(gpu_id, gpu.free))
                    gpu.free = 1.0

                logger.info('gpu<{}>.used is {}, free is {}'.format(gpu_id, gpu.used, gpu.free))
                # if gpu.free < 0:
                #     logger.error('gpu.free is less than 0')

    host.calc_gpu_usage()

    logger.info('host{}: used_mem= {} used_cpu= {} used_gpus= {}'.format(
        host.name, host.used_mem, host.used_cpu_cores, host.used_gpus))
    return host


def print_host_list(host_list, msg='host list', is_detailed=True):
    logger.debug('======{}======'.format(msg))
    import copy
    new_host_list = copy.deepcopy(host_list)
    for h in new_host_list:
        if is_detailed:
            logger.debug('{}：{}'.format(h.name, h.to_json()))
        else:
            logger.debug('{}'.format(h.name))
    del new_host_list
