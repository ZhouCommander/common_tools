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

import etcd
import traceback

import conf
import etcd_util
from log import scheduler_logger as logger
from rabbitmq_wrapper import RabbitMQ


g_min_gpu_cost = 1


class QueueConf:

    def __init__(self):
        # TODO: performace issue
        self.queue_list = get_queue_conf_from_etcd()

        self.queue_dict = {}
        global g_min_gpu_cost
        for q in self.queue_list:
            if q.name == '':
                self.queue_list = []
                return

            if q.gpu <= g_min_gpu_cost:
                g_min_gpu_cost = q.gpu

            self.queue_dict[q.name] = q

    def get_a_queue(self, queue_name):
        q = self.queue_dict.get(queue_name, None)
        if q:
            return q

        logger.error('invalid queue name {}, failed to get queue conf'.format(queue_name))
        return None

    def get_queue_list(self):
        return self.queue_list

    def print_queue_list(self, msg='queue list', is_detailed=True):
        logger.debug('======{}======'.format(msg))
        for q in self.queue_list:
            if is_detailed:
                logger.debug('{}: msg = {} mem = {} cpu = {} gpu = {} works = {} priority = {}'.format(
                    q.name,
                    q.pending_msg_num,
                    q.mem,
                    q.cpu_cores,
                    q.gpu,
                    q.static_worker,
                    q.priority))
            else:
                logger.debug('{}'.format(q.name))


class Queue:

    def __init__(self):
        self.name = ''
        self.host = ''
        self.port = 5672
        self.mem = 512
        self.cpu_cores = 1
        self.gpu = 1
        self.static_worker = 1
        self.max_tasks_per_worker = 1
        self.algo_conf = ''
        self.pending_msg_num = 0
        self.priority = 10

    def get_pending_msg_number(self):
        try:
            ramq = RabbitMQ(self.host, self.port)
            self.pending_msg_num = ramq.GetQueueMsgNumber(queue_name=self.name)
            ramq.Close()
        except Exception as e:
            logger.error('failed to get pending msg num from {0}: {1}'.format(self.name, e))
            logger.error('failed reason is {}'.format(traceback.format_exc()))
        return self.pending_msg_num

    def get_a_msg(self):
        msg = None
        try:
            ramq = RabbitMQ(self.host, self.port)
            msg = ramq.FetchMessage(queue_name=self.name)
            logger.debug('get a message from queue {0} : {1} '.format(self.name, msg))
            ramq.Close()
        except Exception as e:
            logger.error('failed to get a message from queue {0} : {1} '.format(self.name, e))
            logger.error('failed reason is {}'.format(traceback.format_exc()))
        return msg

    def check_config(self):

        self.port = conf.get_a_number(
            self.name + '.port',
            self.port,
            min_value=0,
            max_value=65535,
            def_value=5672)

        self.mem = conf.get_a_number(
            self.name + '.mem_cost_mb',
            self.mem,
            def_value=512)

        self.cpu_cores = conf.get_a_number(
            self.name + '.cpu_cost',
            self.cpu_cores,
            is_int=False,
            max_value=128,
            def_value=1)

        self.gpu = conf.get_a_number(
            self.name + '.gpu_cost',
            self.gpu,
            is_int=False,
            max_value=1.0,
            def_value=1)

        self.static_worker = conf.get_a_number(
            self.name + '.worker_number',
            self.static_worker,
            max_value=20,
            def_value=1)

        self.max_tasks_per_worker = conf.get_a_number(
            self.name + '.max_tasks_per_worker',
            self.max_tasks_per_worker,
            def_value=1)

        self.algo_conf = conf.get_json_str(
            self.name + '.algo_config_json_str',
            self.algo_conf)


def get_queue_conf_from_etcd(client=None):
    if client is None:
        client = etcd_util.new_client()

    queue_list = []

    # for cloud connector
    mq_config = conf.get_conf('./conf/rabbitmq_wrapper.json')
    logger.debug('mq_config is <{}>'.format(mq_config))

    try:
        # get '/db/vm_algo_parameter' config
        algo_key_list = client.read(etcd_util.ALGO_ARGS_PATH)

        for algo_key in algo_key_list.children:
            algo = client.read(algo_key.key)
            queue = Queue()
            for algo_arg in algo.children:
                if algo_arg.key == algo_key.key + '/cpu_cost':
                    if algo_arg.value:
                        queue.cpu_cores = float(algo_arg.value)
                    else:
                        queue.cpu_cores = 1.0

                if algo_arg.key == algo_key.key + '/gpu_cost':
                    if algo_arg.value:
                        queue.gpu = float(algo_arg.value)
                    else:
                        queue.gpu = 0.5
                    # logger.debug('jason queue.gpu= {} algo_arg.value= {}'.format(queue.gpu, algo_arg.value))

                if algo_arg.key == algo_key.key + '/mem_cost_mb':
                    if algo_arg.value:
                        queue.mem = float(algo_arg.value)
                    else:
                        queue.mem = 512

                if algo_arg.key == algo_key.key + '/message_queue_url':
                    queue.host, queue.port = algo_arg.value.split(':')

                    if mq_config:
                        queue.host = mq_config.get('rmq_host')
                        queue.port = mq_config.get('rmq_port')

                if algo_arg.key == algo_key.key + '/name':
                    queue.name = algo_arg.value

                if algo_arg.key == algo_key.key + '/worker_number':
                    queue.static_worker = int(algo_arg.value)

                if algo_arg.key == algo_key.key + '/algo_config_json_str':
                    queue.algo_conf = algo_arg.value

                if algo_arg.key == algo_key.key + '/priority':
                    if algo_arg.value != "None":
                        queue.priority = int(algo_arg.value)
                    else:
                        logger.warn('{} value is None, please check'.format(algo_arg.key))

            if queue.name != '':
                queue.check_config()
                queue_list.append(queue)
            else:
                logger.error('invalid queue conf')

    except etcd.EtcdKeyNotFound:
        logger.error('the key {} doesn’t exists, failed to get queue conf from etcd'.format(etcd_util.ALGO_ARGS_PATH))

    except Exception as e:
        logger.error('failed to get queue conf from etcd: {}'.format(e))
        logger.error('failed to get queue conf from etcd: {}'.format(traceback.format_exc()))

    # logger.debug('queue_list is <{}>'.format(queue_list))
    return queue_list


def get_min_gpu_cost():
    return g_min_gpu_cost


if __name__ == '__main__':
    mq_config = conf.get_conf('./conf/rabbitmq_wrapper.json')
    print mq_config
