from hape.base.model_argument_parser import ModelArgumentParser
from hape.models.k8s_deployment_model import K8SDeployment
from hape.controllers.k8s_deployment_controller import K8SDeploymentController

class K8SDeploymentArgumentParser(ModelArgumentParser):
    def __init__(self):
        super().__init__(K8SDeployment, K8SDeploymentController)

    def extend_subparser(self):
        pass
    
    def extend_actions(self):
        pass