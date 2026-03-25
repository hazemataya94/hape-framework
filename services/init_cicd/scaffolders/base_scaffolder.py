from abc import ABC, abstractmethod

from services.init_cicd.models import DetectedProject, InitCicdResult


class BaseScaffolder(ABC):
    @abstractmethod
    def scaffold(self, detected_project: DetectedProject, deployment_type: str) -> InitCicdResult:
        raise NotImplementedError


if __name__ == "__main__":
    print(BaseScaffolder.__name__)
