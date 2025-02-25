import json
import logging.config
from hape.logging import Logging, CustomJsonFormatter, LOGGING_CONFIG
from hape.config import Config

def bootstrap():
    log_level = Config.get_log_level()
    log_file = Config.get_log_file()
    
    if Config.get_log_rotate_every_run() == "1":
        Logging.rotate_log_file(log_file)
    
    logging_config_json = LOGGING_CONFIG.replace("{{log_level}}", log_level).replace("{{log_file}}", log_file)
    logging_config = json.loads(logging_config_json)
    logging_config["formatters"]["json"] = {
        "()": CustomJsonFormatter,
        "fmt": "%(timestamp)s %(level)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d"
    }
    logging.config.dictConfig(logging_config)
    logger = Logging.get_logger()
    logger.info("Application started!")
