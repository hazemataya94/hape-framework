from hape.logging import Logging
from hape.hape_cli.controllers.json_controller import JsonController

class JsonArgumentParser:
    def __init__(self):
        self.COMMAND = "json"
        self.logger = Logging.get_logger('hape.hape_cli.argument_parsers.json_argument_parser')

    def create_subparser(self, subparsers):    
        self.logger.debug(f"create_subparser(subparsers)")
        json_parser = subparsers.add_parser(self.COMMAND, help="Commands related to JSON to generate model schema templates")
        json_parser_subparser = json_parser.add_subparsers(dest="action")

        json_parser = json_parser_subparser.add_parser("get", help="Get JSON templates and data related to the project")
        json_parser.add_argument("-m", "--model-schema", required=True, action="store_true", help="Template JSON schema of the model")

    def run_action(self, args):
        self.logger.debug(f"run_action(args)")
        if args.command != self.COMMAND:
            return
        if args.action == "get":
            JsonController(args.model_schema).get()
        else:
            self.logger.error(f"Error: Invalid action {args.action} for {args.command}. Use `hape {args.command} --help` for more details.")
            exit(1)
