from hape.logging import Logging
from hape.hape_cli.interfaces.format_argument_parser import FormatArgumentParser

class JsonArgumentParser(FormatArgumentParser):
    def __init__(self):
        super().__init__("json")
        self.logger = Logging.get_logger('hape.hape_cli.argument_parsers.json_argument_parser')
