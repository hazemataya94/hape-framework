CONTROLLER_TEMPLATE = """
from hape.logging import Logging
from hape.base.model_controller import ModelController
from {{project_name_snake_case}}.models.{{model_name_snake_case}}_model import {{model_name_pascal_case}}

class {{model_name_pascal_case}}Controller(ModelController):
    
    def __init__(self):
        super().__init__({{model_name_pascal_case}})
        self.logger = Logging.get_logger('{{project_name_snake_case}}.controllers.{{model_name_snake_case}}_controller')
""".strip()