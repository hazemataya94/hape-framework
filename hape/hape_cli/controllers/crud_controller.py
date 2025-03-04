import json
import yaml
import os

from hape.logging import Logging
from hape.hape_cli.models.crud_model import Crud
from hape.services.file_service import FileService

class CrudController:

    # name is added for the --delete command, to be able to pass the name.
    def __init__(self, name, schema_json, schema_yaml):
        self.logger = Logging.get_logger('hape.hape_cli.controllers.crud_controller')
        file_service = FileService()
        
        schema = None
        
        is_json = bool(schema_json)
        is_yaml = bool(schema_yaml)    
        is_json_string = is_json and isinstance(schema_json, str)
        is_yaml_string = is_yaml and isinstance(schema_yaml, str)
        is_json_file = is_json_string and schema_json.endswith('.json')
        is_yaml_file = is_yaml_string and schema_yaml.endswith('.yaml')
        is_json_default = is_json and isinstance(schema_json, bool)
        is_yaml_default = is_yaml and isinstance(schema_yaml, bool)
        self.logger.debug(f"is_json_string: {is_json_string}")
        self.logger.debug(f"is_yaml_string: {is_yaml_string}")
        self.logger.debug(f"is_json_file: {is_json_file}")
        self.logger.debug(f"is_yaml_file: {is_yaml_file}")
        self.logger.debug(f"is_json_default: {is_json_default}")
        self.logger.debug(f"is_yaml_default: {is_yaml_default}")

        if is_json_string:
            try:
                schema = json.loads(schema_json)
            except e:
                self.logger.error(f"Invalid JSON schema: {schema_json}")
                exit(1)
        elif is_yaml_string:
            try:
                schema = yaml.safe_load(schema_yaml)
            except yaml.YAMLError as e:
                self.logger.error(f"Invalid YAML schema: {schema_yaml}")
                exit(1)
        if is_json_file:
            if not FileService().file_exists(schema_json):
                self.logger.error(f"JSON file not found at {schema_json}")
                exit(1)
            schema = file_service.read_json_file(schema_json)
        elif is_yaml_file:
            if not FileService().file_exists(schema_yaml):
                self.logger.error(f"YAML file not found at {schema_yaml}")
                exit(1)
            schema = file_service.read_yaml_file(schema_yaml)
        elif is_json_default:
            if not FileService().file_exists(Crud.draft_json_file_path):
                self.logger.error(f"Draft JSON file not found at {Crud.draft_json_file_path}")
                exit(1)
            schema = file_service.read_json_file(Crud.draft_json_file_path)
        elif is_yaml_default:
            if not FileService().file_exists(Crud.draft_yaml_file_path):
                self.logger.error(f"Draft YAML file not found at {Crud.draft_yaml_file_path}")
                exit(1)
            schema = file_service.read_yaml_file(Crud.draft_yaml_file_path)
            
        self.crud = Crud(os.path.basename(os.getcwd()), name, schema)
        self.crud.validate()
    
    def generate(self):
        self.crud.validate_schemas()
        self.crud.generate()
        
    def delete(self):
        self.crud.delete()
