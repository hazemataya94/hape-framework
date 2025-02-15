import yaml
from hape.logging import Logging
from hape.hape_cli.models.crud_model import Crud
from hape.hape_cli.interfaces.format_model import FormatModel

class Yaml(FormatModel):
    
    def __init__(self, model_schema_template: bool):
        self.logger = Logging.get_logger('hape.hape_cli.models.yaml_model')
        self.schema = None
        self.model_schema_template = model_schema_template
    def load(self, schema: str):
        self.schema = yaml.safe_load(schema)
    
    def get(self):
        self.logger.debug(f"Getting YAML {{'self.model_schema_template': {self.model_schema_template}'}}")
        self.generate()
            
    def generate(self):
        self.logger.debug(f"Generating YAML {{'self.model_schema_template': {self.model_schema_template}'}}")
        if self.model_schema_template:
            print(Crud._model_schema_template)
        else:
            self.logger.error("Nothing to generate.")
            exit(1)
    
    

