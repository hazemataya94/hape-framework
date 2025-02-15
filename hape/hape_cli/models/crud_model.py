import re
import os
from hape.logging import Logging
from hape.hape_cli.crud_templates.argument_parser_template import ARGUMENT_PARSER_TEMPLATE
from hape.hape_cli.crud_templates.controller_template import CONTROLLER_TEMPLATE
from hape.hape_cli.crud_templates.migration_template import MIGRATION_TEMPLATE
from hape.hape_cli.crud_templates.model_template import MODEL_TEMPLATE
from hape.utils.string_utils import StringUtils

class Crud:
    def __init__(self, project_name: str, model_name: str, schema: dict):
        self.logger = Logging.get_logger('hape.hape_cli.models.crud_model')
        self.project_name = project_name
        self.model_name = model_name
        self.schema = schema
        self.project_path = "."
        self.argument_parser_content = ""
        self.controller_content = ""
        self.migration_content = ""
        self.model_content = ""
        self.migration_counter_digits = 4
        self.migration_counter = ""
        self.migration_columns = ""
        self.model_columns = ""
    
    def validate(self):
        self.logger.debug(f"validate()")
        if not self.model_name:
            self.logger.error("Model name is required")
            exit(1)
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', self.model_name):
            self.logger.error(f"Error: Model name '{self.model_name}' must contain only lowercase letters, numbers, and use '-' as a separator.")
            exit(1)
            
    def _get_migration_counter(self):
        self.logger.debug(f"_get_migration_counter()")
        versions_folder = os.path.join(self.project_path, "migrations", "versions")
        if not os.path.exists(versions_folder):
            self.logger.error(f"Error: Migrations folder not found at {versions_folder}")
            exit(1)
        migration_files = os.listdir(versions_folder)
        if not migration_files:
            return
        migration_files.sort()
        self.migration_counter = migration_files[-1].split("_")[0]
    
    def _increase_migration_counter(self):
        self.logger.debug(f"_increase_migration_counter()")
        self.migration_counter = str(int(self.migration_counter) + 1).zfill(self.migration_counter_digits)
    
    def _get_migration_columns(self):
        self.logger.debug(f"_get_migration_columns()")
        return ""
    
    def _get_model_columns(self):
        self.logger.debug(f"_get_model_columns()")
        return ""

    def _generate_content_argument_parser(self):
        self.logger.debug(f"_generate_content_argument_parser()")
        content = StringUtils.replace_naming_variables(ARGUMENT_PARSER_TEMPLATE, self.project_name, "project_name")
        content = StringUtils.replace_naming_variables(content, self.model_name, "model_name")
        self.argument_parser_content = content
        
    def _generate_content_controller(self):
        self.logger.debug(f"_generate_content_controller()")
        content = StringUtils.replace_naming_variables(CONTROLLER_TEMPLATE, self.project_name, "project_name")
        content = StringUtils.replace_naming_variables(content, self.model_name, "model_name")
        self.controller_content = content
    
    def _generate_content_migration(self):
        self.logger.debug(f"_generate_content_migration()")
        self._get_migration_counter()
        self._increase_migration_counter()
        self._get_migration_columns()
        content = StringUtils.replace_naming_variables(MIGRATION_TEMPLATE, self.project_name, "project_name")
        content = StringUtils.replace_naming_variables(content, self.model_name, "model_name")
        content = content.replace("{{migration_counter}}", self.migration_counter)
        content = content.replace("{{migration_columns}}", self.migration_columns)
        self.migration_content = content

    def _generate_content_model(self):
        self.logger.debug(f"_generate_content_model()")
        content = StringUtils.replace_naming_variables(MODEL_TEMPLATE, self.project_name, "project_name")
        content = StringUtils.replace_naming_variables(content, self.model_name, "model_name")
        content = content.replace("{{model_columns}}", self._get_model_columns())
        self.model_content = content

    def generate(self):
        self.logger.debug(f"generate()")
        self._generate_content_argument_parser()
        self._generate_content_migration()
        self._generate_content_controller()
        self._generate_content_model()

