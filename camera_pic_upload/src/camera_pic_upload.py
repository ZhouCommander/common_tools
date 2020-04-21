# -*- coding: utf-8 -*-

"""
/*******************************************************************************
 * Deep North Confidential
 * Copyright (C) 2018 Deep North Inc. All rights reserved.
 * The source code for this program is not published
 * and protected by copyright controlled
 *******************************************************************************/
"""
import os
import logging
import shutil
import subprocess
import datetime

import rest_sql_wrapper as REST
from Common import *
from itertools import ifilter

class CameraPicUpload:
    log_tag = "CameraPicUpload"

    '''
    capture_status :
        0 --- new request, untreated
        1 --- requested, wait process
        2 --- processed, success
       -1 --- processed, failed
    '''
    # Do not modify this enum
    status_e = {"untreated": 0, "processing": 1, "over": 2, "failed": -1}

    def __init__(self, log_tag, args):
        tag = "%s.%s" % (log_tag, self.log_tag)
        self.log = logging.getLogger(tag)
        self.log.info("CameraPicUpload __init__")
        self.rest = REST.rest_sql_wrapper(tag)
        # self.RootDir = get_file_dir(__file__)
        self.RootDir = os.getcwd() + "/"
        self.tb_camera = "vm_camera"
        self.tb_tasks = "vm_camera_picture_collect"
        self.cloud_path = "dashboardv1_01/adminconsole/"
        self.timeout_s = 10
        self.save_dir = "%scache" % (self.RootDir)
        self.local = ""
        self.urlpref = ""
        self.thread_num = 5
        self.imgpath = ""
        self._init_cfg(args)
        self.log.info("param: RootDir=%s save_dir=%s local=%s urlpref=%s timeout=%d cloud_path=%s imgpath=%s" %
                      (self.RootDir, self.save_dir, self.local, self.urlpref, self.timeout_s, self.cloud_path, self.imgpath))

    def run(self):
        tasks = self._get_tasks()
        for idx in range(len(tasks)):
            successed = False
            id = int(tasks[idx]["id"])
            camera_id = int(tasks[idx]["camera_id"])
            self._update_task_status(id, CameraPicUpload.status_e["processing"], None)
            stream_url = self._get_stream_url(camera_id)
            if stream_url is not None and stream_url.strip() != "":
                stream_url = stream_url.strip()
                if self.imgpath != "":
                    pic_file=self._find_img_path(camera_id)
                else:
                    pic_file = self._capture_pic(camera_id, stream_url, self.timeout_s)

                if os.path.exists(pic_file):
                    pic_url = self._upload_pic(self.local, pic_file, self.cloud_path)
                    if pic_url is not None and pic_url != "":
                        if self._update_capture_url(camera_id, pic_url):
                            self._update_task_status(id, CameraPicUpload.status_e["over"], None)
                            self.log.info("Process over, task id=%d url=%s" % (id, pic_url))
                            successed = True
                        else:
                            self.log.error("_update_capture_url failed, task_id=%d camera_id=%d" % (id, camera_id))
                            self._update_task_status(id, CameraPicUpload.status_e["failed"],
                                                     "Update capture url to table %s failed" % (self.tb_camera))
                    else:
                        self.log.error("Upload img failed, task_id=%d camera_id=%d" % (id, camera_id))
                        self._update_task_status(id, CameraPicUpload.status_e["failed"], "Upload pic failed")
                    if self.local == "" and self.imgpath == "":
                        os.remove(pic_file)
                    else:
                        if self.imgpath == "":
                            if os.path.exists(pic_file):
                                os.remove(pic_file)
                            if not successed:
                                _, fname = os.path.split(pic_file)
                                dst = self.local + fname
                                if os.path.exists(dst):
                                    os.remove(dst)
                else:
                    self.log.error("Capture pic failed, task_id=%d camera_id=%d" % (id, camera_id))
                    self._update_task_status(id, CameraPicUpload.status_e["failed"], "Capture pic failed")
            else:
                self.log.error("The stream_url is empty, task_id=%d camera_id=%d" % (id, camera_id))
                self._update_task_status(id, CameraPicUpload.status_e["failed"], "The stream_url with camera is empty")

    def _get_tasks(self):
        ret, tasks = self.rest.Select(self.tb_tasks, params="capture_status=%28{},{}%29".format(
            CameraPicUpload.status_e["untreated"], CameraPicUpload.status_e["processing"]))
        self.log.info("Get task, ret=%s resp=%s" % (ret, tasks))
        return tasks

    def _get_stream_url(self, camera_id):
        ret, url = self.rest.Select(self.tb_camera, params="id='%d'" % (camera_id), body={"stream_url": 0})
        self.log.info("Get stream url, ret=%s resp=%s" % (ret, url))
        if ret == "200":
            return url[0]["stream_url"]
        return None

    def _capture_pic(self, camera_id, stream_url, timeout_s):
        pic_file = "%s/%s.jpg" % (self.save_dir, short_UUID())
        mk_dir(pic_file)
        cmd = ("%s/etc/ffmpeg/ffmpeg -rtsp_transport tcp -hide_banner -i \"%s\" -y -frames:v 1"
               " -strftime 1 %s") % (self.RootDir, stream_url, pic_file)
        self.log.info("Capture cmd: %s" % (cmd))
        self._timeout_command(cmd, timeout_s)
        return pic_file

    def _isVaildDate(self, date):
        try:
            if ":" in date:
                date_is = time.strptime(date, "%Y-%m-%d %H:%M:%S")
            else:
                date_is = time.strptime(date, "%Y-%m-%d")
            return True,date_is
        except:
            return False,None

    def _find_img_path(self, camera_id):
        pic_file = ""
        camera_path = self.imgpath+str(camera_id)

        if os.path.exists(camera_path):
            date_dirs = os.listdir(camera_path)

            date_dirs1 = list(ifilter(lambda x: '-' in x, date_dirs))
            date_dirs1.sort(reverse=True)
            if date_dirs1.__len__() > 0:
                subdirspath = camera_path + '/' + date_dirs1[0]
                list_file = self.listdir(subdirspath, ext='.jpg;.bmp', sort_reverse=True, with_path=True, ext_sep=";")

                if list_file.__len__() > 0:
                    pic_file= list_file[0]
                else:
                    self.log.error("_find_img_path camera date path is %s, donot find image." % (subdirspath))
            else:
                self.log.error("_find_img_path donot have camera date path, camera_path is %s" % (camera_path))
        else:
            self.log.error("_find_img_path camera_path is %s not existence." % (camera_path))

        self.log.info("_find_img_path result: %s" % (pic_file))

        return pic_file

    def listdir(self, path, ext=None, sort_reverse=False, with_path=True, ext_sep=";"):
        list_file = []
        if os.path.exists(path):
            exts = None
            if ext is not None:
                exts = ext.split(ext_sep)

            for top, dirs, nondirs in os.walk(path):
                for item in nondirs:
                    if exts:
                        _, _, file_ext = self.split_file_name(item)
                        if file_ext not in exts:
                            continue
                    if with_path:
                        list_file.append(os.path.join(top, item))
                    else:
                        list_file.append(item)
        if list_file:
            list_file.sort(reverse=sort_reverse)
        return list_file

    def split_file_name(self,full_path):
        dir, file_name = os.path.split(full_path)
        shotname, extension = os.path.splitext(file_name)
        return dir, shotname, extension

    def _upload_pic(self, dir, pic_file, cloud_path):
        if dir == "":
            # Upload to azure
            ret, msg = self.rest.UploadImg(body={"file": pic_file, "fileCloud_path": cloud_path})
            if ret != "200":
                self.log.error("Upload img failed, ret=%s msg=%s" % (ret, msg))
                return ""
            return msg["url"]
        else:
            # Save into local dir on server
            _, fname = os.path.split(pic_file)
            dst = self.local + fname
            shutil.move(pic_file, dst)
            return self.urlpref + fname

    def _update_task_status(self, task_id, status, remark):
        self.log.info("_update_task task_id=%d status=%d remark=%s" % (task_id, status, remark))
        ret = "200"
        msg = []
        if status > 0:
            ret, msg = self.rest.Update(self.tb_tasks, params="id='%d'" % (task_id),
                                        body={"capture_status": status})
        else:
            ret, msg = self.rest.Update(self.tb_tasks, params="id='%d'" % (task_id),
                                        body={"capture_status": status, "remark": "\'%s\'" % (remark)})
        if ret != "200":
            self.log.error("_update_task_status failed, task_id=%d status=%d remark=%s msg=%s" %
                           (task_id, status, remark, str(msg)))

    def _update_capture_url(self, camera_id, pic_url):
        self.log.info("_update_capture")
        ret, msg = self.rest.Update(self.tb_camera, params="id='%d'" % (
            camera_id), body={"screen_capture": "\"%s\"" % (pic_url)})
        if ret != "200":
            self.log.error("_update_capture_url failed, camera_id=%d ret=%s msg=%s" % (camera_id, ret, msg))
            return False
        return True

    def _init_cfg(self, args):
        if args.local.strip() != "":
            self.local = get_full_path(self.RootDir, args.local.strip())
            if not self.local.endswith("/"):
                self.local = self.local + "/"
            mk_dir(self.local)
            self.urlpref = args.urlpref.strip()
            if not self.urlpref.endswith("/"):
                self.urlpref = self.urlpref + "/"
        if args.cloudpath.strip() != "":
            self.cloud_path = args.cloudpath
            if not self.cloud_path.endswith("/"):
                self.cloud_path = self.cloud_path + "/"
        if args.timeout != 0:
            self.timeout_s = args.timeout
            if self.timeout_s <= 0 or 300 < self.timeout_s:
                self.timeout_s = 10
        if args.threadnum != 0:
            self.thread_num = args.threadnum
            if self.thread_num <= 0 or 30 < self.thread_num:
                self.thread_num = 5
        if args.imgpath != "":
            self.imgpath = args.imgpath
            if not self.imgpath.endswith("/"):
                self.imgpath = self.imgpath + "/"

    def _timeout_command(self, command, timeout):
        start = datetime.datetime.now()
        process = subprocess.Popen(command, shell=True, bufsize=10000, stdout=subprocess.PIPE, close_fds=True)
        while process.poll() is None:
            time.sleep(0.1)
            now = datetime.datetime.now()
            if (now - start).seconds > timeout:
                try:
                    process.terminate()
                except Exception as e:
                    self.log.error("Finded error: %s" % (str(e)))
                    return None
                self.log.error("Finded timeout")
                return None
        out = process.communicate()[0]
        if process.stdin:
            process.stdin.close()
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()
        try:
            process.kill()
        except OSError:
            pass
        return out
