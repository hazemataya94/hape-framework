import os
import json
from dotenv import load_dotenv
from hape.logging import Logging

class Config:
    logger = Logging.get_logger('hape.config')
    _env_loaded = False
    required_env_variables = []

    _env_var_map = {
        "HAPE_LOG_FILE": {
            "key": "HAPE_LOG_FILE",
            "value": "hape.log"
        },
        "HAPE_LOG_LEVEL": {
            "key": "HAPE_LOG_LEVEL",
            "value": "WARNING"
        },
        "HAPE_LOG_ROTATE_EVERY_RUN": {
            "key": "HAPE_LOG_ROTATE_EVERY_RUN",
            "value": "0"
        }
    }

    @staticmethod
    def set_required_env_variable(required_env_variable):
        Config.logger.debug(f"set_required_env_variable({required_env_variable})")
        if required_env_variable not in Config.required_env_variables:
            Config.required_env_variables.append(required_env_variable)

    @staticmethod
    def set_env_var_key(hape_key, new_key):
        #example: set_env_var_key("HAPE_LOG_FILE", "MYAPP_LOG_FILE")
        for key, _ in Config._env_var_map.items():
            if key == hape_key:
                Config._env_var_map[hape_key]["key"] = new_key

    @staticmethod
    def check_variables():
        Config.logger.debug(f"check_variables({Config.required_env_variables})")
        for variable in Config.required_env_variables:
            Config._get_env_value(variable)

    @staticmethod
    def _load_environment():
        if not Config._env_loaded:
            if os.path.exists(".env"):
                load_dotenv()
            Config._env_loaded = True

    @staticmethod
    def _get_env_value(hape_env_key):
        Config._load_environment()
        if Config._env_var_map[hape_env_key]["value"]:
            return Config._env_var_map[hape_env_key]["value"]
        
        env_key = Config._env_var_map[hape_env_key]["key"]
        env_value = os.getenv(env_key)
        if not env_value and env_key in Config.required_env_variables:
            Config.logger.error(f"""Environment variable {env_key} is missing.

To set the value of the environment variable run:
$ export {env_key}="value"

The following environment variables are required:
{json.dumps(Config.required_env_variables, indent=4)}
""")
            exit(1)

        Config._env_var_map[hape_env_key]["value"] = env_value
        return env_value
    
    @staticmethod
    def get_log_level():
        Config.logger.debug(f"get_log_level()")
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        log_level = Config._get_env_value("HAPE_LOG_LEVEL")
        return log_level if log_level and log_level in valid_levels else "WARNING"
    

    @staticmethod
    def get_log_file():
        Config.logger.debug(f"get_log_file()")
        log_file = Config._get_env_value("HAPE_LOG_FILE")
        return log_file if log_file else "hape.log"
    
    @staticmethod
    def get_log_rotate_every_run():
        Config.logger.debug(f"get_log_rotate_every_run()")
        log_file = Config._get_env_value("HAPE_LOG_ROTATE_EVERY_RUN")
        return log_file if log_file else "0"
