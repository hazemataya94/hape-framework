import os
import re
import sys
from hape.logging import logger
from hape.services.file_service import FileService

class Init:

    def __init__(self, name: str):
        self.name = name
        self.name_underscore = name.replace("-", "_")
        self.file_service = FileService()
        self.hape_framework_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.hape_files = [
            ".dockerignore",
            ".env.example",
            ".gitignore",
            "alembic.ini",
            "main.py",
            "Makefile",
            "requirements-dev.txt",
            "setup.py"
        ]
        self.hape_dirs = [
            "dockerfiles",
            "scripts",
        ]

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
            dest_file = os.path.join(self.name, file)
            logger.debug(f'Copying file: {src_file} -> {dest_file}')
            self.file_service.copy_file(src_file, dest_file, overwrite=True)

        for directory in self.hape_dirs:
            src_dir = os.path.join(self.hape_framework_path, directory)
            dest_dir = os.path.join(self.name, directory)
            logger.debug(f'Copying directory: {src_dir} -> {dest_dir}')
            self.file_service.copy_directory(src_dir, dest_dir)

    def __init_project_structure_process_dictionary(self, dictionary: dict, root_path: str):
        for key, value in dictionary.items():
            sub_path = os.path.join(root_path, key)
            if value is None:
                logger.debug(f'Creating file: {sub_path}')
                self.file_service.write_file(sub_path, "")
            elif isinstance(value, str):
                logger.debug(f'Creating file: {sub_path}')
                self.file_service.write_file(sub_path, value)
            elif isinstance(value, list):
                logger.debug(f'Creating directory: {sub_path}')
                self.file_service.create_directory(sub_path)
                for file in value:
                    logger.debug(f'Creating file: {sub_path}')
                    self.file_service.write_file(os.path.join(sub_path, file), "")
            elif isinstance(value, dict):
                self.__init_project_structure_process_dictionary(value, sub_path)

    def __init_project_structure(self):
        logger.debug(f'Creating directory: {self.name}')
        if self.file_service.path_exists(self.name):
            logger.error(f"Error: directory '{self.name}' already exists.")
            sys.exit(1)
        self.file_service.create_directory(self.name)
        self.__init_project_structure_process_dictionary(self.PROJECT_STRUCTURE, self.name)

        readme_path = os.path.join(self.name, "README.md")
        logger.debug(f'Creating file: {readme_path}')
        self.file_service.write_file(readme_path, f"# {self.name}\n")

    def validate(self):
        name = self.name.strip()
        logger.debug(f'Validating project name: {self.name}')
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
            logger.error(f"Error: Project name '{name}' must contain only lowercase letters, numbers, and use '-' as a separator.")
            sys.exit(1)
        logger.debug(f'Valid project name.')

    def init_project(self):
        self.__init_project_structure()
        self.__copy_hape_files()
        logger.info(f'Project {self.name} has been successfully initialized!')
