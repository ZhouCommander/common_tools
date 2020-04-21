#!/usr/bin/env python
# coding=utf-8
"""
/*******************************************************************************
 * Deep North Confidential
 * Copyright (C) 2018 Deep North Inc. All rights reserved.
 * The source code for this program is not published 
 * and protected by copyright controlled
 *******************************************************************************/
"""

from etcd_wrapper import ETCD
import argparse
import os
import etcd
import json
from prettytable import PrettyTable
parser = argparse.ArgumentParser()
parser.add_argument("--url", help="etcd url (http://x.x.x.x:port)")
args = parser.parse_args()
etcd_path = "/deepnorth/farm"
etcd_url = args.url

def get_etcd_content(etcd_url):
    worker_list = []
    try:
        etcd_object = ETCD(etcd_url)
        lines = etcd_object.read_dir(etcd_path)
    except (etcd.EtcdKeyNotFound) as e:
        print e
        return None
    try:
        for children_path in lines._children:
            keys = etcd_object.read_dir(children_path.get('key'))
            host_name = children_path.get('key')
            client_info = {
                "host_name" : "",
                "gpu_worker" : [
                ]
            }
            client_info.update({'host_name':str(host_name).split('/')[-1]})
            for key in keys._children:
                work_info = {
                    "worker_name":"",
                    "worker_message":""
                }
                gpu_worker = key.get('key')
                work_info.update({'worker_name':str(gpu_worker).split('/')[-1]})
                value = etcd_object.read(key.get('key'))
                work_info.update({'worker_message':value})
                client_info['gpu_worker'].append(work_info)       
            worker_list.append(client_info)
        return worker_list     
    except Exception as e:
        print e
        return None

if __name__ =="__main__":
    if not etcd_url :
        print '''ERROR:Please input a etcd url  or input "./view -h" for help'''
    else:
        print "\nETCD SERVER : "+etcd_url
        work_list = get_etcd_content(etcd_url)
        if work_list is None:
            print "ETCD SERVER ACQUIRE MESSAGE ERROR !"
        else:
            total_index = 1
            table = PrettyTable(["Total index", "Sub index", "Gpu index","Host name", "Algo name","Video info"])
            table.padding_width = 1
            for node in work_list:
                index = 1
                for work in node.get('gpu_worker'):
                    gpu_index = str(work.get('worker_name')).split('_')[-2]
                    message = eval(work.get('worker_message'))
                    str_videos = ""
                    for video in message.get('video_file'):
                        str_videos += str(video).split('/')[-1]+"  "
                    table.add_row([str(total_index),str(index),str(int(gpu_index)+1), node.get('host_name'), message.get('algo_name'),str_videos])
                    index+=1
                    total_index+=1
            print table
