
import os
import json
import requests
import logging
requests.packages.urllib3.disable_warnings()
cur_dir = os.getcwd()
cfg_file = os.path.join(cur_dir, "rest_sql_wrapper.json")
with open(cfg_file, mode='r') as f:
    cfg_dict = json.loads(f.read())

class rest_sql_wrapper:

    log_tag = "RestSqlWrapper"

    def __init__(self, log_tag):
        self.log = logging.getLogger("%s.%s" % (log_tag, self.log_tag))
        self.log.info("CameraPicUpload __init__")

        self.token = ""
        self.debug_sql = cfg_dict.get("debug_sql")
        self.retry_num = cfg_dict.get("retry_num")
        if self.retry_num <= 0 or 30 < self.retry_num:
            self.retry_num = 3

        self.oauth_path = "%s/%s" % (cfg_dict.get("rest_url"), cfg_dict.get("oauth_path"))
        self.oauth_path = self.oauth_path.replace("//", "/")
        self.oauth_path = self.oauth_path.replace("//", "/")
        self.oauth_path = self.oauth_path.replace("http:/", "http://")
        self.oauth_path = self.oauth_path.replace("https:/", "https://")

    def Insert(self, path, params=None, body=None, queryflag=None):
        if not self.__checkParams("insert", path, params, body, queryflag):
            return "500", {'msg':'Error: rest_sql_wrapper.Insert() params error'}
        resp = self.__request("insert", path, params, body, queryflag)
        return str(resp[0]["status"]),resp[1]

    def Delete(self, path, params=None, body=None, queryflag=None):
        if not self.__checkParams("delete", path, params, body, queryflag):
            return "500", {'msg':'Error: rest_sql_wrapper.Delete() params error'}
        resp = self.__request("delete", path, params, body, queryflag)
        return str(resp[0]["status"]),resp[1]

    def Update(self, path, params=None, body=None, queryflag=None):
        if not self.__checkParams("update", path, params, body, queryflag):
            return "500", {'msg':'Error: rest_sql_wrapper.Update() params error'}
        resp = self.__request("update", path, params, body, queryflag)
        return str(resp[0]["status"]),resp[1]

    def Select(self, path, params=None, body=None, queryflag=None):
        if not self.__checkParams("select", path, params, body, queryflag):
            return "500", {'msg':'Error: rest_sql_wrapper.Select() params error'}
        resp = self.__request("select", path, params, body, queryflag)
        if self.debug_sql:
            return str(resp[0]["status"]), resp[1]
        return str(resp[0]["status"]),json.loads(resp[1]) 


    def SelectSql(self, path = "", params=None, body=None, queryflag=None):
        if not self.__checkParams("selectsql", path, params, body, queryflag):
            return "500", {'msg':'Error: rest_sql_wrapper.Select() params error'}
        resp = self.__request("selectsql", path, params, body, queryflag)
        if self.debug_sql:
            return str(resp[0]["status"]), resp[1]
        return str(resp[0]["status"]),json.loads(resp[1]) 


    def UploadImg(self, path=None, params=None, body=None, queryflag=None):
        if not self.__checkParams("upload", path, params, body, queryflag):
            return "500", {'msg': 'Error: rest_sql_wrapper.UploadImg() params error'}
        resp = self.__request("uploadImage", path, params, body, queryflag)
        dict_url = {}
        if self.debug_sql:
            return str(resp[0]["status"]), resp[1]
        if resp[0]["status"] == 200:
            dict_url.update({"url":json.loads(resp[1])["url"]})
        return str(resp[0]["status"]), dict_url

    def __refreshToken(self):
        params = {
                'grant_type':cfg_dict.get('grant_type'),
                'client_id':cfg_dict.get("client_id"),
                'client_secret':cfg_dict.get("client_secret"),
                'username':cfg_dict.get("username"),
                'password':cfg_dict.get("password"),
                'scope':cfg_dict.get("scope")
                }
                
        errCnt = 0
        while errCnt <= self.retry_num:
            try:
                resp = requests.post(self.oauth_path,data=params,verify = False)
            except Exception as e:
                self.log.error("__refreshToken POST failed! msg: %s" % (str(e)))
                self.log.error("__refreshToken POST failed, rest_url:%s" % (cfg_dict.get("rest_url")))
                return
                
            if resp.status_code == 200:
                body = resp.content
                body_json = json.loads(body)
                self.token = body_json['access_token']
                return
            self.log.error("Error: rest_sql_wrapper request token failed!")
            errCnt += 1

    def __request(self, cmd, path, params, body, queryflag):
        url = "%s/%s" % (cfg_dict.get("rest_url"), cmd)
        if path is not None:
            url = "%s/%s" % (url, path)
        if params is not None:
            url = "%s?%s" % (url, params)
            if self.debug_sql:
                url = "%s&print_sql=true" % (url)
        else:
            if self.debug_sql:
                url = "%s?print_sql=true" % (url)
        self.log.info("request url: %s, body: %s" % (url, body))
        errCnt = 0
        while errCnt <= self.retry_num:
            try:
                resp = self.__send(cmd, url, body)
            except Exception as e:
                self.log.error("__request send failed! msg: %s" % (str(e)))
                return [{'status': '500'}, "{}"]
            if resp.status_code == 200:
                return [{'status': resp.status_code}, resp.content]
            self.log.error("Error: rest_sql_wrapper %s failed[%d]! status: %s" % (cmd, errCnt, resp.status_code))
            self.log.info("request resp: %s" % (str(resp)))
            if resp.status_code != 401:
                break
            errCnt += 1
            if errCnt <= self.retry_num:
                self.__refreshToken()
        return [{'status': resp.status_code}, "{}"]
            
    def __send(self, cmd, url, body):
        if self.token == "":
            self.__refreshToken()
        header = { 'Authorization' : 'Bearer ' + self.token }
        resp = {}
        if cmd == 'insert':
            resp = requests.post(url,headers = header,data = body,verify = False)
        elif cmd == 'delete':
            resp = requests.delete(url,headers = header,verify = False)  
        elif cmd == 'update':
            resp = requests.put(url,headers = header,data = body,verify = False)        
        elif cmd == 'selectsql':
            resp = requests.post(url,headers = header,data = body,verify = False)
        elif cmd == 'select':
            if "?" not in url:
                url = "%s?1=1" % (url)
            if body != "":
                resp = requests.put(url,headers = header,data = body,verify = False)
            else:
                resp = requests.put(url,headers = header,verify = False)
        elif cmd == 'uploadImage':
            data = {"fileCloud_path": body["fileCloud_path"]}
            _, filename = os.path.split(body["file"])
            _, ext = os.path.splitext(filename)
            multiple_files = [('file', (filename, open(body["file"], 'rb'), 'image/' + ext))]
            resp = requests.post(url, data=data, files=multiple_files, headers=header,verify = False)
        else:
            self.log.error("Error: rest_sql_wrapper params of __send error!")
        return resp
        
    def __checkParams(self, cmd, path, params, body, queryflag):
        if cmd == 'insert':
            if path is None or body is None:
                return False
        elif cmd == 'delete':
            if path is None or params is None:
                return False
        elif cmd == 'update':
            if path is None or params is None or body is None:
                return False
        elif cmd == 'select':
            if path is None:
                return False
        elif cmd == 'selectsql':
            if body is None or path != "":
                return False
        elif cmd == 'upload':
            if body is None:
                return False
        else:
            self.log.error("Error: RestDB params error!")
        return True


