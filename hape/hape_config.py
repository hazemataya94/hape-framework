import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text
from hape.config import Config
from hape.logging import Logging
from hape.enums.environment_variables_enum import EnvironmentVariablesEnum
class HapeConfig:
    logger = Logging.get_logger('hape.config_db')
    _env_loaded = False
    _db_session = None
    _required_env_variables = []

    Config.set_required_env_variable("HAPE_GITLAB_TOKEN")
    Config.set_required_env_variable("HAPE_GITLAB_DOMAIN")
    Config.set_required_env_variable("HAPE_MARIADB_HOST")
    Config.set_required_env_variable("HAPE_MARIADB_USERNAME")
    Config.set_required_env_variable("HAPE_MARIADB_PASSWORD")
    Config.set_required_env_variable("HAPE_MARIADB_DATABASE")

    @staticmethod
    def check_variables():
        Config.logger.debug(f"check_variables()")
        for variable in Config._required_env_variables:
            Config._get_env_value(variable)

    @staticmethod
    def get_db_url(with_database=True):
        Config.logger.debug(f"get_db_url(with_database={with_database})")
        db_url = f"mysql+pymysql://{HapeConfig.get_mariadb_username()}:{HapeConfig.get_mariadb_password()}@{HapeConfig.get_mariadb_host()}"
        if with_database:
            db_url += f"/{HapeConfig.get_mariadb_database()}"
        return db_url
    

    @staticmethod
    def get_db_session(with_database=True) -> sessionmaker:
        Config.logger.debug(f"get_db_url()")
        if not HapeConfig._db_session:
            try:
                DATABASE_URL = HapeConfig.get_db_url(with_database)
                engine = create_engine(DATABASE_URL, echo=False)
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))

                HapeConfig._db_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                Config.logger.info("Database seassion created successfully.")
            except OperationalError:
                Config.logger.error("Error: Unable to connect to the database. Please check the configuration.")
                raise

        return HapeConfig._db_session()
    
    @staticmethod
    def drop_db():
        Config.logger.debug(f"drop_db()")
        engine = create_engine(HapeConfig.get_db_url(with_database=False), echo=True)
        with engine.connect() as connection:
            connection.execute(text(f"DROP DATABASE IF EXISTS {HapeConfig.get_mariadb_database()}"))

    @staticmethod
    def create_db():
        Config.logger.debug(f"create_db()")
        engine = create_engine(HapeConfig.get_db_url(with_database=False), echo=True)
        with engine.connect() as connection:
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {HapeConfig.get_mariadb_database()}"))

    @staticmethod
    def reset_db():
        Config.logger.debug(f"reset_db()")
        HapeConfig.drop_db()
        HapeConfig.create_db()
            
    @staticmethod
    def get_gitlab_token():
        Config.logger.debug(f"get_gitlab_token()")
        return Config._get_env_value(EnvironmentVariablesEnum.HAPE_GITLAB_TOKEN)
    
    @staticmethod
    def get_gitlab_domain():
        Config.logger.debug(f"get_gitlab_domain()")
        return Config._get_env_value(EnvironmentVariablesEnum.HAPE_GITLAB_DOMAIN)
    
    @staticmethod
    def get_mariadb_host():
        Config.logger.debug(f"get_mariadb_host()")
        return Config._get_env_value(EnvironmentVariablesEnum.HAPE_MARIADB_HOST)

    @staticmethod
    def get_mariadb_username():
        Config.logger.debug(f"get_mariadb_username()")
        return Config._get_env_value(EnvironmentVariablesEnum.HAPE_MARIADB_USERNAME)

    @staticmethod
    def get_mariadb_password():
        Config.logger.debug(f"get_mariadb_password()")
        return Config._get_env_value(EnvironmentVariablesEnum.HAPE_MARIADB_PASSWORD)

    @staticmethod
    def get_mariadb_database():
        Config.logger.debug(f"get_mariadb_database()")
        return Config._get_env_value(EnvironmentVariablesEnum.HAPE_MARIADB_DATABASE)
