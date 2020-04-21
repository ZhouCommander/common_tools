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

import os
import etcd
import json
import urlparse


class ETCD(object):
    def __init__(self, cfg_json):
        etcd_url = cfg_json.get("etcd_urls")
        url_list = etcd_url.split(',')
        host_list = []
        for item in url_list:
            url = urlparse.urlparse(item)
            host = (str(url.hostname),url.port)
            host_list.append(host)

        hosts = tuple(host_list)

        self.hosts = hosts
        self.client = etcd.Client(hosts,allow_reconnect=True)
        assert self.client != None

    # write value to path
    def write(self, path, value):
        self.client.write(path, value)

    # read value of a key
    def read(self, path):
        return self.client.read(path).value

    # read directry with path
    def read_dir(self, path):
        return self.client.read(path)

    # delete a key
    def delete(self, path):
        self.client.delete(path, recursive=True)
