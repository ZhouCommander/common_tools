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
import json

from singleton import singleton
from log import scheduler_logger as logger


CONF_PATH = './conf/scheduler.json'

sched_conf = None


def get_conf(config_file, default_conf=None):
    if os.path.isfile(config_file):
        with open(config_file) as f:
            try:
                conf_dict = json.load(f)
                return conf_dict
            except ValueError:
                logger.error('invalid json config file <{}>, use default config'.format(config_file))

                return default_conf
    else:
        # logger.warn('no configuration file <{}>, use default config'.format(config_file))
        pass

        return default_conf


def init(args):
    logger.info('configure init start ...')

    global sched_conf
    if args.conf:
        try:
            conf_dict = json.load(args.conf)
            sched_conf = SchedulerConf(conf_dict)

            logger.info('conf_dict is {}'.format(conf_dict))

        except ValueError:
            logger.error('invalid json file <{}>, exit'.format(args.conf.name))
            sys.exit(-1)

        except IOError as e:
            logger.error(e)
    else:
        logger.info('There is no args in scheduler main.py cmd')
        sched_conf = SchedulerConf()
        logger.info("{} is {}".format(CONF_PATH, sched_conf.__dict__))
        logger.info("configure init done ...")


@singleton
class SchedulerConf:

    def __init__(self, conf_dict=None):
        self.schedule_period_sec = 5
        self.worker_run_timeout = 30
        self.worker_timeout_mulitiple = 5
        self.fetch_mq_msg_timeout = 60
        self.algo_data_sync_period_sec = 60
        self.throughput_interval_sec = 7200
        self.sched_result_save_dir = ''
        self.dump_json_interval_sec = 20
        self.host_info_ttl = 120
        self.etcd_urls = ''

        if isinstance(conf_dict, dict):
            # overwrite default conf
            self.__dict__.update(conf_dict)
            return

        # if no configuration file is specified, read the configuration
        # from the specified path
        if os.path.isfile(CONF_PATH):
            with open(CONF_PATH) as f:
                try:
                    conf_dict = json.load(f)
                    # overwrite default conf from conf file
                    self.__dict__.update(conf_dict)

                except ValueError:
                    logger.error('invalid json file <{}>, exit'.format(CONF_PATH))
                    sys.exit(-1)

        self.schedule_period_sec = get_a_number('schedule_period_sec', self.schedule_period_sec,
                                                min_value=1, def_value=5)
        self.worker_run_timeout = get_a_number('worker_run_timeout', self.worker_run_timeout,
                                               min_value=1, def_value=30)
        self.worker_timeout_mulitiple = get_a_number('worker_timeout_mulitiple', self.worker_timeout_mulitiple,
                                                     min_value=1, def_value=30)
        self.fetch_mq_msg_timeout = get_a_number('fetch_mq_msg_timeout', self.fetch_mq_msg_timeout, min_value=1,
                                                 def_value=60)
        self.algo_data_sync_period_sec = get_a_number('algo_data_sync_period_sec', self.algo_data_sync_period_sec,
                                                      min_value=1, def_value=60)
        self.throughput_interval_sec = get_a_number('throughput_interval_sec', self.throughput_interval_sec,
                                                    min_value=1, def_value=7200)
        self.dump_json_interval_sec = get_a_number('dump_json_interval_sec', self.dump_json_interval_sec, min_value=1,
                                                   def_value=20)
        self.host_info_ttl = get_a_number('host_info_ttl', self.host_info_ttl, min_value=1, def_value=120)


def get_a_number(key, num, max_value=sys.maxint, min_value=0, def_value=None, is_int=True):

    is_valid = True
    try:
        if is_int:
            val = int(num)
        else:
            val = float(num)

        if val < min_value or val > max_value:
            is_valid = False

    except ValueError:
        is_valid = False

    if is_valid:
        return val

    logger.error('invalid configuration value <{} = {}>, use default value <{}>'.format(key, num, def_value))
    return def_value


def get_bool_value(key, value, def_value=False):
    is_valid = True
    if not isinstance(value, bool):
        is_valid = False

    if is_valid:
        return value

    logger.error('invalid boolean configuration value <{} = {}>, use default value <{}>'.format(key, value, def_value))

    return def_value


def get_json_str(key, json_str, def_value=''):
    is_valid = True
    try:
        json.loads(json_str)
    except:
        is_valid = False

    if is_valid:
        return json_str

    logger.error('invalid json configuration value <{} = \'{}\'>, use default value <\'{}\'>'.format(key, json_str, def_value))

    return def_value
