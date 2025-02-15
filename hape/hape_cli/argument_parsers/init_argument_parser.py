from hape.logging import Logging
from hape.hape_cli.controllers.init_controller import InitController

class InitArgumentParser:
    def __init__(self):
        self.COMMAND = "init"
        self.logger = Logging.get_logger('hape.hape_cli.argument_parsers.init_argument_parser')

    def create_subparser(self, subparsers):    
        self.logger.debug(f"create_subparser(subparsers)")
        init_parser = subparsers.add_parser(self.COMMAND, help="Commands related to initializing the workspace")
        init_parser_subparser = init_parser.add_subparsers(dest="action")

        project_parser = init_parser_subparser.add_parser("project", help="Initializes a new project")
        project_parser.add_argument("-n", "--name", required=True, help="Name of the project")

    def run_action(self, args):
        self.logger.debug(f"run_action(args)")
        if args.command != self.COMMAND:
            return
        if args.action == "project":
            InitController(args.name).init_project()
        else:
            self.logger.error(f"Error: Invalid action {args.action} for {args.command}. Use `hape {args.command} --help` for more details.")
            exit(1)
