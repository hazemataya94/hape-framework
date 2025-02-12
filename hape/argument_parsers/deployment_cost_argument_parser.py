from hape.base.model_argument_parser import ModelArgumentParser
from hape.models.deployment_cost_model import DeploymentCost
from hape.controllers.deployment_cost_controller import DeploymentCostController

class DeploymentCostArgumentParser(ModelArgumentParser):
    def __init__(self):
        super().__init__(DeploymentCost, DeploymentCostController)

    def extend_subparser(self):
        pass
    
    def extend_actions(self):
        pass
