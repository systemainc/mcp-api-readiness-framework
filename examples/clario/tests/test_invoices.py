"""
Clario invoice tests.

Note what is present and what is absent:
- Basic CRUD tests: present
- Tenant isolation (cross-tenant access rejected): ABSENT
  This is the gap the framework will flag under Boundary Enforcement.
- Idempotency / duplicate submission tests: ABSENT
  This is the gap the framework will flag under Write Safety.
"""
import pytest
from api.invoices import create_invoice, get_invoice, void_invoice, list_invoices
from api.audit import get_audit_records


def _req(token="tok_demo_readwrite", body=None, headers=None):
    return {
        "_token_ctx": {
            "account_id": "acc_123",
            "scopes": "invoices:read invoices:write",
        },
        "headers": {**(headers or {}), "Authorization": f"Bearer {token}"},
        "body": body or {},
    }


def test_create_invoice_returns_201():
    resp = create_invoice(_req(body={
        "vendor": "Staples Office Supply",
        "amount_cents": 14999,
        "currency": "USD",
        "due_date": "2026-08-31",
    }))
    assert resp["status"] == 201
    assert resp["data"]["vendor"] == "Staples Office Supply"
    assert resp["data"]["status"] == "draft"


def test_get_invoice_returns_data():
    create_resp = create_invoice(_req(body={
        "vendor": "Acme Printing",
        "amount_cents": 5000,
        "currency": "USD",
    }))
    invoice_id = create_resp["data"]["id"]
    get_resp = get_invoice(_req(), invoice_id)
    assert get_resp["status"] == 200
    assert get_resp["data"]["id"] == invoice_id


def test_void_invoice_changes_status():
    create_resp = create_invoice(_req(body={
        "vendor": "Delta Couriers",
        "amount_cents": 2500,
        "currency": "USD",
    }))
    invoice_id = create_resp["data"]["id"]
    void_resp = void_invoice(_req(), invoice_id)
    assert void_resp["status"] == 200
    assert void_resp["data"]["status"] == "void"


def test_audit_log_records_create():
    before = len(get_audit_records())
    create_invoice(_req(body={
        "vendor": "Quick Print Co",
        "amount_cents": 750,
        "currency": "USD",
    }))
    after = len(get_audit_records())
    assert after > before
    last = get_audit_records()[-1]
    assert last["action"] == "invoice.created"
    assert last["outcome"] == "success"


# NOTE: no test_create_invoice_duplicate / test_idempotent_submission
# NOTE: no test_cross_tenant_access_rejected
