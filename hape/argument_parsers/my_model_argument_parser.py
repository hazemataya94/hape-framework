
from hape.base.model_argument_parser import ModelArgumentParser
from hape.models.my_model_model import MyModel
from hape.controllers.my_model_controller import MyModelController

class MyModelArgumentParser(ModelArgumentParser):
    def __init__(self):
        super().__init__(MyModel, MyModelController)

    def extend_subparser(self):
        pass
    
    def extend_actions(self):
        pass

