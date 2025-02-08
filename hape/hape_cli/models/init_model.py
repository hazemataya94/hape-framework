import os
from hape.services.file_service import FileService

class Init:

    def __init__(self, name: str):
        self.name = name
        self.project_name = name.replace("-", "_")
        self.hape_framework_path = os.path.dirname(os.path.abspath(__file__))
        self.file_service = FileService()
        self.PROJECT_STRUCTURE = {
            ".gitignore": None,
            ".dockerignore": None,
            "Makefile": None,
            "README.md": None,
            "alembic.ini": None,
            "dockerfiles": [
                "docker-compose.dev.yml",
                "Dockerfile.dev",
                "Dockerfile.prod"
            ],
            self.project_name: {
                "argument_parsers": [".gitkeep"],
                "cli.py": "",
                "controllers": ["__init__.py"],
                "enums": ["__init__.py"],
                "migrations": ["README", "env.py", "script.py.mako"],
                "migrations/versions": [".gitkeep"],
                "models": ["__init__.py"],
                "services": ["__init__.py"],
            },
        }

    def __copy_hape_files(self):
        hape_files = ["setup.py", "main.py", "requirements-dev.txt"]
        hape_dirs = ["scripts", "playground"]

        for file in hape_files:
            src_file = os.path.join(self.hape_framework_path, file)
            dest_file = os.path.join(self.name, file)
            self.file_service.copy_file(src_file, dest_file)

        for directory in hape_dirs:
            src_dir = os.path.join(self.hape_framework_path, directory)
            dest_dir = os.path.join(self.name, directory)
            self.file_service.copy_directory(src_dir, dest_dir)

    def __create_new_project_structure(self):
        self.file_service.create_directory(self.name)
        
        for item, contents in self.PROJECT_STRUCTURE.items():
            path = os.path.join(self.name, item.replace("{project_name}", self.project_name))

            if contents is None:
                self.file_service.create_file(path, "")
            elif isinstance(contents, list):
                self.file_service.create_directory(path)
                for file in contents:
                    self.file_service.create_file(os.path.join(path, file), "")
            elif isinstance(contents, dict):
                self.file_service.create_directory(path)
                for subfolder, files in contents.items():
                    sub_path = os.path.join(path, subfolder)
                    self.file_service.create_directory(sub_path)
                    if isinstance(files, list):
                        for file in files:
                            self.file_service.create_file(os.path.join(sub_path, file), "")
                    elif isinstance(files, str):
                        self.file_service.create_file(os.path.join(path, subfolder), "")

        readme_path = os.path.join(self.name, "README.md")
        self.file_service.create_file(readme_path, f"# {self.name}\n")

        alembic_src = os.path.join(self.hape_framework_path, "alembic.ini")
        alembic_dest = os.path.join(self.name, "alembic.ini")
        self.file_service.replace_text_in_file(alembic_src, alembic_dest, "hape", self.name)

        setup_path = os.path.join(self.name, "setup.py")
        self.file_service.replace_text_in_file(setup_path, setup_path, "hape", self.name)

    def create_new_project(self):
        self.__create_new_project_structure()
        self.__copy_hape_files()
