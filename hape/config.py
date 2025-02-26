import os
import json
from dotenv import load_dotenv
from hape.logging import Logging
from hape.enums.log_level_enum import LogLevelEnum
from hape.enums.environment_variables_enum import EnvironmentVariablesEnum

class Config:
    logger = Logging.get_logger('hape.config')
    _env_loaded = False
    required_env_variables = []

    _env_var_map = {
        EnvironmentVariablesEnum.HAPE_LOG_FILE: {
            "key": "HAPE_LOG_FILE",
            "value": "hape.log"
        },
        EnvironmentVariablesEnum.HAPE_LOG_LEVEL: {
            "key": "HAPE_LOG_LEVEL",
            "value": "WARNING"
        },
        EnvironmentVariablesEnum.HAPE_LOG_ROTATE_EVERY_RUN: {
            "key": "HAPE_LOG_ROTATE_EVERY_RUN",
            "value": "0"
        },
        EnvironmentVariablesEnum.HAPE_MARIADB_HOST: {
            "key": "HAPE_MARIADB_HOST",
            "value": "host.docker.internal"
        },
        EnvironmentVariablesEnum.HAPE_MARIADB_USERNAME: {
            "key": "HAPE_MARIADB_USERNAME",
            "value": "hape_user"
        },
        EnvironmentVariablesEnum.HAPE_MARIADB_PASSWORD: {
            "key": "HAPE_MARIADB_PASSWORD",
            "value": "hape_password"
        },
        EnvironmentVariablesEnum.HAPE_MARIADB_DATABASE: {
            "key": "HAPE_MARIADB_DATABASE",
            "value": "hape_db"
        },
        EnvironmentVariablesEnum.HAPE_GITLAB_DOMAIN: {
            "key": "HAPE_GITLAB_DOMAIN",
            "value": "gitlab.com"
        },
        EnvironmentVariablesEnum.HAPE_GITLAB_TOKEN: {
            "key": "HAPE_GITLAB_TOKEN",
            "value": "gitlab_token"
        }
    }

    @staticmethod
    def set_required_env_variable(required_env_variable):
        Config.logger.debug(f"set_required_env_variable({required_env_variable})")
        if required_env_variable not in Config.required_env_variables:
            Config.required_env_variables.append(required_env_variable)

    @staticmethod
    def set_env_var_key(hape_key, new_key):
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
        env_key = Config._env_var_map[hape_env_key]["key"]
        env_value = os.getenv(env_key)
        env_default_value = Config._env_var_map[hape_env_key]["value"]
        
        if env_value:
            Config._env_var_map[hape_env_key]["value"] = env_value
            return env_value
        elif env_default_value:
            return env_default_value
        elif env_key in Config.required_env_variables:
            Config.logger.error(f"""Environment variable {env_key} is missing.

To set the value of the environment variable run:
$ export {env_key}="value"

The following environment variables are required:
{json.dumps(Config.required_env_variables, indent=4)}
""")
            exit(1)    
        return None
    
    @staticmethod
    def get_log_level():
        Config.logger.debug(f"get_log_level()")
        log_level = Config._get_env_value(EnvironmentVariablesEnum.HAPE_LOG_LEVEL)
        return log_level if log_level and LogLevelEnum(log_level) else LogLevelEnum.WARNING

    @staticmethod
    def get_log_file():
        Config.logger.debug(f"get_log_file()")
        log_file = Config._get_env_value(EnvironmentVariablesEnum.HAPE_LOG_FILE)
        return log_file if log_file else "hape.log"
    
    @staticmethod
    def get_log_rotate_every_run():
        Config.logger.debug(f"get_log_rotate_every_run()")
        log_rotate_every_run = Config._get_env_value(EnvironmentVariablesEnum.HAPE_LOG_ROTATE_EVERY_RUN)
        return log_rotate_every_run if log_rotate_every_run else "0"
