from hape.hape_cli.models.init_model import Init

class InitController:

    def __init__(self, name):
        self.init = Init(name)
        self.init.validate()
    
    def init_project(self):
        self.init.init_project()
