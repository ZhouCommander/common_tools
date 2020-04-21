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
import argparse
import logging
import traceback
from logging.handlers import RotatingFileHandler
import json

from Common import *
from camera_pic_upload import CameraPicUpload
from clean_tmp import clean_tmp


BUILD_DATE = '__BUILD_DATE__'
BUILD_VERSION = '__BUILD_VERSION__'

LOG_TAG = "camera_pic_upload"
LOG_LEVEL = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
global g_log_level
global g_default_level


def init_log(args):
    log_level = logging.ERROR
    if args:
        if args.debug:
            log_level = logging.DEBUG
        elif args.info:
            log_level = logging.INFO
        elif args.warn:
            log_level = logging.WARNING
        elif args.error:
            log_level = logging.ERROR

    global g_log_level
    g_log_level = log_level
    global g_default_level
    g_default_level = log_level

    log_file_path = "%slog/" % (get_file_dir(__file__))
    log_name = LOG_TAG
    logMaxBytes = 20 * 1024 * 1024
    logBackupCount = 5

    mk_dir(log_file_path)
    logger = logging.getLogger(LOG_TAG)
    logger.setLevel(log_level)
    rHandler = RotatingFileHandler('%s%s.log' % (log_file_path, log_name),
                                   maxBytes=logMaxBytes, backupCount=logBackupCount)
    rHandler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s[%(lineno)d] %(message)s')
    rHandler.setFormatter(formatter)
    logger.addHandler(rHandler)


def refresh_log_level(logger, root_dir):
    global g_log_level
    global g_default_level
    log_level = -1
    cfg_file = os.path.join(root_dir, "log_level.json")
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, mode='r') as f:
                cfg_dict = json.loads(f.read())
                if "log_level" in cfg_dict.keys():
                    level = int(cfg_dict["log_level"])
                    if 0 <= level and level <= 3:
                        log_level = level
        except Exception as e:
            # Must be print, because there are no self.log objects at this point
            print "Error: Read log level config failed, msg: %s, use default %d" % (str(e), log_level)
    if log_level < 0 or len(LOG_LEVEL) < log_level:
        log_level = g_default_level
    else:
        log_level = LOG_LEVEL[log_level]

    if g_log_level != log_level:
        g_log_level = log_level
        logger.setLevel(log_level)
        for handler in logger.handlers:
            handler.setLevel(log_level)


def parse_args():
    parser = argparse.ArgumentParser(description='camera pic upload')
    parser.add_argument('-v', '--version', action='store_true', help='show version and exit')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--debug', action='store_true', help='print message with level DEBUG')
    group.add_argument('--info', action='store_true', help='print message with level INFO')
    group.add_argument('--warn', action='store_true', help='print message with level WARNING')
    group.add_argument('--error', action='store_true', help='print message with level ERROR')

    parser.add_argument('--local', type=str, default="", help='The local dir where capture pic save in')
    parser.add_argument('--urlpref', type=str, default="", help='The pic url prefix, must be together with --local')
    parser.add_argument('--interval', type=int, default=2, help='scan db interval sec')
    parser.add_argument('--loopnum', type=int, default=0, help='scan db num')
    parser.add_argument('--timeout', type=int, default=10, help='The max timeout(seconds) when connect camera')
    parser.add_argument('--cloudpath', type=str, default="", help='The cloud path where pic upload to azure')
    parser.add_argument('--threadnum', type=int, default=5, help='Maximum number of simultaneous tasks')
    parser.add_argument('--imgpath', type=str, default="", help='img path, example /videos/cameraid/date/')
    return parser.parse_args()


def main():
    '''
    Camera acquisition process：
    1. PHP inserts the camera information to be collected into the database
       table when AdminConsole click capture button.
    2. Running a Python program locally scans the table continuously (every 2s)
       through db-rest.
    3. After scanning the acquisition requirements, collect the images and
       upload Azure by calling the interface of db-rest. Meanwhile, update
       the field vm_camera.screen_capture. It is recommended to use short
       uuid for the image name.
    The database table：vm_camera_picture_collect
    Fields:
    id
    camera_id
    capture_status :
        0 --- new request, untreated
        1 --- requested, wait process
        2 --- processed, success
       -1 --- processed, failed
    remark：If processing fails, fill in the reason for failure.
    create_time
    update_time
    '''
    root_dir = get_file_dir(__file__)
    args = parse_args()
    if args.version:
        print('camera_pic_upload %s, %s' % (BUILD_VERSION, BUILD_DATE))
        sys.exit(0)

    init_log(args)
    log = logging.getLogger(LOG_TAG)
    log.info("")
    log.info("")
    log.info("main start...")

    interval_s = 2
    if 0 <= args.interval and args.interval < 300:
        interval_s = args.interval
        log.info("Find param interval=%d" % (interval_s))

    loopnum = 0
    if 0 <= args.loopnum:
        loopnum = args.loopnum
        log.info("Find param loopnum=%d" % (loopnum))

    if args.local.strip() != "" and args.urlpref.strip() == "":
        log.error("Find param --local, but --urlpref is empty")
        return -1

    up = CameraPicUpload(LOG_TAG, args)

    num = 0
    while loopnum == 0 or num < loopnum:
        refresh_log_level(log, root_dir)

        try:
            up.run()
        except Exception as e:
            log.error("camera_pic_upload run failed, msg: %s" % (str(e)))
            log.error(traceback.format_exc())

        if interval_s == 0:
            break
        num += 1

        try:
            time.sleep(interval_s)
        except KeyboardInterrupt:
            log.info("Keyboard interrupt")
            sys.exit(0)
    log.info("run over")


if __name__ == '__main__':
    clean_tmp()
    main()
