"""Tests for the Interface Legibility dimension checks (deterministic only)."""
import os
import pytest
from framework.checks.interface_legibility import check_interface_legibility
from framework.scoring.engine import score_dimension

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
FULL = os.path.join(FIXTURES, "full_coverage")
NONE = os.path.join(FIXTURES, "no_coverage")
CLARIO = os.path.join(os.path.dirname(__file__), "..", "examples", "clario")


def test_full_coverage_openapi_present():
    checks = check_interface_legibility(FULL, {})
    spec_check = next(c for c in checks if c.id == "interface_legibility.openapi_present")
    assert spec_check.passed


def test_no_coverage_openapi_absent():
    checks = check_interface_legibility(NONE, {})
    spec_check = next(c for c in checks if c.id == "interface_legibility.openapi_present")
    assert not spec_check.passed


def test_clario_openapi_present():
    checks = check_interface_legibility(CLARIO, {})
    spec_check = next(c for c in checks if c.id == "interface_legibility.openapi_present")
    assert spec_check.passed


def test_clario_has_operation_descriptions():
    checks = check_interface_legibility(CLARIO, {})
    desc_check = next(c for c in checks if c.id == "interface_legibility.operation_descriptions")
    assert desc_check.passed


def test_clario_has_structured_errors():
    checks = check_interface_legibility(CLARIO, {})
    err_check = next(c for c in checks if c.id == "interface_legibility.structured_errors")
    assert err_check.passed


def test_full_coverage_has_structured_errors():
    checks = check_interface_legibility(FULL, {})
    err_check = next(c for c in checks if c.id == "interface_legibility.structured_errors")
    assert err_check.passed
