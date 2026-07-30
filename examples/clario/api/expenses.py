"""
Clario API - Expense endpoints.

Gaps present in this module (deliberate, for the worked example):

1. Write Safety - POST /expenses has no idempotency support at all. No
   Idempotency-Key header, no dedup window. An agent that retries a
   failed expense submission creates duplicate expense records.

2. Operational Containment - No input size cap on the `notes` field. An
   agent that interpolates a large context window excerpt into `notes` will
   succeed regardless of the payload size.

3. Operational Containment - No rate limiting. A looping agent can POST
   thousands of expense records without any throttle.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from .auth import require_scope
from .audit import audit_log


_expenses: dict[str, dict] = {}


@require_scope("expenses:write")
def submit_expense(request: dict) -> dict:
    """POST /expenses - No idempotency support."""
    ctx = request["_token_ctx"]
    body = request.get("body", {})

    expense_id = f"exp_{uuid.uuid4().hex[:8]}"
    expense = {
        "id": expense_id,
        "account_id": ctx["account_id"],
        "category": body.get("category"),
        "amount_cents": body.get("amount_cents"),
        "currency": body.get("currency", "USD"),
        "merchant": body.get("merchant"),
        "notes": body.get("notes", ""),  # Gap: no max_length enforcement
        "date": body.get("date"),
        "status": "pending_review",
        "submitted_at": datetime.utcnow().isoformat(),
    }
    _expenses[expense_id] = expense
    audit_log(
        actor_id=ctx.get("account_id", "unknown"),
        action="expense.submitted",
        resource_id=expense_id,
        outcome="success",
    )
    return {"status": 201, "data": expense}


@require_scope("expenses:read")
def get_expense(request: dict, expense_id: str) -> dict:
    """GET /expenses/{expense_id}"""
    ctx = request["_token_ctx"]
    expense = _expenses.get(expense_id)
    if not expense:
        return {"status": 404, "error": "Not found", "error_code": "EXPENSE_NOT_FOUND"}
    if expense["account_id"] != ctx["account_id"]:
        return {"status": 403, "error": "Forbidden", "error_code": "TENANT_BOUNDARY_VIOLATION"}
    return {"status": 200, "data": expense}


@require_scope("expenses:read")
def list_expenses(request: dict) -> dict:
    """GET /expenses"""
    ctx = request["_token_ctx"]
    account_id = ctx["account_id"]
    results = [exp for exp in _expenses.values() if exp["account_id"] == account_id]
    return {"status": 200, "data": results, "total": len(results)}


@require_scope("expenses:write")
def approve_expense(request: dict, expense_id: str) -> dict:
    """POST /expenses/{expense_id}/approve"""
    ctx = request["_token_ctx"]
    expense = _expenses.get(expense_id)
    if not expense:
        return {"status": 404, "error": "Not found", "error_code": "EXPENSE_NOT_FOUND"}
    if expense["account_id"] != ctx["account_id"]:
        return {"status": 403, "error": "Forbidden", "error_code": "TENANT_BOUNDARY_VIOLATION"}
    expense["status"] = "approved"
    expense["approved_at"] = datetime.utcnow().isoformat()
    audit_log(
        actor_id=ctx.get("account_id", "unknown"),
        action="expense.approved",
        resource_id=expense_id,
        outcome="success",
    )
    return {"status": 200, "data": expense}
