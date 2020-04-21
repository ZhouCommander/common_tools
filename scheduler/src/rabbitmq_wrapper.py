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

import pika
import datetime
import time

from log import scheduler_logger as logger
"""
RabbitMQ Wrapper
Refer : https://github.com/pika/pika
"""


class RabbitMQ:
    def __init__(self, host, port, retry_count=10):
        self.host = host
        self.port = port
        # self.user = cfg_dict.get("mq_user")
        # self.pwd = cfg_dict.get("mq_pwd")
        self.vhost = "/"
        self.retry = retry_count
        self.channel = None
        self.connection = None

        self.blocked_conn_timeout = 10

    def __GetConnect(self, forever=False):
        # self.Close()
        # connect MQ and return connection.channel()

        for index in range(self.retry):
            try:
                # credentials = pika.credentials.PlainCredentials(self.user,self.pwd)
                # pika_conn_params = pika.ConnectionParameters(self.host, self.port, self.vhost)  # ,credentials)
                pika_conn_params = pika.ConnectionParameters(self.host, self.port, self.vhost,
                                                             blocked_connection_timeout=self.blocked_conn_timeout)
                if pika_conn_params:
                    self.connection = pika.BlockingConnection(pika_conn_params)
                    if self.connection:
                        self.channel = self.connection.channel()
                        if self.channel is not None:
                            break
                logger.debug('Retry connection<%d> %s' % (index, datetime.datetime.now()))
            except Exception as e:
                logger.warn('Find connect exception<%d>, msg: %s' % (index, str(e)))

            time.sleep(1)

        if not self.channel:
            raise (NameError, "Failed connect RabbitMQ")
        else:
            return self.channel

    def Close(self):
        """
        Close connection
        """
        if self.channel is not None:
            try:
                self.channel.close()
                self.channel = None
            except Exception as e:
                logger.warn('close rabbit mq: %s' % (str(e)))
        if self.connection is not None:
            try:
                self.connection.close()
                self.connection = None
            except Exception as e:
                logger.warn('close rabbit mq: %s' % (str(e)))

    def GetQueueMsgNumber(self, queue_name):
        """
        Get message number in a queue
        """
        try:
            channel = self.__GetConnect(forever=True)
        except Exception as e:
            logger.warn('Get connection failed, msg: %s' % (str(e)))
            return 0

        my_queue = channel.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)
        return my_queue.method.message_count

    def PutMessage(self, queue_name, message):
        """
        Send message to queue
        """
        try:
            channel = self.__GetConnect()
        except Exception as e:
            logger.warn('Get connection failed, msg: %s' % (str(e)))
            return 0

        # declare queue for the first time
        my_queue = channel.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)
        # get queue status for return message count
        my_queue = channel.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)
        return my_queue.method.message_count

    def FetchMessage(self, queue_name):
        message = None
        for i in range(self.retry):
            try:
                try:
                    chanl = self.__GetConnect(forever=True)
                except Exception as e:
                    self.Close()
                    logger.warn('Get connection failed, msg: %s' % (str(e)))
                    time.sleep(1)
                    continue

                method, _, body = chanl.basic_get(queue_name)
                if method:
                    chanl.basic_ack(method.delivery_tag)
                    message = body
                    self.Close()
                    break
                time.sleep(1)

            except Exception as e:
                self.Close()
                logger.error('failed to fetch msg from queue <{}>, error: <{}>'.format(queue_name, e))
                time.sleep(1)

        return message

    def FetchMessageC(self, queue_name):
        """
        Fetch message from queue without close
        """
        message = None
        for i in range(self.retry):
            # check channel
            if self.channel is None:
                try:
                    self.channel = self.__GetConnect(forever=True)
                except Exception as e:
                    self.Close()
                    logger.warn('Get connection failed in FetchMessageC, msg: %s' % (str(e)))
                    time.sleep(1)
                    continue

            if self.channel.is_open is not True:
                try:
                    self.channel = self.__GetConnect(forever=True)
                except Exception as e:
                    self.Close()
                    logger.warn('Get connection failed in FetchMessageC, msg: %s' % (str(e)))
                    continue

            try:
                method, _, body = self.channel.basic_get(queue_name)
                if method:
                    self.channel.basic_ack(method.delivery_tag)
                    message = body
                    break
            except Exception as e:
                self.Close()
                logger.error('failed to fetch msg from queue <{}>, error: <{}>'.format(queue_name, e))
            time.sleep(1)

        return message

    '''
    def FetchMessage(self, queue_name):
        # Fetch message from queue
        while True:
            message = None
            try:
                chanl = self.__GetConnect(forever=True)
            except Exception as e:
                self.Close()
                logger.warn('Get connection failed, msg: %s' % (str(e)))
                time.sleep(1)
                continue

            my_queue = chanl.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)
            for method, method_frame, body in chanl.consume(queue_name):
                chanl.basic_ack(delivery_tag=method.delivery_tag)
                message = body
                self.Close()
                break
            else:
                self.Close()
                logger.error('failed to consume a messages from destination queue %s' % queue_name)
                time.sleep(1)
                continue

            # Cancel the consumer and return any pending messages
            requeued_messages = chanl.cancel()
            if requeued_messages > 0:
                logger.debug('Requeued %i messages' % requeued_messages)
            self.Close()
            return message
    '''

    # def FetchMessageC(self, queue_name):
    #     """
    #     Fetch message from queue without close
    #     """
    #     while True:
    #         message = None
    #         chanl = self.channel
    #         # check channel
    #         if chanl is None:
    #             chanl = self.__GetConnect(forever=True)
    #         elif chanl.is_open is not True:
    #             chanl = self.__GetConnect(forever=True)
    #         try:
    #             if chanl is not None:
    #                 chanl.queue_declare(queue=queue_name, durable=True, exclusive=False, auto_delete=False)
    #                 for method, method_frame, body in chanl.consume(queue_name):
    #                     chanl.basic_ack(delivery_tag=method.delivery_tag)
    #                     message = body
    #                     break
    #                 else:
    #                     logger.error('failed to consume a messages from destination queue %s' % queue_name)
    #                     time.sleep(1)
    #                     continue
    #             else:
    #                 continue
    #         except Exception as e:
    #             logger.error(e)
    #             chanl = self.__GetConnect()
    #             self.channel = chanl
    #             continue
    #         # Cancel the consumer and return any pending messages
    #         requeued_messages = chanl.cancel()
    #         if requeued_messages > 0:
    #             logger.debug('Requeued %i messages' % requeued_messages)
    #         return message
