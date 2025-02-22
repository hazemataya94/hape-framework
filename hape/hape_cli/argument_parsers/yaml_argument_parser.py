from hape.logging import Logging
from hape.hape_cli.interfaces.format_argument_parser import FormatArgumentParser

class YamlArgumentParser(FormatArgumentParser):
    def __init__(self):
        super().__init__("yaml")
        self.logger = Logging.get_logger('hape.hape_cli.argument_parsers.yaml_argument_parser')
