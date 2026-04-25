from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from services.eks_deployment_cost_service import EksDeploymentCostService

router = APIRouter(prefix="/eks-deployment-cost", tags=["eks-deployment-cost"])


class ReportRequest(BaseModel):
    kube_context: str
    kube_config_file: str | None = None
    aws_profile: str
    aws_region: str | None = None
    resource_types: str | None = None
    namespaces: str | None = None
    top_n: int = 20
    output_dir: str


@router.post("/report")
def report(payload: ReportRequest) -> dict:
    service = EksDeploymentCostService()
    return service.generate_report(
        kube_context=payload.kube_context,
        kube_config_file=payload.kube_config_file,
        aws_profile=payload.aws_profile,
        aws_region=payload.aws_region,
        resource_types_csv=payload.resource_types,
        namespaces_csv=payload.namespaces,
        top_n=payload.top_n,
        output_dir=payload.output_dir,
    )
