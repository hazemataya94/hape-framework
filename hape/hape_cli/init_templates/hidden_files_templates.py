DOCKER_IGNORE = """
.venv
dockerfiles
**docker-compose.yml**
*.md
""".strip()

ENV_EXAMPLE = """
{{project_name_upper}}_MARIADB_HOST="127.0.0.1"
{{project_name_upper}}_MARIADB_USERNAME="{{project_name_snake_case}}_user"
{{project_name_upper}}_MARIADB_PASSWORD="{{project_name_snake_case}}_password"
{{project_name_upper}}_MARIADB_DATABASE="{{project_name_snake_case}}_db"
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
