from abc import ABC, abstractmethod
from sqlalchemy import Integer, String, Float, Boolean

from appname.src.interfaces.model_controller import ModelController

class ModelArgumentParser(ABC):

    _sqlalchemy_type_map = {
        Integer: int,
        String: str,
        Float: float,
        Boolean: lambda x: x.lower() in ('true', '1', 'yes')
    }

    def __init__(self, model_class, controller_class):
        self.model_class = model_class
        self.model_name = model_class.__name__
        self.model_command = ''.join(['-' + char.lower() if char.isupper() else char for char in model_class.__name__]).lstrip('-')
        self.model_columns = {
            column.name: self._sqlalchemy_type_map.get(type(column.type), str)
            for column in self.model_class.__table__.columns
        }
        self.controller = controller_class()
        self.model_parser = None
        self.args = None
    
    @abstractmethod
    def extend_subparser(self):
        pass
    
    @abstractmethod
    def extend_actions(self):
        pass
    
    def create_subparser(self, subparsers):  
        self.model_parser = subparsers.add_parser(self.model_command, help=f"Commands to manage {self.model_name} model")
        model_subparser = self.model_parser.add_subparsers(dest="action")

        for action in ["save", "get", "get-all", "delete", "delete-all"]:
            object_word = "objects" if "-all" in action else "object"
            parser = model_subparser.add_parser(action, help=f"{action.capitalize()} {self.model_name} {object_word} based on passed arguments or filters")
            
            for column_name, column_type in self.model_columns.items():
                column_name_dashes = column_name.replace('_', '-')
                parser.add_argument(f"--{column_name_dashes}", required=False, help=f"Value for {column_name_dashes} type {column_type.__name__}")

        self.extend_subparser()
    
    def run_action(self, args):
        
        self.args = args
        if args.command != self.model_command:
            return
        
        filters = {key: getattr(args, key) for key in self.model_columns.keys() if hasattr(args, key) and getattr(args, key)}

        for column_name, column_type in self.model_columns.items():
            if hasattr(args, column_name) and getattr(args, column_name):
                try:
                    filters[column_name] = column_type(getattr(args, column_name))
                except ValueError as e:
                    print(f"Error casting {column_name}: {str(e)}")
                    exit(1)
        
        if args.action == "save":
            model = self.model_class(**filters)
            self.controller.save(model)
            print(model.json())
        
        elif args.action == "get":
            model = self.controller.get(**filters)
            if not model:
                print(f"{self.model_name} object not found.")
                exit(0)
            print(model.json())
        
        elif args.action == "get-all":
            model_list = self.controller.get_all(**filters)
            if not model_list:
                print(f"No {self.model_name} objects found.")
                exit(0)
            print(self.model_class.list_to_json(model_list))
        
        elif args.action == "delete":
            model = self.controller.get(**filters)
            if not model:
                print(f"{self.model_name} object not found.")
                exit(0)
            self.controller.delete(model)
            print("Deleted ojects")
            print(model.json())
        
        elif args.action == "delete-all":
            model_list = self.controller.get_all(**filters)
            if not model_list:
                print(f"No {self.model_name} objects found.")
                exit(0)
            for model in model_list:
                self.controller.delete()
            print("Deleted ojects:")
            print(self.model_class.list_to_json(model_list))
        
        else:
            self.extend_actions()
