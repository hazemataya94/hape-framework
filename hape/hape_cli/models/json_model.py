import json
from hape.logging import Logging
from hape.hape_cli.models.crud_model import Crud
from hape.hape_cli.interfaces.format_model import FormatModel

class Json(FormatModel):
    
    def __init__(self, model_schema: bool):
        self.logger = Logging.get_logger('hape.hape_cli.models.json_model')
        self.schema = None
        self.model_schema = model_schema        
    
    def load(self, schema: str):
        self.schema = json.loads(schema)
    
    def get(self):
        self.generate()
            
    def generate(self):
        self.logger.debug(f"Generating JSON {{'self.model_schema_json': {self.model_schema}'}}")
        if self.model_schema:
            print(Crud._model_schema_json)
        else:
            self.logger.error("Nothing to generate.")
            exit(1)

