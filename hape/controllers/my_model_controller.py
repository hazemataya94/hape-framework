
from hape.base.model_controller import ModelController
from hape.models.my_model_model import MyModel

class MyModelController(ModelController):
    
    def __init__(self):
        super().__init__(MyModel)

