import os
import re
import sys
import importlib.util
from hape.logging import Logging
from hape.services.file_service import FileService
from hape.utils.naming_utils import NamingUtils
from hape.hape_cli.init_templates.init_project_template import INIT_PROJECT_TEMPLATE
from hape.utils.string_utils import StringUtils
from hape.hape_config import HapeConfig

class Init:

    def __init__(self, name: str):
        self.logger = Logging.get_logger('hape.hape_cli.models.init_model')
        self.name = name
        self.file_service = FileService()
        
        spec = importlib.util.find_spec("hape")
        if spec and spec.origin:
            self.hape_framework_path = os.path.dirname(os.path.abspath(spec.origin))
        else:
            self.logger.error("Couldn't not find `hape` package. Execute `pip install --upgrade hape`.")
            exit(1)

    def validate(self):
        self.logger.debug(f"validate()")
        name = self.name.strip()
        self.logger.debug(f'Validating project name: {self.name}')
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
            self.logger.error(f"Error: Project name '{name}' must contain only lowercase letters, numbers, and use '-' as a separator.")
            sys.exit(1)
        self.logger.debug(f'Valid project name.')

    def _init_file(self, path: str, content: str):
        self.logger.debug(f"_init_file(path: {path}, content: {content})")

        if content:
            content = StringUtils.replace_name_case_placeholders(content, self.name, "project_name")
            content = content.replace("{{db_url}}", HapeConfig.get_db_url())

        self.file_service.write_file(path, content)

    def _init_directory(self, root_path: str, dictionary: dict):
        self.logger.debug(f"_init_directory(root_path: {root_path}, dictionary: {dictionary})")
        for name, content in dictionary.items():
            if name == '{{project_name}}':
                name = NamingUtils.convert_to_snake_case(self.name)
            sub_path = os.path.join(root_path, name)
            if content is None:
                self._init_file(sub_path,"")
            elif isinstance(content, str):
                self._init_file(sub_path, content)
            elif isinstance(content, dict):
                self.file_service.create_directory(sub_path)
                self._init_directory(sub_path, content)
            else:
                self.logger.error(f"Content type for {content} is not supported.")
                exit(1)

    def _init_project_template(self):
        self.logger.debug(f"_init_project_template()")
        if self.file_service.path_exists(self.name):
            self.logger.warning(f"Directory '{self.name}' already exists.")
            user_input = input(f"ALL DATA IN '{self.name}' WILL BE LOST. Do you want to remove '{self.name}' and initialize a new project? yes/no: ").strip().lower()
            if user_input == 'yes':
                self.file_service.delete_directory(self.name)
            else:
                print("Operation canceled. Keeping the directory.")
                sys.exit(1)
        self.file_service.create_directory(self.name)
        self._init_directory(self.name, INIT_PROJECT_TEMPLATE)

    def init_project(self):
        self.logger.debug(f"init_project()")
        self._init_project_template()
        self.logger.info(f'Project {self.name} has been successfully initialized!')
        print(f'Project {self.name} has been successfully initialized!')

