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
import time
import etcd
import socket
import urlparse

from log import reports_to_etcd_logger as logger
import conf

HOST_NAME = socket.gethostname()

ALGO_ARGS_PATH = '/db/vm_algo_parameter'
CAMERA_ARGS_PATH = '/db/vm_camera'
ETCD_ROOT = '/db/deepnorth/'

SCHEDULER_PATH = ETCD_ROOT + 'scheduler/'
HOSTS_PATH = SCHEDULER_PATH + 'hosts/'
MASTER_PATH = SCHEDULER_PATH + 'master'

# for reports
HOST_STATISTICS_PATH = SCHEDULER_PATH + 'statistics/hosts/'
ALGO_STATISTICS_PATH = SCHEDULER_PATH + 'statistics/algorithms/'
ALLOCATION_PATH = SCHEDULER_PATH + 'allocation/'
HOST_THROUGHPUT_PATH = SCHEDULER_PATH + 'throughput/hosts/'
ALGO_THROUGHPUT_PATH = SCHEDULER_PATH + 'throughput/algorithms/'

ETCD_LOCK_TTL = 3


def create_dir(dir_name, retry_times=3, client=None):
    for i in range(retry_times):
        if client is None:
            client = new_client()
        if client is None:
            logger.error('Failed to create_dir, dir_name<{}>'.format(dir_name))
            time.sleep(1)
            continue

        try:
            client.write(dir_name, None, dir=True)
            break
        except (etcd.EtcdAlreadyExist, etcd.EtcdNotFile):
            break
        except Exception as e:
            logger.error('Failed to create dir in etcd, dir_name=<{}> error = <{}>'.format(dir_name, e))
            time.sleep(1)


def write_ext(key, value, retry_times=3, client=None):
    for i in range(retry_times):
        if client is None:
            client = new_client()
        if client is None:
            logger.error('Failed to write_ext, key<{}> value<{}>'.format(key, value))
            time.sleep(1)
            continue

        try:
            client.write(key, value)
            break
        except Exception as e:
            logger.error('failed to write etcd, key = <{}> value = <{}> error = <{}>'.format(key, value, e))
            time.sleep(1)


def read_ext(key, client=None):
    if client is None:
        client = new_client()
    if client is None:
        logger.error('Failed to read_ext, connect ETCD failed')
        return None

    try:
        value = client.read(key)
        return value
    except Exception as e:
        logger.error('failed to read etcd, key = <{}> error = <{}>'.format(key, e))
        return None


def init():
    logger.debug("etcd init ...")
    logger.debug("etcd server is <{}>".format(conf.sched_conf.etcd_urls))

    init_path_list = [
        ETCD_ROOT,
        HOSTS_PATH,
        HOST_STATISTICS_PATH + HOST_NAME,
        ALGO_STATISTICS_PATH,
        ALLOCATION_PATH,
        HOST_THROUGHPUT_PATH,
        ALGO_THROUGHPUT_PATH
    ]

    for path in init_path_list:
        create_dir(path)
        logger.debug("create etcd dir is {}".format(path))


def update_master_ttl():
    hostname = socket.gethostname()

    logger.debug('update_master_ttl new_client ')
    client = new_client()
    if client is None:
        logger.error('update_master_ttl failed, connect ETCD failed')
        return None

    HOST_INFO_TTL = conf.sched_conf.host_info_ttl

    try:
        client.test_and_set(MASTER_PATH, hostname, hostname, HOST_INFO_TTL)
    except etcd.EtcdKeyNotFound:
        client.write(MASTER_PATH, hostname, HOST_INFO_TTL, prevExist=False)
    except ValueError as ve:
        hostname = ve.message.split()[-1][:-1]
    except etcd.EtcdConnectionFailed:
        logger.error('failed to connect etcd server <{}:{}>'.format(
            conf.sched_conf.etcd_host, conf.sched_conf.etcd_port))
        # sys.exit(-1)
        return None

    logger.info("master is <{}>, HOST_INFO_TTL is <{}>".format(MASTER_PATH + hostname, HOST_INFO_TTL))
    return hostname


def delete_host_info(prevValue, retry_times=10):
    client = None
    for i in range(retry_times):
        if client is None:
            client = new_client()
        if client is None:
            time.sleep(ETCD_LOCK_TTL)
            continue

        try:
            hostname = socket.gethostname()
            client.delete(MASTER_PATH, prevValue=prevValue)
            client.delete(HOSTS_PATH + hostname + '/host_data', prevValue=prevValue)
            logger.info("delete host is <{}>".format(HOSTS_PATH + hostname + '/host_data'))
            break
        except Exception as e:
            logger.warn("Delete host from ETCD failed, prevValue<{}>, msg: {}".format(prevValue, e))


def get_etcd_lock(lock_name, logger, retry_times=10, timeout=10, client=None):
    for i in range(retry_times):
        if client is None:
            client = new_client()
        if client is None:
            logger.error('Failed to get etcd lock<{}>, retry'.format(lock_name))
            time.sleep(ETCD_LOCK_TTL)
            continue

        logger.debug('start get etcd lock <{}>'.format(lock_name))
        etcd_lock = etcd.Lock(client, lock_name)
        try:
            # etcd_lock.acquire(blocking=True, lock_ttl=ETCD_LOCK_TTL)
            etcd_lock.acquire(blocking=True, lock_ttl=ETCD_LOCK_TTL, timeout=timeout)
        except Exception as e:
            logger.warn('failed to get etcd lock <{}>, retry, msg: {}'.format(lock_name, e))
            time.sleep(ETCD_LOCK_TTL)
            gc.collect()
            # logger.debug('run garbage collection at get_etcd_lock')

        if etcd_lock.is_acquired:
            logger.debug('get etcd lock <{}> ok'.format(lock_name))
            return etcd_lock
    return None


def new_client(retry_times=60, caller='func', logger=logger):
    client = None
    for i in range(retry_times):
        try:
            url_list = conf.sched_conf.etcd_urls.split(',')
            host_list = []
            for item in url_list:
                url = urlparse.urlparse(item)
                host = (str(url.hostname), url.port)
                host_list.append(host)

            hosts = tuple(host_list)
            client = etcd.Client(hosts, read_timeout=60, allow_reconnect=True)

        except Exception as e:
            logger.error('new etcd client error: {}'.format(e))

        if client:
            break

        logger.error('failed to new etcd client, retry {} times'.format(i))
        time.sleep(1)

        if i % 3 == 0:
            logger.debug('run garbage collection at new_client')
            gc.collect()

    if client:
        logger.debug('{}: get etcd client'.format(caller))
    return client
