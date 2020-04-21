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
import time
import traceback
import argparse

from texttable import Texttable

sys.path.append("..")
sys.path.append("../../../")
import host as host_module
import etcd_util

from common.logger import logger
from common.conf import config
from common.etcd_wrapper import etcd_wrapper


BUILD_DATE = '__BUILD_DATE__'
BUILD_VERSION = '__BUILD_VERSION__'

conf_dir = os.getenv('SCHEDULER_CONF_DIR')

if not conf_dir:
    print 'failed to get scheduler conf by env <SCHEDULER_CONF_DIR>, exit'
    sys.exit(1)

CONF_FILE = conf_dir + '/scheduler.json'

log = logger.get_logger('dhosts')
config = config.get_conf(CONF_FILE)

etcd_urls = config.get('etcd_urls')
if etcd_urls is None:
    log.error('failed to get etcd_urls from configuration file \
<{}>'.format(CONF_FILE))
    sys.exit(1)

log.info('etcd_urls is <{}>'.format(etcd_urls))

DATA_FACTOR = 1024 * 1024
MAX_HOSTNAME_WIDTH = 10
HOST_TITLE_LENGTH = 8

etcd_obj = etcd_wrapper.ETCDWrapper(config.get('etcd_urls'), log)


def fmt_data_quantity(bytes, multiple=1024):
    try:
        bytes = int(bytes)
        if bytes < multiple * multiple:
            return "%dK" % ((bytes) / multiple)

        quantity = bytes / multiple / multiple
        for unit in ['M', 'G', 'T', 'P', 'E', 'Z']:
            # if quantity < 10G, unit is M
            if quantity < multiple * 10:
                return "%d%s" % (quantity, unit)
            quantity /= multiple

        return "%d%s" % (quantity, 'Y')

    except TypeError:
        return '0M'


def get_host_info_title():
    host_info_title = [
        'name',
        'status',
        'cpu',
        'gpu',
        'mem',
        'used_cpu',
        'used_gpu',
        'used_mem',
    ]
    return host_info_title


def get_host_row_info(host, args=None):
    host_table = []
    hostname = host.name
    if not (args and args.detail):
        if len(hostname) > MAX_HOSTNAME_WIDTH:
            hostname = hostname[:MAX_HOSTNAME_WIDTH - 1] + '*'

    host_table.append(hostname)
    host_table.append(host.get_status_str())
    host_table.append(host.total_cpu_cores)
    host_table.append(host.total_gpus)
    total_mem_str = fmt_data_quantity(host.total_mem * DATA_FACTOR)
    host_table.append(total_mem_str)
    host_table.append(host.used_cpu_cores)
    host_table.append(host.used_gpus)
    used_mem_str = fmt_data_quantity(host.used_mem * DATA_FACTOR)
    host_table.append(used_mem_str)

    return host_table


def wait_host_exit(hostname):
    while True:
        host_info = etcd_obj.read(etcd_util.HOSTS_PATH + hostname)
        if host_info is None:
            print 'host <{}> scheduler has exit'.format(hostname)
            return
        time.sleep(2)


def block_hosts(args):
    hosts_key_lock = etcd_obj.get_etcd_lock('hosts_key_lock')
    if hosts_key_lock is None:
        print('[block_hosts] Failed to get hosts_key_lock, forced continue')

    host_name_list = args.block
    try:
        for hostname in host_name_list:
            host_obj = host_module.get_cur_host_from_etcd(etcd_obj.client, log)

            if host_obj is None:
                print 'failed to get host <{}> info from etcd, exit'.format(hostname)
                sys.exit(-1)
            try:
                host_obj.set_status(host_module.HOST_STATUS_BLOCK)
                host_json = host_obj.to_json()
                host_key = etcd_util.HOSTS_PATH + host_obj.name + '/host_data'
                etcd_obj.write(host_key, host_json)

            except Exception as e:
                print('block_hosts error: {}'.format(e))
                print(traceback.format_exc())

            if args.wait:
                wait_host_exit(hostname)
            print 'block host <{}> done'.format(hostname)
    finally:
        if hosts_key_lock:
            hosts_key_lock.release()

    sys.exit(0)


def display_hosts_info(hosts_info):
    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype([
        't',  # text
        't',
        'i',  # integer
        'i',
        't',
        'f',  # float
        'f',
        't',
    ])

    table.set_cols_width([MAX_HOSTNAME_WIDTH] + [8] + [3] * 2 + [6] + [8] * 3)
    table.set_cols_align(['c'] * HOST_TITLE_LENGTH)
    table.set_precision(1)
    table.set_chars(['-', '|', '+', '-'])
    table.add_rows(hosts_info)
    print table.draw()


def parse_args():
    parser = argparse.ArgumentParser(description='dhosts')

    parser.add_argument(
        '-b',
        '--block',
        help='block specifiy hostname',
        type=str,
        nargs='+',
        metavar='hostname')

    parser.add_argument(
        '-w',
        '--wait',
        help='waiting for the host to be blocked',
        action='store_true')

    parser.add_argument(
        '-s',
        '--statis',
        help='display host worker statistics',
        action='store_true')

    parser.add_argument(
        '-d',
        '--detail',
        help='display detail hosts information',
        action='store_true')

    parser.add_argument('-v',
                        '--version',
                        help='show version and exit',
                        action='store_true')

    return parser.parse_args()


def fetch_host_statis_from_etcd(hostname):
    host_cnt = {
        'name': hostname,
        'running': 0,
        'error': 0,
        'finished': 0,
    }

    host_dir = etcd_obj.read(etcd_util.HOST_STATISTICS_PATH + hostname)
    for host in host_dir.children:
        gpu_idx_dir = etcd_obj.read(host.key)
        for status_dir in gpu_idx_dir.children:
            status = os.path.basename(status_dir.key)
            host_cnt[status] += int(status_dir.value)

    return host_cnt


def get_host_statis_row_info(statis, args=None):
    statis_table = []
    hostname = statis['name']
    if not (args and args.detail):
        if len(hostname) > MAX_HOSTNAME_WIDTH:
            hostname = hostname[:MAX_HOSTNAME_WIDTH - 1] + '*'
    statis_table.append(hostname)
    statis_table.append(statis['running'])
    statis_table.append(statis['finished'])
    statis_table.append(statis['error'])

    return statis_table


def get_host_statis_title():
    host_statis_title = [
        'name',
        'running',
        'finished',
        'error',
    ]
    return host_statis_title


def display_hosts_statis(hosts_info):
    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype([
        't',  # text
        'i',  # integer
        'i',
        'i',
    ])

    table.set_cols_width([MAX_HOSTNAME_WIDTH] + [8] * 3)
    table.set_cols_align(['c'] * 4)
    table.set_precision(1)
    table.set_chars(['-', '|', '+', '-'])
    table.add_rows(hosts_info)
    print table.draw()


def dhosts():
    args = parse_args()
    if args.version:
        print('dhosts {}, {}'.format(BUILD_VERSION, BUILD_DATE))
        sys.exit(0)

    if args.block:
        block_hosts(args)

    hosts_key_lock = etcd_obj.get_etcd_lock('hosts_key_lock')
    if hosts_key_lock is None:
        print('[dhosts] Failed to get hosts_key_lock')
        return

    try:
        host_list = host_module.get_all_hosts_from_etcd(etcd_obj.client, log)
        if not host_list:
            print 'no hosts found'
            sys.exit(0)

        host_list.sort(
            key=lambda host: (host.name),
            reverse=True)

        if args.statis:
            host_name_list = [h.name for h in host_list]
            host_statis_list = []
            for hostname in host_name_list:
                host_statis = fetch_host_statis_from_etcd(hostname)
                host_statis_list.append(host_statis)

            host_statis_list.sort(key=lambda que: (
                que['running']),
                reverse=True)
            host_statis_table = [get_host_statis_title()]
            for statis in host_statis_list:
                statis_row = get_host_statis_row_info(statis, args)
                host_statis_table.append(statis_row)
            display_hosts_statis(host_statis_table)
            sys.exit(0)

        title = get_host_info_title()
        host_table = [title]
        for host in host_list:
            host_row = get_host_row_info(host, args)
            host_table.append(host_row)

        display_hosts_info(host_table)
    except Exception as e:
        log.error('failed to get all hosts from etcd, error: {}'.format(e))
        print(traceback.format_exc())
    finally:
        hosts_key_lock.release()


if __name__ == '__main__':
    dhosts()
