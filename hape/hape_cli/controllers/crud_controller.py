import json
import yaml
import os

from hape.logging import Logging
from hape.hape_cli.models.crud_model import Crud

class CrudController:

    def __init__(self, name, schema_json, schema_yaml):
        self.logger = Logging.get_logger('hape.hape_cli.controllers.crud_controller')
        if schema_json:
            try:
                schema = json.loads(schema_json)
            except Exception as e:
                self.logger.error(f"Error: Invalid schema format. Please provide a valid JSON or YAML schema.")
                exit(1)
        elif schema_yaml:
            try:
                schema = yaml.safe_load(schema_yaml)
            except Exception as e:
                self.logger.error(f"Error: Invalid schema format. Please provide a valid JSON or YAML schema.")
                exit(1)
        else:
            self.logger.error(f"Error: No schema provided. Please provide a valid JSON or YAML schema.")
            exit(1)
            
        self.crud = Crud(os.path.basename(os.getcwd()), name, schema)
        
        self.crud.validate()
    
    def generate(self):
        self.crud.generate()
