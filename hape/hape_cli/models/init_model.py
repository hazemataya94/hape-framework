import os
import re
import sys
import importlib.util

from hape.logging import Logging
from hape.services.file_service import FileService

class Init:

    def __init__(self, name: str):
        self.logger = Logging.get_logger('hape.hape_cli.init_model')
        self.name = name
        self.name_underscore = name.replace("-", "_")
        self.file_service = FileService()
        
        spec = importlib.util.find_spec("hape")
        if spec and spec.origin:
            self.hape_framework_path = os.path.dirname(os.path.abspath(spec.origin))
        else:
            self.logger.error("Couldn't not find `hape` package. Execute `pip install --upgrade hape`.")
            exit(1)
        
        self.hape_files = [
            'artifacts/Makefile',
            'artifacts/alembic.ini',
            'artifacts/main.py',
            'artifacts/requirements.txt',
            'artifacts/setup.py'
        ]
        # self.hape_files = [
        #     "artifacts/.dockerignore",
        #     "artifacts/.env.example",
        #     "artifacts/.gitignore",
        #     "artifacts/alembic.ini",
        #     "artifacts/main.py",
        #     "artifacts/Makefile",
        #     "artifacts/requirements.txt",
        #     "artifacts/setup.py"
        # ]
        
        self.hape_dirs = []
        # self.hape_dirs = [
        #     "artifacts/dockerfiles",
        #     "artifacts/scripts",
        # ]

        self.PROJECT_STRUCTURE = {
            ".dockerignore": None,
            ".env.example": None,
            ".gitignore": None,
            "alembic.ini": None,
            "main.py": None,
            "Makefile": None,
            "README.md": None,
            "requirements-dev.txt": None,
            "setup.py": None,
            "dockerfiles": [],
            "scripts": [],
            self.name_underscore: {
                "argument_parsers": [".gitkeep"],
                "cli.py": None,
                "controllers": ["__init__.py"],
                "enums": ["__init__.py"],
                "migrations": ["README", "env.py", "script.py.mako"],
                "migrations/versions": [".gitkeep"],
                "models": ["__init__.py"],
                "services": ["__init__.py"],
            }
        }

    def __copy_hape_files(self):
        for file in self.hape_files:
            src_file = os.path.join(self.hape_framework_path, file)
            dest_file = os.path.join(self.name, file).replace('artifacts/', '')
            self.logger.debug(f'Copying file: {src_file} -> {dest_file}')
            self.file_service.copy_file(src_file, dest_file, overwrite=True)

        for directory in self.hape_dirs:
            src_dir = os.path.join(self.hape_framework_path, directory)
            dest_dir = os.path.join(self.name, directory)
            self.logger.debug(f'Copying directory: {src_dir} -> {dest_dir}')
            self.file_service.copy_directory(src_dir, dest_dir)

    def __init_project_structure_process_dictionary(self, dictionary: dict, root_path: str):
        for key, value in dictionary.items():
            sub_path = os.path.join(root_path, key)
            if value is None:
                self.logger.debug(f'Creating file: {sub_path}')
                self.file_service.write_file(sub_path, "")
            elif isinstance(value, str):
                self.logger.debug(f'Creating file: {sub_path}')
                self.file_service.write_file(sub_path, value)
            elif isinstance(value, list):
                self.logger.debug(f'Creating directory: {sub_path}')
                self.file_service.create_directory(sub_path)
                for file in value:
                    self.logger.debug(f'Creating file: {sub_path}')
                    self.file_service.write_file(os.path.join(sub_path, file), "")
            elif isinstance(value, dict):
                self.__init_project_structure_process_dictionary(value, sub_path)

    def __init_project_structure(self):
        self.logger.debug(f'Creating directory: {self.name}')
        if self.file_service.path_exists(self.name):
            self.logger.error(f"Error: directory '{self.name}' already exists.")
            sys.exit(1)
        self.file_service.create_directory(self.name)
        self.__init_project_structure_process_dictionary(self.PROJECT_STRUCTURE, self.name)

        readme_path = os.path.join(self.name, "README.md")
        self.logger.debug(f'Creating file: {readme_path}')
        self.file_service.write_file(readme_path, f"# {self.name}\n")

    def validate(self):
        name = self.name.strip()
        self.logger.debug(f'Validating project name: {self.name}')
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
            self.logger.error(f"Error: Project name '{name}' must contain only lowercase letters, numbers, and use '-' as a separator.")
            sys.exit(1)
        self.logger.debug(f'Valid project name.')

    def init_project(self):
        self.__init_project_structure()
        self.__copy_hape_files()
        self.logger.info(f'Project {self.name} has been successfully initialized!')
