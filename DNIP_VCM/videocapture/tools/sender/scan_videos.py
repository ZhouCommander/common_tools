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
import os
import sys
import shutil
import time
import json
from rabbitmq_wrapper import RabbitMQ
from etcd_wrapper import ETCD


def _sendToMq(queue_name, msg, mq=None):
    if not mq:
        mq = RabbitMQ()
    num = mq.PutMessage(queue_name=queue_name, message=msg)
    mq.Close()
    print "Send msg: %s to %s, return %d" % (msg, queue_name, num)


def _listdir(path, list_name):
    if os.path.exists(path):
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isdir(file_path):
                _listdir(file_path, list_name)
            else:
                list_name.append(file_path)
    list_name.sort(reverse=False)


def split_file_name(full_path):
    dir, file_name = os.path.split(full_path)
    shotname, extension = os.path.splitext(file_name)
    return dir, shotname, extension


def listdir(path, camera_ids=None, video_time_start=None, video_time_end=None, exts=None, sort_reverse=False, with_path=True, ext_sep=";", log=None):
    list_file = []
    if os.path.exists(path):
        for top, dirs, nondirs in os.walk(path):
            for item in nondirs:
                _, file_name, file_ext = split_file_name(item)
                if exts and file_ext not in exts:
                    continue
                fn = file_name.split("_")
                if len(fn) != 3:
                    continue
                if camera_ids and int(fn[0]) not in camera_ids:
                    continue
                if video_time_start and fn[1] < video_time_start:
                    continue
                if video_time_end and video_time_end <= fn[1]:
                    continue

                if with_path:
                    list_file.append(os.path.join(top, item))
                else:
                    list_file.append(item)
    if list_file:
        list_file.sort(reverse=sort_reverse)
    return list_file


def _mk_dir(path):
    # wipe off unnecessary space
    path = path.rstrip()
    if path.endswith("/"):
        if not os.path.exists(path):
            os.makedirs(path)
    else:
        _, file_name = os.path.split(path)
        if file_name and ("." in file_name):
            path = os.path.dirname(path)
        if not os.path.exists(path):
            os.makedirs(path)

def _split_file_name(full_path):
    dir, file_name = os.path.split(full_path)
    shotname, extension = os.path.splitext(file_name)
    return dir, shotname, extension


def usage():
    print "Usage:"
    print "    %s CFG_FILE" % (sys.argv[0])
    print "    sample:"
    print "      python %s scan_videos.json" % (sys.argv[0])
    print ""


def _read_camera_algo(cfg_json):
    info = {}
    etcdwrapper = ETCD(cfg_json)
    try:
        r = etcdwrapper.read_dir('/db/vm_camera/')
        for child in r.children:
            ret = child.key
            camera_id = str(ret.split("/")[-1])
            # print "find camera id: ", camera_id

            if str(camera_id) not in info:
                try:
                    etcd_dir = '/db/vm_camera/{row_id}/algo_parameter_id'.format(row_id=camera_id)
                    algo_id = etcdwrapper.read(etcd_dir)
                    # print "find algo_id: ", algo_id, type(algo_id)
                    if algo_id and algo_id != "None":
                        algo_dir = '/db/vm_algo_parameter/{row_id}/name'.format(row_id=algo_id)
                        algo_name = etcdwrapper.read(algo_dir)
                        info[str(camera_id)] = algo_name
                except Exception as e:
                    print "Read camera<%s>'s algo name failed, msg: %s" % (str(camera_id), str(e))
    except Exception as e:
        print "Read ETCD failed, msg: %s" % (str(e))
    print "Find camera' algo name: ", info
    return info


def main():
    cfg_file = "scan_videos.json"
    if len(sys.argv) >= 2:
        cfg_file = sys.argv[1]

    cfg_json = {}
    try:
        with open(cfg_file, mode='r') as f:
            cfg_json = json.loads(f.read())
    except Exception as e:
        print "error: Read config failed"
        return

    new_camera_ids = []
    ids = cfg_json["camera_ids"]
    if len(ids) > 0:
        for idx in range(len(ids)):
            if isinstance(ids[idx], int):
                new_camera_ids.append(ids[idx])
            else:
                tmp = ids[idx].split("-")
                cur_id = int(tmp[0])
                while cur_id <= int(tmp[1]):
                    new_camera_ids.append(int(cur_id))
                    cur_id += 1
        new_camera_ids = list(set(new_camera_ids))
        new_camera_ids.sort()
    cfg_json["camera_ids"] = new_camera_ids

    queue_name = _read_camera_algo(cfg_json)
    if not queue_name:
        print "error: Read camera info from ETCD failed"
        return

    video_bak_path = cfg_json["video_bak_dir"]
    if video_bak_path:
        if not video_bak_path.endswith("/"):
            video_bak_path += "/"
        _mk_dir(video_bak_path)

    mq = RabbitMQ(cfg_json)

    videos = listdir(cfg_json["video_dir"], cfg_json["camera_ids"], cfg_json["video_time_start"], cfg_json["video_time_end"], cfg_json["video_exts"])
    if videos:
        for video in videos:
            try:
                _, video_name, ext = _split_file_name(video)
                time_now = time.time()
                time_last_modify = os.path.getmtime(video)
                if (time_now - time_last_modify) > 60:
                    if video_bak_path:
                        shutil.move(video,video_bak_path)
                    names = video_name.split("_")
                    camera_id = names[0]
                    date = names[1].split("-")
                    video_date = "%s-%s-%s %s:%s:%s" % (date[0], date[1], date[2], date[3], date[4], date[5])
                    if camera_id in queue_name:
                        if video_bak_path:
                            msg = {"camera_id": int(camera_id), "capture_time": video_date,
                               "capture_duration_seconds": int(names[2]), "file_path": video_bak_path + video_name + ext}
                        else:
                            msg = {"camera_id": int(camera_id), "capture_time": video_date,
                               "capture_duration_seconds": int(names[2]), "file_path": video}
                        _sendToMq(queue_name[camera_id], json.dumps(msg), mq=mq)
            except Exception as e:
                print "Process %s failed, msg: %s" % (video, str(e))


if __name__ == "__main__":
    main()
