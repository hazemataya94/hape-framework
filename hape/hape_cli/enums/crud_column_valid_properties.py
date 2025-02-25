import enum

class CrudColumnValidPropertiesEnum(enum.Enum):
    NULLABLE = "nullable"
    REQUIRED = "required"
    UNIQUE = "unique"
    PRIMARY = "primary"
    AUTOINCREMENT = "autoincrement"
    FOREIGN_KEY = "foreign-key"
    INDEX = "index"
