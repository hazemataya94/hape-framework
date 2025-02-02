from appname.src.config.config import Config

class ConfigController:

    @classmethod
    def check_configurations(self):
        Config.check_variables()
        print('Configurations are set correctly.')
