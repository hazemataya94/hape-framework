import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text
from hape.logging import Logging

class Config:
    logger = Logging.get_logger('hape.config')
    _env_loaded = False
    _db_session = None
    _required_env_variables = []

    @staticmethod
    def check_variables():
        Config.logger.debug(f"check_variables()")
        for variable in Config._required_env_variables:
            Config._get_env_value(variable)

    @staticmethod
    def _load_environment():
        if not Config._env_loaded:
            if os.path.exists(".env"):
                load_dotenv()
            Config._env_loaded = True

    @staticmethod
    def _get_env_value(env):
        Config._load_environment()
        env_value = os.getenv(env)
        
        if not env_value and env in Config._required_env_variables:
            Config.logger.error(f"""Environment variable {env} is missing.

To set the value of the environment variable run:
$ export {env}="value"

The following environment variables are required:
{json.dumps(Config._required_env_variables, indent=4)}
""")
            exit(1)
        return env_value

    @staticmethod
    def get_db_url():
        Config.logger.debug(f"get_db_url()")
        return f"mysql+pymysql://{Config.get_mysql_username()}:{Config.get_mysql_password()}@{Config.get_mysql_host()}/{Config.get_mysql_database()}"

    @staticmethod
    def get_db_session() -> sessionmaker:
        Config.logger.debug(f"get_db_url()")
        if not Config._db_session:
            try:
                DATABASE_URL = Config.get_db_url()
                engine = create_engine(DATABASE_URL, echo=True)
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))

                Config._db_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                Config.logger.info("Database seassion created successfully.")
            except OperationalError:
                Config.logger.error("Error: Unable to connect to the database. Please check the configuration.")
                raise

        return Config._db_session()

    @staticmethod
    def get_gitlab_token():
        Config.logger.debug(f"get_gitlab_token()")
        return Config._get_env_value("HAPE_GITLAB_TOKEN")
    
    @staticmethod
    def get_gitlab_domain():
        Config.logger.debug(f"get_gitlab_domain()")
        return Config._get_env_value("HAPE_GITLAB_DOMAIN")
    
    @staticmethod
    def get_mysql_host():
        Config.logger.debug(f"get_mysql_host()")
        return Config._get_env_value("HAPE_MARIADB_HOST")

    @staticmethod
    def get_mysql_username():
        Config.logger.debug(f"get_mysql_username()")
        return Config._get_env_value("HAPE_MARIADB_USERNAME")

    @staticmethod
    def get_mysql_password():
        Config.logger.debug(f"get_mysql_password()")
        return Config._get_env_value("HAPE_MARIADB_PASSWORD")

    @staticmethod
    def get_mysql_database():
        Config.logger.debug(f"get_mysql_database()")
        return Config._get_env_value("HAPE_MARIADB_DATABASE")
    
    @staticmethod
    def get_log_level():
        Config.logger.debug(f"get_log_level()")
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        log_level = Config._get_env_value("HAPE_LOG_LEVEL")
        return log_level if log_level and log_level in valid_levels else "DEBUG"
    
    @staticmethod
    def get_log_file():
        Config.logger.debug(f"get_log_file()")
        log_file = Config._get_env_value("HAPE_LOG_FILE")
        return log_file if log_file else "hape.log"
    
    @staticmethod
    def get_log_rotate_every_run():
        Config.logger.debug(f"get_log_rotate_every_run()")
        log_file = Config._get_env_value("HAPE_LOG_ROTATE_EVERY_RUN")
        return log_file if log_file else "1"
