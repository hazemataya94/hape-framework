import logging
import logging.config
import os
from pythonjsonlogger import jsonlogger

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def parse(self):
        return ["timestamp", "level", "name", "message", "module", "funcName", "lineno"]

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        },
        "json": {
            "()": CustomJsonFormatter,
            "fmt": "%(timestamp)s %(level)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "level": "INFO",
            "filename": LOG_FILE,
            "maxBytes": 10485760,
            "backupCount": 5
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False
        },
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("global_logger")
logger.info("Global logger initialized.")
