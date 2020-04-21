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
import re
import json
import time
import traceback
import multiprocessing

import conf
import etcd_util
from log import worker_logger
from log import camera_status_logger as logger

g_value_list = []
g_param_list = []

lock = multiprocessing.RLock()


def enable_capture_status(worker):
    camera_id = worker.msg.get('camera_id', None)
    if not camera_id:
        logger.error('invalid <worker{}> msg: <{}>'.format(worker.id, worker.msg))
        return False

    key = etcd_util.CAMERA_ARGS_PATH + '/' + str(camera_id) + '/' + 'extra_parameter'
    extra_param = etcd_util.read_ext(key)
    logger.info('camera_id is <{}>, extra_parameter is <{}>'.format(camera_id, extra_param))

    pattern = re.compile(r'capturestatus\s*=\s*on')
    if extra_param and pattern.search(extra_param.value):
        return True
    return False


def collect_camera_status(worker):
    if worker is None or worker.msg is None:
        return

    logger.info('enable_capture_status flag is {}'.format(enable_capture_status(worker)))
    if not enable_capture_status(worker):
        return

    start_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(worker.start_time))

    schedule_seconds = worker.interprocess_dict.get('schedule_seconds', 0)
    return_code = worker.interprocess_dict.get('return_code', None)

    if return_code is None:
        worker_logger.warn('failed to get <worker{}> process_data return_code'.format(worker.id))
        return_code = worker.exitcode

    finish_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(worker.finish_time))

    values = [
        start_date,
        int(schedule_seconds),
        worker.retry_times,
        finish_date,
        return_code,
        worker.decision.queue.name,
        worker.decision.hostname]

    format_values = []
    for v in values:
        if isinstance(v, basestring):
            format_values.append(v)
        else:
            format_values.append(str(v))

    file_name = worker.msg.get('file_path')
    with lock:
        global g_value_list
        global g_param_list
        g_value_list.append(format_values)
        g_param_list.append({'capture_file_name': file_name})


def dump_sched_result(values, params):
    logger.debug('call dump_sched_result ...')

    if len(values) == 0 or len(params) == 0:
        return

    if len(values) != len(params):
        logger.error('invalid values <{}> and params <{}>'.format(values, params))
        return

    sched_result = {
        'operations': {
            'update': {
                'table': 'vm_camera_status',
                'columns': [
                    'schedule_start_date',
                    'schedule_seconds',
                    'retrys',
                    'schedule_finish_date',
                    'return_code',
                    'algo_name',
                    'worker_host',
                ],
                'values': values,
                'params': params
            }
        }
    }

    json_save_dir = conf.sched_conf.sched_result_save_dir
    if not os.path.exists(json_save_dir):
        os.makedirs(json_save_dir)

    try:
        full_file_path = json_save_dir + '/' + str(time.time()) + '_dbrest.json'
        with open(full_file_path, 'w') as f:
            json.dump(sched_result, f, sort_keys=True, indent=4)

        logger.info('sched_result is {}'.format(sched_result))
        logger.debug('create file <{}> json done'.format(full_file_path))

    except Exception as e:
        logger.error('failed to create json for file <{}>, error: <{}>'.format(full_file_path, e))
        logger.error(traceback.format_exc())


def dump_all_camera_status():
    logger.debug('call dump_all_camera_status ...')

    while True:
        time.sleep(conf.sched_conf.dump_json_interval_sec)
        with lock:
            global g_value_list
            global g_param_list
            dump_sched_result(g_value_list, g_param_list)
            g_value_list = []
            g_param_list = []
