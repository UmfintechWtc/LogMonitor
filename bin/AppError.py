#!/usr/bin/env python
#-*- coding: UTF8 -*-

import os
import re
import time
import json
import base
import tail
import yaml
import queue
import requests
import threading

task_queue = queue.Queue()
res_queue = queue.Queue()
exception_dict = {}
blacklistpath = os.path.join(base.DATA_DIRECTORY, "blacklist")
blacklist=yaml.safe_load(open(blacklistpath, "r"))

def send_to_wechat(url,**dictargs):
    request_data = dictargs
    response_data = requests.post(url,data=json.dumps(request_data))
    return response_data.json()

class AppLogThread(base.Base, threading.Thread):
    def __init__(self, module, conf):
        base.Base.__init__(self, confName='AppError.conf', logConf='log')
        threading.Thread.__init__(self, name='AppLogThread -- {}: '.format(module))
        self.req_url     = self.get_conf('wechat')['url']
        self.rework_step = self.get_conf('rework_step')
        self.module      = module
        self.conf        = conf
        self.tailer      = tail.Tail(self.conf['log_file'])
        self.hostname    = self.get_hostname()

    def process_line(self, line, exception_dict):
        for black_content in blacklist[self.module]:
            black_content = black_content
            exception_keyword_occ=len(re.findall(black_content, line, re.M|re.I))
            if exception_keyword_occ:
                if black_content not in exception_dict:
                    exception_dict[black_content] = exception_keyword_occ
                else:
                    exception_dict[black_content] += exception_keyword_occ
            else:
                exception_dict[black_content] = 0
        self.logger.info("{} exception error: {} ".format(self.get_hostname(), str(exception_dict)))
        for exception_key,exception_dict_occ in exception_dict.items():
            if exception_dict_occ >= 3:
                content = "{}---{} {} {}关键词近1min出现{}次".format(time.strftime("%Y-%m-%d %H:%M:%S"), self.get_hostname(), self.module, exception_key, exception_dict_occ)
                response_data = send_to_wechat(self.req_url, send_type="wechat",content=content)
                self.logger.info(response_data)

    def run(self):
        self.logger.info('begin to analyse the log %s' % self.conf['log_file'])
        while 1:
            try:
                time.sleep(self.rework_step) # process per one second
                exception_dict = {}
                fmt_error=""
                for line in self.tailer:
                    fmt_error+=line.strip()
                self.process_line(fmt_error, exception_dict)
            except Exception as e:
                self.logger.exception('analyse log exception')

class DiskZtail(base.Base):
    def __init__(self):
        base.Base.__init__(self, confName='AppError.conf', logConf='log')
        self.module_list = self.get_conf('module_list')

    def analyse(self):
        thread_list = []
        for module in self.module_list:
            t = AppLogThread(module, self.module_list[module])
            t.start()
if __name__ == '__main__':
    zt = DiskZtail()
    zt.analyse()