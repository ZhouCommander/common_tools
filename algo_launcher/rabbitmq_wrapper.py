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
import pika
import os
import time
import logging
cur_dir = os.path.dirname(__file__)
cfg_file = os.path.join(os.getcwd(), "rabbitmq_wrapper.json")
print cur_dir
with open(cfg_file, mode='r') as f:
    cfg_dict = json.loads(f.read())
logger = logging.getLogger(__name__)

"""
RabbitMQ Wrapper
Refer : https://github.com/pika/pika
"""


class RabbitMQ:
    def __init__(self):
        self.host = cfg_dict.get("mq_host")
        self.port = cfg_dict.get("mq_port")
        # self.user = cfg_dict.get("mq_user")
        # self.pwd = cfg_dict.get("mq_pwd")
        self.vhost = cfg_dict.get("mq_vhost")
        self.retry = cfg_dict.get("mq_connect_retry_count")
        self.channel = None
        self.connection = None

    def __GetConnect(self, forever=False):
        self.Close()
        # connect MQ and return connection.channel()
        for index in range(self.retry):
            # credentials = pika.credentials.PlainCredentials(self.user,self.pwd)
            pika_conn_params = pika.ConnectionParameters(self.host, self.port, self.vhost)  # ,credentials)
            if pika_conn_params:
                self.connection = pika.BlockingConnection(pika_conn_params)
                if self.connection:
                    self.channel = self.connection.channel()
                    if self.channel != None:
                        break
                    elif forever == True:
                        time.sleep(1)
                        print('Retry connection %s' % datetime.datetime.now())
                        continue

        if not self.channel:
            raise (NameError, "Failed connect RabbitMQ")
        else:
            return self.channel

    def Close(self):
        """
        Close connection
        """
        if self.channel != None:
            self.channel.close()
            self.channel = None
        if self.connection != None:
            self.connection.close()
            self.connection = None

    def GetQueueMsgNumber(self, queue_name):
        """
        Get message number in a queue
        """
        channel = self.__GetConnect()
        my_queue = channel.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)
        return my_queue.method.message_count

    def PutMessage(self, queue_name, message):
        """
        Send message to queue
        """
        channel = self.__GetConnect()
        # declare queue for the first time
        my_queue = channel.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)
        # get queue status for return message count
        my_queue = channel.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)
        return my_queue.method.message_count

    def FetchMessage(self, queue_name):
        """
        Fetch message from queue
        """
        while True:
            message = None
            chanl = self.__GetConnect(forever=True)
            my_queue = chanl.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)
            for method, method_frame, body in chanl.consume(queue_name):
                print(body)
                chanl.basic_ack(delivery_tag=method.delivery_tag)
                message = body
                break;
            else:
                print('failed to consume a messages from destination queue %s' % queue_name)
                time.sleep(1)
                continue

            # Cancel the consumer and return any pending messages
            requeued_messages = chanl.cancel()
            if requeued_messages > 0:
                print('Requeued %i messages' % requeued_messages)
            return message

    def FetchMessageC(self, queue_name):
        """
        Fetch message from queue without close
        """
        while True:
            message = None
            chanl = self.channel
            # check channel
            if chanl == None:
                chanl = self.__GetConnect(forever=True)
            elif chanl.is_open != True:
                chanl = self.__GetConnect(forever=True)
            try:
                if chanl != None:
                    my_queue = chanl.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)
                    for method, method_frame, body in chanl.consume(queue_name):
                        print(body)
                        chanl.basic_ack(delivery_tag=method.delivery_tag)
                        message = body
                        break
                    else:
                        print('failed to consume a messages from destination queue %s' % queue_name)
                        time.sleep(1)
                        continue
                else:
                    continue
            except Exception as e:
                logger.error(e)
                chanl= self.__GetConnect()
                self.channel = chanl
                continue
            # Cancel the consumer and return any pending messages
            requeued_messages = chanl.cancel()
            if requeued_messages > 0:
                print('Requeued %i messages' % requeued_messages)
            return message
