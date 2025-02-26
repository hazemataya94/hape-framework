from hape.logging import Logging
from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger, ForeignKey, Index, Date, DateTime, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from hape.base.model import Model

class K8SDeployment(Model):
    __tablename__ = 'k8s_deployment'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(255), nullable=True)
    pod_cpu = Column(String(255), nullable=True)
    pod_ram = Column(String(255), nullable=True)
    autoscaling = Column(Boolean, nullable=True)
    min_replicas = Column(Integer, nullable=True)
    max_replicas = Column(Integer, nullable=True)
    current_replicas = Column(Integer, nullable=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    k8s_deployment_id = Column(Integer, ForeignKey('k8s_deployment.id', ondelete='CASCADE'), nullable=False)
    pod_cost = Column(String(255), nullable=True)
    number_of_pods = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)
    
    relationship('K8SDeployment', back_populates='k8s_deployments')

    def __init__(self, **kwargs):
        self.logger = Logging.get_logger('{{project_name}}.k8s_deployment.K8SDeployment')
        filtered_kwargs = {key: kwargs[key] for key in self.__table__.columns.keys() if key in kwargs}
        super().__init__(**filtered_kwargs)
        for key, value in filtered_kwargs.items():
            setattr(self, key, value)