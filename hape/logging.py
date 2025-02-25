######################
######################
# You must not include config.py to avoid circular import.
# Config class uses loggers
######################
import os
import sys
import shutil
import logging
from datetime import datetime
from pythonjsonlogger import jsonlogger

GLOBAL_LOGGER_NAME = "hape.global"

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def parse(self):
        return ["timestamp", "level", "name", "message", "module", "funcName", "lineno"]

LOGGING_CONFIG = '{"version":1,"disable_existing_loggers":false,"formatters":{"standard":{"format":"%(asctime)s %(levelname)s - %(name)s - %(message)s"}},"handlers":{"console":{"class":"logging.StreamHandler","formatter":"standard","level":"{{log_level}}"},"file":{"class":"logging.handlers.RotatingFileHandler","formatter":"json","level":"{{log_level}}","filename":"{{log_file}}","maxBytes":10485760,"backupCount":5}},"loggers":{"":{"handlers":["console","file"],"level":"{{log_level}}","propagate":false},"uvicorn":{"handlers":["console","file"],"level":"{{log_level}}","propagate":false}}}'

class Logging:

    @staticmethod
    def get_logger(name=GLOBAL_LOGGER_NAME):
        logger = logging.getLogger(name)
        if "--version" in sys.argv:
            logging.disable(logging.CRITICAL)
        return logger

    @staticmethod
    def rotate_log_file(log_file):
        if os.path.exists(log_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name, file_ext = os.path.splitext(log_file)
            file_ext = ".log"
            new_log_file = f"{file_name}_{timestamp}{file_ext}"
            shutil.move(log_file, new_log_file)
