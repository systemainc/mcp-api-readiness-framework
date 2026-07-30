"""Tests for the Forensics dimension checks."""
import os
import pytest
from framework.checks.forensics import check_forensics
from framework.scoring.engine import score_dimension

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
FULL = os.path.join(FIXTURES, "full_coverage")
NONE = os.path.join(FIXTURES, "no_coverage")
CLARIO = os.path.join(os.path.dirname(__file__), "..", "examples", "clario")


def test_full_coverage_passes_all_checks():
    checks = check_forensics(FULL, {})
    assert all(c.passed for c in checks), [c for c in checks if not c.passed]


def test_no_coverage_fails_all_checks():
    checks = check_forensics(NONE, {})
    assert not any(c.passed for c in checks)


def test_clario_passes_correlation_id_check():
    checks = check_forensics(CLARIO, {})
    corr = next(c for c in checks if c.id == "forensics.correlation_id")
    assert corr.passed


def test_clario_passes_audit_log_check():
    checks = check_forensics(CLARIO, {})
    audit = next(c for c in checks if c.id == "forensics.audit_log")
    assert audit.passed


def test_clario_fails_failure_auditing():
    """Clario only audits successes, not failure paths."""
    checks = check_forensics(CLARIO, {})
    fail_audit = next(c for c in checks if c.id == "forensics.failure_auditing")
    assert not fail_audit.passed


def test_clario_passes_actor_identity():
    checks = check_forensics(CLARIO, {})
    actor = next(c for c in checks if c.id == "forensics.actor_identity")
    assert actor.passed
