# CLI To API Parity Mapping

## Contract
Workflow endpoints that exist on the API use strict 1:1 naming with CLI command paths.
All command-execution endpoints use HTTP POST.

Intentional CLI-only surfaces: `linkedin`, `ecr`, and interactive `github auth` commands.

## Mappings
- `hape config init-config-file` -> `POST /config/init-config-file`
- `hape config show` -> `POST /config/show`
- `hape gitlab clone` -> `POST /gitlab/clone`
- `hape gitlab mr-count-per-day` -> `POST /gitlab/mr-count-per-day`
- `hape github init-repo` -> `POST /github/init-repo`
- `hape github create repo` -> `POST /github/create/repo`
- `hape github list-repos` -> `POST /github/list-repos`
- `hape github user-info` -> `POST /github/user-info`
- `hape github delete-repos` -> `POST /github/delete-repos`
- `hape github v2 managed-destination status` -> `GET /github/v2/managed-destinations/{destination_id}/status`
- `hape github v2 managed-target setup-url` -> `POST /github/v2/managed-targets/setup-url`
- `hape github v2 managed-target verify` -> `POST /github/v2/managed-targets/verify`
- `hape github v2 managed-target status` -> `GET /github/v2/managed-targets/{target_binding_id}/status`
- `hape github v2 managed-repository create-private` -> `POST /github/v2/managed-repositories`
- `hape github v2 managed-repository publish-baseline` -> `POST /github/v2/managed-repositories/{repository_id}/commits/baseline`
- `hape github v2 managed-repository publish-artifact` -> `POST /github/v2/managed-repositories/{repository_id}/commits/artifact`
- `hape github v2 managed-repository publish-tag` -> `POST /github/v2/managed-repositories/{repository_id}/tags`
- `hape github v2 managed-repository dispose` -> `POST /github/v2/managed-repositories/{repository_id}/dispose`
- `hape github v2 provider-operation get` -> `GET /github/v2/provider-operations/{operation_id}`
- `hape github v2 provider-receipt get` -> `GET /github/v2/provider-receipts/{receipt_id}`
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
- `hape vault kv-get` -> `POST /vault/kv-get`
