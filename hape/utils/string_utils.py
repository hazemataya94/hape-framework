from hape.logging import Logging
from hape.utils.naming_utils import NamingUtils
class StringUtils:
    
    logger = Logging.get_logger(__name__)
    
    @staticmethod
    def replace_name_case_placeholders(content: str, name: str, name_key_prefix: str) -> str:
        StringUtils.logger.debug(f"replace_name_case_placeholders(content, name: {name}, name_key_prefix: {name_key_prefix})")
        
        snake_case_key = f"{{{{{name_key_prefix}_snake_case}}}}"
        camel_case_key = f"{{{{{name_key_prefix}_camel_case}}}}"
        upper_case_key = f"{{{{{name_key_prefix}_upper_case}}}}"
        title_case_key = f"{{{{{name_key_prefix}_title_case}}}}"
        
        content = content.replace(snake_case_key, NamingUtils.convert_to_snake_case(name))
        content = content.replace(camel_case_key, NamingUtils.convert_to_camel_case(name))
        content = content.replace(upper_case_key, NamingUtils.convert_to_upper_case(name))
        content = content.replace(title_case_key, NamingUtils.convert_to_title_case(name))
        return content