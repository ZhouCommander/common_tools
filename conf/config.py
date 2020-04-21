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
