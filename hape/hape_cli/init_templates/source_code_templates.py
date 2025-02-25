BOOTSTRAP_PY = """
def bootstrap():
    pass
""".strip()


MAIN_PY = """
from {{project_name_snake_case}}.cli import main

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
from {{project_name_snake_case}}.bootstrap import bootstrap
from {{project_name_snake_case}}.argument_parsers.main_argument_parser import MainArgumentParser

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

from {{project_name_snake_case}}.argument_parsers.playground_argument_parser import PlaygroundArgumentParser

class MainArgumentParser:

    def create_parser(self):
        parser = argparse.ArgumentParser(
            description="{{project_name_title}} created by HAPE Framework"
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
            self.logger.error(f"Error: Invalid command {args.command}. Use `hape --help` for more details.")
            exit(1)
""".strip()

PLAYGROUND_ARGUMENT_PARSER = """
from {{project_name_snake_case}}.playground import Playground

class PlaygroundArgumentParser:
    def create_subparser(self, subparsers):    
        play_parser = subparsers.add_parser("play")
        play_parser.description = "Runs Playground.play() function"        

    def run_action(self, args):
        if args.command != "play":
            return
        
        Playground.main()
"""

MIGRATION_ENV_PY = """
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from hape.base.model import Base  # Modify this to match your project structure
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""