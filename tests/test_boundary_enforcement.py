"""Tests for the Boundary Enforcement dimension checks."""
import os
import pytest
from framework.checks.boundary_enforcement import check_boundary_enforcement
from framework.scoring.engine import score_dimension

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
FULL = os.path.join(FIXTURES, "full_coverage")
NONE = os.path.join(FIXTURES, "no_coverage")
CLARIO = os.path.join(os.path.dirname(__file__), "..", "examples", "clario")


def test_full_coverage_passes_all_checks():
    checks = check_boundary_enforcement(FULL, {})
    assert all(c.passed for c in checks), [c for c in checks if not c.passed]


def test_no_coverage_fails_all_checks():
    checks = check_boundary_enforcement(NONE, {})
    assert not any(c.passed for c in checks)


def test_clario_passes_tenant_filter_check():
    checks = check_boundary_enforcement(CLARIO, {})
    tenant = next(c for c in checks if c.id == "boundary_enforcement.tenant_filter")
    assert tenant.passed


def test_clario_passes_role_check():
    checks = check_boundary_enforcement(CLARIO, {})
    role = next(c for c in checks if c.id == "boundary_enforcement.role_check")
    assert role.passed


def test_clario_fails_adversarial_tests():
    """Clario has no cross-tenant adversarial tests."""
    checks = check_boundary_enforcement(CLARIO, {})
    adv = next(c for c in checks if c.id == "boundary_enforcement.adversarial_tests")
    assert not adv.passed


def test_full_coverage_adversarial_tests_passes():
    """full_coverage fixture has test_cross_tenant_access_returns_403."""
    checks = check_boundary_enforcement(FULL, {})
    adv = next(c for c in checks if c.id == "boundary_enforcement.adversarial_tests")
    assert adv.passed


def test_score_dimension_minimum_not_silently_zeroed():
    """A dimension with no checks gets insufficient_data=True, not a fake score."""
    result = score_dimension("boundary_enforcement", "Boundary Enforcement", [])
    assert result.insufficient_data is True
    assert result.level == 1
