from hape.hape_cli.controllers.init_controller import InitController

class InitArgumentParser:
    def __init__(self):
        self.COMMAND = "init"

    def create_subparser(self, subparsers):    
        init_parser = subparsers.add_parser(self.COMMAND, help="Commands related to initializing the workspace")
        init_parser_subparser = init_parser.add_subparsers(dest="action")

        new_project_parser = init_parser_subparser.add_parser("new-project", help="Initializes a new project")
        new_project_parser.add_argument("-n", "--name", required=True, help="Name of the project")

    def run_action(self, args):
        if args.command != self.COMMAND:
            return
        
        controller = InitController()

        if args.action == "new-project":
            controller.create_new_project(args.name)
        else:
            print(f"Error: Invalid {args.command} action. Use `hape {args.command} --help` for more details.")
            exit(1)
