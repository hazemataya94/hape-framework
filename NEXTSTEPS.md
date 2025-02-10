## Support project creation
```
$ hape init project --name myawesomeplatform
myawesomeplatform/
│── dockerfiles/  (Copied from HAPE Framework)
│── Makefile      (Copied from HAPE Framework)
│── src/
│   ├── migrations/
│   ├── models/
│   ├── controllers/
│   ├── services/
│   ├── utils/
│   ├── config/
│   ├── tests/
│── docs/
│── scripts/
│── setup.py
│── README.md
```

## Support CRUD Geneartion and Generate migrations/json/model_name.json 
```
$ hape crud generate --json """
{
    "name": "deployment-cost"
    "schema": {
        "id": ["int","autoincrement"],
        "service-name": ["string"],
        "pod-cpu": ["string"],
        "pod-ram": ["string"],
        "autoscaling": ["bool"],
        "min-replicas": ["int","nullable"],
        "max-replicas": ["int","nullable"],
        "current-replicas": ["int"],
        "pod-cost": ["string"],
        "number-of-pods": ["int"],
        "total-cost": ["float"],
        "cost-unit": ["string"]
    }
}
"""
$ hape deployment-cost --help
usage: myawesomeplatform deployment-cost [-h] {save,get,get-all,delete,delete-all} ...

positional arguments:
  {save,get,get-all,delete,delete-all}
    save                Save DeploymentCost object based on passed arguments or filters
    get                 Get DeploymentCost object based on passed arguments or filters
    get-all             Get-all DeploymentCost objects based on passed arguments or filters
    delete              Delete DeploymentCost object based on passed arguments or filters
    delete-all          Delete-all DeploymentCost objects based on passed arguments or filters

options:
  -h, --help            show this help message and exit
```

## Create migrations/json/model_name.json and run CRUD Geneartion for file in migrations/schema_json/{*}.json if models/file.py doesn't exist
```
$ export MY_JSON_FILE="""
{
    "name": "deployment-cost"
    "schema": {
        "id": ["int","autoincrement"],
        "service-name": ["string"],
        "pod-cpu": ["string"],
        "pod-ram": ["string"],
        "autoscaling": ["bool"],
        "min-replicas": ["int","nullable"],
        "max-replicas": ["int","nullable"],
        "current-replicas": ["int"],
        "pod-cost": ["string"],
        "number-of-pods": ["int"],
        "total-cost": ["float"],
        "cost-unit": ["string"]
    }
}
"""
$ echo "${MY_JSON_FILE}" > migrations/schema_json/deployment_cost.json
$ hape crud generate
$ hape deployment-cost --help
usage: hape deployment-cost [-h] {save,get,get-all,delete,delete-all} ...

positional arguments:
  {save,get,get-all,delete,delete-all}
    save                Save DeploymentCost object based on passed arguments or filters
    get                 Get DeploymentCost object based on passed arguments or filters
    get-all             Get-all DeploymentCost objects based on passed arguments or filters
    delete              Delete DeploymentCost object based on passed arguments or filters
    delete-all          Delete-all DeploymentCost objects based on passed arguments or filters

options:
  -h, --help            show this help message and exit
```

## Support Scalable Secure RESTful API
```
$ hape serve http --allow-cidr '0.0.0.0/0,10.0.1.0/24' --deny-cidr '10.200.0.0/24,0,10.0.1.0/24,10.107.0.0/24' --workers 2 --port 80
or
$ hape serve http --json """
{
    "port": 8088
    "allow-cidr": "0.0.0.0/0,10.0.1.0/24",
    "deny-cidr": "10.200.0.0/24,0,10.0.1.0/24,10.107.0.0/24"
}
"""
Spawnining workers
hape-worker-random-string-1 is up
hape-worker-random-string-2 failed
hape-worker-random-string-2 restarting (up to 3 times)
hape-worker-random-string-2 is up
All workers are up
Database connection established
Any other needed step

Serving HAPE on http://127.0.0.1:8088
```

