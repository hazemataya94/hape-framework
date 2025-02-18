from abc import abstractmethod
from typing import Any


class FormatModel:
    
    @abstractmethod
    def __init__(self, model_schema: bool):
        pass
    
    @abstractmethod
    def load (self, schema: str) -> Any:
        pass
    
    @abstractmethod
    def get(self):
        pass
    
    @abstractmethod
    def generate(self):
        pass
