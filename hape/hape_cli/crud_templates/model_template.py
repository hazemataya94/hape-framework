MODEL_TEMPLATE = """
from hape.logging import Logging
from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger
from datetime import datetime
from hape.base.model import Model

class {{model_name_camel_case}}(Model):
    __tablename__ = '{{model_name_snake_case}}'
    
    {{model_columns}}

    def __init__(self, **kwargs):
        logger = Logging.get_logger('{{project_name}}.{{model_name_snake_case}}.{{model_name_camel_case}}')
        filtered_kwargs = {key: kwargs[key] for key in self.__table__.columns.keys() if key in kwargs}
        super().__init__(**filtered_kwargs)
        for key, value in filtered_kwargs.items():
            setattr(self, key, value)    
""".strip()