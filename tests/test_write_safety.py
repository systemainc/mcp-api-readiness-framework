"""Tests for the Write Safety dimension checks."""
import os
import pytest
from framework.checks.write_safety import check_write_safety
from framework.scoring.engine import score_dimension

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
FULL = os.path.join(FIXTURES, "full_coverage")
NONE = os.path.join(FIXTURES, "no_coverage")
CLARIO = os.path.join(os.path.dirname(__file__), "..", "examples", "clario")


def test_full_coverage_fixture_passes_all_checks():
    checks = check_write_safety(FULL, {})
    assert all(c.passed for c in checks), [c for c in checks if not c.passed]


def test_no_coverage_fixture_fails_all_checks():
    checks = check_write_safety(NONE, {})
    assert not any(c.passed for c in checks)


def test_clario_passes_idempotency_key_check():
    checks = check_write_safety(CLARIO, {})
    idem_check = next(c for c in checks if c.id == "write_safety.idempotency_key")
    assert idem_check.passed


def test_clario_fails_dedup_window_check():
    """Clario accepts the Idempotency-Key header but has no dedup store."""
    checks = check_write_safety(CLARIO, {})
    dedup_check = next(c for c in checks if c.id == "write_safety.dedup_window")
    assert not dedup_check.passed


def test_clario_fails_idempotency_test_coverage():
    """Clario's tests don't cover duplicate-submission behavior."""
    checks = check_write_safety(CLARIO, {})
    test_check = next(c for c in checks if c.id == "write_safety.idempotency_tests")
    assert not test_check.passed


def test_full_coverage_scores_level_4():
    checks = check_write_safety(FULL, {})
    result = score_dimension("write_safety", "Write Safety", checks)
    assert result.level == 4


def test_no_coverage_scores_level_1():
    checks = check_write_safety(NONE, {})
    result = score_dimension("write_safety", "Write Safety", checks)
    assert result.level == 1


def test_check_ids_are_stable():
    checks = check_write_safety(FULL, {})
    ids = [c.id for c in checks]
    assert "write_safety.idempotency_key" in ids
    assert "write_safety.dedup_window" in ids
    assert "write_safety.conditional_requests" in ids
    assert "write_safety.idempotency_tests" in ids
