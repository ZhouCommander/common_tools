# -*- coding: utf-8 -*-

"""
/*******************************************************************************
 * Deep North Confidential
 * Copyright (C) 2018 Deep North Inc. All rights reserved.
 * The source code for this program is not published
 * and protected by copyright controlled
 *******************************************************************************/
"""
import os
import time
import datetime
import uuid

SAFEHASH = [x for x in "0123456789-abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ"]


def mk_dir(path):
    # wipe off unnecessary space
    path = path.strip()
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    if not os.path.exists(path):
        os.makedirs(path)


def get_file_dir(file_name):
    return "%s/" % (os.path.dirname(os.path.abspath(file_name)))


def get_full_path(root_dir, file_path):
    if not file_path.startswith("/"):
        return "%s%s" % (root_dir, file_path)
    return file_path


def split_file_name(full_path):
    dir, file_name = os.path.split(full_path)
    shotname, extension = os.path.splitext(file_name)
    return dir, shotname, extension


def getTimestamp():
    return int(round(time.time() * 1000))


def format_datetime_from_str(date_str, time_format):
    date_time = None
    try:
        date_time = datetime.datetime.strptime(date_str, time_format)
    except Exception:
        return date_time
    return date_time


def get_line_id(obj_data, line_name):
    try:
        lines = obj_data.DataCfgJson["vm_linespec"]
        for i in range(len(lines)):
            if lines[i]["name"] == line_name:
                return lines[i]["id"]
    except Exception:
        return "0"
    return "0"


def short_UUID():
    '''
    According to http://www.ietf.org/rfc/rfc1738.txt, encoded by uuid expanding domain generation string of characters
    Include: [0-9a-zA-Z\-_], total of 64.
    Length: (32-2)/3*2 = 20
    Remark: can use everyone on earth, don't repeat use 100 (2 ^ 120)
    :return:String
    '''
    row = str(uuid.uuid4()).replace('-', '')
    safe_code = ''
    for i in xrange(10):
        enbin = "%012d" % int(bin(int(row[i * 3] + row[i * 3 + 1] + row[i * 3 + 2], 16))[2:], 10)
        safe_code += (SAFEHASH[int(enbin[0:6], 2)] + SAFEHASH[int(enbin[6:12], 2)])
    return safe_code
