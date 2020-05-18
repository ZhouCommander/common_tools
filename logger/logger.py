#!/usr/bin/python
# coding=utf-8
"""
*Author: team of develop platform(vmaxx)
*Date:2018-10
*The source code made by our team is opened
*Take care of it please and welcome to update it 
"""

import os
import logging
from logging.handlers import RotatingFileHandler


LOG_LEVELS = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'notset': logging.NOTSET,
}


def get_logger(log_file_name, max_bytes=50 * 1024 * 1024, backup_cnt=10):
    logger = logging.getLogger(log_file_name)
    level = os.getenv('DEEPNORTH_LOG_LEVEL', 'info')
    logger.setLevel(LOG_LEVELS[level])
    log_dir = './log/'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_path = log_dir + log_file_name + '.log'
    file_handler = RotatingFileHandler(log_path,
                                       mode='a',
                                       maxBytes=max_bytes,
                                       backupCount=backup_cnt)
    # define log format, e.g.
    # 2018-10-08 18:21:58,071 - test.py[line:31] - INFO - info message
    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s -\
 [pid:%(process)d] - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
