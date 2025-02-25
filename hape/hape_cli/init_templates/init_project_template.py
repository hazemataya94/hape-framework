from hape.hape_cli.init_templates.source_code_templates import BOOTSTRAP_PY, MAIN_PY, PLAYGROUND_PY, CLI_PY, MAIN_ARGUMENT_PARSER, PLAYGROUND_ARGUMENT_PARSER, MIGRATION_ENV_PY
from hape.hape_cli.init_templates.dockerfiles_templates import DOCKERFILE_DEV, DOCKERFILE_PROD, DOCKER_COMPOSE
from hape.hape_cli.init_templates.hidden_files_templates import DOCKER_IGNORE, ENV_EXAMPLE, GIT_IGNORE
from hape.hape_cli.init_templates.requirements_templates import REQUIREMENTS_DEV, REQUIREMENTS_CLI
from hape.hape_cli.init_templates.makefile_template import MAKEFILE
from hape.hape_cli.init_templates.alembic_template import ALEMBIC_INI
from hape.hape_cli.init_templates.setup_templates import SETUP_PY, MANIFEST_IN

INIT_PROJECT_TEMPLATE = {
    ".dockerignore": DOCKER_IGNORE,
    ".env.example": ENV_EXAMPLE,
    ".gitignore": GIT_IGNORE,
    "alembic.ini": ALEMBIC_INI,
    "main.py": MAIN_PY,
    "Makefile": MAKEFILE,
    "MANIFEST.in": MANIFEST_IN,
    "README.md": "# {{project_name_title}}",
    "requirements-dev.txt": REQUIREMENTS_DEV,
    "requirements-cli.txt": REQUIREMENTS_CLI,
    "setup.py": SETUP_PY,
    "dockerfiles": {
        "Dockerfile.dev": DOCKERFILE_DEV,
        "Dockerfile.prod": DOCKERFILE_PROD,
        "docker-compose.yml": DOCKER_COMPOSE,
    },
    "{{project_name}}": {
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
            "env.py": MIGRATION_ENV_PY,
            "script.py.mako": None,
            "versions": {
                ".gitkeep": None
            },
            "json": {
                ".gitkeep": None
            },
            "yaml": {
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