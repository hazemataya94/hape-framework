import re
import os
import json
from hape.logging import Logging
from hape.services.file_service import FileService
from hape.hape_cli.crud_templates.argument_parser_template import ARGUMENT_PARSER_TEMPLATE
from hape.hape_cli.crud_templates.controller_template import CONTROLLER_TEMPLATE
from hape.hape_cli.crud_templates.migration_template import MIGRATION_TEMPLATE
from hape.hape_cli.crud_templates.model_template import MODEL_TEMPLATE
from hape.utils.naming_utils import NamingUtils
from hape.utils.string_utils import StringUtils

class Crud:
    
    valid_types = ["string", "int", "boolean", "float", "date", "datetime", "timestamp"]
    valid_properties = ["nullable", "required", "unique", "primary", "autoincrement"]
    
    _model_schema_template = """
{
    "valid_types": {{valid-types}},
    "valid_properties": {{valid-properties}},
    "name": "model-name",
    "schema": {
        "__column_name": {"valid-type": ["valid-property"]},
        "_id": {"valid-type": ["valid-property"]},
        "id": {"int": ["primary"]},
        "_updated_at": {"valid-type": []},
        "updated_at": {"timestamp": []},
        "_name": {"valid-type": ["valid-property"]},
        "name": {"string": []},
        "_enabled": {"valid-type": ["valid-property"]},
        "enabled": {"int": []}  
    }
}
""".replace("{{valid-types}}", json.dumps(valid_types)) \
    .replace("{{valid-properties}}", json.dumps(valid_properties)) \
    .strip()
    
    def __init__(self, project_name: str, model_name: str, schema: dict):
        self.logger = Logging.get_logger('hape.hape_cli.models.crud_model')
        self.file_service = FileService()

        self.project_name = project_name
        self.model_name = model_name
        self.schema = schema
        self.source_code_path = NamingUtils.convert_to_snake_case(project_name)
        if self.source_code_path == "hape_framework":
            self.source_code_path = "hape"
            
        self.migration_counter_digits = 6
        self.migration_counter = "000001"
        self.migration_columns = ""
        self.model_columns = ""

        model_name_snake_case = NamingUtils.convert_to_snake_case(model_name)
        self.argument_parser_path = os.path.join(self.source_code_path, "argument_parsers", f"{model_name_snake_case}_argument_parser.py")
        self.controller_path = os.path.join(self.source_code_path, "controllers", f"{model_name_snake_case}_controller.py")
        self.migration_path = os.path.join(self.source_code_path, "migrations", "versions", f"{self.migration_counter}_{model_name_snake_case}_migration.py")
        self.model_path = os.path.join(self.source_code_path, "models", f"{model_name_snake_case}_model.py")
            
        self.argument_parser_content = ""
        self.controller_content = ""
        self.migration_content = ""
        self.model_content = ""
        
        self.argument_parser_generated = False
        self.controller_generated = False
        self.migration_generated = False
        self.model_generated = False
        
    def validate(self):
        self.logger.debug(f"validate()")
        if not self.model_name:
            self.logger.error("Model name is required")
            exit(1)
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', self.model_name):
            self.logger.error(f"Error: Model name '{self.model_name}' must contain only lowercase letters, numbers, and use '-' as a separator.")
            exit(1)
    
    def _validat_schema_structure(self):
        self.logger.debug(f"_validat_schema_structure()")
        if not self.schema:
            self.logger.error("Schema is required")
            exit(1)
        if not isinstance(self.schema, dict):
            self.logger.error(f"Schema must be a dictionary, but got {type(self.schema)}: {self.schema}")
            exit(1)
        for column_name, column_type_and_properties in self.schema.items():
            if not isinstance(column_name, str):
                self.logger.error(f"Column name must be a string, but got {type(column_name)}: {column_name}")
                exit(1)
            if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', column_name):
                self.logger.error(f"Column name '{column_name}' must contain only lowercase letters, numbers, and use '-' as a separator.")
                exit(1)
            if not isinstance(column_type_and_properties, object):
                self.logger.error(f"Each column must have be an object, but got {type(column_type_and_properties)}: {column_type_and_properties}")
                exit(1)
            column_type = list(column_type_and_properties.keys())[0]
            column_properties = list(column_type_and_properties.values())[0]
            if not isinstance(column_type, str):
                self.logger.error(f"Each column must have a type, but got {type(column_type)}: {column_type}")
                exit(1)
            if column_type not in self.valid_types:
                self.logger.error(f"Invalid column type '{column_type}'. Must be one of {self.valid_types}")
                exit(1)
            if not isinstance(column_properties, list):
                self.logger.error(f"Each column must have a list of properties or empty list, but got {type(column_properties)}: {column_properties}")
                exit(1)
            for column_property in column_properties:
                if not isinstance(column_property, str):
                    self.logger.error("Each column property must be a string")
                    exit(1)
                if column_property not in self.valid_properties:
                    self.logger.error(f"Invalid column property '{column_property}'. Must be one of {self.valid_properties}")
                    exit(1)
    
    def set_schema(self, schema: dict):
        self.logger.debug(f"set_schema()")
        self.schema = schema
    
    def validate_schema(self):
        self.logger.debug(f"validate_schema()")
        self.logger.debug(f"self.schema: {self.schema}")
        if not self.schema:
            self.logger.error("Schema is required")
            exit(1)
        self._validat_schema_structure()
            
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
        self.logger.debug(f"migration_counter: {self.migration_counter}")
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
        
        content = StringUtils.replace_name_case_placeholders(CONTROLLER_TEMPLATE, self.source_code_path, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, self.model_name, "model_name")
        self.controller_content = content
        
        self.logger.info(f"Generating: {self.controller_path}")
        self.file_service.write_file(self.controller_path, self.controller_content)
        
        self.controller_generated = True
    
    def _generate_content_migration(self):
        self.logger.debug(f"_generate_content_migration()")
        if self.file_service.file_exists(self.migration_path):
            self.logger.warning(f"Migration file already exists at {self.migration_path}")
            return
        
        # self._set_migration_counter()
        # self._increase_migration_counter()
        # self._get_migration_columns()
        
        content = StringUtils.replace_name_case_placeholders(MIGRATION_TEMPLATE, self.source_code_path, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, self.model_name, "model_name")
        content = content.replace("{{migration_counter}}", self.migration_counter)
        content = content.replace("{{migration_columns}}", self.migration_columns)
        self.migration_content = content
        
        self.logger.info(f"Generating: {self.migration_path}")  
        self.file_service.write_file(self.migration_path, self.migration_content)
        
        self.migration_generated = True

    def _generate_content_model(self):
        self.logger.debug(f"_generate_content_model()")
        if self.file_service.file_exists(self.model_path):
            self.logger.warning(f"Model file already exists at {self.model_path}")
            return
        
        content = StringUtils.replace_name_case_placeholders(MODEL_TEMPLATE, self.source_code_path, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, self.model_name, "model_name")
        content = content.replace("{{model_columns}}", self._get_model_columns())
        self.model_content = content
        
        self.logger.info(f"Generating: {self.model_path}")
        self.file_service.write_file(self.model_path, self.model_content)
        
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
        
        if self.argument_parser_generated:
            self.logger.info(f"Generated argument parser at {self.argument_parser_path}")
        if self.controller_generated:
            self.logger.info(f"Generated controller at {self.controller_path}")
        if self.migration_generated:
            self.logger.info(f"Generated migration at {self.migration_path}")
        if self.model_generated:
            self.logger.info(f"Generated model at {self.model_path}")
        
        if not self.argument_parser_generated and not self.controller_generated and not self.migration_generated and not self.model_generated:
            self.logger.info(f"All model files already exist at {self.source_code_path}")
            self.logger.info(f"Argument parser file: {self.argument_parser_path}")
            self.logger.info(f"Controller file: {self.controller_path}")
            self.logger.info(f"Migration file: {self.migration_path}")
            self.logger.info(f"Model file: {self.model_path}")
            self.logger.info(f"If you want to regenerate the model files, please run `$ hape crud delete --name {self.model_name}` first to delete the model files and run the command again.")
            exit(1)
            
    def delete(self):
        self.logger.debug(f"delete()")
        if self.file_service.file_exists(self.argument_parser_path):
            self.file_service.delete_file(self.argument_parser_path)
        if self.file_service.file_exists(self.controller_path):
            self.file_service.delete_file(self.controller_path)
        if self.file_service.file_exists(self.migration_path):
            self.file_service.delete_file(self.migration_path)
        if self.file_service.file_exists(self.model_path):
            self.file_service.delete_file(self.model_path)
        
        self.logger.debug(f"Deleted: {self.argument_parser_path}")
        self.logger.debug(f"Deleted: {self.controller_path}")
        self.logger.debug(f"Deleted: {self.migration_path}")
        self.logger.debug(f"Deleted: {self.model_path}")
        self.logger.info(f"All model files have been deleted successfully!")

