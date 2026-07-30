"""
Clario API - Invoice endpoints.

Gaps present in this module (deliberate, for the Clario Example):

1. Write Safety - Idempotency-Key is accepted on POST /invoices but there is
   no deduplication store backing it. The header value is read and logged but
   never checked against a "seen keys" record. A retry will create a second
   invoice with a different ID.

2. Forensics - The audit log records the actor_id (good) and the outcome
   (good), but failure paths (e.g., a rejected void) do not emit audit
   events. Only successful mutations are recorded.

3. Interface Legibility - The error messages are written for a human reading
   a browser console ("Something went wrong with the void operation"), not for
   an agent that needs to decide whether to retry, correct its input, or
   escalate.

4. Boundary Enforcement - create_invoice has no @require_scope check, unlike
   every other mutating endpoint in this module. POST /invoices can be called
   with no Authorization header at all and still succeeds. This is kept as a
   deliberate gap rather than fixed, so the scorer's output reflects a real
   missing check instead of a contrived one.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from .auth import require_scope
from .audit import audit_log


# In-memory store (demo only)
_invoices: dict[str, dict] = {}


def create_invoice(request: dict) -> dict:
    """POST /invoices"""
    ctx = request.get("_token_ctx", {})
    account_id = ctx.get("account_id")

    # Idempotency-Key is read but not enforced - Gap: no dedup store
    idempotency_key = request.get("headers", {}).get("Idempotency-Key")
    # TODO: check _seen_idempotency_keys before proceeding

    body = request.get("body", {})
    invoice_id = f"inv_{uuid.uuid4().hex[:8]}"
    invoice = {
        "id": invoice_id,
        "account_id": account_id,
        "vendor": body.get("vendor"),
        "amount_cents": body.get("amount_cents"),
        "currency": body.get("currency", "USD"),
        "due_date": body.get("due_date"),
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
    }
    _invoices[invoice_id] = invoice
    audit_log(
        actor_id=ctx.get("account_id", "unknown"),
        action="invoice.created",
        resource_id=invoice_id,
        outcome="success",
    )
    return {"status": 201, "data": invoice}


@require_scope("invoices:read")
def get_invoice(request: dict, invoice_id: str) -> dict:
    """GET /invoices/{invoice_id}"""
    ctx = request["_token_ctx"]
    invoice = _invoices.get(invoice_id)
    if not invoice:
        return {"status": 404, "error": "Not found", "error_code": "INVOICE_NOT_FOUND"}
    # tenant isolation: account_id check
    if invoice["account_id"] != ctx["account_id"]:
        return {"status": 403, "error": "Forbidden", "error_code": "TENANT_BOUNDARY_VIOLATION"}
    return {"status": 200, "data": invoice}


@require_scope("invoices:write")
def void_invoice(request: dict, invoice_id: str) -> dict:
    """POST /invoices/{invoice_id}/void"""
    ctx = request["_token_ctx"]
    invoice = _invoices.get(invoice_id)
    if not invoice:
        return {"status": 404, "error": "Not found", "error_code": "INVOICE_NOT_FOUND"}
    if invoice["account_id"] != ctx["account_id"]:
        return {"status": 403, "error": "Forbidden", "error_code": "TENANT_BOUNDARY_VIOLATION"}
    if invoice["status"] == "paid":
        # Gap: failure path - no audit event emitted here
        return {
            "status": 422,
            "error": "Something went wrong with the void operation",  # Gap: not agent-legible
        }
    invoice["status"] = "void"
    audit_log(
        actor_id=ctx.get("account_id", "unknown"),
        action="invoice.voided",
        resource_id=invoice_id,
        outcome="success",
    )
    return {"status": 200, "data": invoice}


@require_scope("invoices:read")
def list_invoices(request: dict) -> dict:
    """GET /invoices"""
    ctx = request["_token_ctx"]
    account_id = ctx["account_id"]
    # tenant_id filter: only return this account's invoices
    results = [inv for inv in _invoices.values() if inv["account_id"] == account_id]
    return {"status": 200, "data": results, "total": len(results)}
