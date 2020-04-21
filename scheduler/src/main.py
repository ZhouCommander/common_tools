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
import glob
import time
import fcntl
import shutil
import argparse
import tempfile
import threading


import log
import traceback
import host
import conf
import worker
import reports
import scheduler
import etcd_util
import camera_status
import algo_data_conf

from log import scheduler_logger as logger

BUILD_DATE = '__BUILD_DATE__'
BUILD_VERSION = '__BUILD_VERSION__'


def check_another_sched_instance(pid_file):
    try:
        fcntl.lockf(pid_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        logger.error('scheduler another instance is running ... so exit this process!!')
        if pid_file:
            pid_file.close()
        sys.exit(-1)


def parse_args():
    parser = argparse.ArgumentParser(description='algorithm scheduler')
    parser.add_argument('--debug',
                        help='print message with level DEBUG',
                        action='store_true')

    parser.add_argument('--info',
                        help='print message with level INFO',
                        action='store_true')

    parser.add_argument('--warn',
                        help='print message with level WARNING',
                        action='store_true')

    parser.add_argument('--error',
                        help='print message with level ERROR',
                        action='store_true')

    parser.add_argument('--conf',
                        help='config file path',
                        type=file,
                        metavar='conf_path')

    parser.add_argument('--gpus',
                        help='specifiy the number of gpus',
                        type=int,
                        choices=range(0, 1024),
                        metavar='gpus')

    parser.add_argument('--version',
                        help='show version and exit',
                        action='store_true')

    return parser.parse_args()


def main():
    args = parse_args()
    log.init(args)

    if args.version:
        logger.debug('scheduler {}, {}'.format(BUILD_VERSION, BUILD_DATE))
        # sys.exit(0)
        return 0

    logger.info('all args is {}'.format(args))

    try:
        profile_lock = '/var/tmp/instance_dc0ab83c-610f-43c5-9f35-e3d1ea3e1989.lock'
        pid_file = open(profile_lock, 'w')
        check_another_sched_instance(pid_file)
    except Exception as e:
        logger.warn('check_another_sched_instance failed, msg<{}>'.format(e))

    conf.init(args)
    etcd_util.init()

    logger.debug('scheduler init done')
    logger.debug('scheduler conf: {}'.format(conf.sched_conf.__dict__))

    cur_host = host.collect_host_static_info(args.gpus)

    algo_data_conf.fetch_algo_data()

    worker_main_thread = threading.Thread(target=worker.launcher, name='worker_main_thread')
    worker_main_thread.daemon = True
    worker_main_thread.start()

    host_status_thread = threading.Thread(target=host.update_host_status, name='host_status_thread', args=(args.gpus,))
    host_status_thread.daemon = True
    host_status_thread.start()

    sync_algo_data = threading.Thread(target=algo_data_conf.sync_algo_data_from_etcd, name='sync_algo_data')
    sync_algo_data.daemon = True
    sync_algo_data.start()

    reports.init(cur_host)

    update_reports_thread = threading.Thread(target=reports.update_reports_to_etcd, name='update_reports_thread')
    update_reports_thread.daemon = True
    update_reports_thread.start()

    camera_status_thread = threading.Thread(target=camera_status.dump_all_camera_status, name='camera_status_thread')
    camera_status_thread.daemon = True
    camera_status_thread.start()

    block_status_thread = threading.Thread(target=worker.check_host_block(), name='check_host_thread')
    block_status_thread.daemon = True
    block_status_thread.start()

    schedule_period_sec = conf.sched_conf.schedule_period_sec
    logger.debug('schedule_period_sec is <{}>'.format(schedule_period_sec))

    while True:
        try:
            master = etcd_util.update_master_ttl()
            logger.debug('master is <{}>, host.HOST_NAME is <{}>'.format(master, host.HOST_NAME))

            if master and master == host.HOST_NAME:
                scheduler.calc_sched_decision()

            time.sleep(schedule_period_sec)

        except KeyboardInterrupt:
            logger.error('master find KeyboardInterrupt, exit')
            etcd_util.delete_host_info(master)
            # sys.exit(0)
            break
        except Exception as e:
            logger.error('master find exception, msg: {}'.format(e))
            logger.error(traceback.format_exc())
            time.sleep(schedule_period_sec)
    return 0


if __name__ == '__main__':
    try:
        tempfile.tempdir = '/deepruntime'
        print ("cleanup outdated temporary files")
        dirs = glob.glob("/deepruntime/_MEI*")
        for sub_dir in dirs:
            t = int((time.time() - os.path.getmtime(sub_dir)) / 3600)
            if t >= 36:
                shutil.rmtree(sub_dir)
    except Exception as e:
        print ("errors when delete dir, failed reason is: {}".format(e))
    finally:
        main()