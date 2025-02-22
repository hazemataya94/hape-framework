import re
import os
import json
from typing import List
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from hape.logging import Logging
from hape.services.file_service import FileService
from hape.hape_cli.crud_templates.argument_parser_template import ARGUMENT_PARSER_TEMPLATE
from hape.hape_cli.crud_templates.controller_template import CONTROLLER_TEMPLATE
from hape.hape_cli.crud_templates.migration_template import MIGRATION_TEMPLATE
from hape.hape_cli.crud_templates.model_template import MODEL_TEMPLATE
from hape.utils.naming_utils import NamingUtils
from hape.utils.string_utils import StringUtils
from hape.hape_cli.models.crud_column_parser import CrudColumnParser
from hape.hape_cli.enums.crud_column_valid_types import CrudColumnValidTypesEnum
from hape.hape_cli.enums.crud_column_valid_properties import CrudColumnValidPropertiesEnum
from hape.hape_cli.enums.crud_column_fk_on_delete import CrudColumnFkOnDeleteEnum
from hape.hape_cli.models.crud_column import CrudColumn

class Crud:
    
    valid_types = [valid_type.value for valid_type in CrudColumnValidTypesEnum]
    valid_properties = [valid_property.value for valid_property in CrudColumnValidPropertiesEnum]
    valid_foreign_key_on_delete = [valid_foreign_key_on_delete.value for valid_foreign_key_on_delete in CrudColumnFkOnDeleteEnum]
    
    _model_schema_json = """
{
    "valid_types": {{valid-types}},
    "valid_properties": {{valid-properties}},
    "valid_foreign_key_on_delete": {{valid-foreign-key-on-delete}},
    "foreign_key_syntax": "foreign-key(foreign-key-model.foreign-key-attribute, on-delete=foreign-key-on-delete)",
    
    
    "model-name": {
        "column_name": {"valid-type": ["valid-property"]},
        "id": {"valid-type": ["valid-property"]},
        "updated_at": {"valid-type": []},
        "name": {"valid-type": ["valid-property", "valid-property"]},
        "enabled": {"valid-type": []},
    }
    
    "example-model": {
        "id": {"int": ["primary"]},
        "updated_at": {"timestamp": []},
        "name": {"string": ["required", "unique"]},
        "enabled": {"bool": []}
    }
}
""".replace("{{valid-types}}", json.dumps(valid_types)) \
    .replace("{{valid-properties}}", json.dumps(valid_properties)) \
    .replace("{{valid-foreign-key-on-delete}}", json.dumps(valid_foreign_key_on_delete)) \
    .strip()

    _model_schema_yaml = """
valid_types: {{valid-types}}
valid_properties: {{valid-properties}}
valid_foreign_key_on_delete: {{valid-foreign-key-on-delete}}
foreign_key_syntax: "foreign-key(foreign-key-model.foreign-key-attribute, on-delete=foreign-key-on-delete)"

model-name:
  column_name:
    valid-type: 
      - valid-property
  id:
    valid-type: 
      - valid-property
  updated_at:
    valid-type: []
  name:
    valid-type: 
      - valid-property
      - valid-property
  enabled:
    valid-type: []

example-model:
  id:
    int: 
      - primary
  updated_at:
    timestamp: []
  name:
    string: 
      - required
      - unique
  enabled:
    bool: []
""".replace("{{valid-types}}", json.dumps(valid_types)) \
    .replace("{{valid-properties}}", json.dumps(valid_properties)) \
    .replace("{{valid-foreign-key-on-delete}}", json.dumps(valid_foreign_key_on_delete)) \
    .strip()
    
    def __init__(self, project_name: str, model_name: str, schema: dict):
        self.logger = Logging.get_logger('hape.hape_cli.models.crud_model')
        self.file_service = FileService()
        
        self.schema = schema
        self.model_name = model_name if model_name else list(self.schema.keys())[0]
        self.model_name_snake_case = NamingUtils.convert_to_snake_case(self.model_name) if self.model_name else ""
        self.project_name = project_name
        self.source_code_path = NamingUtils.convert_to_snake_case(project_name)
        if self.source_code_path == "hape_framework":
            self.source_code_path = "hape"
            
        self.crud_columns: List[CrudColumn] = []
        self.crud_column_parsers: List[CrudColumnParser] = []
                
        self.is_default_migration_counter = False
        self.migration_counter_digits = 6
        self.migration_counter = "000001"
        self.migration_counter = self._get_migration_counter_and_path()
        self.migration_columns = ""
        self.alembic_config_path = os.path.join(os.getcwd(), "alembic.ini")
        
        self.argument_parser_path = os.path.join(self.source_code_path, "argument_parsers", f"{self.model_name_snake_case}_argument_parser.py")
        self.controller_path = os.path.join(self.source_code_path, "controllers", f"{self.model_name_snake_case}_controller.py")
        self.migration_path = os.path.join(self.source_code_path, "migrations", "versions", f"{self.migration_counter}_{self.model_name_snake_case}_migration.py")
        self.model_path = os.path.join(self.source_code_path, "models", f"{self.model_name_snake_case}_model.py")
            
        self.argument_parser_content = ""
        self.controller_content = ""
        self.migration_content = ""
        self.model_content = ""
        
        self.argument_parser_generated = False
        self.controller_generated = False
        self.migration_generated = False
        self.model_generated = False
        
        if self.schema:
            for model_name, columns in schema.items():
                self.logger.debug(f"columns: {columns}")
                self.model_name = model_name
                self.logger.debug(f"model_name: {self.model_name}")
                for column_name, column_type_and_properties in columns.items():
                    crud_column_name = column_name
                    crud_column_type = list(column_type_and_properties.keys())[0]
                    crud_column_properties = list(column_type_and_properties.values())[0]
                    
                    crud_column = CrudColumn(
                        crud_column_name,
                        crud_column_type,
                        crud_column_properties
                    )
                    
                    self.crud_column_parsers.append(CrudColumnParser(crud_column))
        
        
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
        if not self.schema.keys():
            self.logger.error("Schema must be a dictionary have at least one key")
            exit(1)
        for model_name, columns in self.schema.items():
            if not isinstance(model_name, str):
                self.logger.error(f"Model name must be a string, but got {type(model_name)}: {model_name}")
                exit(1)
            if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', model_name):
                self.logger.error(f"Model name '{model_name}' must contain only lowercase letters, numbers, and use '-' as a separator.")
                exit(1)
            for column_name, column_type_and_properties in columns.items():
                if not isinstance(column_name, str):
                    self.logger.error(f"Column name must be a string, but got {type(column_name)}: {column_name}")
                    exit(1)
                if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', column_name):
                    self.logger.error(f"Column name '{column_name}' must contain only lowercase letters, numbers, and use '-' as a separator.")
                    exit(1)
                if not isinstance(column_type_and_properties, dict):
                    self.logger.error(f"Each column must have be a dictionary, but got {type(column_type_and_properties)}: {column_type_and_properties}")
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
    
    def validate_schema(self):
        self.logger.debug(f"validate_schema()")
        self.logger.debug(f"self.schema: {self.schema}")
        if not self.schema:
            self.logger.error("Schema is required")
            exit(1)
        if len(self.schema) > 1:
            self.logger.error("Schema must have only one model")
            exit(1)
            
        self._validat_schema_structure()
    
    def _get_orm_columns(self):
        self.logger.debug(f"_get_orm_columns()")
        parsed_orm_columns = ""
        splitter = ",\n    "
        for crud_column_parser in self.crud_column_parsers:
            parsed_orm_columns += crud_column_parser.parsed_orm_column + splitter
        return parsed_orm_columns.rstrip(splitter)
    
    def _get_orm_relationships(self):
        self.logger.debug(f"_get_orm_relationships()")
        parsed_orm_relationships = ""
        splitter = ",\n    "
        for crud_column_parser in self.crud_column_parsers:
            parsed_orm_relationships += crud_column_parser.orm_relationships + splitter
        return parsed_orm_relationships.rstrip(splitter)
    
    def _generate_content_model(self):
        self.logger.debug(f"_generate_content_model()")
        if self.file_service.file_exists(self.model_path):
            self.logger.warning(f"Model file already exists at {self.model_path}")
            return
        
        content = StringUtils.replace_name_case_placeholders(MODEL_TEMPLATE, self.source_code_path, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, self.model_name, "model_name")
        content = content.replace("{{model_columns}}", self._get_orm_columns())
        content = content.replace("{{model_relationships}}", self._get_orm_relationships())
        self.model_content = content
        
        self.logger.info(f"Generating: {self.model_path}")
        self.file_service.write_file(self.model_path, self.model_content)
        
        self.model_generated = True
    
    def _get_migration_counter_and_path(self):
        self.logger.debug(f"_get_migration_counter_and_path()")
        versions_folder = os.path.join(self.source_code_path, "migrations", "versions")
        
        if not os.path.exists(versions_folder):
            self.logger.error(f"Error: Migrations folder not found at {versions_folder}")
            exit(1)
        
        migration_files = os.listdir(versions_folder)
        if not migration_files:
            self.migration_counter = "000001"
            self.is_default_migration_counter = True
            return self.migration_counter
        
        migration_files_counters = []
        for migration_file in migration_files:
            migration_file_counter = migration_file.split("_")[0]
            if migration_file.endswith(f"{self.model_name_snake_case}_migration.py"):
                self.migration_path = os.path.join(versions_folder, migration_file)
                self.migration_counter = migration_file_counter
                return self.migration_counter
            
            if not migration_file_counter.startswith("0"):
                continue
            
            migration_files_counters.append(migration_file_counter)
        
        if not migration_files_counters:
            self.migration_counter = "000001"
            self.is_default_migration_counter = True
            return self.migration_counter
        
        migration_files_counters.sort(reverse=True)
        self.migration_counter = migration_files_counters[0]
        return self.migration_counter
    
    def _increase_migration_counter(self):
        self.logger.debug(f"migration_counter: {self.migration_counter}")
        self.logger.debug(f"_increase_migration_counter()")
        new_migration_counter = str(int(self.migration_counter) + 1).zfill(self.migration_counter_digits)
        self.logger.debug(f"new_migration_counter: {new_migration_counter}")
        self.migration_path = os.path.join(self.source_code_path, "migrations", "versions", f"{new_migration_counter}_{self.model_name_snake_case}_migration.py")
        self.migration_counter = new_migration_counter
        return new_migration_counter
    
    def _get_migration_columns(self):
        self.logger.debug(f"_get_migration_columns()")
        migration_columns = ""
        splitter = ",\n        "
        for crud_column_parser in self.crud_column_parsers:
            migration_columns += crud_column_parser.parsed_migration_column + splitter
        return migration_columns.rstrip(splitter)
    
    def _generate_content_migration(self):
        self.logger.debug(f"_generate_content_migration()")
        if self.file_service.file_exists(self.migration_path):
            self.logger.warning(f"Migration file already exists at {self.migration_path}")
            return

        if not self.is_default_migration_counter:
            self.migration_counter = self._increase_migration_counter()
        self.migration_columns = self._get_migration_columns()
        
        content = StringUtils.replace_name_case_placeholders(MIGRATION_TEMPLATE, self.source_code_path, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, self.model_name, "model_name")
        content = content.replace("{{migration_counter}}", self.migration_counter)
        content = content.replace("{{migration_columns}}", self.migration_columns)
        self.migration_content = content
        
        self.logger.info(f"Generating: {self.migration_path}")  
        self.file_service.write_file(self.migration_path, self.migration_content)
        
        self.migration_generated = True

    def _run_migrations(self):
        self.logger.debug(f"_run_migrations()")
        alembic_config = Config(self.alembic_config_path)
        script = ScriptDirectory.from_config(alembic_config)

        heads = script.get_heads()
        if len(heads) > 1:
            self.logger.warning(f"Multiple heads detected: {heads}")
            merge_message = "Auto-merge multiple Alembic heads"
            command.revision(alembic_config, message=merge_message, head=heads, branch_label="merge_heads")
            self.logger.info("Merged multiple heads. Now running upgrade...")
        command.upgrade(alembic_config, "head")
        
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
    
    def generate(self):
        self.logger.debug(f"generate()")
        self._generate_content_argument_parser()
        self._generate_content_migration()
        self._generate_content_controller()
        self._generate_content_model()
        try:
            self._run_migrations()
        except Exception as e:
            self.logger.error(f"Error: {e}")
            print(f"Error: {e}")
            exit(1)
        
        if self.argument_parser_generated:
            print(f"Generated: {self.argument_parser_path}")
        if self.controller_generated:
            print(f"Generated: {self.controller_path}")
        if self.migration_generated:
            print(f"Generated: {self.migration_path}")
        if self.model_generated:
            print(f"Generated: {self.model_path}")
            
        print(f"All model files have been generated successfully!")
        
        if not self.argument_parser_generated and not self.controller_generated and not self.migration_generated and not self.model_generated:
            print(f"All model files already exist at {self.source_code_path}")
            print(f"Argument parser file: {self.argument_parser_path}")
            print(f"Controller file: {self.controller_path}")
            print(f"Migration file: {self.migration_path}")
            print(f"Model file: {self.model_path}")
            print(f"If you want to regenerate the model files, please run `$ hape crud delete --name {self.model_name}` first to delete the model files and run the command again.")
            exit(1)
            
    def delete(self):
        self.logger.debug(f"delete()")
        if self.file_service.file_exists(self.argument_parser_path):
            self.file_service.delete_file(self.argument_parser_path)
            print(f"Deleted: {self.argument_parser_path}")
        if self.file_service.file_exists(self.controller_path):
            self.file_service.delete_file(self.controller_path)
            print(f"Deleted: {self.controller_path}")
        if self.file_service.file_exists(self.migration_path):
            self.file_service.delete_file(self.migration_path)
            print(f"Deleted: {self.migration_path}")
        if self.file_service.file_exists(self.model_path):
            self.file_service.delete_file(self.model_path)
            print(f"Deleted: {self.model_path}")
        
        print(f"All model files have been deleted successfully!")

