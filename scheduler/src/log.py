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
import socket
import logging
from singleton import singleton
from logging.handlers import RotatingFileHandler


scheduler_logger = logging.getLogger('scheduler')
worker_logger = logging.getLogger('worker')
check_host_logger = logging.getLogger('check_host')
camera_status_logger = logging.getLogger('camera_status')
reports_to_etcd_logger = logging.getLogger('reports_to_etcd')
sync_algo_data_logger = logging.getLogger('sync_algo_data')
update_host_status_logger = logging.getLogger('host_status')

scheduler_logger.setLevel(logging.DEBUG)
worker_logger.setLevel(logging.DEBUG)
check_host_logger.setLevel(logging.DEBUG)
camera_status_logger.setLevel(logging.DEBUG)
reports_to_etcd_logger.setLevel(logging.DEBUG)
sync_algo_data_logger.setLevel(logging.DEBUG)
update_host_status_logger.setLevel(logging.DEBUG)



@singleton
class Logger():
    def __init__(self, args):
        # log_root_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")
        # log_root_dir = os.path.join(os.path.dirname(__file__), "log")
        log_root_dir = './log/'
        module_name_log = ["scheduler", "main_worker", "check_host", "camera_status", "reports_to_etcd",
                           "sync_algo_data", "update_host_status"]

        for module_log in module_name_log:
            if not os.path.exists(log_root_dir + module_log):
                try:
                    os.makedirs(log_root_dir + module_log)
                except Exception as e:
                    print ('failed to create log dir <{}>, error: <{}>'.format(log_root_dir, e))
                    sys.exit(-1)

        self.scheduler_logger = logging.getLogger('scheduler')
        self.worker_logger = logging.getLogger('worker')
        self.check_host_logger = logging.getLogger('check_host')
        self.camera_status_logger = logging.getLogger('camera_status')
        self.reports_to_etcd_logger = logging.getLogger('reports_to_etcd')
        self.sync_algo_data_logger = logging.getLogger('sync_algo_data')
        self.update_host_status_logger = logging.getLogger('host_status')

        console_handler = logging.StreamHandler()
        hostname = socket.gethostname()

        scheduler_log_name = 'scheduler' + '_' + hostname + '.log'
        # scheduler_log_path = os.path.join(log_root_dir, "scheduler", scheduler_log_name)
        scheduler_log_path = log_root_dir + "scheduler/" + scheduler_log_name
        scheduler_file_handler = get_file_handler(scheduler_log_path)

        worker_log_name = 'main_worker' + '_' + hostname + '.log'
        # worker_log_path = os.path.join(log_root_dir, "main_worker", worker_log_name)
        worker_log_path = log_root_dir + "main_worker/" + worker_log_name
        worker_file_handler = get_file_handler(worker_log_path)

        check_host_log_name = 'check_host' + '_' + hostname + '.log'
        # check_host_log_path = os.path.join(log_root_dir, "check_host", check_host_log_name)
        check_host_log_path = log_root_dir + "check_host/" + check_host_log_name
        check_host_file_handler = get_file_handler(check_host_log_path)

        camera_status_log_name = 'camera_status' + '_' + hostname + '.log'
        camera_status_log_path = os.path.join(log_root_dir, "camera_status", camera_status_log_name)
        camera_status_log_path = log_root_dir + "camera_status/" + camera_status_log_name
        camera_status_file_handler = get_file_handler(camera_status_log_path)

        reports_to_etcd_log_name = 'reports_to_etcd' + '_' + hostname + '.log'
        reports_to_etcd_log_path = os.path.join(log_root_dir, "reports_to_etcd", reports_to_etcd_log_name)
        reports_to_etcd_log_path = log_root_dir + "reports_to_etcd/" + reports_to_etcd_log_name
        reports_to_etcd_file_handler = get_file_handler(reports_to_etcd_log_path)

        sync_algo_data_log_name = 'sync_algo_data' + '_' + hostname + '.log'
        sync_algo_data_log_path = os.path.join(log_root_dir, "sync_algo_data", sync_algo_data_log_name)
        sync_algo_data_log_path = log_root_dir + "sync_algo_data/" + sync_algo_data_log_name
        sync_algo_data_file_handler = get_file_handler(sync_algo_data_log_path)

        update_host_status_log_name = 'update_host_status' + '_' + hostname + '.log'
        update_host_status_log_path = os.path.join(log_root_dir, "update_host_status", update_host_status_log_name)
        update_host_status_log_path = log_root_dir + "update_host_status/" + update_host_status_log_name
        update_host_status_file_handler = get_file_handler(update_host_status_log_path)

        if args.debug:
            self.scheduler_logger.setLevel(logging.DEBUG)
            self.worker_logger.setLevel(logging.DEBUG)
            self.check_host_logger.setLevel(logging.DEBUG)
            self.camera_status_logger.setLevel(logging.DEBUG)
            self.reports_to_etcd_logger.setLevel(logging.DEBUG)
            self.sync_algo_data_logger.setLevel(logging.DEBUG)
            self.update_host_status_logger.setLevel(logging.DEBUG)

        if args.info:
            self.scheduler_logger.setLevel(logging.INFO)
            self.worker_logger.setLevel(logging.INFO)
            self.check_host_logger.setLevel(logging.INFO)
            self.camera_status_logger.setLevel(logging.INFO)
            self.reports_to_etcd_logger.setLevel(logging.INFO)
            self.sync_algo_data_logger.setLevel(logging.INFO)
            self.update_host_status_logger.setLevel(logging.INFO)

        if args.warn:
            self.scheduler_logger.setLevel(logging.WARNING)
            self.worker_logger.setLevel(logging.WARNING)
            self.check_host_logger.setLevel(logging.WARNING)
            self.camera_status_logger.setLevel(logging.WARNING)
            self.reports_to_etcd_logger.setLevel(logging.WARNING)
            self.sync_algo_data_logger.setLevel(logging.WARNING)
            self.update_host_status_logger.setLevel(logging.WARNING)

        if args.error:
            self.scheduler_logger.setLevel(logging.ERROR)
            self.worker_logger.setLevel(logging.ERROR)
            self.check_host_logger.setLevel(logging.ERROR)
            self.camera_status_logger.setLevel(logging.ERROR)
            self.reports_to_etcd_logger.setLevel(logging.ERROR)
            self.sync_algo_data_logger.setLevel(logging.ERROR)
            self.update_host_status_logger.setLevel(logging.ERROR)


        # define log format, e.g.
        # 2018-10-08 18:21:58,071 - scheduler.py[line:31] - INFO - info message
        formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s - [pid:%(process)d] - %(message)s')

        console_handler.setFormatter(formatter)

        scheduler_file_handler.setFormatter(formatter)
        self.scheduler_logger.addHandler(console_handler)
        self.scheduler_logger.addHandler(scheduler_file_handler)

        worker_file_handler.setFormatter(formatter)
        self.worker_logger.addHandler(console_handler)
        self.worker_logger.addHandler(worker_file_handler)

        check_host_file_handler.setFormatter(formatter)
        self.check_host_logger.addHandler(console_handler)
        self.check_host_logger.addHandler(check_host_file_handler)

        camera_status_file_handler.setFormatter(formatter)
        self.camera_status_logger.addHandler(console_handler)
        self.camera_status_logger.addHandler(camera_status_file_handler)

        reports_to_etcd_file_handler.setFormatter(formatter)
        self.reports_to_etcd_logger.addHandler(console_handler)
        self.reports_to_etcd_logger.addHandler(reports_to_etcd_file_handler)

        sync_algo_data_file_handler.setFormatter(formatter)
        self.sync_algo_data_logger.addHandler(console_handler)
        self.sync_algo_data_logger.addHandler(sync_algo_data_file_handler)

        update_host_status_file_handler.setFormatter(formatter)
        self.update_host_status_logger.addHandler(console_handler)
        self.update_host_status_logger.addHandler(update_host_status_file_handler)

        global scheduler_logger
        global worker_logger
        global check_host_logger
        global camera_status_logger
        global reports_to_etcd_logger
        global sync_algo_data_logger
        global update_host_status_logger

        scheduler_logger = self.scheduler_logger
        worker_logger = self.worker_logger
        check_host_logger = self.check_host_logger
        camera_status_logger = self.camera_status_logger
        reports_to_etcd_logger = self.reports_to_etcd_logger
        sync_algo_data_logger = self.sync_algo_data_logger
        update_host_status_logger = self.update_host_status_logger


def get_file_handler(log_path):

    return RotatingFileHandler(log_path,
                               mode='a',
                               maxBytes=20 * 1024 * 1024,
                               backupCount=10)


def init(args):
    Logger(args)

