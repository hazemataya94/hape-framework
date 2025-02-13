from hape.hape_cli.models.init_model import Init

class InitController:

    def __init__(self, name):
        self.__init = Init(name)
        self.__init.validate()
    
    def init_project(self):
        self.__init.init_project()
