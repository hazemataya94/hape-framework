from hape.hape_cli.models.init_model import Init
import re

class InitController:

    def __init__(self):
        self.__init = Init()
    
    def create_new_project(self, name):
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
            print("Error: Project name must contain only lowercase letters, numbers, and use '-' as a separator.")
            exit(1)

        self.__init.create_new_project(name)
