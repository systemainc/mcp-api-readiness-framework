"""Synthetic fixture: all patterns present."""
# Write Safety
idempotency_key = request.headers.get("Idempotency-Key")
idempotency_store = {}
if_match = request.headers.get("If-Match")
etag = compute_etag(resource)

# Boundary Enforcement
tenant_id = ctx["tenant_id"]
require_permission("invoices:write")
validate_scope(token_scopes, "invoices:write")

# Consent & Auth
scoped_token = issue_token(scopes=["invoices:read"])
token_expiry = datetime.utcnow() + timedelta(hours=1)
refresh_token = generate_refresh()

# Forensics
correlation_id = request.headers.get("X-Correlation-Id")
audit_log(actor_id=ctx["user_id"], action="invoice.created", outcome="success", correlation_id=correlation_id)
audit_log(actor_id=ctx["user_id"], action="invoice.rejected", outcome="failure", correlation_id=correlation_id)

# Operational Containment
TIMEOUT = 30
rate_limiter(token=bearer_token, limit=100)
max_length=500
sanitize(user_input)
