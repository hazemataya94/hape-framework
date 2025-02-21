from hape.base.model_controller import ModelController
from hape.models.k8s_deployment_model import K8SDeployment

class K8SDeploymentController(ModelController):
    
    def __init__(self):
        super().__init__(K8SDeployment)