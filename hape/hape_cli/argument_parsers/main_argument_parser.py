import argparse
from importlib.metadata import version
from hape.logging import Logging
from hape.hape_cli.argument_parsers.init_argument_parser import InitArgumentParser
from hape.hape_cli.argument_parsers.crud_argument_parser import CrudArgumentParser
from hape.hape_cli.argument_parsers.json_argument_parser import JsonArgumentParser
from hape.hape_cli.argument_parsers.yaml_argument_parser import YamlArgumentParser

class MainArgumentParser:
    
    def __init__(self):
        self.logger = Logging.get_logger('hape.hape_cli.argument_parsers.main_argument_parser')

    def create_parser(self):
        parser = argparse.ArgumentParser(description="HAPE Framework CLI")

        try:
            parser.add_argument("-v", "--version", action="version", version=version("hape"))
        except:
            parser.add_argument("-v", "--version", action="version", version="0.0.0")
        
        subparsers = parser.add_subparsers(dest="command")
        
        InitArgumentParser().create_subparser(subparsers)
        CrudArgumentParser().create_subparser(subparsers)
        JsonArgumentParser().create_subparser(subparsers)
        YamlArgumentParser().create_subparser(subparsers)
        
        return parser

    def run_action(self, args):

        if args.command == "init":
            InitArgumentParser().run_action(args)
        elif args.command == "crud":
            CrudArgumentParser().run_action(args)
        elif args.command == "json":
            JsonArgumentParser().run_action(args)
        elif args.command == "yaml":
            YamlArgumentParser().run_action(args)
        else:
            self.logger.error(f"Error: Main Parser Invalid command {args.command}")
            exit(1)
