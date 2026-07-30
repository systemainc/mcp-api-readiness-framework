"""Tests for the Consent & Auth Surface dimension checks."""
import os
import pytest
from framework.checks.consent_auth import check_consent_auth
from framework.scoring.engine import score_dimension

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
FULL = os.path.join(FIXTURES, "full_coverage")
NONE = os.path.join(FIXTURES, "no_coverage")
CLARIO = os.path.join(os.path.dirname(__file__), "..", "examples", "clario")


def test_full_coverage_fixture_passes_all_checks():
    checks = check_consent_auth(FULL, {})
    assert all(c.passed for c in checks), [c for c in checks if not c.passed]


def test_no_coverage_fixture_fails_all_checks():
    checks = check_consent_auth(NONE, {})
    assert not any(c.passed for c in checks)


def test_clario_passes_scoped_tokens_check():
    checks = check_consent_auth(CLARIO, {})
    scoped = next(c for c in checks if c.id == "consent_auth.scoped_tokens")
    assert scoped.passed


def test_clario_passes_discoverable_auth_check():
    checks = check_consent_auth(CLARIO, {})
    discoverable = next(c for c in checks if c.id == "consent_auth.discoverable_auth")
    assert discoverable.passed


def test_clario_passes_per_tool_permission_check():
    checks = check_consent_auth(CLARIO, {})
    per_tool = next(c for c in checks if c.id == "consent_auth.per_tool_permission")
    assert per_tool.passed


def test_clario_fails_token_expiry_check():
    """Clario's tokens are valid indefinitely until manually revoked - no expiry."""
    checks = check_consent_auth(CLARIO, {})
    expiry = next(c for c in checks if c.id == "consent_auth.token_expiry")
    assert not expiry.passed


def test_clario_fails_token_revocation_check():
    """Clario's auth.py claims tokens are 'valid indefinitely until manually revoked'
    but implements no revoke function - the claimed escape hatch doesn't exist in code."""
    checks = check_consent_auth(CLARIO, {})
    revocation = next(c for c in checks if c.id == "consent_auth.token_revocation")
    assert not revocation.passed


def test_clario_fails_step_up_confirmation_check():
    """void_invoice is gated by the same @require_scope as any routine write - no extra confirmation."""
    checks = check_consent_auth(CLARIO, {})
    step_up = next(c for c in checks if c.id == "consent_auth.step_up_confirmation")
    assert not step_up.passed


def test_full_coverage_scores_level_4():
    checks = check_consent_auth(FULL, {})
    result = score_dimension("consent_auth", "Consent & Auth Surface", checks)
    assert result.level == 4


def test_no_coverage_scores_level_1():
    checks = check_consent_auth(NONE, {})
    result = score_dimension("consent_auth", "Consent & Auth Surface", checks)
    assert result.level == 1


def test_check_ids_are_stable():
    checks = check_consent_auth(FULL, {})
    ids = [c.id for c in checks]
    assert "consent_auth.scoped_tokens" in ids
    assert "consent_auth.discoverable_auth" in ids
    assert "consent_auth.per_tool_permission" in ids
    assert "consent_auth.token_expiry" in ids
    assert "consent_auth.token_revocation" in ids
    assert "consent_auth.step_up_confirmation" in ids
