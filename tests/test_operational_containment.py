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
