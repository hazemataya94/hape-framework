from typing import List
from hape.utils.naming_utils import NamingUtils
from hape.logging import Logging
from hape.hape_cli.models.crud_column import CrudColumn
from hape.hape_cli.enums.crud_column_valid_properties import CrudColumnValidPropertiesEnum
from hape.hape_cli.enums.crud_column_valid_types import CrudColumnValidTypesEnum
from hape.hape_cli.enums.crud_column_fk_on_delete import CrudColumnFkOnDeleteEnum


class CrudColumnParser:
    
    def __init__(self, crud_column: CrudColumn):
        self.logger = Logging.get_logger('hape.hape_cli.models.crud_column_parser')
        self.crud_column = crud_column
        
        self.orm_column_name = NamingUtils.convert_to_snake_case(self.crud_column.name)
        self.orm_column_type = self._parse_orm_column_type()
        self.orm_relationships = "" # set in _parse_orm_column_properties()
        self.orm_column_properties = self._parse_orm_column_properties()
        
        self.parsed_orm_column_template = "{{model_column_name_snake_case}} = Column({{orm_column_type_camel_case}}, {{orm_column_properties}})"
        self.parsed_orm_column = self.parsed_orm_column_template.replace("{{model_column_name_snake_case}}", self.orm_column_name)
        self.parsed_orm_column = self.parsed_orm_column.replace("{{orm_column_type_camel_case}}", self.orm_column_type)
        self.parsed_orm_column = self.parsed_orm_column.replace("{{orm_column_properties}}", self.orm_column_properties)
        self.parsed_orm_column = self.parsed_orm_column.replace(", )", ")")

        self.parsed_migration_column_template = "sa.Column('{{model_column_name_snake_case}}', sa.{{orm_column_type_snake_case}}, {{orm_column_properties}})"
        self.parsed_migration_column = self.parsed_migration_column_template.replace("{{model_column_name_snake_case}}", self.orm_column_name)
        self.parsed_migration_column = self.parsed_migration_column.replace("{{orm_column_type_snake_case}}", self.orm_column_type)
        self.parsed_migration_column = self.parsed_migration_column.replace("{{orm_column_properties}}", self.orm_column_properties)
        self.parsed_migration_column = self.parsed_migration_column.replace(", )", ")")
        self.parsed_migration_column = self.parsed_migration_column.replace("ForeignKey", "sa.ForeignKey")
        
    def _parse_orm_column_type(self):
        self.logger.debug(f"_parse_orm_column_type()")
        
        orm_column_type = ""
        
        if self.crud_column.type == CrudColumnValidTypesEnum.INT:
            orm_column_type = "Integer"
        elif self.crud_column.type == CrudColumnValidTypesEnum.FLOAT:
            orm_column_type = "Float"
        elif self.crud_column.type == CrudColumnValidTypesEnum.BOOL:
            orm_column_type = "Boolean"
        elif self.crud_column.type == CrudColumnValidTypesEnum.DATE:
            orm_column_type = "Date"
        elif self.crud_column.type == CrudColumnValidTypesEnum.DATETIME:
            orm_column_type = "DateTime"
        elif self.crud_column.type == CrudColumnValidTypesEnum.TIMESTAMP:
            orm_column_type = "TIMESTAMP"
        elif self.crud_column.type == CrudColumnValidTypesEnum.TEXT:
            orm_column_type = "Text"
        elif self.crud_column.type == CrudColumnValidTypesEnum.STRING:
            orm_column_type = "String(255)"
        else:
            self.logger.error(f"Invalid column type: {self.crud_column.type}")
            exit(1)
                
        return orm_column_type
                
    def _parse_orm_column_properties(self):
        self.logger.debug(f"_parse_orm_column_properties()")
        orm_column_properties = ""
        orm_column_relationships = ""
        for property in self.crud_column.crud_column_properties:
            if property.property == CrudColumnValidPropertiesEnum.PRIMARY:
                orm_column_properties += "primary_key=True, "
            elif property.property == CrudColumnValidPropertiesEnum.AUTOINCREMENT:
                orm_column_properties += "autoincrement=True, "
            elif property.property == CrudColumnValidPropertiesEnum.UNIQUE:
                orm_column_properties += "unique=True, "
            elif property.property == CrudColumnValidPropertiesEnum.INDEX:
                orm_column_properties += "index=True, "
            elif property.property == CrudColumnValidPropertiesEnum.FOREIGN_KEY:
                orm_column_properties += f"ForeignKey('{property.foreign_key.foreign_key_table}.{property.foreign_key.foreign_key_column}', ondelete='{property.foreign_key.foreign_key_on_delete}'), "
                
                foreign_key_model_camel_case = NamingUtils.convert_to_camel_case(property.foreign_key.foreign_key_table)
                
                orm_column_relationships += f"relationship('{foreign_key_model_camel_case}', back_populates='{self.orm_column_name.rstrip('_id').rstrip('s')}s')\n    "
                
        self.orm_relationships = orm_column_relationships.strip()
        
        for property in self.crud_column.crud_column_properties:
            
            if property.property == CrudColumnValidPropertiesEnum.NULLABLE:
                orm_column_properties += "nullable=True"
            elif property.property == CrudColumnValidPropertiesEnum.REQUIRED:
                orm_column_properties += "nullable=False"
                
        return orm_column_properties
    