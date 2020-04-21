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
    def __init__(self,etcd_urls):
        url_list = etcd_urls.split(',')
        host_list = []
        for item in url_list:
            url = urlparse.urlparse(item)
            host = (str(url.hostname),url.port)
            host_list.append(host)
        hosts = tuple(host_list)
        self.client = etcd.Client(hosts,allow_reconnect=True)
        self.path = "/deepnorth/farm"
        assert self.client != None

    # write value to path
    def write(self, path, value,append = False ,ttl = None,prevExist = False):
        return self.client.write(path, value,append=append,ttl=ttl,prevExist = prevExist)
        
    # read value of a key
    def read(self, path):
        return self.client.read(path).value
        
    # read directry with path
    def read_dir(self, path):
        return self.client.read(path)
    
    # delete a key
    def delete(self, path):
        self.client.delete(path, recursive=True)


    def etced_regisiter(self,etcd_key,ectd_value):

        bool_flag = False
        etcd_ttl = 20
        try:
            etcd_key = self.path + etcd_key
            bool_flag =self.write(etcd_key,ectd_value,ttl = etcd_ttl,prevExist=False)
        except (etcd.EtcdAlreadyExist):
            bool_flag = self.write(etcd_key,ectd_value,ttl = etcd_ttl,prevExist=True)
        except Exception as e:
            print e
            raise e
            return False
        if bool_flag:
            return True
        else:
            return False
