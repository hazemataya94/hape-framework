import yaml
from hape.logging import Logging
from hape.hape_cli.models.crud_model import Crud
from hape.hape_cli.interfaces.format_model import FormatModel

class Yaml(FormatModel):
    
    def __init__(self, model_schema: bool):
        self.logger = Logging.get_logger('hape.hape_cli.models.yaml_model')
        self.schema = None
        self.model_schema = model_schema
    
    def load(self, schema: str):
        self.schema = yaml.safe_load(schema)
    
    def get(self):
        self.logger.debug(f"get()")
        if self.model_schema:
            print(Crud._model_schema_yaml)
        else:
            self.logger.error("Nothing to generate.")
            exit(1)
