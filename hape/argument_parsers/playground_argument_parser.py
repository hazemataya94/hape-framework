import sys
from hape.playground import Playground

class PlaygroundArgumentParser:

    def create_subparser(self, subparsers):    
        if len(sys.argv) > 1 and sys.argv[1] == "play":
            play_parser = subparsers.add_parser("play")
            play_parser.description = ""        

    def run_action(self, args):
        if args.command != "play":
            return
        
        Playground.main()
    