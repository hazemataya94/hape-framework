from hape.logging import Logging

from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger
from datetime import datetime
from hape.base.model import Model

class DeploymentCost(Model):
    __tablename__ = 'deployment_costs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(BigInteger, default=lambda: int(datetime.utcnow().timestamp()), nullable=False)
    service_name = Column(String(255), nullable=False)
    pod_cpu = Column(String(50), nullable=False)
    pod_ram = Column(String(50), nullable=False)
    autoscaling = Column(Boolean, nullable=False)
    min_replicas = Column(Integer, nullable=True)
    max_replicas = Column(Integer, nullable=True)
    current_replicas = Column(Integer, nullable=False)
    pod_cost = Column(Float, nullable=False)
    number_of_pods = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=False)
    cost_unit = Column(String(50), nullable=False)

    def __init__(self, **kwargs):
        filtered_kwargs = {key: kwargs[key] for key in self.__table__.columns.keys() if key in kwargs}
        super().__init__(**filtered_kwargs)
        for key, value in filtered_kwargs.items():
            setattr(self, key, value)
