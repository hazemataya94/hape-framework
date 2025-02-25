from hape.logging import Logging
from hape.hape_cli.interfaces.format_controller import FormatController

class JsonController(FormatController):

    def __init__(self):
        super().__init__("json")
        self.logger = Logging.get_logger('hape.hape_cli.controllers.json_controller')
