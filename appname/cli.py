from appname.src.bootstrap import bootstrap_application

from appname.argument_parsers.main_argument_parser import MainArgumentParser

def main():
    bootstrap_application()
    
    main_parser = MainArgumentParser()
    
    parser = main_parser.create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    main_parser.run_action(args)

if __name__ == "__main__":
    main()
