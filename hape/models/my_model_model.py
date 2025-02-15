from hape.logging import Logging
from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger
from datetime import datetime
from hape.base.model import Model

class MyModel(Model):
    __tablename__ = 'my_model'
    
    

    def __init__(self, **kwargs):
        logger = Logging.get_logger('{{project_name}}.my_model.MyModel')
        filtered_kwargs = {key: kwargs[key] for key in self.__table__.columns.keys() if key in kwargs}
        super().__init__(**filtered_kwargs)
        for key, value in filtered_kwargs.items():
            setattr(self, key, value)