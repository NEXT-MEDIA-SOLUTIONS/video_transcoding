#!/usr/bin/env python
# coding: utf-8

__author__ = "Mohammed EL-KHOU"
__copyright__ = "Altice Media"
__license__ = "DWH"
__service__ = "logging"
__version__ = "1.0"

import sys, os, stat, json
import logging
from logging import Logger, FileHandler
from glob import glob
from datetime import date
# import queue

sys.path.append('.')
workdir=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(workdir)

from src.helpers.env import Env

pyv=int(sys.version_info.major)
if pyv not in [2,3]:
    print("ERROR :: Python version not recognized py='%s' => exit(1)" % pyv)
    exit(1)
    
def get_error_traceback(e):
    d=None
    if pyv>=3:
        d={
            "filename": str(e.__traceback__.tb_frame.f_code.co_filename),
            "name": str(e.__traceback__.tb_frame.f_code.co_name),
            "line": int(e.__traceback__.tb_lineno),
            "type": str(type(e)),
            "message": str(e)
        }
    else:
        d={
            "filename": str(sys.exc_info()[2].tb_frame.f_code.co_filename),
            "name": str(sys.exc_info()[2].tb_frame.f_code.co_name),
            "line": int(sys.exc_info()[2].tb_lineno),
            "type": str(sys.exc_info()[0].__name__),
            "message": str(e)
        }
    return json.dumps(d)


logging.basicConfig(level=logging.INFO, encoding='utf-8')
class CustomLogger(Logger):

    def __init__(
        self,
        log_file=None,
        log_format="%(asctime)s.%(msecs)03d | %(name)s | %(filename)s.%(lineno)d | %(levelname)s | %(message)s",
        *args,
        **kwargs
    ):

        self.formatter = logging.Formatter(fmt=log_format, datefmt='%Y-%m-%d %H:%M:%S')
        if log_file is None:
            APP_LOG_DIR = Env.get('APP_LOG_DIR','./logs')
            os.makedirs(APP_LOG_DIR, exist_ok=True)
            self.log_file = os.path.join(APP_LOG_DIR, "%s.log" % date.today().strftime('%Y-%m-%d'))
        else:
            self.log_file = log_file

        Logger.__init__(self, *args, **kwargs)

        self.addHandler(self.get_console_handler())
        self.addHandler(self.get_file_handler())

        # with this pattern, it's rarely necessary to propagate the| error up to parent
        self.propagate = False

    def get_console_handler(self):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(self.formatter)
        return console_handler

    def get_file_handler(self):
        # file_handler = TimedRotatingFileHandler(self.log_file, when="midnight")
        file_handler = FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(self.formatter)
        return file_handler


class LOG:
    logger = None
    today = None
    APP_LOG_DIR = Env.get('APP_LOG_DIR','./logs')
    
    if APP_LOG_DIR is None:
        print(f"CRITICAL !! APP_LOG_DIR introuvable dans les variables d'environnement !! exit(1)")
        exit(1)
    if not os.path.isdir(APP_LOG_DIR):
        try:
            # Create the folder and subfolders
            os.makedirs(APP_LOG_DIR, exist_ok=True)
            # Set the permissions to 777
            os.chmod(APP_LOG_DIR, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        except Exception as e:
            print(f"CRITICAL !! Impossible de créer le répertoire APP_LOG_DIR : '{APP_LOG_DIR}' avec Exception : '{get_error_traceback(e)}' !! exit(1)")
            exit(1)

    log_backup_duration_by_days = int(Env.get('APP_LOG_BACKUP',-1))

    @staticmethod
    def log(name="main", log_dir_path=None, log_file_path=None):
        if LOG.logger is None:
            if log_file_path is None:
                if log_dir_path is not None:
                    if not os.path.isdir(log_dir_path):
                        os.makedirs(log_dir_path)
                    LOG.APP_LOG_DIR = log_dir_path
                else:
                    LOG.APP_LOG_DIR = os.path.dirname(os.path.abspath(log_file_path))
                LOG.today = date.today().strftime('%Y-%m-%d')
                log_file_path=os.path.join(LOG.APP_LOG_DIR, "%s.log" % LOG.today)
            LOG.logger = CustomLogger(log_file=log_file_path, name=name)
        LOG.logger.name=name
        return LOG.logger

    @staticmethod
    def clean(name="main", log_dir_path=None):
        # LOG.logger.close()
        LOG.logger = None
        if LOG.log_backup_duration_by_days > 0:
            nw = date.today()
            LOG.log(name, log_dir_path).info("Logs Cleaner [START]")
            cnt = 0
            for f_log in glob(LOG.APP_LOG_DIR+"*.*"):
                st = os.path.getmtime(f_log)
                mod = date.fromtimestamp(st)
                if abs(nw - mod).days > LOG.log_backup_duration_by_days:
                    os.remove(f_log)
                    cnt+=1
            LOG.log(name, log_dir_path).info("Logs Cleaner [DONE]; %s logs deleted 🗑♻♻" % cnt)
        LOG.logger = None


if __name__ == "__main__":
    LOG.log("MH1").debug("this is a debug message")
    LOG.log().name="MH2"
    LOG.log().info("this is a info message")
    LOG.log().warning("I'm a warning. Beware!")

"""
● NOTSET
● DEBUG
● INFO
● WARNING
● ERROR
● CRITICAL
"""