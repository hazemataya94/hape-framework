from hape.logging import Logging
from hape.hape_cli.interfaces.format_model import FormatModel

class Json(FormatModel):
    def __init__(self):
        super().__init__("json")
        self.logger = Logging.get_logger('hape.hape_cli.models.json_model')
