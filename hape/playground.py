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

    def play(self):
        
        # json_model = Json(model_schema=True)
        # # json_model.load(Crud._model_schema_json)
        # yaml_model = Yaml(model_schema=True)
        
        # json_model.get()
        # print()
        # yaml_model.get()
        
        # valid_types = ["string", "int", "bool", "float", "date", "datetime", "timestamp"]
        # valid_properties = ["nullable", "required", "unique", "primary", "autoincrement", "foreign-key", "index"]
        
        
        
        {
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
        
        Crud(
            project_name="hape",
            model_name="k8s-deployment",
            schema={
                "k8s-deployment": {
                    "id": {"int": ["primary", "autoincrement"]},
                    "service-name": {"string": []},
                    "pod-cpu": {"string": []},
                    "pod-ram": {"string": []},
                    "autoscaling": {"bool": []},
                    "min-replicas": {"int": ["nullable"]},
                    "max-replicas": {"int": ["nullable"]},
                    "current-replicas": {"int": []},
                }
            }
        ).generate()
        
        Crud(
            project_name="hape",
            model_name="k8s-deployment-cost",
            schema={
                "k8s-deployment-cost": {
                    "id": {"int": ["primary", "autoincrement"]},
                    "k8s-deployment-id": {"int": ["required", "foreign-key(k8s-deployment.id, on-delete=cascade)"]},
                    "pod-cost": {"string": []},
                    "number-of-pods": {"int": []},
                    "total-cost": {"float": []}
                }
            }
        ).generate()
        
        # Playground().save_deployment_cost()
        # Playground().get_all_deployment_costs()
        # Playground().delete_deployment_cost()
        # Playground().delete_all_deployment_cost()
        # Playground().generate_gitlab_changes_report()
