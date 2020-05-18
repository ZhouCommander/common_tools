#!/usr/bin/python
# coding=utf-8
"""
*Author: team of develop platform(vmaxx)
*Date:2018-10
*The source code made by our team is opened
*Take care of it please and welcome to update it 
"""

import os
import json


def get_conf(config_file, default_conf=None):
    if os.path.isfile(config_file):
        with open(config_file) as f:
            try:
                conf_dict = json.load(f)
                return conf_dict
            except ValueError:
                print 'invalid json config file <{}>, use default \
config'.format(config_file)

                return default_conf
    else:
        print 'no configuration file <{}>, use default \
config'.format(config_file)

        return default_conf
