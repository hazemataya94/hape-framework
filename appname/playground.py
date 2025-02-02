import json

from appname.src.models.deployment_cost_model import DeploymentCost
from appname.src.controllers.deployment_cost_controller import DeploymentCostController

class Playground:

    deployment_cost_controller = DeploymentCostController()

    # main playground function
    @classmethod
    def main(self):
        playground = Playground()
        playground.save_deployment_cost()
        # playground.get_all_deployment_costs()
        # playground.delete_deployment_cost()
        # playground.delete_all_deployment_cost()

        
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
