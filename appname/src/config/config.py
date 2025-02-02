import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

class Config:
    _env_loaded = False
    _db_session = None
    required_env_variables = ["GITLAB_TOKEN", "GITLAB_DOMAIN", "MYSQL_HOST", "MYSQL_USERNAME", "MYSQL_PASSWORD", "MYSQL_DATABASE"]

    @staticmethod
    def check_variables():
        for variable in Config.required_env_variables:
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
        
        if not env_value and env in Config.required_env_variables:
            print(f"""
Error: One or more of the required environment variables is missing.

To set the value of the environment variable run:
$ export ENV_VARIABLE_NAME="value"

The following environment variables are required
{Config.required_env_variables}
""")
            exit(1)
        return env_value

    # DB Session Initialization
    @staticmethod
    def get_db_url():
        return f"mysql+pymysql://{Config.get_mysql_username()}:{Config.get_mysql_password()}@{Config.get_mysql_host()}/{Config.get_mysql_database()}"

    @staticmethod
    def get_db_session() -> sessionmaker:
        
        try:
            DATABASE_URL = Config.get_db_url()
            engine = create_engine(DATABASE_URL)
            with engine.connect() as connection:
                connection.execute("SELECT 1")  # Basic check to see if DB is reachable
            print("Database connection validated successfully.")
        except OperationalError:
            print("Error: Unable to connect to the database. Please check the configuration.")
            raise
        
        if not Config._db_session:
            try:
                DATABASE_URL = Config.get_db_url()
                engine = create_engine(DATABASE_URL, echo=True)
                with engine.connect() as connection:
                    connection.execute("SELECT 1")  # Basic check to see if DB is reachable
                Config._db_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                print("Database seassion created successfully.")
            except OperationalError:
                print("Error: Unable to connect to the database. Please check the configuration.")
                raise

        return Config._db_session()

    # Env Variables Methods
    ## GITLAB
    @staticmethod
    def get_gitlab_token():
        return Config._get_env_value("GITLAB_TOKEN")
    
    @staticmethod
    def get_gitlab_domain():
        return Config._get_env_value("GITLAB_DOMAIN")
    
    ## MYSQL
    @staticmethod
    def get_mysql_host():
        Config._load_environment()
        return os.getenv("MYSQL_HOST", "localhost")

    @staticmethod
    def get_mysql_username():
        Config._load_environment()
        return os.getenv("MYSQL_USERNAME", "root")

    @staticmethod
    def get_mysql_password():
        Config._load_environment()
        return os.getenv("MYSQL_PASSWORD", "")

    @staticmethod
    def get_mysql_database():
        Config._load_environment()
        return os.getenv("MYSQL_DATABASE", "deployments_db")