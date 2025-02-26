import argparse
from importlib.metadata import version

from hape.argument_parsers.playground_argument_parser import PlaygroundArgumentParser
from hape.argument_parsers.config_argument_parser import ConfigArgumentParser
from hape.argument_parsers.git_argument_parser import GitArgumentParser
from hape.argument_parsers.k8s_deployment_argument_parser import K8SDeploymentArgumentParser
from hape.argument_parsers.k8s_deployment_cost_argument_parser import K8SDeploymentCostArgumentParser

class MainArgumentParser:

    def create_parser(self):
        parser = argparse.ArgumentParser(
            description="hape cli - streamline your development operations"
        )
        try:
            parser.add_argument("-v", "--version", action="version", version=version("hape"))
        except:
            parser.add_argument("-v", "--version", action="version", version="0.0.0")
        
        subparsers = parser.add_subparsers(dest="command")
        
        PlaygroundArgumentParser().create_subparser(subparsers)
        ConfigArgumentParser().create_subparser(subparsers)
        GitArgumentParser().create_subparser(subparsers)
        K8SDeploymentArgumentParser().create_subparser(subparsers)
        K8SDeploymentCostArgumentParser().create_subparser(subparsers)
        
        return parser
    
    def run_action(self, args):
        
        if args.command == "play":
            PlaygroundArgumentParser().run_action(args)
        elif args.command == "config":
            ConfigArgumentParser().run_action(args)
        elif args.command == "git":
            GitArgumentParser().run_action(args)
        elif args.command == "k8s-deployment":
            K8SDeploymentArgumentParser().run_action(args)
        elif args.command == "k8s-deployment-cost":
            K8SDeploymentCostArgumentParser().run_action(args)
        else:
            self.logger.error(f"Invalid command {args.command}. Use `hape --help` for more details.")
            exit(1)
