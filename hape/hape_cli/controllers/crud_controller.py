import json
import yaml
import os

from hape.logging import Logging
from hape.hape_cli.models.crud_model import Crud

class CrudController:

    def __init__(self, name, schema_json, schema_yaml):
        self.logger = Logging.get_logger('hape.hape_cli.controllers.crud_controller')
        schema = {}
        if schema_json:
            schema = json.loads(schema_json)
        elif schema_yaml:
            schema = yaml.safe_load(schema_yaml)
        
        self.crud = Crud(os.path.basename(os.getcwd()), name, schema)
        self.crud.validate()
    
    def generate(self):
        self.crud.validate_schema()
        self.crud.generate()
        
    def delete(self):
        self.crud.delete()
