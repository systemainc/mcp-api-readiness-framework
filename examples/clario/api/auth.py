"""
Clario API - Authentication and authorization middleware.

Gap: token expiry and rotation are not implemented. Tokens are valid
indefinitely until manually revoked. An agent that acquires a token in
session 1 will still hold a valid token in session 1000.

Also note: scope validation happens at the middleware level (good) but the
scope list is a single flat string rather than a structured set, making
per-tool permission declarations awkward to express.
"""
from __future__ import annotations

import os
from functools import wraps
from typing import Optional


# Simulated token store - in production this would be a database
_TOKENS = {
    "tok_demo_readwrite": {
        "account_id": "acc_123",
        "scopes": "invoices:read invoices:write expenses:read expenses:write",
    },
    "tok_demo_readonly": {
        "account_id": "acc_123",
        "scopes": "invoices:read expenses:read",
    },
    "tok_other_account": {
        "account_id": "acc_456",
        "scopes": "invoices:read invoices:write expenses:read expenses:write",
    },
}


def _parse_bearer(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:]


def get_token_context(auth_header: Optional[str]) -> Optional[dict]:
    token = _parse_bearer(auth_header)
    if token is None:
        return None
    return _TOKENS.get(token)


def require_scope(scope: str):
    """Decorator: reject requests that lack the required scope."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(request, *args, **kwargs):
            ctx = get_token_context(request.get("headers", {}).get("Authorization"))
            if ctx is None:
                return {"status": 401, "error": "Unauthorized"}
            token_scopes = set(ctx.get("scopes", "").split())
            if scope not in token_scopes:
                return {"status": 403, "error": "Insufficient scope"}
            request["_token_ctx"] = ctx
            return fn(request, *args, **kwargs)
        return wrapper
    return decorator


# Gap: no per-tool consent mechanism. All tokens for an account share the same
# scope string. There is no way to issue a token that permits only
# "void this specific invoice" without also permitting "void any invoice".
# This limits an agent's ability to acquire minimum-necessary permissions.
