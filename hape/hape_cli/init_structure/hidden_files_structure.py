DOCKER_IGNORE = """
.venv
dockerfiles
**docker-compose.yml**
*.md
""".strip()

ENV_EXAMPLE = """
HAPE_MARIADB_HOST="127.0.0.1"
HAPE_MARIADB_USERNAME="{{project_name}}_user"
HAPE_MARIADB_PASSWORD="{{project_name}}_password"
HAPE_MARIADB_DATABASE="{{project_name}}_db"
NEW_VAR_1="1"
NEW_VAR_2="2"
""".strip()

GIT_IGNORE = """
dockerfiles/*-init
playground/*
!playground/.gitkeep
!{{project_name}}/migrations/.gitkeep
*.zip
*.venv
*.vscode

.DS_Store
*.DS_Store
**.DS_Store

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
# Usually these files are written by a python script from a template
# before PyInstaller builds the executable, when PyInstaller is instructed to
# follow the import statements of scripts it is given, and so they must be
# included in source control in order to be able to recreate the executable
# later from this source control.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# Environments
.env
.venv
venv/
""".strip()
