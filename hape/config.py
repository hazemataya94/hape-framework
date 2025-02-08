import os
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text
from hape.logging import logger



class Config:
    _env_loaded = False
    _db_session = None
    _required_env_variables = ["HAPE_GITLAB_TOKEN", "HAPE_GITLAB_DOMAIN", "HAPE_MARIADB_HOST", "HAPE_MARIADB_USERNAME", "HAPE_MARIADB_PASSWORD", "HAPE_MARIADB_DATABASE"]

    @staticmethod
    def check_variables():
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
            logger.error(f"""One or more of the required environment variables is missing.

To set the value of the environment variable run:
$ export ENV_VARIABLE_NAME="value"

The following environment variables are required:
{json.dumps(Config._required_env_variables, indent=4)}
""")
            exit(1)
        return env_value

    @staticmethod
    def get_db_url():
        return f"mysql+pymysql://{Config.get_mysql_username()}:{Config.get_mysql_password()}@{Config.get_mysql_host()}/{Config.get_mysql_database()}"

    @staticmethod
    def get_db_session() -> sessionmaker:
        if not Config._db_session:
            try:
                DATABASE_URL = Config.get_db_url()
                engine = create_engine(DATABASE_URL, echo=True)
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))

                Config._db_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                logger.info("Database seassion created successfully.")
            except OperationalError:
                logger.error("Error: Unable to connect to the database. Please check the configuration.")
                raise

        return Config._db_session()

    @staticmethod
    def get_gitlab_token():
        return Config._get_env_value("HAPE_GITLAB_TOKEN")
    
    @staticmethod
    def get_gitlab_domain():
        return Config._get_env_value("HAPE_GITLAB_DOMAIN")
    
    @staticmethod
    def get_mysql_host():
        return Config._get_env_value("HAPE_MARIADB_HOST")

    @staticmethod
    def get_mysql_username():
        return Config._get_env_value("HAPE_MARIADB_USERNAME")

    @staticmethod
    def get_mysql_password():
        return Config._get_env_value("HAPE_MARIADB_PASSWORD")

    @staticmethod
    def get_mysql_database():
        return Config._get_env_value("HAPE_MARIADB_DATABASE")