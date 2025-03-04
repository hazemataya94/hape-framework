from hape.logging import Logging
from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger, ForeignKey, Index, Date, DateTime, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from hape.base.model import Model

class K8SDeployment(Model):
    __tablename__ = 'k8s_deployment'
    logger = Logging.get_logger('hape.models.k8s_deployment')
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(255), nullable=False)
    pod_cpu = Column(String(255), nullable=False)
    pod_ram = Column(String(255), nullable=False)
    autoscaling = Column(Boolean, nullable=False)
    min_replicas = Column(Integer, nullable=True)
    max_replicas = Column(Integer, nullable=True)
    current_replicas = Column(Integer, nullable=False)
    
    def __init__(self, **kwargs):
        filtered_kwargs = {key: kwargs[key] for key in self.__table__.columns.keys() if key in kwargs}
        super().__init__(**filtered_kwargs)
        for key, value in filtered_kwargs.items():
            setattr(self, key, value)
        self.logger = Logging.get_logger('hape.models.k8s_deployment')