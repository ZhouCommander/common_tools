#!/usr/bin/ python
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
import ctypes
import signal
from multiprocessing import Lock, Process
from algo_launcher_mq import AlgoLauncher
import time


def init_log_path(log_folder_path,curr_user_log_path,algo_output_log_path):

    if not os.path.exists(log_folder_path) :
        try:
            os.mkdir(log_folder_path,0777)
            os.chmod(log_folder_path,0777)
        except Exception as e:
            print e
        
    if not os.path.exists(curr_user_log_path) :
        try:
            os.mkdir(curr_user_log_path,0777)
            os.chmod(curr_user_log_path,0777)
        except Exception as e:
            print e


    if not os.path.exists(algo_output_log_path) :
        try:
            os.mkdir(algo_output_log_path,0777)
            os.chmod(algo_output_log_path,0777)
        except Exception as e:
            print e


def run_algo(algo_num,queue_name,algo_path,algo_type,algo_output_log_path,time_out,media_path,etcd_url,sql_model):
    algo_object_list =[] 
    for gpu_idx,num in enumerate(algo_num):
        if num == -1:
            continue
        else:
            for farmer_idx in range(num):
                log_name =str(algo_type)+"_"+ str(gpu_idx)+'-'+str(farmer_idx)
                algo_object = AlgoLauncher(gpu_idx,farmer_idx,algo_path,algo_type,algo_output_log_path,queue_name,time_out,media_path,log_name,etcd_url,sql_model)
                algo_object.start()
                if algo_object.is_alive():
                    algo_object_list.append( algo_object)
    return algo_object_list


def restart_woker(worker_object):
    gpu_idx = worker_object.gpu_index
    farmer_idx = worker_object.woker_index
    algo_path = worker_object.algo_path
    algo_type = worker_object.algo_type
    algo_output_log_path = worker_object.algo_output_log_path
    queue_name = worker_object.queue_name
    time_out = worker_object.timeout
    media_path = worker_object.media_path
    log_name = worker_object.log_name
    etcd_url = worker_object.etcd_url
    algo_object = None
    try:
        algo_object = AlgoLauncher(gpu_idx,farmer_idx,algo_path,algo_type,algo_output_log_path,queue_name,time_out,media_path,log_name,etcd_url)
        algo_object.start()
    except Exception as e:
        print e
    return algo_object


def checkout_license():
    so = ctypes.CDLL('./libdeepnorth_lic.so')
    result = so.checkLicense('algo_launcher','3.0')
    return result



def algo_guard_thread(algo_object_list,sleep_time):
    while True:
        for algo in algo_object_list:
            for i in algo:
                if not i.is_alive():
                    i.start()
        time.sleep(sleep_time)

