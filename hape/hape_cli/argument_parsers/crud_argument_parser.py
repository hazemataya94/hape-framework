from hape.logging import Logging
from hape.hape_cli.controllers.crud_controller import CrudController

class CrudArgumentParser:
    def __init__(self):
        self.COMMAND = "crud"
        self.logger = Logging.get_logger('hape.argument_parsers.crud_argument_parser')

    def create_subparser(self, subparsers):    
        self.logger.debug(f"create_subparser(subparsers)")
        crud_parser = subparsers.add_parser(self.COMMAND, help="Commands related to CRUD operations")
        crud_parser_subparser = crud_parser.add_subparsers(dest="action")

        generate_parser = crud_parser_subparser.add_parser("generate", help="Generates a new CRUD operation")
        generate_parser.add_argument("-n", "--name", required=True, help="Name of the model")
        schema_group = generate_parser.add_mutually_exclusive_group(required=True)
        schema_group.add_argument("-j", "--schema-json", help="Schema of the model in JSON format")
        schema_group.add_argument("-y", "--schema-yaml", help="Schema of the model in YAML format")
        
    def run_action(self, args):
        self.logger.debug(f"run_action(args)")
        if args.command != self.COMMAND:
            return
        self.logger.debug(f"Running action: {args.action}")
        if args.action == "generate":
            CrudController(args.name, args.schema_json, args.schema_yaml).generate()
        else:
            self.logger.error(f"Error: Invalid {args.command} action. Use `hape {args.command} --help` for more details.")
            exit(1)
