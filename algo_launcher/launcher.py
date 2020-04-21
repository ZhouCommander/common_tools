
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

import json
import subprocess
import GPUtil
import argparse
import os
import signal
import socket
import ctypes
import time
import threading
from launcher_lib import *
# add Argument
parser = argparse.ArgumentParser()
parser.add_argument("--kill", help="kill all farmers", action="store_true")
parser.add_argument("--config_path", help="config file path")
args = parser.parse_args()
algo_config_path = args.config_path
cur_dir = os.path.dirname(__file__)
algo_path = os.path.join(cur_dir,"adaptor")
log_folder_path = os.path.join(os.getcwd(), "logs")
node_name = socket.gethostname()
curr_user_log_path =os.path.join(log_folder_path, node_name)
algo_output_log_path = os.path.join(curr_user_log_path,"algo_output_logs")


if __name__ == '__main__':

    if args.kill:
        os.system("sudo kill -9 `ps -ef|grep adaptor|awk '{print $2}'`")
        os.system("sudo kill -9 `ps -ef|grep launcher|awk '{print $2}'`")

    else:
        if not algo_config_path :
            print '''ERROR:Please input a config file path  or input "./launcher -h" for help'''
        elif True:
            init_log_path(log_folder_path,curr_user_log_path,algo_output_log_path)
            with open(algo_config_path) as f:
                cfg = json.load(f)
            alist = cfg.get('Algo_List')
            etcd_url = cfg.get('etcd_url')
            sql_model = cfg.get('sql_model')
            algo_object_list = []
            for conf_json in alist:
                algo_num = conf_json["gpu"]
                algo_type = conf_json["adaptor"]
                queue_name = conf_json["Q_name"]
                time_out = conf_json["timeout"]
                media_path = conf_json["algo_path"]
                algo_object = run_algo(algo_num, queue_name,algo_path, algo_type,algo_output_log_path, time_out,media_path,etcd_url,sql_model)
                algo_object_list.append(algo_object)
            print "launcher successful..."
            while True:
                for algo in algo_object_list:
                    for i in algo:
                        if not i.is_alive():
                            try:
                                new_worker_object = restart_woker(i)
                                if not new_worker_object:
                                    i = new_worker_object
                            except Exception as e:
                                print e
                time.sleep(3)
        else:
            print"<WARNING: your License has expired,Please contact us www.deepnorth.cn >"









