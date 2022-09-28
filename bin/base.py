#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import os
import sys
import logging
import logging.handlers
import time
import socket
import json
import yaml

BIN_DIRECTORY  = os.path.dirname(os.path.realpath(__file__))
BASE_DIRECTORY = os.path.dirname(BIN_DIRECTORY)
CONF_DIRECTORY = os.path.join(BASE_DIRECTORY, 'conf')
LOG_DIRECTORY  = os.path.join(BASE_DIRECTORY, 'logs')
LIB_DIRECTORY  = os.path.join(BASE_DIRECTORY, 'lib')
DATA_DIRECTORY = os.path.join(BASE_DIRECTORY, 'data')
COMM_LIB_DIRECTORY = os.path.join(os.path.abspath(os.path.join(BASE_DIRECTORY, "../..")), "lib")
if not LIB_DIRECTORY in sys.path:
    sys.path.insert(0, LIB_DIRECTORY)

if not COMM_LIB_DIRECTORY in sys.path:
    sys.path.insert(0, COMM_LIB_DIRECTORY)
#日志级别
LOGLEVELS = {
    'DEBUG'   : logging.DEBUG,
    'INFO'    : logging.INFO,
    'WARNING' : logging.WARNING,
    'ERROR'   : logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

class Base(object):
    logger = None
    def __init__(self, confName='base', logConf='log'):
        self.confName = confName
        self.data_to_send = []
        self.producer = None
        self.init_conf() 
        self.init_log(logConf)  # read conf [log] info init log config
        self.hostname = self.get_hostname()

    def init_conf(self):
        global CONF_DIRECTORY
        confFile = os.path.join(CONF_DIRECTORY, self.confName)
        f = open(confFile)
        self.conf = yaml.safe_load(f)
        f.close()

    def get_hostname(self):
        hostname = None
        try:
            hostname = socket.gethostname()
        except Exception as e:
            hostname = ''
        return hostname

    def init_log(self, logConf):
        #如果基类的logger还没初始化则新建一个
        if Base.logger is None:
            Base.logger = logging.getLogger()
            global LOG_DIRECTORY
            filename = os.path.join(LOG_DIRECTORY, self.conf[logConf]['filename'])
            level = self.conf[logConf]['level']
            backupCount = self.conf[logConf]['backupCount']
            handler = logging.handlers.RotatingFileHandler(filename, maxBytes = 300*1024*1024, backupCount = backupCount)
            formatter = logging.Formatter('%(levelname)-5s %(asctime)s %(filename)s %(threadName)s %(message)s')
            handler.setFormatter(formatter)
            Base.logger.addHandler(handler)
            Base.logger.setLevel(LOGLEVELS.get(level, logging.INFO))
            #使用基类的logger
            self.logger = Base.logger
        self.logger.info('init logger success')

    #根据key取对应的配置项
    def get_conf(self, key):
        return self.conf.get(key)