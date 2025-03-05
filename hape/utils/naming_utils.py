class NamingUtils:

    def _make_first_letter_upper(name: str) -> str:
        return name[:1].upper() + name[1:] if name else name

    def _make_first_letter_lower(name: str) -> str:
        return name[:1].lower() + name[1:] if name else name

    def convert_to_snake_case(name: str) -> str:
        return name.replace("-", "_").replace(" ", "_")
    
    def convert_to_kebab_case(name: str) -> str:
        return name.replace("_", "-").replace(" ", "-")
    
    def convert_to_upper_snake_case(name: str) -> str:
        return name.upper().replace("-", "_").replace(" ", "_")
    
    def convert_to_upper_kebab_case(name: str) -> str:
        return name.upper().replace("_", "-").replace(" ", "-")
    
    def convert_to_camel_case(name: str) -> str:
        return NamingUtils._make_first_letter_lower(name.title().replace("_", "").replace("-", ""))
    
    def convert_to_pascal_case(name: str) -> str:
        return NamingUtils._make_first_letter_upper(name.title().replace("_", "").replace("-", ""))
    
    def convert_to_title_case(name: str) -> str:
        return name.title().replace("_", " ").replace("-", " ")
    
    