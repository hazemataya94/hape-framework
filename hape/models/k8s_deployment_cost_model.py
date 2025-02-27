from hape.logging import Logging
from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger, ForeignKey, Index, Date, DateTime, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from hape.base.model import Model

class K8SDeploymentCost(Model):
    __tablename__ = 'k8s_deployment_cost'
    logger = Logging.get_logger('hape.models.k8s_deployment_cost')
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    k8s_deployment_id = Column(Integer, ForeignKey('k8s_deployment.id', ondelete='CASCADE'), nullable=False)
    pod_cost = Column(String(255), nullable=False)
    number_of_pods = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=False)

    relationship('K8SDeployment', back_populates='k8s_deployments')

    def __init__(self, **kwargs):
        filtered_kwargs = {key: kwargs[key] for key in self.__table__.columns.keys() if key in kwargs}
        super().__init__(**filtered_kwargs)
        for key, value in filtered_kwargs.items():
            setattr(self, key, value)
        self.logger = Logging.get_logger('hape.models.k8s_deployment_cost')