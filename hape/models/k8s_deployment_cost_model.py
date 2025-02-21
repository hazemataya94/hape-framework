from hape.logging import Logging
from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger, ForeignKey, Index, Date, DateTime, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from hape.base.model import Model

class K8SDeploymentCost(Model):
    __tablename__ = 'k8s_deployment_cost'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    k8s_deployment_id = Column(Integer, ForeignKey('k8s_deployment.id', ondelete='CASCADE'), nullable=False)
    pod_cpu = Column(Integer, nullable=False)
    pod_ram = Column(Boolean, index=True, nullable=True)
    autoscaling = Column(Float, nullable=True)
    min_replicas = Column(Date, nullable=True)
    max_replicas = Column(DateTime, nullable=True)
    current_replicas = Column(TIMESTAMP, nullable=True)
    
    relationship('K8SDeployment', back_populates='k8s_deployments')

    def __init__(self, **kwargs):
        self.logger = Logging.get_logger('{{project_name}}.k8s_deployment_cost.K8SDeploymentCost')
        filtered_kwargs = {key: kwargs[key] for key in self.__table__.columns.keys() if key in kwargs}
        super().__init__(**filtered_kwargs)
        for key, value in filtered_kwargs.items():
            setattr(self, key, value)