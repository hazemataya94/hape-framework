from hape.logging import Logging
from hape.utils.naming_utils import NamingUtils
from hape.hape_cli.enums.crud_column_fk_on_delete import CrudColumnFkOnDeleteEnum

class CrudColumnForeignKey:
    def __init__(self, foreign_key_property_value: str):
        self.logger = Logging.get_logger('hape.hape_cli.models.crud_column_foreign_key')
        
        self.foreign_key_table = ""
        self.foreign_key_column = ""
        self.foreign_key_on_delete = ""
        
        foreign_key_parts = foreign_key_property_value.split(",")
            
        foreign_key_table = NamingUtils.convert_to_snake_case(foreign_key_parts[0].split(".")[0])
        foreign_key_column = NamingUtils.convert_to_snake_case(foreign_key_parts[0].split(".")[1])
        
        self.foreign_key_table = foreign_key_table
        self.foreign_key_column = foreign_key_column
        
        foreign_key_on_delete = foreign_key_parts[1].split("=")[1]
        
        if foreign_key_on_delete == CrudColumnFkOnDeleteEnum.CASCADE.value:
            self.foreign_key_on_delete = "CASCADE"
        elif foreign_key_on_delete == CrudColumnFkOnDeleteEnum.SET_NULL.value:
            self.foreign_key_on_delete = "SET_NULL"
        elif foreign_key_on_delete == CrudColumnFkOnDeleteEnum.SET_DEFAULT.value:
            self.foreign_key_on_delete = "SET_DEFAULT"
        elif foreign_key_on_delete == CrudColumnFkOnDeleteEnum.RESTRICT.value:
            self.foreign_key_on_delete = "RESTRICT"
        elif foreign_key_on_delete == CrudColumnFkOnDeleteEnum.NO_ACTION.value:
            self.foreign_key_on_delete = "NO_ACTION"
        else:
            self.logger.error(f"Invalid on_delete value: {foreign_key_on_delete}")
            exit(1)
    