"""
Dimension 3 - Consent & Auth Surface

Agents need to be able to acquire exactly the permission they need for a
specific tool call, no more. This dimension checks for scoped tokens,
discoverable auth metadata, and per-tool consent patterns. A single
"admin" token that grants everything is the opposite of this.
"""
from __future__ import annotations

from ..schema import CheckResult
from ._util import grep_files, file_exists, glob_exists


def check_consent_auth(target_dir: str, dim_config: dict) -> list[CheckResult]:
    results = []

    # Check 1: scoped token / least-privilege token patterns
    scoped_token_hits = grep_files(
        target_dir,
        r"scoped.*token|token.*scope|least.privilege|minimum.permission|granular.*permission|fine.grained.*permission",
        "**/*.py",
    )
    results.append(CheckResult(
        id="consent_auth.scoped_tokens",
        description="Scoped / least-privilege token pattern present",
        passed=len(scoped_token_hits) > 0,
        evidence=(
            f"Found {len(scoped_token_hits)} reference(s): {scoped_token_hits[0][0]}:{scoped_token_hits[0][1]}"
            if scoped_token_hits
            else "No scoped-token or least-privilege pattern found"
        ),
        score_contribution=2,
    ))

    # Check 2: discoverable auth - OpenAPI securitySchemes or equivalent metadata
    openapi_files = glob_exists(target_dir, "**/*.yaml") + glob_exists(target_dir, "**/*.json")
    openapi_with_security = []
    from pathlib import Path
    for rel_path in openapi_files:
        try:
            content = (Path(target_dir) / rel_path).read_text(errors="replace")
            if "securitySchemes" in content or "security_schemes" in content or '"security"' in content:
                openapi_with_security.append(rel_path)
        except OSError:
            pass

    results.append(CheckResult(
        id="consent_auth.discoverable_auth",
        description="Auth metadata is machine-discoverable (OpenAPI securitySchemes or equivalent)",
        passed=len(openapi_with_security) > 0,
        evidence=(
            f"Found auth metadata in: {openapi_with_security[0]}"
            if openapi_with_security
            else "No discoverable auth metadata found (OpenAPI securitySchemes absent)"
        ),
        score_contribution=2,
    ))

    # Check 3: per-tool or per-endpoint permission declaration
    per_tool_hits = grep_files(
        target_dir,
        r"required_permissions|required_scopes|tool_permissions|endpoint_scopes|permission.*decorator|@require_scope",
        "**/*.py",
    )
    results.append(CheckResult(
        id="consent_auth.per_tool_permission",
        description="Per-tool or per-endpoint permission declaration present",
        passed=len(per_tool_hits) > 0,
        evidence=(
            f"Found {len(per_tool_hits)} reference(s): {per_tool_hits[0][0]}:{per_tool_hits[0][1]}"
            if per_tool_hits
            else "No per-tool permission declarations found; all tools may share one blanket auth check"
        ),
        score_contribution=2,
    ))

    # Check 4: token expiry / rotation support
    expiry_hits = grep_files(
        target_dir,
        r"token_expiry|expires_at|token_ttl|refresh_token|rotate_token|TokenExpired",
        "**/*.py",
    )
    results.append(CheckResult(
        id="consent_auth.token_expiry",
        description="Token expiry or rotation mechanism present",
        passed=len(expiry_hits) > 0,
        evidence=(
            f"Found {len(expiry_hits)} reference(s): {expiry_hits[0][0]}:{expiry_hits[0][1]}"
            if expiry_hits
            else "No token expiry or rotation mechanism found"
        ),
        score_contribution=1,
    ))

    return results
