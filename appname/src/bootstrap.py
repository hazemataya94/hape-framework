from appname.src.config.logging import logger
from appname.src.config.config import Config
from appname.src.models.deployment_cost_model import DeploymentCost

def bootstrap_application():
    logger.info("Checking configurations.")
    Config.check_variables()

    session = Config.get_db_session()
    try:
        DeploymentCost.initialize_from_sqlalchemy(DeploymentCost)
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        session.close()

    logger.info("Application started!")