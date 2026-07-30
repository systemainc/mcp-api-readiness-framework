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


def test_full_coverage_passes_new_checks():
    checks = check_forensics(FULL, {})
    ids = [c.id for c in checks]
    assert "forensics.read_audit_logging" in ids
    assert "forensics.append_only_audit" in ids
    for c in checks:
        assert c.passed


def test_no_coverage_fails_new_checks():
    checks = check_forensics(NONE, {})
    read_audit = next(c for c in checks if c.id == "forensics.read_audit_logging")
    append_only = next(c for c in checks if c.id == "forensics.append_only_audit")
    assert not read_audit.passed
    assert not append_only.passed


def test_clario_fails_read_audit_logging():
    """Clario's get_invoice/get_expense read handlers never call audit_log."""
    checks = check_forensics(CLARIO, {})
    read_audit = next(c for c in checks if c.id == "forensics.read_audit_logging")
    assert not read_audit.passed


def test_clario_passes_append_only_audit():
    """Clario's audit.py docstring claims append-only, and the implementation
    backs it up: only audit_log() (append) and get_audit_records() (read) exist,
    no update/delete function touches _audit_records."""
    checks = check_forensics(CLARIO, {})
    append_only = next(c for c in checks if c.id == "forensics.append_only_audit")
    assert append_only.passed
