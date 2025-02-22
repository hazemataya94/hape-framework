from hape.logging import Logging
from hape.hape_cli.interfaces.format_model import FormatModel

class Yaml(FormatModel):
    def __init__(self):
        super().__init__("yaml")
        self.logger = Logging.get_logger('hape.hape_cli.models.yaml_model')
