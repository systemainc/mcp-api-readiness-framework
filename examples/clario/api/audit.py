"""
Clario API - Audit logging.

The audit log is append-only and records actor_id, action, resource_id,
and outcome for successful mutations. correlation_id is threaded through
from the request context when present.

Gaps:
- correlation_id is accepted but not generated at the gateway; if the
  caller omits it, the audit entry has no trace link.
- Failure paths (rejected mutations, auth failures) do not call audit_log.
  Only successful writes are recorded.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional


_audit_records: list[dict] = []


def audit_log(
    actor_id: str,
    action: str,
    resource_id: str,
    outcome: str,
    correlation_id: Optional[str] = None,
) -> None:
    _audit_records.append({
        "ts": datetime.utcnow().isoformat(),
        "actor_id": actor_id,
        "action": action,
        "resource_id": resource_id,
        "outcome": outcome,
        "correlation_id": correlation_id,
    })


def get_audit_records() -> list[dict]:
    return list(_audit_records)
