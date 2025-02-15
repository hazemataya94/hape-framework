from hape.utils.naming_utils import NamingUtils
class StringUtils:
    
    def replace_naming_variables(self, content: str, name: str, name_key_prefix: str) -> str:
        content = content.replace(f"{{{name_key_prefix}_{name}}}", NamingUtils.convert_to_snake_case(name))
        content = content.replace(f"{{{name_key_prefix}_{name}}}", NamingUtils.convert_to_camel_case(name))
        content = content.replace(f"{{{name_key_prefix}_{name}}}", NamingUtils.convert_to_capitalized(name))
        content = content.replace(f"{{{name_key_prefix}_{name}}}", NamingUtils.convert_to_title(name))
        return content