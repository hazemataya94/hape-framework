from hape.logging import Logging

import kubernetes.config
import kubernetes.client

class KubernetesService:
    
    _context_dev = ""
    _context_test = ""
    _context_prod = ""

    def __init__(self, context):
        if context == 'dev':
            cluster_context = self._context_dev
        elif context == 'test':
            cluster_context = self._context_test
        elif context == 'prod':
            cluster_context = self._context_prod
        else:
            raise ValueError("Error: Kubernetes context not defined")
        
        kubernetes.config.load_kube_config(context=cluster_context)

        self.logger = Logging.get_logger('hape.services.kubernetes_model')
        self.core_v1 = kubernetes.client.CoreV1Api()
        self.apps_v1 = kubernetes.client.AppsV1Api()
        self.autoscaling_v2 = kubernetes.client.AutoscalingV2Api()

    def get_deployments(self, namespace):
        self.logger.debug(f"get_deployments(namespace: {namespace})")
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace)
            return [deployment.metadata.name for deployment in deployments.items]
        except kubernetes.client.rest.ApiException as e:
            print(f"Error listing deployments in namespace {namespace}: {e}")
            exit(1)

    def get_deployment_replicas(self, namespace):
        self.logger.debug(f"get_deployment_replicas(namespace: {namespace})")
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace)
            return {deployment.metadata.name: deployment.spec.replicas for deployment in deployments.items}
        except kubernetes.client.rest.ApiException as e:
            print(f"Error fetching deployment replicas in namespace {namespace}: {e}")
            exit(1)
    
    def get_deployment_cost_details(self, namespace):
        self.logger.debug(f"get_deployment_cost_details(namespace: {namespace})")
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace)
            cost_details = {}

            for deployment in deployments.items:
                name = deployment.metadata.name
                replicas = deployment.spec.replicas or 0
                cpu_limit = "N/A"
                ram_limit = "N/A"

                if deployment.spec.template.spec.containers:
                    for container in deployment.spec.template.spec.containers:
                        if container.resources and container.resources.limits:
                            cpu_limit = container.resources.limits.get("cpu", "N/A")
                            ram_limit = container.resources.limits.get("memory", "N/A")
                            break  # Take limits from the first container

                cost_details[name] = {
                    "replicas": replicas,
                    "cpu": cpu_limit,
                    "ram": ram_limit
                }
            return cost_details
        
        except kubernetes.client.rest.ApiException as e:
            print(f"Error fetching deployment cost details in namespace {namespace}: {e}")
            exit(1)

    def remove_hpa_downscaling_annotations(self, hpa_item):
        self.logger.debug(f"remove_hpa_downscaling_annotations(hpa_item: {hpa_item})")
        if not hpa_item.metadata.annotations:
            return
        
        annotations = hpa_item.metadata.annotations.copy()
        keys_to_remove = ["downscaler/downtime-replicas", "downscaler/uptime"]

        for key in keys_to_remove:
            annotations.pop(key, None)

        metadata = kubernetes.V1ObjectMeta(annotations=annotations)
        body = kubernetes.V2HorizontalPodAutoscaler(metadata=metadata)

        try:
            self.autoscaling_v2.patch_namespaced_horizontal_pod_autoscaler(
                name=hpa_item.metadata.name,
                namespace=hpa_item.metadata.namespace,
                body=body
            )
        except kubernetes.client.rest.ApiException as e:
            print(f"Error removing HPA annotations in {hpa_item.metadata.namespace}/{hpa_item.metadata.name}: {e}")

    def remove_hpa_downscaling_annotations_namespaced(self, namespace):
        self.logger.debug(f"remove_hpa_downscaling_annotations_namespaced(namespace: {namespace})")
        try:
            result = self.autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(namespace)
            for item in result.items:
                self.remove_hpa_downscaling_annotations(item)
        except kubernetes.client.rest.ApiException as e:
            print(f"Error listing HPAs in namespace {namespace}: {e}")

    def add_hpa_downscaling_annotations(self, hpa_item):
        self.logger.debug(f"add_hpa_downscaling_annotations(hpa_item: {hpa_item})")
        annotations = hpa_item.metadata.annotations or {}
        annotations["downscaler/downtime-replicas"] = "1"
        annotations["downscaler/uptime"] = "Mon-Fri 05:30-20:30 Europe/Berlin"

        metadata = kubernetes.V1ObjectMeta(annotations=annotations)
        body = kubernetes.V2HorizontalPodAutoscaler(metadata=metadata)

        try:
            self.autoscaling_v2.patch_namespaced_horizontal_pod_autoscaler(
                name=hpa_item.metadata.name,
                namespace=hpa_item.metadata.namespace,
                body=body
            )
        except kubernetes.client.rest.ApiException as e:
            print(f"Error adding HPA annotations in {hpa_item.metadata.namespace}/{hpa_item.metadata.name}: {e}")

    def add_hpa_downscaling_annotations_namespaced(self, namespace):
        self.logger.debug(f"add_hpa_downscaling_annotations_namespaced(namespace: {namespace})")
        try:
            result = self.autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(namespace)
            for item in result.items:
                self.add_hpa_downscaling_annotations(item)
        except kubernetes.client.rest.ApiException as e:
            print(f"Error listing HPAs in namespace {namespace}: {e}")
