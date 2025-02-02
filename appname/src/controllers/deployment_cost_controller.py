from appname.interfaces.model_controller import ModelController
from appname.src.models.deployment_cost_model import DeploymentCost

class DeploymentCostController(ModelController):
    
    def __init__(self):
        super().__init__(DeploymentCost)
