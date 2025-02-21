from hape.hape_cli.enums.crud_column_valid_properties import CrudColumnValidPropertiesEnum
from hape.hape_cli.models.crud_column_foreign_key import CrudColumnForeignKey

class CrudColumnProperty:
    def __init__(self, property: CrudColumnValidPropertiesEnum, foreign_key_value: str = None):
        self.property: CrudColumnValidPropertiesEnum = CrudColumnValidPropertiesEnum(property)
        self.foreign_key: CrudColumnForeignKey = None
        
        if property == CrudColumnValidPropertiesEnum.FOREIGN_KEY and foreign_key_value:
            self.foreign_key = CrudColumnForeignKey(foreign_key_value)
