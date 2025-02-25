import json
from datetime import datetime
from hape.services.gitlab_service import GitlabService
from hape.services.file_service import FileService
from hape.hape_cli.models.crud_model import Crud
from hape.hape_cli.models.json_model import Json
from hape.hape_cli.models.yaml_model import Yaml
class Playground:

    @classmethod
    def main(self):
        playground = Playground()
        playground.play()
        
    def generate_gitlab_changes_report(self):
        gitlab = GitlabService()
        start_date = datetime(2025, 2, 3)
        end_date = datetime(2025, 2, 5)
        gitlab.generate_csv_changes_in_cicd_repos(
            group_id=178,
            start_date=start_date,
            end_date=end_date,
            output_file="/Users/hazemataya/Desktop/workspace/innodp/playground/test.csv",
            file_regex=r".*values.*.yaml"
        )
        
    def play_with_crud(self):
        try:
            Crud(
                project_name="hape",
                model_name="k8s-deployment"
            ).delete()
        except Exception as e:
            print(f"Error deleting k8s-deployment: {e}")

        try:
            Crud(
                project_name="hape",
                model_name="k8s-deployment-cost"
            ).delete()
        except Exception as e:
            print(f"Error deleting k8s-deployment-cost: {e}")
                    
        Crud(
            project_name="hape",
            schemas={   
            "k8s-deployment": {
                "id": {"int": ["primary", "autoincrement"]},
                "service-name": {"string": []},
                "pod-cpu": {"string": []},
                "pod-ram": {"string": []},
                "autoscaling": {"bool": []},
                "min-replicas": {"int": ["nullable"]},
                "max-replicas": {"int": ["nullable"]},
                "current-replicas": {"int": []},
            },
            "k8s-deployment-cost": {
                "id": {"int": ["primary", "autoincrement"]},
                "k8s-deployment-id": {"int": ["required", "foreign-key(k8s-deployment.id, on-delete=cascade)"]},
                "pod-cost": {"string": []},
                "number-of-pods": {"int": []},
                    "total-cost": {"float": []}
                }
            }
        ).generate()

    def play(self):
        self.play_with_crud()
