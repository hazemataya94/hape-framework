# How HAPE compares

## Purpose

Show where HAPE Framework differs from common automation workflows.

HAPE complements CI and IaC.

It does not replace Terraform or Kubernetes.

## Legend

✅ Yes  ❌ No  ◐ Partial

## Comparison

| Approach | Named repeatable CLI | Safety level before run | Approval for write or delete | Shared human and AI rules | Secret redaction |
| --- | --- | --- | --- | --- | --- |
| Ad-hoc scripts plus kubectl | ❌ | ❌ | ❌ | ❌ | ◐ |
| GitHub Actions or GitLab CI | ◐ | ❌ | ◐ | ❌ | ◐ |
| Terraform | ✅ | ◐ | ◐ | ❌ | ◐ |
| Unrestricted AI agent in an IDE | ❌ | ❌ | ❌ | ❌ | ❌ |
| HAPE Framework | ✅ | ✅ | ✅ | ✅ | ✅ |

## Partial cells

- Ad-hoc scripts can hide secrets if the operator writes that behavior.
- CI systems have named jobs and some branch protections, and they can mask log values.
- Terraform has a named CLI and a plan versus apply split, not a read/write/delete safety label shared with AI coding agents.

## Related documentation

- [Five-minute quick start](../getting-started/five-minute-quickstart.md)
- [First useful output](../getting-started/first-useful-output.md)
- [Command safety](../getting-started/safety-basics.md)
- [CLI, API, service, and client model](cli-api-service-client.md)
