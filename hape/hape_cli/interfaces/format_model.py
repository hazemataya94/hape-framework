import json
import yaml
from hape.logging import Logging
from hape.hape_cli.models.crud_model_schema import CrudModelSchema

class FormatModel:
    
    supported_formats = ["json", "yaml"]
    
    def __init__(self, format: str):
        self.logger = Logging.get_logger('hape.hape_cli.interfaces.format_model')
        self.schema = None
        self.format = format
    
    def load(self, schema: str):
        if self.format == "json":
            self.schema = json.loads(schema)
        elif self.format == "yaml":
            self.schema = yaml.safe_load(schema)
        else:
            self.logger.error(f"Invalid format: {self.format}")
            exit(1)
        return self.schema
    
    def get(self):
        if self.format == "json":
            print(CrudModelSchema._model_schema_json)
        elif self.format == "yaml":
            print(CrudModelSchema._model_schema_yaml)
        else:
            self.logger.error(f"Invalid format: {self.format}. Supported formats are: json, yaml")
            exit(1)
        