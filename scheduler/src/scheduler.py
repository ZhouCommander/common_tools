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

import copy
import json
import etcd
import traceback
import time

import etcd_util
import queue_conf
import host as host_module
from log import scheduler_logger as logger


g_decision_id = 0


def get_decision_id():
    global g_decision_id
    g_decision_id = g_decision_id + 1
    return g_decision_id


class SchedDecision:
    def __init__(self, hostname=None):
        self.id = None
        self.hostname = hostname
        self.queue = None
        self.alloc_workers = 0
        self.alloc_gpu_ids = []


def calc_sched_decision():
    logger.debug('==============calc_sched_decision==============')
    queues = queue_conf.QueueConf()
    all_queues = queues.get_queue_list()

    if len(all_queues) == 0:
        logger.info('all_queues number is 0')
        return

    hosts_key_lock = etcd_util.get_etcd_lock('hosts_key_lock', logger)
    if hosts_key_lock is None:
        logger.warn('Failed to get hosts_key_lock from ETCD')
        return

    try:
        host_list = host_module.get_all_hosts_from_etcd()

    except Exception as e:
        logger.error('failed to get all hosts from etcd when '
                     'calc_sched_decision, error: {}'.format(e))
    finally:
        hosts_key_lock.release()

    if len(host_list) == 0:
        logger.error('failed to get host info')
        return

    host_module.print_host_list(host_list, 'start calc_sched_decision')

    # if queue have no message, remove it
    queue_list = []
    for queue in all_queues:
        queue.get_pending_msg_number()
        if queue.pending_msg_num > 0:
            queue_list.append(queue)
        else:
            # logger.warn('queue <{}> have no msg, ignore'.format(queue.name))
            pass

    queue_list.sort(key=lambda queue: (queue.priority, queue.pending_msg_num), reverse=True)

    logger.info("**********queue list sorted result**********")
    for queue in queue_list:
        logger.info("queue_name: <{}> priority: <{}> penging_msg_num: <{}>".format(
            queue.name, queue.priority, queue.pending_msg_num))

    queues.print_queue_list()

    host_list.sort(key=lambda host: (
        host.free_gpus, host.free_cpu_cores, host.free_mem), reverse=True)

    decision_dict = {}
    decisions = []

    # logger.info('before decision --- queue_list is {}'.format(queue_list))
    # logger.info('before decision --- host_list is {}'.format(host_list))

    for que in queue_list:
        logger.info('que is {}'.format(vars(que)))
        satisfied_hosts = []
        for idx, host_info in enumerate(host_list):
            if is_satisfied_host(host_info, que):
                satisfied_hosts.append(host_info)

        total_satisfied_hosts = len(satisfied_hosts)
        if total_satisfied_hosts == 0:
            logger.info('no satisfied host for queue <{}>'.format(que.name))
            continue

        if que.static_worker <= total_satisfied_hosts:
            if que.static_worker == 1:
                hostname = satisfied_hosts[0].name
                sched_dec = SchedDecision(hostname)
                sched_dec.id = get_decision_id()
                sched_dec.alloc_workers = 1
                sched_dec.queue = que
                alloc_gpu_ids = alloc_host_gpus(satisfied_hosts[0], que)
                sched_dec.alloc_gpu_ids = alloc_gpu_ids
                update_host_list(satisfied_hosts[0], sched_dec)
                add_sched_decision(decision_dict, sched_dec)
                decisions.append(sched_dec)
            else:
                for idx in xrange(que.static_worker):
                    sched_dec = SchedDecision(satisfied_hosts[idx].name)
                    sched_dec.id = get_decision_id()
                    sched_dec.alloc_workers = 1
                    sched_dec.queue = que
                    alloc_gpu_ids = alloc_host_gpus(satisfied_hosts[idx], que)
                    sched_dec.alloc_gpu_ids = alloc_gpu_ids
                    update_host_list(satisfied_hosts[idx], sched_dec)
                    add_sched_decision(decision_dict, sched_dec)
                    decisions.append(sched_dec)
        else:
            works_per_host = que.static_worker / total_satisfied_hosts
            remainder = que.static_worker % total_satisfied_hosts
            decision_list = []
            for idx, satisfied_host in enumerate(satisfied_hosts):
                dec = SchedDecision(satisfied_host.name)
                dec.id = get_decision_id()
                dec.alloc_workers = works_per_host
                dec.queue = que
                decision_list.append(dec)

            # works = 6 hosts = 3 -> 2 2 2 works/per host
            # works = 5 hosts = 3 -> 2 2 1 works/per host
            if remainder != 0:
                for idx in xrange(que.static_worker - total_satisfied_hosts * works_per_host):
                    decision_list[idx].alloc_workers += 1

            for idx, deci in enumerate(decision_list):
                satisfied_host = get_host_from_list(satisfied_hosts, deci.hostname)
                if satisfied_host:
                    if is_satisfied_host(satisfied_host, que, deci.alloc_workers):
                        alloc_gpu_ids = alloc_host_gpus(satisfied_host, que, deci.alloc_workers)
                        for i in xrange(len(alloc_gpu_ids)):
                            new_deci = copy.deepcopy(deci)
                            new_deci.alloc_gpu_ids = [alloc_gpu_ids[i]]
                            new_deci.alloc_workers = 1
                            update_host_list(satisfied_host, new_deci)
                            add_sched_decision(decision_dict, new_deci)
                            decisions.append(new_deci)
                    else:
                        decision_list[idx].alloc_workers = 1
                        alloc_gpu_ids = alloc_host_gpus(satisfied_host, que)
                        decision_list[idx].alloc_gpu_ids = alloc_gpu_ids
                        update_host_list(satisfied_host, decision_list[idx])
                        add_sched_decision(decision_dict, decision_list[idx])
                        decisions.append(decision_list[idx])

    logger.info('after decision .....')
    host_module.print_host_list(host_list, 'calc_sched_decision done')
    print_decision_list(decisions, is_detailed=True)

    if not decisions:
        logger.debug('no decisons')
        return

    host_module.update_all_hosts_to_etcd(decisions)
    send_sched_decision_to_etcd(decision_dict)
    logger.info('decision_dict is {}'.format(decision_dict))


def add_sched_decision(decision_dict, decision):
    hostname = decision.hostname
    if decision_dict.get(hostname, None):
        decision_dict[hostname].append(decision)
    else:
        decision_dict[hostname] = [decision]


def send_sched_decision_to_etcd(decision_dict, retry_times=10):
    logger.debug('send_sched_decision_to_etcd')

    client = etcd_util.new_client()
    if client is None:
        logger.warn('send_sched_decision_to_etcd Create new_client failed')
        return

    for hostname, dec_list in decision_dict.items():
        decisions = []
        for idx, dec in enumerate(dec_list):
            dec_list[idx].queue = dec.queue.__dict__
            decison_info = json.dumps(dec.__dict__)
            decisions.append(decison_info)

        decisions_json = json.dumps(decisions)
        deci_key = etcd_util.HOSTS_PATH + hostname + '/decisions'

        dec_lock = etcd_util.get_etcd_lock('decision_lock_' + hostname, logger, client=client)
        if dec_lock is None:
            logger.warn('Failed to get host<{}> decision_lock from ETCD'.format(hostname))
            continue

        try:
            old_decis = ''
            try:
                old_decis = client.read(deci_key).value
            except etcd.EtcdKeyNotFound:
                pass
            if old_decis:
                decisions_json = old_decis[:-1] + ', ' + decisions_json[1:]
            client.write(deci_key, decisions_json)
            logger.debug('write to etcd, key is {}, value is {}'.format(deci_key, decisions_json))
        except Exception as e:
            logger.error('send_sched_decision_to_etcd error: {}'.format(e))
            logger.error(traceback.format_exc())
        finally:
            dec_lock.release()


def get_host_from_list(host_list, hostname):
    for h in host_list:
        if h.name == hostname:
            return h

    return None


def is_satisfied_host(host, que, works=1):
    if host.status == host_module.HOST_STATUS_BLOCK:
        return False

    if gpu_is_free(host, que, works) and \
            que.cpu_cores * works <= host.free_cpu_cores and \
            que.mem * works <= host.free_mem:
        return True

    return False


def gpu_is_free(host, que, works=1):
    alloc_gpus = 0
    for i in xrange(works):
        for gpu in host.gpu_list:
            if que.gpu <= gpu.free:
                alloc_gpus += 1
                logger.info('gpu_is_free find gpu, que.gpu<{}> gpu.free<{}>'.format(repr(que.gpu), repr(gpu.free)))

            if alloc_gpus == works:
                return True
    return False


def alloc_host_gpus(host, que, works=1):
    gpu_ids = []
    alloc_gpus = 0
    for i in xrange(works):
        for gpu in host.gpu_list:
            free_new = gpu.free - que.gpu
            # if que.gpu <= gpu.free:
            if free_new >= 0:
                # logger.info("alloc_host_gpus gpu= {}, free= {}, used= {}".format(que.gpu, gpu.free, gpu.used))
                gpu.used += que.gpu
                gpu.free -= que.gpu
                gpu_ids.append(gpu.id)
                alloc_gpus += 1

                if gpu.used < 0.0:
                    logger.warn('alloc_host_gpus find gpu.used= {}, change to 0'.format(gpu.used))
                    gpu.used = 0.0
                if gpu.used > 1.0:
                    logger.warn('alloc_host_gpus find gpu.used= {}, change to 1'.format(gpu.used))
                    gpu.used = 1.0
                if gpu.free < 0.0:
                    logger.warn('alloc_host_gpus find gpu.free= {}, change to 0'.format(gpu.free))
                    gpu.free = 0.0
                if gpu.free > 1.0:
                    logger.warn('alloc_host_gpus find gpu.free= {}, change to 1'.format(gpu.free))
                    gpu.free = 1.0

                # logger.debug("alloc_host_gpus gpu2= {}, free2= {}, used2= {}".format(que.gpu, gpu.free, gpu.used))

            if alloc_gpus == works:
                return gpu_ids

    return gpu_ids


def update_host_list(host, decision):
    que = decision.queue
    alloc_workers = decision.alloc_workers

    host.used_mem += alloc_workers * que.mem
    host.used_cpu_cores += alloc_workers * que.cpu_cores

    host.free_mem = host.total_mem - host.used_mem
    host.free_cpu_cores = host.total_cpu_cores - host.used_cpu_cores

    host.calc_gpu_usage()


def print_decision_list(decision_list, msg='decision list', is_detailed=True):
    logger.debug('======{}======'.format(msg))
    for d in decision_list:
        if is_detailed:
            logger.debug('{}:{}:{}'.format(
                d.hostname, d.__dict__, d.queue.__dict__))
        else:
            logger.debug('hostname = {} decision_id = {} gpus = {} \
alloc_workers = {}'.format(d.hostname, d.id, d.alloc_gpu_ids, d.alloc_workers))
