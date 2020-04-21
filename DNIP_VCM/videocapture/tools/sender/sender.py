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

import sys
from rabbitmq_wrapper import RabbitMQ


def _sendToMq(queue_name, msg):
    mq = RabbitMQ()
    num = mq.PutMessage(queue_name=queue_name, message=msg)
    mq.Close()
    print "Send msg: %s to %s, return %d" % (msg, queue_name, num)


def usage():
    print "Usage:"
    print "    %s QUEUE_NAME MSG_JSON_STR" % (sys.argv[0])
    print "    sample:"
    print "      python %s cam_1 \"{'camera_id':'1', 'capture_time':'2018-12-14 10:0:0', 'capture_duration_seconds':'60', 'file_path':'/home/deepnorth/xxx.mp4'}\"" % (sys.argv[0])
    print ""


def main():
    if len(sys.argv) != 3:
        usage()
        return
    _sendToMq(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
