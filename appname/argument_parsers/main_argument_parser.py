import argparse
from importlib.metadata import version

from appname.argument_parsers.playground_argument_parser import PlaygroundArgumentParser
from appname.argument_parsers.config_argument_parser import ConfigArgumentParser
from appname.argument_parsers.git_argument_parser import GitArgumentParser
from appname.argument_parsers.deployment_cost_argument_parser import DeploymentCostArgumentParser

class MainArgumentParser:

    def create_parser(self):
        parser = argparse.ArgumentParser(
            description="AppNameShortLong used to streamline development operations"
        )
        try:
            parser.add_argument("-v", "--version", action="version", version=version("appname"))
        except:
            parser.add_argument("-v", "--version", action="version", version="0.0.0")
        
        subparsers = parser.add_subparsers(dest="command")
        
        PlaygroundArgumentParser().create_subparser(subparsers)
        ConfigArgumentParser().create_subparser(subparsers)
        GitArgumentParser().create_subparser(subparsers)
        DeploymentCostArgumentParser().create_subparser(subparsers)

        return parser
    
    def run_action(self, args):
        
        if args.command == "play":
            PlaygroundArgumentParser().run_action(args)
        elif args.command == "config":
            ConfigArgumentParser().run_action(args)
        elif args.command == "git":
            GitArgumentParser().run_action(args)
        elif args.command == "deployment-cost":
            DeploymentCostArgumentParser().run_action(args)
        else:
            print(f"Error: Invalid command {args.command}")
            exit(1)
