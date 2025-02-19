from hape.logging import Logging
from hape.hape_cli.models.yaml_model import Yaml

class YamlController:

    def __init__(self, model_schema: bool):
        self.logger = Logging.get_logger('hape.hape_cli.controllers.yaml_controller')    
        self.yaml = Yaml(model_schema)
    
    def get(self):
        self.yaml.get()