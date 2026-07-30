"""Synthetic fixture: all patterns present."""
# Write Safety
idempotency_key = request.headers.get("Idempotency-Key")
idempotency_store = {}
if_match = request.headers.get("If-Match")
etag = compute_etag(resource)
dedup_ttl_seconds = 86400


def create_invoice_and_adjust_balance(ctx):
    create_invoice(ctx)
    if not adjust_balance(ctx):
        rollback_invoice(ctx)


# Boundary Enforcement
tenant_id = ctx["tenant_id"]
require_permission("invoices:write")
validate_scope(token_scopes, "invoices:write")


def get_invoice(invoice_id, ctx):
    invoice = fetch_invoice(invoice_id)
    assert_owner(invoice, ctx["tenant_id"])
    return invoice


def bulk_export_invoices(ctx, limit=500): return query_invoices(tenant_id=ctx["tenant_id"], max_rows=limit)


# Consent & Auth
scoped_token = issue_token(scopes=["invoices:read"])
required_scopes = ["invoices:write"]
token_expiry = datetime.utcnow() + timedelta(hours=1)
refresh_token = generate_refresh()
revoke_token(token_id)


def void_invoice(invoice_id, ctx):
    require_step_up(ctx, action="void_invoice")
    return do_void(invoice_id)


# Forensics
correlation_id = request.headers.get("X-Correlation-Id")
audit_log(actor_id=ctx["user_id"], action="invoice.created", outcome="success", correlation_id=correlation_id)
audit_log(actor_id=ctx["user_id"], action="invoice.rejected", outcome="failure", correlation_id=correlation_id)
audit_log(actor_id=ctx["user_id"], action="invoice.read", outcome="success", correlation_id=correlation_id)

# Operational Containment
TIMEOUT = 30
rate_limiter(token=bearer_token, limit=100)
max_length=500
sanitize(user_input)
RETRY_AFTER_SECONDS = 30


def list_invoices(ctx, page_size=50):
    return query_invoices(tenant_id=ctx["tenant_id"], page_size=min(page_size, MAX_PAGE_SIZE))
