change this:
{
    "name": "deployment-cost"
    "schema": {
        "id": {"int": ["primary", "autoincrement"]},
        "service-name": {"string": []},
        "pod-cpu": {"string": []},
        "pod-ram": {"string": []},
        "autoscaling": {"bool": []},
        "min-replicas": {"int": ["nullable"]},
        "max-replicas": {"int": ["nullable"]},
        "current-replicas": {"int": []},
        "pod-cost": {"string": []},
        "number-of-pods": {"int": []},
        "total-cost": {"float": []},
        "cost-unit": {"string": []}
    }
}
to
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