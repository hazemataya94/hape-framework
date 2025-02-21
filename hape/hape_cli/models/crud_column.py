from hape.logging import Logging
from hape.utils.naming_utils import NamingUtils
from typing import List
from hape.hape_cli.enums.crud_column_valid_properties import CrudColumnValidPropertiesEnum
from hape.hape_cli.enums.crud_column_valid_types import CrudColumnValidTypesEnum
from hape.hape_cli.enums.crud_column_fk_on_delete import CrudColumnFkOnDeleteEnum
from hape.hape_cli.models.crud_column_property import CrudColumnProperty

class CrudColumn:
    def __init__(self, name: str, type: str, properties: List[str]):
        self.logger = Logging.get_logger('hape.hape_cli.models.crud_column')
        
        self.name: str = name
        self.type: CrudColumnValidTypesEnum = CrudColumnValidTypesEnum(type)
        
        self.crud_column_properties: List[CrudColumnProperty] = self._parse_properties(properties)
        
        self.is_id = name == 'id'
        self.is_primary = CrudColumnValidPropertiesEnum.PRIMARY.value in properties
        self.is_autoincrement = CrudColumnValidPropertiesEnum.AUTOINCREMENT.value in properties
        self.is_unique = CrudColumnValidPropertiesEnum.UNIQUE.value in properties
        self.is_index = CrudColumnValidPropertiesEnum.INDEX.value in properties
        self.is_nullable = CrudColumnValidPropertiesEnum.NULLABLE.value in properties
        self.is_required = CrudColumnValidPropertiesEnum.REQUIRED.value in properties
         
    def _parse_properties(self, properties: List[str]) -> List[CrudColumnProperty]:
        self.logger.debug(f"_parse_properties()")
        
        crud_column_properties = []
        
        for property in properties:
            crud_column_property = None
            if property.startswith("foreign-key"):
                foreign_key_value = property.split("(")[1].split(")")[0]
                crud_column_property = CrudColumnProperty(
                    CrudColumnValidPropertiesEnum.FOREIGN_KEY,
                    foreign_key_value
                )
            else:
                crud_column_property = CrudColumnProperty(property)
                
            crud_column_properties.append(crud_column_property)
        
        if not crud_column_properties or (
            CrudColumnValidPropertiesEnum.NULLABLE.value not in properties 
            and CrudColumnValidPropertiesEnum.REQUIRED.value not in properties
            and CrudColumnValidPropertiesEnum.PRIMARY.value not in properties
        ):
            crud_column_properties.append(CrudColumnProperty(CrudColumnValidPropertiesEnum.NULLABLE.value))
        
        return crud_column_properties
