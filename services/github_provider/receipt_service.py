from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from services.github_provider.models import RECEIPT_ENVELOPE_VERSION, ProviderReceipt
from services.github_provider.errors import GitHubV2Error


class ReceiptService:
    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def build(self, fields: dict[str, Any]) -> ProviderReceipt:
        issued_at = self._now()
        status = str(fields["status"])
        completed_at = issued_at if status in {"succeeded", "failed", "reconciled"} else None
        return ProviderReceipt(
            receipt_id=str(uuid.uuid4()),
            envelope_version=RECEIPT_ENVELOPE_VERSION,
            operation_id=str(fields["operation_id"]),
            operation=str(fields["operation"]),
            subject_id=str(fields["subject_id"]),
            target_binding_id=str(fields["target_binding_id"]),
            repository_id=fields.get("repository_id"),
            input_digest=str(fields["input_digest"]),
            output_digest=str(fields.get("output_digest") or ""),
            status=status,
            issued_at=issued_at,
            completed_at=completed_at,
            safe_provider_ids=fields.get("safe_provider_ids") or {},
            retry_class=str(fields.get("retry_class") or "none"),
            customer_safe_error_code=str(fields.get("customer_safe_error_code") or ""),
        )

    def to_public(self, receipt: ProviderReceipt) -> dict[str, Any]:
        if receipt.envelope_version != RECEIPT_ENVELOPE_VERSION:
            raise GitHubV2Error("policy_denied")
        return {
            "receipt_id": receipt.receipt_id,
            "envelope_version": receipt.envelope_version,
            "operation_id": receipt.operation_id,
            "operation": receipt.operation,
            "subject_id": receipt.subject_id,
            "target_binding_id": receipt.target_binding_id,
            "repository_id": receipt.repository_id,
            "input_digest": receipt.input_digest,
            "output_digest": receipt.output_digest,
            "status": receipt.status,
            "issued_at": receipt.issued_at,
            "completed_at": receipt.completed_at,
            "safe_provider_ids": receipt.safe_provider_ids,
            "retry_class": receipt.retry_class,
            "customer_safe_error_code": receipt.customer_safe_error_code,
        }


if __name__ == "__main__":
    service = ReceiptService()
    receipt = service.build({"operation_id": "op", "operation": "managed_destination.status", "subject_id": "sub", "target_binding_id": "tgt", "input_digest": "in", "output_digest": "out", "status": "succeeded"})
    print(service.to_public(receipt)["envelope_version"])
