from hape.logging import Logging
from hape.hape_cli.interfaces.format_controller import FormatController

class YamlController(FormatController):

    def __init__(self):
        super().__init__("yaml")
        self.logger = Logging.get_logger('hape.hape_cli.controllers.yaml_controller')