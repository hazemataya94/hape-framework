import re
from hape.logging import Logging

class Crud:
    def __init__(self, project_name: str, model_name: str, json_schema: dict):
        self.logger = Logging.get_logger('hape.hape_cli.models.crud_model')
        self.project_name = project_name
        self.project_name_underscore = project_name.replace("-", "_")
        self.project_name_camel_case = project_name.title().replace("-", "")
        self.model_name = model_name
        self.model_name_underscore = model_name.replace("-", "_")
        self.model_name_camel_case = model_name.title().replace("-", "")
        self.json_schema = json_schema
        self.model_content = ""
        self.controller_content = ""
        self.argument_parser_content = ""

    def validate(self):
        self.logger.debug(f"validate()")
        if not self.model_name:
            self.logger.error("Model name is required")
            exit(1)
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', self.model_name):
            self.logger.error(f"Error: Model name '{self.model_name}' must contain only lowercase letters, numbers, and use '-' as a separator.")
            exit(1)
    
    def _generate_content_model(self):
        self.logger.debug(f"_generate_content_model()")
        self.model_content = """
from hape.base.model import Model

class {model_name}(Model):
    __tablename__ = '{model_name_underscore}'
""".strip()

    def _generate_content_controller(self):
        self.logger.debug(f"_generate_content_controller()")
#         from hape.models.deployment_cost_model import DeploymentCost

# class DeploymentCostController(ModelController):
    
    # def __init__(self):
    #     super().__init__(DeploymentCost)

        self.controller_content = """
from hape.base.model_controller import ModelController
from hape.models.deployment_cost_model import DeploymentCost

class DeploymentCostController(ModelController):
    
    def __init__(self):
        super().__init__(DeploymentCost)
""".strip()

