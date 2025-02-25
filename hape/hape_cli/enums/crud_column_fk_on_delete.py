import enum

class CrudColumnFkOnDeleteEnum(enum.Enum):
    CASCADE = "cascade"
    SET_NULL = "set-null"
    SET_DEFAULT = "set-default"
    RESTRICT = "restrict"
    NO_ACTION = "no-action"
