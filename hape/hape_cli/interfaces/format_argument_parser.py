from hape.logging import Logging
from hape.hape_cli.interfaces.format_model import FormatModel
from hape.hape_cli.interfaces.format_controller import FormatController

class FormatArgumentParser:
    
    def __init__(self, format: str):
        self.logger = Logging.get_logger('hape.hape_cli.argument_parsers.format_argument_parser')
        if format not in FormatModel.supported_formats:
            self.logger.error(f"Invalid format: {format}. Supported formats are: {', '.join(FormatModel.supported_formats)}")
            exit(1)
        self.format = format
        self.COMMAND = format

    def create_subparser(self, subparsers):    
        self.logger.debug(f"create_subparser(subparsers)")
        format_parser = subparsers.add_parser(self.COMMAND, help=f"Commands related to {self.format.upper()} to generate model schema templates")
        format_parser_subparser = format_parser.add_subparsers(dest="action")

        format_parser = format_parser_subparser.add_parser("get", help=f"Get {self.format.upper()} templates and data related to the project")
        format_parser.add_argument("-m", "--model-schema", required=True, action="store_true", help=f"Template {self.format.upper()} schema of the model")

    def run_action(self, args):
        self.logger.debug(f"run_action(args)")
        if args.command != self.COMMAND:
            return
        if args.action == "get":
            FormatController(args.model_schema, self.format).get()
        else:
            self.logger.error(f"Error: Invalid action {args.action} for {args.command}. Use `hape {args.command} --help` for more details.")
            exit(1)
