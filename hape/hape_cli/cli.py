from hape.bootstrap import bootstrap
from hape.hape_cli.argument_parsers.main_argument_parser import MainArgumentParser

def main():
    bootstrap()
    
    main_parser = MainArgumentParser()
    
    parser = main_parser.create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    main_parser.run_action(args)
