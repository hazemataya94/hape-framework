import json
from hape.hape_cli.enums.crud_column_fk_on_delete import CrudColumnFkOnDeleteEnum
from hape.hape_cli.enums.crud_column_valid_properties import CrudColumnValidPropertiesEnum
from hape.hape_cli.enums.crud_column_valid_types import CrudColumnValidTypesEnum

class CrudModelSchema:
    
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
