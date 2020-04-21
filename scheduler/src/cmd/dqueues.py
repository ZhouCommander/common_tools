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
import sys
import argparse

from texttable import Texttable

sys.path.append("..")
sys.path.append("../../../")
import etcd_util
from common.etcd_wrapper import etcd_wrapper
from common.logger import logger
from common.conf import config
import queue_conf


BUILD_DATE = '__BUILD_DATE__'
BUILD_VERSION = '__BUILD_VERSION__'

conf_dir = os.getenv('SCHEDULER_CONF_DIR')

if not conf_dir:
    print 'failed to get scheduler conf by env <SCHEDULER_CONF_DIR>, exit'
    sys.exit(1)

CONF_FILE = conf_dir + '/scheduler.json'

log = logger.get_logger('dqueues')
config = config.get_conf(CONF_FILE)
etcd_urls = config.get('etcd_urls')
if etcd_urls is None:
    log.error('failed to get etcd_urls from configuration file \
<{}>'.format(CONF_FILE))
    sys.exit(1)

log.info('etcd_urls is <{}>'.format(etcd_urls))

etcd_obj = etcd_wrapper.ETCDWrapper(config.get('etcd_urls'), log)

MAX_QUE_NAME_WIDTH = 10
QUE_TITLE_LENGTH = 4


def get_que_info_title():
    que_info_title = [
        'name',
        'pending',
        'finished',
        'error',
    ]
    return que_info_title


def get_que_row_info(que, args=None):
    que_table = []
    que_name = que['name']
    if not (args and args.detail):
        if len(que_name) > MAX_QUE_NAME_WIDTH:
            que_name = que_name[:MAX_QUE_NAME_WIDTH - 1] + '*'
    que_table.append(que_name)
    que_table.append(que['pending'])
    que_table.append(que['finished'])
    que_table.append(que['error'])

    return que_table


def display_queues_info(queues_info):
    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype([
        't',  # text
        'i',  # integer
        'i',
        'i',
    ])

    table.set_cols_width([MAX_QUE_NAME_WIDTH] + [8] * 3)
    table.set_cols_align(['c'] * QUE_TITLE_LENGTH)
    table.set_precision(1)
    table.set_chars(['-', '|', '+', '-'])
    table.add_rows(queues_info)
    print table.draw()


def parse_args():
    parser = argparse.ArgumentParser(description='dqueues')
    parser.add_argument(
        '-d',
        '--detail',
        help='display detail queues information',
        action='store_true')

    parser.add_argument('-v',
                        '--version',
                        help='show version and exit',
                        action='store_true')

    return parser.parse_args()


def dqueues():
    args = parse_args()
    if args.version:
        print('dqueues {}, {}'.format(BUILD_VERSION, BUILD_DATE))
        sys.exit(0)

    etcd_urls = config.get('etcd_urls')
    if etcd_urls is None:
        log.error('failed to get etcd_urls from configuration file \
<{}>'.format(CONF_FILE))
        sys.exit(1)

    log.info('etcd_urls is <{}>'.format(etcd_urls))
    queue_list = []
    que_name_list = get_queue_names_from_etcd()
    for name in que_name_list:
        que_cnt = fetch_queue_cnt_from_etcd(name)
        queue_list.append(que_cnt)

    queue_list.sort(key=lambda que: (que['pending']), reverse=True)
    que_table = [get_que_info_title()]
    for que in queue_list:
        que_row = get_que_row_info(que, args)
        que_table.append(que_row)
    display_queues_info(que_table)


def fetch_queue_cnt_from_etcd(queue_name):
    queue_cnt = {
        'name': queue_name,
        'pending': 0,
        'error': 0,
        'finished': 0,
    }

    que_dir = etcd_obj.read(etcd_util.ALGO_STATISTICS_PATH + queue_name)
    for que in que_dir.children:
        worker_status = etcd_obj.read(que.key)
        for status_dir in worker_status.children:
            status = os.path.basename(status_dir.key)
            if status == 'pending':
                queue_cnt[status] = int(status_dir.value)
            else:
                queue_cnt[status] += int(status_dir.value)

    return queue_cnt


def get_queue_names_from_etcd():
    que_name_list = []
    que_dir = etcd_obj.read(etcd_util.ALGO_STATISTICS_PATH)
    for que in que_dir.children:
        que_name_list.append(os.path.basename(que.key))
    return que_name_list


if __name__ == '__main__':
    dqueues()
