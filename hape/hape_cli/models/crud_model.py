import re
import os

from hape.logging import Logging
from hape.services.file_service import FileService
from hape.hape_cli.crud_templates.argument_parser_template import ARGUMENT_PARSER_TEMPLATE
from hape.hape_cli.crud_templates.controller_template import CONTROLLER_TEMPLATE
from hape.hape_cli.crud_templates.migration_template import MIGRATION_TEMPLATE
from hape.hape_cli.crud_templates.model_template import MODEL_TEMPLATE
from hape.utils.naming_utils import NamingUtils
from hape.utils.string_utils import StringUtils

class Crud:
    def __init__(self, project_name: str, model_name: str, schema: dict):
        self.logger = Logging.get_logger('hape.hape_cli.models.crud_model')
        self.file_service = FileService()
        self.project_name = project_name
        self.model_name = model_name
        self.schema = schema
        self.source_code_path = NamingUtils.convert_to_snake_case(project_name)
        if self.source_code_path == "hape_framework":
            self.source_code_path = "hape"
        
        model_name_snake_case = NamingUtils.convert_to_snake_case(model_name)
        self.argument_parser_path = os.path.join(self.source_code_path, "argument_parsers", f"{model_name_snake_case}_argument_parser.py")
        self.controller_path = os.path.join(self.source_code_path, "controllers", f"{model_name_snake_case}_controller.py")
        self.migration_path = os.path.join(self.source_code_path, "migrations", "versions", f"{model_name_snake_case}_migration.py")
        self.model_path = os.path.join(self.source_code_path, "models", f"{model_name_snake_case}_model.py")
            
        self.argument_parser_content = ""
        self.controller_content = ""
        self.migration_content = ""
        self.model_content = ""
        
        self.argument_parser_generated = False
        self.controller_generated = False
        self.migration_generated = False
        self.model_generated = False
        
        self.migration_counter_digits = 4
        self.migration_counter = "0000"
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
        versions_folder = os.path.join(self.source_code_path, "migrations", "versions")
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
        if self.file_service.file_exists(self.argument_parser_path):
            self.logger.warning(f"Argument parser file already exists at {self.argument_parser_path}")
            return
        
        content = StringUtils.replace_name_case_placeholders(ARGUMENT_PARSER_TEMPLATE, self.source_code_path, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, self.model_name, "model_name")
        self.argument_parser_content = content
        
        self.argument_parser_contents = StringUtils.replace_name_case_placeholders(content, self.model_name, "model_name")
        self.argument_parser_contents = StringUtils.replace_name_case_placeholders(self.argument_parser_contents, self.project_name, "project_name")
        
        self.logger.info(f"Generating: {self.argument_parser_path}")
        self.file_service.write_file(self.argument_parser_path, self.argument_parser_content)
        
        self.argument_parser_generated = True
        
    def _generate_content_controller(self):
        self.logger.debug(f"_generate_content_controller()")
        if self.file_service.file_exists(self.controller_path):
            self.logger.warning(f"Controller file already exists at {self.controller_path}")
            return
        
        content = StringUtils.replace_name_case_placeholders(CONTROLLER_TEMPLATE, self.project_name, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, self.model_name, "model_name")
        self.controller_content = content
        
        self.controller_generated = True
    
    def _generate_content_migration(self):
        self.logger.debug(f"_generate_content_migration()")
        if self.file_service.file_exists(self.migration_path):
            self.logger.warning(f"Migration file already exists at {self.migration_path}")
            return
        
        # self._get_migration_counter()
        # self._increase_migration_counter()
        # self._get_migration_columns()
        content = StringUtils.replace_name_case_placeholders(MIGRATION_TEMPLATE, self.project_name, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, self.model_name, "model_name")
        content = content.replace("{{migration_counter}}", self.migration_counter)
        content = content.replace("{{migration_columns}}", self.migration_columns)
        self.migration_content = content
        
        self.migration_generated = True

    def _generate_content_model(self):
        self.logger.debug(f"_generate_content_model()")
        if self.file_service.file_exists(self.model_path):
            self.logger.warning(f"Model file already exists at {self.model_path}")
            return
        
        content = StringUtils.replace_name_case_placeholders(MODEL_TEMPLATE, self.project_name, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, self.model_name, "model_name")
        content = content.replace("{{model_columns}}", self._get_model_columns())
        self.model_content = content
        
        self.model_generated = True

    def _run_migrations(self):
        self.logger.debug(f"_run_migrations()")
        
    def generate(self):
        self.logger.debug(f"generate()")
        self._generate_content_argument_parser()
        self._generate_content_migration()
        self._generate_content_controller()
        self._generate_content_model()
        self._run_migrations()
        
        print(f"CRUD files have been generated successfully!")
        if self.argument_parser_generated:
            print(f"Argument parser file generated at {self.argument_parser_path}")
        if self.controller_generated:
            print(f"Controller file generated at {self.controller_path}")
        if self.migration_generated:
            print(f"Migration file generated at {self.migration_path}")
        if self.model_generated:
            print(f"Model file generated at {self.model_path}")
        
        if not self.argument_parser_generated and not self.controller_generated and not self.migration_generated and not self.model_generated:
            print(f"All model files already exist at {self.source_code_path}")
            print(f"If you want to generate one or more files, please delete the file/s and run the command again.")
            exit(1)


