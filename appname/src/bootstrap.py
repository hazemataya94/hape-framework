from appname.src.config.config import Config
from appname.src.models.deployment_cost_model import DeploymentCost

def bootstrap_application():
    session = Config.get_db_session()
    try:
        DeploymentCost.initialize_from_sqlalchemy(DeploymentCost)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        session.close()