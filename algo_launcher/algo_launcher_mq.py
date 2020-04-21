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
import logging
import sys
import os
import socket
import subprocess
import time
import json
from etcd_wrapper import ETCD
from threading import Timer
from rabbitmq_wrapper import RabbitMQ
from multiprocessing import Lock, Process
cur_dir = os.path.dirname(__file__)
log_file_path = os.path.join(os.getcwd(), "logs")



class AlgoLauncher(Process):

    def __init__(self,gpu_index,farmer_idx,algo_path,algo_type,algo_output_log_path,queue_name,timeout,media_path,log_name,etcd_url,sql_model):
        Process.__init__(self)
        self.gpu_index = gpu_index
        self.algo_path = algo_path
        self.algo_type = algo_type
        self.queue_name = queue_name
        self.timeout = timeout
        self.media_path = media_path
        self.log_name = log_name
        self.algo_output_log_path = algo_output_log_path
        self.process_object = None
        self.task_number = 1
        self.node_name = socket.gethostname()
        self.current_message = ""
        self.woker_index = farmer_idx
        self.etcd_url = etcd_url
        self.sql_model = sql_model

    def etcd_register_timer(self):

        if self.current_message:
            try:
                config = json.loads(self.current_message)
                videoname = config.get("videoname")
                cameraId = config.get("cameraId")
                ectd_value = {
                "video_file":videoname,
                "camera_id":cameraId,
                "algo_name":self.algo_type,
                "other_nessacery_info":""
                }
                etcd_key = "/{}/Gpu_index_{}_{}_{}".format(self.node_name,self.algo_type,self.gpu_index,self.woker_index)
                etcd_object = ETCD(self.etcd_url)
                if not etcd_object.etced_regisiter(etcd_key,str(ectd_value)):
                    logging.info("etcd register error")
            except Exception as e:
                print e
                logging.error(e)
        Timer(10,self.etcd_register_timer).start()


    def call_algo(self,body):
        logging.info('\n**************  Message Received **************(the %sth tasks)'%self.task_number)
        # print body
        self.task_number = self.task_number + 1
        logging.info(' ==Message Body==:   ' +body)
        tic = time.time()
        time_out_flag = False
        cm = 'python {}/{}.py'.format(self.algo_path,self.algo_type)+' --message  '+"'" +body+"'"+' --gpu_index {} --nfs {} --sql_model {}'.format(self.gpu_index,self.media_path,self.sql_model)
        try:
            ret = None
            algo_output_log_file = os.path.join(self.algo_output_log_path,"%s_out.log"%self.log_name)
            print algo_output_log_file
            with open(algo_output_log_file,'a+') as f:
                ret = subprocess.Popen(cm,shell=True,stdout=f)
        except Exception as e:
            logging.error(e)
            ret.kill()
            return False
        time_last = 0
        # timeout judger
        while ret.poll() == None:
            if self.timeout != -1:
                time_last = time.time()-tic
                if time_last >=  self.timeout:
                    logging.error('Task timeout: {}'.format(body))
                    logging.error('\n**************  Task Time Out, timeout threshold={},  time cost: {}  **************\n\n\n'.format( self.timeout,time.time()-tic))
                    ret.kill()
                    time_out_flag = True
                    break
            time.sleep(3)
        else:
            if time_out_flag:
                return False
            tac = time.time()
            time_cost = tac-tic
            error_message = ret.communicate()[1]
            if ret.poll() == 0:
                logging.info('\n**************  Task Complete, time cost: {} **************\n\n\n'.format(time_cost))
                return True
            else:
                logging.error('\n**************  Task Error, Rejected **************\n\n\n') 
                logging.error(error_message)
                return False
    

    def run(self):
        logging.basicConfig(filename='{}/{}/{}.log'.format(log_file_path,self.node_name,self.log_name),
            filemode='a',
            level=logging.INFO,
            format='\n %(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s \n',
            datefmt='%a, %d %b %Y %H:%M:%S')
        logging.info(' [*] Waiting for messages. To exit press CTRL+C \n')
        ramq_object = RabbitMQ()
        error_flag = 0
        
        if self.etcd_url :
            Timer(10,self.etcd_register_timer).start()
            logging.info("etcd"+self.etcd_url)

        while ramq_object:
            self.current_message = ""
            try:
                self.current_message = ramq_object.FetchMessageC(queue_name=self.queue_name)
                if  self.current_message:
                    bool_call_algo = self.call_algo(body = self.current_message)
                    if not bool_call_algo:
                        error_flag = error_flag + 1
                        if error_flag >5:
                            break
                    else:
                        error_flag = 0
                        continue
            except Exception as e:
                logging.error(e)
                try:
                    ramq_object.Close()
                except Exception as e:
                    print e
                ramq_object = RabbitMQ()
                continue
            time.sleep(3)
