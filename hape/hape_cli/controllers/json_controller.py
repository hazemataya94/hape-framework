from hape.logging import Logging
from hape.hape_cli.models.json_model import Json

class JsonController:

    def __init__(self, model_schema_template: bool):
        self.logger = Logging.get_logger('hape.hape_cli.controllers.json_controller')    
        self.json = Json(model_schema_template)
    
    def get(self):
        self.json.get()