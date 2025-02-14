from hape.logging import Logging
from hape.config import Config
from hape.config_db import ConfigDB

class ConfigArgumentParser:

    def __init__(self):
        logger = Logging.get_logger('hape.argument_parsers.config_argument_parser')

    def create_subparser(self, subparsers):    
        self.logger.debug(f"create_subparser(subparsers: {subparsers})")
        config_parser = subparsers.add_parser("config", help="Commands related to the configurations of the cli")
        
        config_subparser = config_parser.add_subparsers(dest="action")
        check_parser = config_subparser.add_parser("check", help="Check if required configurations for the cli to work are set")

    def run_action(self, args):
        self.logger.debug(f"run_action(args: {args})")
        if args.command != "config":
            return
        
        if args.action == "check":
            Config.check_variables(Config._required_env_variables)
            Config.check_variables(ConfigDB._required_env_variables)
            print("Configurations are set correctly.")
        else:
            print(f"Error: Invalid {args.comman} action. Use `hape {args.comman} --help` for more details.")
            exit(1)
