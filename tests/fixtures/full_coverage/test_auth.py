# pragma: no-collect (synthetic fixture - not real tests)


def test_cross_tenant_access_returns_403():
    resp = client.get("/invoices/inv_other_account", headers={"Authorization": "Bearer tok_tenant_a"})
    assert resp.status_code == 403


def test_create_invoice_duplicate_idempotent():
    key = "idem-key-1"
    r1 = client.post("/invoices", json={}, headers={"Idempotency-Key": key})
    r2 = client.post("/invoices", json={}, headers={"Idempotency-Key": key})
    assert r1.json()["id"] == r2.json()["id"]
