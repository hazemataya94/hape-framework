from hape.base.model_controller import ModelController
from hape.src.models.deployment_cost_model import DeploymentCost

class DeploymentCostController(ModelController):
    
    def __init__(self):
        super().__init__(DeploymentCost)
