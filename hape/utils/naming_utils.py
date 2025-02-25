class NamingUtils:

    def convert_to_snake_case(name: str) -> str:
        return name.replace("-", "_")
    
    def convert_to_upper_case(name: str) -> str:
        return name.upper()
    
    def convert_to_camel_case(name: str) -> str:
        name = name.title().replace("_", "")
        name = name.replace("-", "")
        return name
    
    def convert_to_title_case(name: str) -> str:
        name = name.title().replace("_", " ")
        name = name.replace("-", " ")
        return name
