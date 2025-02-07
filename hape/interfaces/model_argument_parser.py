from abc import ABC, abstractmethod
from sqlalchemy import Integer, String, Float, Boolean

from hape.interfaces.model_controller import ModelController

class ModelArgumentParser(ABC):

    _sqlalchemy_type_map = {
        Integer: int,
        String: str,
        Float: float,
        Boolean: lambda x: x.lower() in ('true', '1', 'yes')
    }

    def __init__(self, model_class, controller_class):
        self._model_class = model_class
        self._model_name = model_class.__name__
        self._model_command = ''.join(['-' + char.lower() if char.isupper() else char for char in model_class.__name__]).lstrip('-')
        self._model_columns = {
            column.name: self._sqlalchemy_type_map.get(type(column.type), str)
            for column in self._model_class.__table__.columns
        }
        self._controller = controller_class()
        self.model_subparser = None
        self.args = None
    
    @abstractmethod
    def extend_subparser(self):
        pass
    
    @abstractmethod
    def extend_actions(self):
        pass
    
    def create_subparser(self, subparsers):  
        model_parser = subparsers.add_parser(self._model_command, help=f"Commands to manage {self._model_name} model")
        self.model_subparser = model_parser.add_subparsers(dest="action")

        for action in ["save", "get", "get-all", "delete", "delete-all"]:
            object_word = "objects" if "-all" in action else "object"
            parser = self.model_subparser.add_parser(action, help=f"{action.capitalize()} {self._model_name} {object_word} based on passed arguments or filters")
            
            for column_name, column_type in self._model_columns.items():
                column_name_dashes = column_name.replace('_', '-')
                parser.add_argument(f"--{column_name_dashes}", required=False, help=f"Value for {column_name_dashes} type {column_type.__name__}")

        self.extend_subparser()
    
    def run_action(self, args):
        
        self.args = args
        if args.command != self._model_command:
            return
        
        filters = {}
        for column_name, column_type in self._model_columns.items():
            if hasattr(args, column_name) and getattr(args, column_name):
                try:
                    filters[column_name] = column_type(getattr(args, column_name))
                except ValueError as e:
                    raise ValueError(f"Error casting {column_name}: {str(e)}")
        
        if args.action == "save":
            model = self._model_class(**filters)
            if not model.validate():
                raise ValueError("Model validation failed.")
            self._controller.save(model)
            print(model.json())
        
        elif args.action == "get":
            model = self._controller.get(**filters)
            if not model:
                print(f"{self._model_name} object not found.")
                return
            print(model.json())
        
        elif args.action == "get-all":
            model_list = self._controller.get_all(**filters)
            if not model_list:
                print(f"No {self._model_name} objects found.")
                return
            print(self._model_class.list_to_json(model_list))
        
        elif args.action == "delete":
            model = self._controller.get(**filters)
            if not model:
                print(f"{self._model_name} object not found.")
                return
            self._controller.delete(model)
            print("Deleted object:")
            print(model.json())
        
        elif args.action == "delete-all":
            model_list = self._controller.get_all(**filters)
            if not model_list:
                print(f"No {self._model_name} objects found.")
                return
            for model in model_list:
                self._controller.delete(model)
            print("Deleted objects:")
            print(self._model_class.list_to_json(model_list))
        
        else:
            self.extend_actions()
