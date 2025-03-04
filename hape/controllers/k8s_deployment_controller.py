from hape.logging import Logging
from hape.base.model_controller import ModelController
from hape.models.k8s_deployment_model import K8SDeployment

class K8SDeploymentController(ModelController):
    
    def __init__(self):
        super().__init__(K8SDeployment)
        self.logger = Logging.get_logger('hape.controllers.k8s_deployment_controller')