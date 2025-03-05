ARGUMENT_PARSER_TEMPLATE = """
from hape.logging import Logging
from hape.base.model_argument_parser import ModelArgumentParser
from {{project_name_snake_case}}.models.{{model_name_snake_case}}_model import {{model_name_pascal_case}}
from {{project_name_snake_case}}.controllers.{{model_name_snake_case}}_controller import {{model_name_pascal_case}}Controller

class {{model_name_pascal_case}}ArgumentParser(ModelArgumentParser):
    def __init__(self):
        super().__init__({{model_name_pascal_case}}, {{model_name_pascal_case}}Controller)
        self.logger = Logging.get_logger('{{project_name_snake_case}}.argument_parsers.{{model_name_snake_case}}_argument_parser')

    def extend_subparser(self):
        pass
    
    def extend_actions(self):
        pass

""".strip()