from appname.src.controllers.config_controller import ConfigController

class ConfigArgumentParser:

    def create_subparser(self, subparsers):    
        config_parser = subparsers.add_parser("config", help="Commands related to the configurations of the cli")
        
        config_subparser = config_parser.add_subparsers(dest="action")
        check_parser = config_subparser.add_parser("check", help="Check if required configurations for the cli to work are set")

    def run_action(self, args):
        if args.command != "config":
            return
        
        if args.action == "check":
            ConfigController.check_configurations()
        else:
            print(f"Error: Invalid {args.comman} action. Use `appname {args.comman} --help` for more details.")
            exit(1)
