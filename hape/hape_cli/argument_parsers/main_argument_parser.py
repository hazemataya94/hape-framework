import argparse
from importlib.metadata import version

from hape.hape_cli.argument_parsers.init_argument_parser import InitArgumentParser

class MainArgumentParser:

    def create_parser():
        parser = argparse.ArgumentParser(description="HAPE Framework CLI")

        try:
            parser.add_argument("-v", "--version", action="version", version=version("hape"))
        except:
            parser.add_argument("-v", "--version", action="version", version="0.0.0")
        
        subparsers = parser.add_subparsers(dest="command")
        
        InitArgumentParser().create_subparser(subparsers)

        return parser

    def run_action(self, args):

        if args.command == "init":
            InitArgumentParser().run_action(args)
        else:
            print(f"Error: Invalid command {args.command}")
            exit(1)
