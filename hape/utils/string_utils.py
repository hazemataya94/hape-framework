from hape.logging import Logging
from hape.utils.naming_utils import NamingUtils
class StringUtils:
    
    logger = Logging.get_logger(__name__)
    
    @staticmethod
    def replace_name_case_placeholders(content: str, name: str, name_key_prefix: str) -> str:
        StringUtils.logger.debug(f"replace_name_case_placeholders(content, name: {name}, name_key_prefix: {name_key_prefix})")
        
        snake_case_key = f"{{{{{name_key_prefix}_snake_case}}}}"
        kebab_case_key = f"{{{{{name_key_prefix}_kebab_case}}}}"
        upper_snake_case_key = f"{{{{{name_key_prefix}_upper_snake_case}}}}"
        upper_kebab_case_key = f"{{{{{name_key_prefix}_upper_kebab_case}}}}"
        camel_case_key = f"{{{{{name_key_prefix}_camel_case}}}}"
        pascal_case_key = f"{{{{{name_key_prefix}_pascal_case}}}}"
        title_case_key = f"{{{{{name_key_prefix}_title_case}}}}"
        
        content = content.replace(snake_case_key, NamingUtils.convert_to_snake_case(name))
        content = content.replace(kebab_case_key, NamingUtils.convert_to_kebab_case(name))
        content = content.replace(upper_snake_case_key, NamingUtils.convert_to_upper_snake_case(name))
        content = content.replace(upper_kebab_case_key, NamingUtils.convert_to_upper_kebab_case(name))
        content = content.replace(camel_case_key, NamingUtils.convert_to_camel_case(name))
        content = content.replace(pascal_case_key, NamingUtils.convert_to_pascal_case(name))
        content = content.replace(title_case_key, NamingUtils.convert_to_title_case(name))
        return content