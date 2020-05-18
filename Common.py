# -*- coding: utf-8 -*-

"""
*Author: team of develop platform(vmaxx)
*Date:2018-10
*The source code made by our team is opened
*Take care of it please and welcome to update it 
"""
import os
import time
import datetime
import cv2
import shutil
import math
import traceback


# Return code
class RetCode:
    SUCCESS = 0
    DECODE_OVER = 1
    NO_FRAME = 2
    NO_BODY = 3

    INTERRUPT = -1
    INTERNAL_ERROR = -2
    MALLOC_ERROR = -3
    OTHER = -4

    UNINIT = -255


# Algo define
class AlgoDef:
    CPU_DECODE = 0
    GPU_DECODE = 1
    V4L2_DECODE = 2

    RGB2BGR = 0
    BGR2RGB = 1

    BILINEAR = 0
    BICUBIC = 1
    NEAREST = 2
    LETTERBOX = 3

    CpuData = 0
    GpuData = 1

    FP32 = 0
    FP16 = 1

    FHORIZONTAL_AXIS = 0
    FVERTICAL_AXIS = 1
    FBOTH_AXIS = 2


# Common function
save_img_idx = 0


def mk_dir(path):
    # wipe off unnecessary space
    path = path.rstrip()
    if path.endswith("/"):
        if not os.path.exists(path):
            os.makedirs(path)
    else:
        _, file_name = os.path.split(path)
        if file_name and ("." in file_name):
            path = os.path.dirname(path)
        if not os.path.exists(path):
            os.makedirs(path)


def get_file_dir(file_name):
    return "%s/" % (os.path.dirname(os.path.abspath(file_name)))


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


def save_img(img_dir, img, *tupleArg):
    global save_img_idx
    mk_dir(img_dir)
    filename = "_".join(tupleArg) + "_" + str(save_img_idx) + ".png"
    cv2.imwrite(os.path.join(img_dir, filename), img)
    save_img_idx += 1


def get_frame_timestamp(start_datetime, frame_idx, fps):
    return round(time.mktime(start_datetime.timetuple()) + (frame_idx - 1) * 1. / fps, 3)


def timestamp_2_str(ts, format, save_ms=False, sep="_"):
    # format : "%Y-%m-%d %H:%M:%S"
    tmp = time.strftime(format, time.localtime(ts))
    if save_ms:
        ms = "%03d" % int(math.modf(ts)[0] * 1000)
        tmp += sep + ms
    return tmp


def move_file(src, dst, log_obj=None):
    ret = False
    if not os.access(src, os.R_OK):
        return ret

    for idx in range(3):
        try:
            mk_dir(dst)
            shutil.move(src, dst)
            ret = True
            break
        except Exception as e:
            if log_obj is not None:
                log_obj.error("move_file failed %d, src: %s, dst: %s, msg: %s" % (idx, src, dst, str(e)))
                log_obj.error(traceback.format_exc())
            time.sleep(0.5)
            continue
    return ret


def rename_file(src, dst, log_obj=None):
    ret = False
    for idx in range(3):
        try:
            mk_dir(dst)
            os.rename(src, dst)
            ret = True
            break
        except Exception as e:
            if log_obj is not None:
                log_obj.error("rename_file failed %d, src: %s, dst: %s, msg: %s" % (idx, src, dst, str(e)))
                log_obj.error(traceback.format_exc())
            time.sleep(0.5)
            continue
    return ret


def listdir(path, ext, list_name):
    if os.path.exists(path):
        for file in os.listdir(path):
            if not os.path.islink(file):
                _, _, file_ext = split_file_name(file)
                if ext and file_ext != ext:
                    continue
                file_path = os.path.join(path, file)
                if os.path.isdir(file_path):
                    listdir(file_path, list_name)
                else:
                    list_name.append(file_path)
    list_name.sort(reverse=False)


def transRet(ret, log=None, func=None):
    # ret & 0b11
    # ret & 0b11 == 0b10
    if(ret == 'SUCCESS'):  # 0
        return RetCode.SUCCESS

    retCode = RetCode.OTHER
    if(ret == 'DECODE OVER'):  # 1
        if log:
            log.warn("transRet func<{}> return {}".format(func, ret))
        retCode = RetCode.DECODE_OVER
    elif(ret == 'NO FRAME'):  # 2
        # if log:
        #     log.info("transRet func<{}> return {}".format(func, ret))
        retCode = RetCode.NO_FRAME
    elif(ret == 'MALLOC ERROR'):  # return frame  -3
        if log:
            log.error("transRet func<{}> return {}".format(func, ret))
        retCode = RetCode.MALLOC_ERROR
    elif(ret == 'NO BODY'):
        if log:
            log.warn("transRet func<{}> return {}".format(func, ret))
        retCode = RetCode.NO_BODY
    else:  # return frame  -4
        if log:
            log.error("transRet func<{}> return {}".format(func, ret))
    return retCode


def check_data_is_video(data_file_name):
    if not os.path.exists(data_file_name):
        return False

    ret = False
    postfixs = {".mp4", ".MP4", ".avi", ".AVI"}
    for postfix in postfixs:
        if data_file_name.endswith(postfix):
            ret = True
            break
    if not ret:
        return False

    return True
