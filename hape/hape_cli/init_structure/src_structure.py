BOOTSTRAP_PY = """
import hape.bootstrap

def bootstrap():
    hape.bootstrap.bootstrap()
""".strip()


MAIN_PY = """
from {{project_name}}.cli import main

if __name__ == "__main__":
    main()
""".strip()


PLAYGROUND_PY = """
class Playground:

    @classmethod
    def main(self):
        playground = Playground()
        playground.play()

    def play(self):
        print("Playground.play() ran successfully!")
""".strip()


CLI_PY = """
from {{project_name}}.bootstrap import bootstrap
from {{project_name}}.argument_parsers.main_argument_parser import MainArgumentParser

def main():
    bootstrap()
    
    main_parser = MainArgumentParser()
    
    parser = main_parser.create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    main_parser.run_action(args)
""".strip()


MAIN_ARGUMENT_PARSER = """
import argparse
from importlib.metadata import version

from {{project_name}}.argument_parsers.playground_argument_parser import PlaygroundArgumentParser

class MainArgumentParser:

    def create_parser(self):
        parser = argparse.ArgumentParser(
            description="{{project_name}} created by HAPE Framework"
        )
        try:
            parser.add_argument("-v", "--version", action="version", version=version("{{project_name}}"))
        except:
            parser.add_argument("-v", "--version", action="version", version="0.0.0")
        
        subparsers = parser.add_subparsers(dest="command")
        
        PlaygroundArgumentParser().create_subparser(subparsers)
        return parser
    
    def run_action(self, args):
        if args.command == "play":
            PlaygroundArgumentParser().run_action(args)
        else:
            print(f"Error: Invalid command {args.command}")
            exit(1)
""".strip()

PLAYGROUND_ARGUMENT_PARSER = """
import sys
from {{project_name}}.playground import Playground

class PlaygroundArgumentParser:
    def create_subparser(self, subparsers):    
        play_parser = subparsers.add_parser("play")
        play_parser.description = "Runs Playground.play() function"        

    def run_action(self, args):
        if args.command != "play":
            return
        
        Playground.main()
"""