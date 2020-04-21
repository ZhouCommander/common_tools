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

import time
import etcd
import json
import multiprocessing
import traceback
import conf
import etcd_util
from log import worker_logger
from log import sync_algo_data_logger as logger

LINE_SPEC_ETCD_PATH = "/db/vm_linespec"
POLYGON_SPEC_ETCD_PATH = "/db/vm_polygonspec"
CAMERA_ETCD_PATH = "/db/vm_camera"

lock = multiprocessing.Lock()
mgr = multiprocessing.Manager()
# key -> camera_id value -> algo data
all_algo_data = mgr.dict()


def get_all_algo_data():
    return all_algo_data


def sync_algo_data_from_etcd():
    logger.debug('call sync_algo_data_from_etcd')

    while True:
        try:
            fetch_algo_data()
        except Exception as e:
            logger.error("sync_algo_data_from_etcd find except, msg: %s" % (str(e)))
        time.sleep(conf.sched_conf.algo_data_sync_period_sec)


def get_vmtable_data(etcd_path, client):
    data_list = []
    try:
        records = etcd_util.read_ext(etcd_path, client=client)
        if records:
            for vm_table_line_key in records.children:
                line = client.read(vm_table_line_key.key)  # /db/vm_camera/id
                vm_table_dict = {}
                for line_arg in line.children:
                    vm_table_dict[line_arg.key[len(vm_table_line_key.key) + 1:]] = line_arg.value
                if vm_table_dict and len(vm_table_dict) > 1:
                    data_list.append(vm_table_dict)
    except etcd.EtcdKeyNotFound:
        logger.warn('The key {} not exists, failed to get info from etcd'.format(etcd_path))
    except Exception as e:
        logger.error('Failed to get key {} from etcd: {} '.format(etcd_path, e))
        logger.error(traceback.format_exc())

    return data_list


def fetch_algo_data():
    starttime = time.time()
    logger.debug('call fetch_algo_data')
    client = etcd_util.new_client()
    if client is None:
        logger.error('fetch_algo_data error: failed to new etcd client')
        # sys.exit(0)
        return

    all_camera = get_vmtable_data(CAMERA_ETCD_PATH, client)
    if not all_camera:
        logger.error('failed to read etcd key <{}>'.format(CAMERA_ETCD_PATH))
        return

    all_line = get_vmtable_data(LINE_SPEC_ETCD_PATH, client)
    all_polygon = get_vmtable_data(POLYGON_SPEC_ETCD_PATH, client)

    for camera_rec in all_camera:
        if camera_rec['enabled'] != '0':
            algo_data_conf = {}

            algo_data_conf['vm_linespec'] = []
            for line_rec in all_line:
                if line_rec['camera_id'] == camera_rec['id'] and line_rec['enabled'] != '0':
                    algo_data_conf['vm_linespec'].append(line_rec)

            algo_data_conf['vm_polygonspec'] = []
            for polygon_rec in all_polygon:
                if polygon_rec['camera_id'] == camera_rec['id'] and polygon_rec['enabled'] != '0':
                    algo_data_conf['vm_polygonspec'].append(polygon_rec)

            algo_data_conf['camera'] = camera_rec
            algo_data_conf['msg_body'] = None

            with lock:
                all_algo_data[int(camera_rec['id'])] = algo_data_conf

    logger.debug('fetch_algo_data use <{}>, all_algo_data is :<{}>'.format(time.time() - starttime, all_algo_data))


def get_algo_data(msg, logger=worker_logger):
    camera_id = msg.get('camera_id', None)
    if camera_id is None:
        logger.error('invalid msg <{}>, failed to get camera_id'.format(msg))
        return None

    logger.info('get camera_id <{}> algo data'.format(camera_id))

    try:
        with lock:
            algo_conf = all_algo_data.get(int(camera_id), None)
            if algo_conf is None:
                logger.error('failed to get msg <{}> algo conf, all_algo_data is <{}>'.format(msg, all_algo_data))
                return None
            algo_conf['msg_body'] = msg
            algo_str = json.dumps(algo_conf)
    except Exception as e:
        logger.error('get_algo_data find exception, msg: {}'.format(e))
        logger.error(traceback.format_exc())
        algo_str = None

    logger.info('get_algo_data camera_id<{}> algo_conf is {}'.format(camera_id, algo_str))
    return algo_str


def get_line_from_etcd(client, camera_id, logger):
    logger.info('get_line_from_etcd camera_id<{}>'.format(camera_id))
    # client = etcd_util.new_client(logger=logger)

    line_list = []
    try:
        # logger.debug('get_line_from_etcd camera_id {}.'.format(camera_id))
        lines = client.read(LINE_SPEC_ETCD_PATH)
        for line_key in lines.children:
            line = client.read(line_key.key)
            camera_in_line = False
            line_dict = {}
            key_len = len(line_key.key) + 1
            key_camera_id = line_key.key + '/camera_id'
            for line_arg in line.children:
                line_dict[line_arg.key[key_len:]] = line_arg.value
                if line_arg.key == key_camera_id and str(camera_id) == line_arg.value:
                    camera_in_line = True
            if camera_in_line and line_dict["enabled"] == "1":
                line_list.append(line_dict)

    except etcd.EtcdKeyNotFound:
        logger.warn('the key {} doesn’t exists, failed to get line info from etcd'.format(LINE_SPEC_ETCD_PATH))

    except Exception as e:
        logger.error('failed to get line info from etcd: {} '.format(e))

    # logger.debug('leave get_line_from_etcd')
    return line_list


def get_camera_from_etcd(client, camera_id, logger):
    logger.info('get_camera_from_etcd camera_id<{}>'.format(camera_id))
    # client = etcd_util.new_client()

    camera_dict = {}
    try:
        # logger.debug('get_camera_from_etcd camera_id {}.'.format(camera_id))
        camera_full_path = CAMERA_ETCD_PATH + '/' + str(camera_id)
        camera_path_len = len(camera_full_path) + 1
        camera = client.read(camera_full_path)
        for camera_key in camera.children:
            camera_dict[camera_key.key[camera_path_len:]] = camera_key.value
    except etcd.EtcdKeyNotFound:
        logger.warn('the key {} doesn’t exists, failed to get camera info from etcd'.format(CAMERA_ETCD_PATH))

    except Exception as e:
        logger.error('failed to get camera info from etcd: {} '.format(e))

    # logger.debug('leave get_camera_from_etcd')
    if camera_dict["enabled"] != "0":
        return camera_dict
    return None


def get_polygon_from_etcd(client, camera_id, logger):
    logger.info('get_polygon_from_etcd camera_id<{}>'.format(camera_id))
    # client = etcd_util.new_client(logger=logger)

    polygon_list = []
    try:
        # logger.debug('get_polygon_from_etcd camera_id {}.'.format(camera_id))
        polygons = client.read(POLYGON_SPEC_ETCD_PATH)
        for polygon_key in polygons.children:
            polygon = client.read(polygon_key.key)
            camera_in_polygon = False
            polygon_dict = {}
            key_len = len(polygon_key.key) + 1
            key_camera_id = polygon_key.key + '/camera_id'
            for polygon_arg in polygon.children:
                polygon_dict[polygon_arg.key[key_len:]] = polygon_arg.value
                if polygon_arg.key == key_camera_id and str(camera_id) == polygon_arg.value:
                    camera_in_polygon = True
            if camera_in_polygon and polygon_dict["enabled"] == "1":
                polygon_list.append(polygon_dict)

    except etcd.EtcdKeyNotFound:
        logger.warn('the key {} doesn’t exists, failed to get polygon info from etcd'.format(POLYGON_SPEC_ETCD_PATH))

    except Exception as e:
        logger.error('failed to get polygon info from etcd: {} '.format(e))

    # logger.debug('leave get_polygon_from_etcd')
    return polygon_list
