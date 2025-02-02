from appname.interfaces.model import Model

class ModelController():

    def __init__(self, model_class):
        self.model_class = model_class
    
    def save(self, model):
        if model.validate():
            try:
                return model.save()
            except Exception as e:
                raise RuntimeError(f"An error occurred while saving: {e}")
        
        raise ValueError("Model validation failed.")

    def get(self, **filters):
        if not filters:
            raise ValueError("Filters cannot be empty for get operation.")
        return self.model_class.get(**filters)
    
    def get_all(self, **filters):
        return self.model_class.get_all(**filters)
    
    def delete(self, model):
        if not isinstance(model, self.model_class):
            raise TypeError("Invalid model instance for deletion.")
        return model.delete()
    
    def delete_all(self, **filters):
        if not filters:
            raise ValueError("Filters cannot be empty for delete_all operation.")
        return self.model_class.delete_all(**filters)
