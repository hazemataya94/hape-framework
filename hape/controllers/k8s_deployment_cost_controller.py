from hape.base.model_controller import ModelController
from hape.models.k8s_deployment_cost_model import K8SDeploymentCost

class K8SDeploymentCostController(ModelController):
    
    def __init__(self):
        super().__init__(K8SDeploymentCost)