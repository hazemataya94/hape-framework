from appname.src.interfaces.model import Model

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
        return self.model_class.get(**filters)
    
    def get_all(self, **filters):
        return self.model_class.get_all(**filters)
    
    def delete(self, model):
        return model.delete()
    
    def delete_all(self, **filters):
        return self.model_class.delete_all(**filters)
    
