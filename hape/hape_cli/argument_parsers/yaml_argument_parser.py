from hape.logging import Logging
from hape.hape_cli.controllers.yaml_controller import YamlController

class YamlArgumentParser:
    def __init__(self):
        self.COMMAND = "yaml"
        self.logger = Logging.get_logger('hape.hape_cli.argument_parsers.yaml_argument_parser')

    def create_subparser(self, subparsers):    
        self.logger.debug(f"create_subparser(subparsers)")
        yaml_parser = subparsers.add_parser(self.COMMAND, help="Commands related to YAML to generate model schema templates")
        yaml_parser_subparser = yaml_parser.add_subparsers(dest="action")

        yaml_parser = yaml_parser_subparser.add_parser("get", help="Get YAML templates and data related to the project")
        yaml_parser.add_argument("-m", "--model-schema", required=True, action="store_true", help="Template YAML schema of the model")

    def run_action(self, args):
        self.logger.debug(f"run_action(args)")
        if args.command != self.COMMAND:
            return
        if args.action == "get":
            YamlController(args.model_schema).get()
        else:
            self.logger.error(f"Error: Invalid action {args.action} for {args.command}. Use `hape {args.command} --help` for more details.")
            exit(1)
