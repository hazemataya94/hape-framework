class NamingUtils:

    def convert_to_snake_case(name: str) -> str:
        return name.replace("-", "_")
    
    def convert_to_upper(name: str) -> str:
        return name.upper()
    
    def convert_to_camel_case(name: str) -> str:
        return name.title().replace("-", "")
    
    def convert_to_title(name: str) -> str:
        return name.title().replace("-", " ")
