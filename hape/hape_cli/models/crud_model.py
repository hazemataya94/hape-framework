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
from hape.hape_cli.crud_templates.migration_template import MIGRATION_TEMPLATE, MIGRATION_MODEL_TABLE_CREATION_TEMPLATE, MIGRATION_MODEL_TABLE_DROP_TEMPLATE
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
    
    def __init__(self, project_name: str, model_name: str, schemas: dict[str, dict]):
        self.logger = Logging.get_logger('hape.hape_cli.models.crud_model')
        self.file_service = FileService()
        
        self.model_count = 0
        if schemas:
            self.model_count = len(schemas)
        elif model_name:
            self.model_count = 1
        else:
            self.logger.error("Model name or schema is required to create a CRUD object.")
            exit(1)
        
        self.schemas: dict[str, dict] = {}
        self.model_names: list[str] = []
        self.model_names_snake_case: dict[str, str] = {}
        if schemas:
            self.schemas = schemas
            for model_name, _ in schemas.items():
                self.model_names.append(model_name)
                self.model_names_snake_case[model_name] = NamingUtils.convert_to_snake_case(model_name)
        elif model_name:
            self.model_names.append(model_name)
            self.model_names_snake_case[model_name] = NamingUtils.convert_to_snake_case(model_name)
        else:
            self.logger.error("Model name or schema is required to create a CRUD object.")
            exit(1)
        
        self.project_name = project_name
        self.source_code_path = NamingUtils.convert_to_snake_case(project_name)
        if self.source_code_path == "hape_framework":
            self.source_code_path = "hape"
                
        self.argument_parser_paths: dict[str, str] = {}
        for model_name in self.model_names:
            self.argument_parser_paths[model_name] = os.path.join(self.source_code_path, "argument_parsers", f"{self.model_names_snake_case[model_name]}_argument_parser.py")
        self.controller_paths: dict[str, str] = {}
        for model_name in self.model_names:
            self.controller_paths[model_name] = os.path.join(self.source_code_path, "controllers", f"{self.model_names_snake_case[model_name]}_controller.py")
        self.model_paths: dict[str, str] = {}
        for model_name in self.model_names:
            self.model_paths[model_name] = os.path.join(self.source_code_path, "models", f"{self.model_names_snake_case[model_name]}_model.py")
            
        self.argument_parser_contents: dict[str, str] = {}
        self.controller_contents: dict[str, str] = {}
        self.model_contents: dict[str, str] = {}
        self.migration_content: str = ""
        
        self.argument_parser_generated: dict[str, bool] = {}
        self.controller_generated: dict[str, bool] = {}
        self.model_generated: dict[str, bool] = {}
        self.migration_generated: bool = False
        self.should_generate_migration: bool = False
        
        self.crud_columns: dict[str, List[CrudColumn]] = {}
        self.crud_column_parsers: dict[str, List[CrudColumnParser]] = {}
        
        self.is_default_migration_counter: bool = False
        self.migration_counter_digits: int = 6
        self.migration_counter: str = "000001"
        self.migration_columns: str = ""
        self.migration_path = os.path.join(self.source_code_path, "migrations", "versions", f"{self.migration_counter}_migration.py")
        self.alembic_config_path = os.path.join(os.getcwd(), "alembic.ini")
        
        self.models_tables_creation_statements: str = ""
        self.models_tables_drop_statements: str = ""
        
        if self.schemas:
            self._init_object_model_dictionaries()
        
    def _init_object_model_dictionaries(self):
        self.logger.debug(f"_init_object_model_dictionaries()")
        if not self.schemas:
            self.logger.warning("Schema is required")
            return
        
        for model_name, _ in self.schemas.items():
            self.argument_parser_contents[model_name] = ""
            self.controller_contents[model_name] = ""
            self.model_contents[model_name] = ""
            self.argument_parser_generated[model_name] = False
            self.controller_generated[model_name] = False
            self.model_generated[model_name] = False
            self.migration_generated = False
            self.crud_columns[model_name] = []
            self.crud_column_parsers[model_name] = []
        
        for model_name, columns in self.schemas.items():
            for column_name, column_type_and_properties in columns.items():
                crud_column_name = column_name
                crud_column_type = list(column_type_and_properties.keys())[0]
                crud_column_properties = list(column_type_and_properties.values())[0]
            crud_column = CrudColumn(
                crud_column_name,
                crud_column_type,
                crud_column_properties
            )
            self.crud_column_parsers[model_name].append(CrudColumnParser(crud_column))
                
    def validate(self):
        self.logger.debug(f"validate()")
        if not self.model_names:
            self.logger.error("Model name is required")
            exit(1)
        for model_name in self.model_names:
            if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', model_name):
                self.logger.error(f"Error: Model name '{model_name}' must contain only lowercase letters, numbers, and use '-' as a separator.")
                exit(1)
    
    def validate_schemas(self):
        self.logger.debug(f"validate_schemas()")
        self.logger.debug(f"self.schemas: {self.schemas}")
        if not self.schemas:
            self.logger.error("Schema is required")
            exit(1)
            
        self._validate_schemas_structure()
        
    def _validate_schemas_structure(self):
        self.logger.debug(f"_validate_schemas_structure()")
        if not self.schemas:
            self.logger.error("Schema is required")
            exit(1)
        if not isinstance(self.schemas, dict):
            self.logger.error(f"Schema must be a dictionary, but got {type(self.schemas)}: {self.schemas}")
            exit(1)
        if not self.schemas.keys():
            self.logger.error("Schema must be a dictionary have at least one key")
            exit(1)
        for model_name, columns in self.schemas.items():
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
                    if column_property not in self.valid_properties and not column_property.startswith("foreign-key"):
                        self.logger.error(f"Invalid column property '{column_property}'. Must be one of {self.valid_properties}")
                        exit(1)
    
    def _get_orm_columns(self):
        self.logger.debug(f"_get_orm_columns()")
        if not self.schemas:
            self.logger.warning(f"Schema is required")
            return ""

        parsed_orm_columns = ""
        splitter = ",\n    "
        for model_name in self.model_names:
            for crud_column_parser in self.crud_column_parsers[model_name]:
                parsed_orm_columns += crud_column_parser.parsed_orm_column + splitter

        return parsed_orm_columns.rstrip(splitter)
    
    def _get_orm_relationships(self):
        self.logger.debug(f"_get_orm_relationships()")
        if not self.schemas:
            self.logger.warning("Schema is required")
            return ""
        
        parsed_orm_relationships = ""
        splitter = ",\n    "
        for model_name in self.model_names:
            for crud_column_parser in self.crud_column_parsers[model_name]:
                parsed_orm_relationships += crud_column_parser.orm_relationships + splitter
                
        return parsed_orm_relationships.rstrip(splitter)
    
    def _generate_content_model(self, model_name):
        self.logger.debug(f"_generate_content_model(model_name: {model_name})")
        if self.file_service.file_exists(self.model_paths[model_name]):
            self.logger.warning(f"Model file already exists at {self.model_paths[model_name]}")
            return
    
        content = StringUtils.replace_name_case_placeholders(MODEL_TEMPLATE, self.source_code_path, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, model_name, "model_name")
        content = content.replace("{{model_columns}}", self._get_orm_columns())
        content = content.replace("{{model_relationships}}", self._get_orm_relationships())
        self.model_content = content
    
        self.logger.info(f"Generating: {self.model_paths[model_name]}")
        self.file_service.write_file(self.model_paths[model_name], self.model_content)
        
        self.model_generated[model_name] = True
    
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
        self.migration_path = os.path.join(self.source_code_path, "migrations", "versions", f"{new_migration_counter}_migration.py")
        self.migration_counter = new_migration_counter
        return new_migration_counter
    
    def _get_migration_columns(self, model_name):
        self.logger.debug(f"_get_migration_columns(model_name: {model_name})")
        if not self.crud_column_parsers[model_name]:
            self.logger.warning(f"No columns to migrate for {model_name}")
            return ""
        
        migration_columns = ""
        splitter = ",\n        "
        for crud_column_parser in self.crud_column_parsers[model_name]:
            migration_columns += crud_column_parser.parsed_migration_column + splitter
        return migration_columns.rstrip(splitter)
    
    def _generate_model_table_creation_statement(self, model_name):
        self.logger.debug(f"_generate_model_table_creation_statement(model_name: {model_name})")
        
        content = StringUtils.replace_name_case_placeholders(MIGRATION_MODEL_TABLE_CREATION_TEMPLATE, model_name, "model_name")
        content = content.replace("{{migration_columns}}", self._get_migration_columns(model_name))
        
        self.models_tables_creation_statements += content + "\n    "
    
    def _generate_model_table_drop_statement(self, model_name):
        self.logger.debug(f"_generate_model_table_drop_statement(model_name: {model_name})")
        
        content = StringUtils.replace_name_case_placeholders(MIGRATION_MODEL_TABLE_DROP_TEMPLATE, model_name, "model_name")
        
        self.models_tables_drop_statements += content + "\n    "
        
    def _generate_content_migration(self):
        self.logger.debug(f"_generate_content_migration()")
        
        if self.file_service.file_exists(self.migration_path):
            self.logger.warning(f"Migration file already exists at {self.migration_path}")
            return
            
        for model_name in self.model_names: 
            if not self.model_generated[model_name]:
                self.logger.warning(f"No database changes to migrate for {model_name}")
                continue    
            self._generate_model_table_creation_statement(model_name)
            self._generate_model_table_drop_statement(model_name)
            self.should_generate_migration = True
        
        if not self.should_generate_migration:
            self.logger.warning("Migration file will not be generated. No database changes to migrate")
            return
        
        self.migration_content = StringUtils.replace_name_case_placeholders(MIGRATION_TEMPLATE, self.source_code_path, "project_name")
        self.migration_content = self.migration_content.replace("{{migration_counter}}", self.migration_counter)
        self.migration_content = self.migration_content.replace("{{model_table_creation_statements}}", self.models_tables_creation_statements)
        self.migration_content = self.migration_content.replace("{{model_table_drop_statements}}", self.models_tables_drop_statements)
        
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
        
    def _generate_content_controller(self, model_name):
        self.logger.debug(f"_generate_content_controller(model_name: {model_name})")
        if self.file_service.file_exists(self.controller_paths[model_name]):
            self.logger.warning(f"Controller file already exists at {self.controller_paths[model_name]}")
            return
        
        content = StringUtils.replace_name_case_placeholders(CONTROLLER_TEMPLATE, self.source_code_path, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, model_name, "model_name")
        self.controller_content = content
        
        self.logger.info(f"Generating: {self.controller_paths[model_name]}")
        self.file_service.write_file(self.controller_paths[model_name], self.controller_content)
        
        self.controller_generated[model_name] = True
    
    def _generate_content_argument_parser(self, model_name):
        self.logger.debug(f"_generate_content_argument_parser(model_name: {model_name})")
        if self.file_service.file_exists(self.argument_parser_paths[model_name]):
            self.logger.warning(f"Argument parser file already exists at {self.argument_parser_paths[model_name]}")
            return
        
        content = StringUtils.replace_name_case_placeholders(ARGUMENT_PARSER_TEMPLATE, self.source_code_path, "project_name")
        content = StringUtils.replace_name_case_placeholders(content, model_name, "model_name")
        self.argument_parser_content = content
        
        self.argument_parser_contents[model_name] = StringUtils.replace_name_case_placeholders(content, model_name, "model_name")
        self.argument_parser_contents[model_name] = StringUtils.replace_name_case_placeholders(self.argument_parser_contents[model_name], self.project_name, "project_name")
        
        self.logger.info(f"Generating: {self.argument_parser_paths[model_name]}")
        self.file_service.write_file(self.argument_parser_paths[model_name], self.argument_parser_content)
        
        self.argument_parser_generated[model_name] = True
    
    def generate(self):
        self.logger.debug(f"generate()")
        for model_name in self.model_names:
            self._generate_content_model(model_name)
            self._generate_content_controller(model_name)
            self._generate_content_argument_parser(model_name)
            
            if self.argument_parser_generated[model_name]:
                print(f"Generated: {self.argument_parser_paths[model_name]}")
            if self.controller_generated[model_name]:
                print(f"Generated: {self.controller_paths[model_name]}")
            if self.model_generated[model_name]:
                print(f"Generated: {self.model_paths[model_name]}")
        
        self._generate_content_migration()
        if self.migration_generated:
            print(f"Generated: {self.migration_path}")
        print(f"self.migration_content: {self.migration_content}")
        try:
            self._run_migrations()
        except Exception as e:
            self.logger.error(f"Error: {e}")
            print(f"Error: {e}")
            exit(1)
            
    def delete(self):
        self.logger.debug(f"delete()")
        for model_name in self.model_names:
            if self.file_service.file_exists(self.model_paths[model_name]):
                self.file_service.delete_file(self.model_paths[model_name])
                print(f"Deleted: {self.model_paths[model_name]}")
            if self.file_service.file_exists(self.controller_paths[model_name]):
                self.file_service.delete_file(self.controller_paths[model_name])
                print(f"Deleted: {self.controller_paths[model_name]}")
            if self.file_service.file_exists(self.argument_parser_paths[model_name]):
                self.file_service.delete_file(self.argument_parser_paths[model_name])
                print(f"Deleted: {self.argument_parser_paths[model_name]}")
        
        print(f"All model files -except the migration file- have been deleted successfully!")
        print( "--------------------------------")
        print(f"Migration file location: {os.path.dirname(self.migration_path)}")
        print(f"Make sure to modify the migration file to stop the model table creation, or delete the migration file manually if you don't want it anymore.")
    
    def delete_migration(self):
        self.logger.debug(f"delete_migration()")
        if self.file_service.file_exists(self.migration_path):
            self.file_service.delete_file(self.migration_path)
            print(f"Deleted: {self.migration_path}")

