"""
Clario expense tests.

Similar pattern to test_invoices.py: basic CRUD covered, adversarial
cross-tenant and idempotency tests absent.
"""
import pytest
from api.expenses import submit_expense, get_expense, approve_expense


def _req(body=None):
    return {
        "_token_ctx": {
            "account_id": "acc_123",
            "scopes": "expenses:read expenses:write",
        },
        "headers": {"Authorization": "Bearer tok_demo_readwrite"},
        "body": body or {},
    }


def test_submit_expense_returns_201():
    resp = submit_expense(_req(body={
        "category": "travel",
        "amount_cents": 8500,
        "currency": "USD",
        "merchant": "Rideshare Co",
        "date": "2026-07-15",
    }))
    assert resp["status"] == 201
    assert resp["data"]["status"] == "pending_review"


def test_get_expense_returns_data():
    create_resp = submit_expense(_req(body={
        "category": "meals",
        "amount_cents": 3200,
        "currency": "USD",
        "merchant": "The Corner Diner",
        "date": "2026-07-20",
    }))
    expense_id = create_resp["data"]["id"]
    get_resp = get_expense(_req(), expense_id)
    assert get_resp["status"] == 200
    assert get_resp["data"]["id"] == expense_id


def test_approve_expense_changes_status():
    create_resp = submit_expense(_req(body={
        "category": "office",
        "amount_cents": 1200,
        "currency": "USD",
        "merchant": "Paper Plus",
        "date": "2026-07-22",
    }))
    expense_id = create_resp["data"]["id"]
    approve_resp = approve_expense(_req(), expense_id)
    assert approve_resp["status"] == 200
    assert approve_resp["data"]["status"] == "approved"


# NOTE: no test for cross-tenant expense access
# NOTE: no test for notes field size limit
# NOTE: no test for duplicate expense submission
