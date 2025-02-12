from hape.hape_cli.init_structure.src_structure import BOOTSTRAP_PY, MAIN_PY, PLAYGROUND_PY, CLI_PY, MAIN_ARGUMENT_PARSER, PLAYGROUND_ARGUMENT_PARSER
from hape.hape_cli.init_structure.dockerfiles_structure import DOCKERFILE_DEV, DOCKERFILE_PROD, DOCKER_COMPOSE
from hape.hape_cli.init_structure.hidden_files_structure import DOCKER_IGNORE, ENV_EXAMPLE, GIT_IGNORE
from hape.hape_cli.init_structure.requirements_structure import REQUIREMENTS_DEV, REQUIREMENTS_CLI
from hape.hape_cli.init_structure.makefile_structure import MAKEFILE
from hape.hape_cli.init_structure.alembic_structure import ALEMBIC_INI
from hape.hape_cli.init_structure.setup_structure import SETUP_PY

NEW_PROJECT_STRUCTURE = {
    ".dockerignore": DOCKER_IGNORE,
    ".env.example": ENV_EXAMPLE,
    ".gitignore": GIT_IGNORE,
    "alembic.ini": ALEMBIC_INI,
    "main.py": MAIN_PY,
    "Makefile": MAKEFILE,
    "README.md": "# {{project_name}}",
    "requirements-dev.txt": REQUIREMENTS_DEV,
    "requirements-cli.txt": REQUIREMENTS_CLI,
    "setup.py": SETUP_PY,
    "dockerfiles": {
        "Dockerfile.dev": DOCKERFILE_DEV,
        "Dockerfile.prod": DOCKERFILE_PROD,
        "docker-compose.yml": DOCKER_COMPOSE,
    },
    "project_name": {
        "__init__.py": None,
        "cli.py": CLI_PY,
        "bootstrap.py": BOOTSTRAP_PY,
        "playground.py": PLAYGROUND_PY,
        "argument_parsers": {
            "__init__.py": None,
            "playground_argument_parser.py": PLAYGROUND_ARGUMENT_PARSER,
            "main_argument_parser.py": MAIN_ARGUMENT_PARSER
        },
        "controllers": {
            "__init__.py": None   
        },
        "enums": {
            "__init__.py": None
        },
        "migrations": {
            "README": None,
            "env.py": None,
            "script.py.mako": None,
            "versions": {
                ".gitkeep": None
            }
        },
        "models": {
            "__init__.py" : None  
        },
        "services": {
            "__init__.py": None
        },
    }
}