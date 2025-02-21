import json
from datetime import datetime
from hape.models.deployment_cost_model import DeploymentCost
from hape.controllers.deployment_cost_controller import DeploymentCostController
from hape.services.gitlab_service import GitlabService
from hape.services.file_service import FileService
from hape.hape_cli.models.crud_model import Crud
from hape.hape_cli.models.json_model import Json
from hape.hape_cli.models.yaml_model import Yaml
class Playground:

    deployment_cost_controller = DeploymentCostController()

    @classmethod
    def main(self):
        playground = Playground()
        playground.play()
        
    def get_all_deployment_costs(self):
        deployment_costs = DeploymentCost.get_all()
        print(DeploymentCost.list_to_json(deployment_costs))

    def save_deployment_cost(self):
        deployment_cost = DeploymentCost(
            service_name="Test Service",
            pod_cpu="2",
            pod_ram="4Gi",
            autoscaling=True,
            min_replicas=1,
            max_replicas=5,
            current_replicas=3,
            pod_cost=0.10,
            number_of_pods=3,
            total_cost=0.30,
            cost_unit="$"
        )
        if self.deployment_cost_controller.save(deployment_cost):
            print('-----saved successfully-----')
        else:
            print('-----saving failed-----')
        
        print(deployment_cost.json())

    def delete_deployment_cost(self):
        deployment_cost = DeploymentCost.get(id=2)
        if not deployment_cost:
            print("Object id=2 does not exist!")
            return
        print(deployment_cost.json())
        deployment_cost.delete()

    def delete_all_deployment_cost(self):
        print("delete all where id in [1,4] and service_name='Test Service'")
        DeploymentCost.delete_all(id=["1", "4"], service_name="Test Service")

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
        
        crud = Crud(
            project_name="hape",
            model_name="k8s-deployment-cost",
            schema={
                "k8s-deployment-cost": {
                    "id": {"int": ["primary", "autoincrement"]},
                    "k8s-deployment-id": {"int": ["required", "foreign-key(k8s-deployment.id, on-delete=cascade)"]},
                    "pod-cpu": {"int": ["required"]},
                    "pod-ram": {"bool": ["index"]},
                    "autoscaling": {"float": []},
                    "min-replicas": {"date": ["nullable"]},
                    "max-replicas": {"datetime": ["nullable"]},
                    "current-replicas": {"timestamp": []},
                }
            }
        )
        
        crud._generate_content_model()
        
        # Playground().save_deployment_cost()
        # Playground().get_all_deployment_costs()
        # Playground().delete_deployment_cost()
        # Playground().delete_all_deployment_cost()
        # Playground().generate_gitlab_changes_report()
