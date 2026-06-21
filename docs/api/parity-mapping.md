# CLI To API Parity Mapping

## Contract
Every CLI command path must have an API endpoint with strict 1:1 naming.
All command-execution endpoints use HTTP POST.

## Mappings
- `hape config init-config-file` -> `POST /config/init-config-file`
- `hape gitlab clone` -> `POST /gitlab/clone`
- `hape gitlab mr-count-per-day` -> `POST /gitlab/mr-count-per-day`
- `hape github init-repo` -> `POST /github/init-repo`
- `hape github create repo` -> `POST /github/create/repo`
- `hape github list-repos` -> `POST /github/list-repos`
- `hape github user-info` -> `POST /github/user-info`
- `hape github delete-repos` -> `POST /github/delete-repos`
- `hape jira md-to-comment` -> `POST /jira/md-to-comment`
- `hape confluence get-page` -> `POST /confluence/get-page`
- `hape confluence create-page` -> `POST /confluence/create-page`
- `hape confluence md-to-page` -> `POST /confluence/md-to-page`
- `hape csv from-json` -> `POST /csv/from-json`
- `hape csv to-json` -> `POST /csv/to-json`
- `hape markdown export-tables-to-csv` -> `POST /markdown/export-tables-to-csv`
- `hape markdown import-csv-table` -> `POST /markdown/import-csv-table`
- `hape dora validate-config` -> `POST /dora/validate-config`
- `hape dora list-projects` -> `POST /dora/list-projects`
- `hape dora list-deployments` -> `POST /dora/list-deployments`
- `hape dora compute-project` -> `POST /dora/compute-project`
- `hape eks-deployment-cost report` -> `POST /eks-deployment-cost/report`
- `hape kube-agent investigate pod` -> `POST /kube-agent/investigate/pod`
- `hape kube-agent investigate deployment` -> `POST /kube-agent/investigate/deployment`
- `hape kube-agent investigate node` -> `POST /kube-agent/investigate/node`
- `hape kube-agent investigate alert` -> `POST /kube-agent/investigate/alert`
- `hape kube-agent cost-analyze` -> `POST /kube-agent/cost-analyze`
- `hape kube-agent incidents list` -> `POST /kube-agent/incidents/list`
- `hape kube-agent incidents show` -> `POST /kube-agent/incidents/show`
- `hape init-cicd` -> `POST /init-cicd`
