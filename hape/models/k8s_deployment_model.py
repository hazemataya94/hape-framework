from hape.logging import Logging
from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger, ForeignKey, Index, Date, DateTime, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from hape.base.model import Model

class K8SDeployment(Model):
    __tablename__ = 'k8s_deployment'
    
    id = Column(Integer, primary_key=True, autoincrement=True),
    service_name = Column(String, nullable=True),
    pod_cpu = Column(String, nullable=True),
    pod_ram = Column(String, nullable=True),
    autoscaling = Column(Boolean, nullable=True),
    min_replicas = Column(Integer, nullable=True),
    max_replicas = Column(Integer, nullable=True),
    current_replicas = Column(Integer, nullable=True)
    

    def __init__(self, **kwargs):
        self.logger = Logging.get_logger('{{project_name}}.k8s_deployment.K8SDeployment')
        filtered_kwargs = {key: kwargs[key] for key in self.__table__.columns.keys() if key in kwargs}
        super().__init__(**filtered_kwargs)
        for key, value in filtered_kwargs.items():
            setattr(self, key, value)