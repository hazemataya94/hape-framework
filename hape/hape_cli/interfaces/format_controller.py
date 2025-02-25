
from hape.logging import Logging
from hape.hape_cli.interfaces.format_model import FormatModel

class FormatController:

    def __init__(self, format: str):
        self.logger = Logging.get_logger('hape.hape_cli.interfaces.format_controller')
        if format not in FormatModel.supported_formats:
            self.logger.error(f"Invalid format: {format}. Supported formats are: {', '.join(FormatModel.supported_formats)}")
            exit(1)
        self.format = FormatModel(format)
    
    def get(self):
        self.format.get()