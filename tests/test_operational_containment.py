"""Tests for the Operational Containment dimension checks."""
import os
import pytest
from framework.checks.operational_containment import check_operational_containment
from framework.scoring.engine import score_dimension

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
FULL = os.path.join(FIXTURES, "full_coverage")
NONE = os.path.join(FIXTURES, "no_coverage")
CLARIO = os.path.join(os.path.dirname(__file__), "..", "examples", "clario")


def test_full_coverage_passes_all_checks():
    checks = check_operational_containment(FULL, {})
    assert all(c.passed for c in checks), [c for c in checks if not c.passed]


def test_no_coverage_fails_all_checks():
    checks = check_operational_containment(NONE, {})
    assert not any(c.passed for c in checks)


def test_clario_fails_rate_limits():
    """Clario has no rate limiting."""
    checks = check_operational_containment(CLARIO, {})
    rl = next(c for c in checks if c.id == "operational_containment.rate_limits")
    assert not rl.passed


def test_clario_fails_input_size_cap():
    """Clario has no max_length on the notes field."""
    checks = check_operational_containment(CLARIO, {})
    size = next(c for c in checks if c.id == "operational_containment.input_size_cap")
    assert not size.passed


def test_clario_fails_untrusted_input():
    """Clario does not sanitize agent-interpolated input."""
    checks = check_operational_containment(CLARIO, {})
    untrusted = next(c for c in checks if c.id == "operational_containment.untrusted_input")
    assert not untrusted.passed


def test_full_coverage_passes_new_checks():
    checks = check_operational_containment(FULL, {})
    ids = [c.id for c in checks]
    assert "operational_containment.retry_after" in ids
    assert "operational_containment.pagination_ceiling" in ids
    for c in checks:
        assert c.passed


def test_no_coverage_fails_new_checks():
    checks = check_operational_containment(NONE, {})
    retry_after = next(c for c in checks if c.id == "operational_containment.retry_after")
    pagination = next(c for c in checks if c.id == "operational_containment.pagination_ceiling")
    assert not retry_after.passed
    assert not pagination.passed


def test_clario_fails_retry_after():
    """Clario has no rate limiting at all, so it has no Retry-After signal either."""
    checks = check_operational_containment(CLARIO, {})
    retry_after = next(c for c in checks if c.id == "operational_containment.retry_after")
    assert not retry_after.passed


def test_clario_fails_pagination_ceiling():
    """list_invoices/list_expenses return every matching record with no page_size or limit."""
    checks = check_operational_containment(CLARIO, {})
    pagination = next(c for c in checks if c.id == "operational_containment.pagination_ceiling")
    assert not pagination.passed
