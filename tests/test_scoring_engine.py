"""Tests for the scoring engine: level math and overall-level calculation."""
import pytest
from framework.schema import CheckResult, ScorecardResult, DimensionResult
from framework.scoring.engine import score_dimension, compute_overall


def _check(passed: bool, weight: int = 1) -> CheckResult:
    return CheckResult(
        id="test.check",
        description="test",
        passed=passed,
        evidence="",
        score_contribution=weight,
    )


def test_all_passed_is_level_4():
    checks = [_check(True), _check(True), _check(True), _check(True)]
    result = score_dimension("d", "D", checks)
    assert result.level == 4


def test_none_passed_is_level_1():
    checks = [_check(False), _check(False), _check(False)]
    result = score_dimension("d", "D", checks)
    assert result.level == 1


def test_half_passed_is_level_3():
    # 2 of 4 points = 50% -> Level 3
    checks = [_check(True, 2), _check(False, 2)]
    result = score_dimension("d", "D", checks)
    assert result.level == 3


def test_quarter_passed_is_level_2():
    # 1 of 4 points = 25% -> Level 2
    checks = [_check(True, 1), _check(False, 3)]
    result = score_dimension("d", "D", checks)
    assert result.level == 2


def test_empty_checks_returns_insufficient_data():
    result = score_dimension("d", "D", [])
    assert result.insufficient_data is True
    assert result.level == 1


def test_overall_level_is_minimum_across_dimensions():
    scorecard = ScorecardResult(target="test")
    scorecard.dimensions = [
        DimensionResult(id="a", name="A", level=4),
        DimensionResult(id="b", name="B", level=2),
        DimensionResult(id="c", name="C", level=3),
    ]
    assert compute_overall(scorecard) == 2


def test_overall_treats_insufficient_data_as_worst_case():
    """A dimension that couldn't be checked caps the scorecard at Level 1."""
    scorecard = ScorecardResult(target="test")
    scorecard.dimensions = [
        DimensionResult(id="a", name="A", level=3),
        DimensionResult(id="b", name="B", level=1, insufficient_data=True),
        DimensionResult(id="c", name="C", level=3),
    ]
    assert compute_overall(scorecard) == 1


def test_high_weight_check_dominates_score():
    # 2-weight pass + 1-weight fail = 2/3 = 66.7% -> Level 3
    checks = [_check(True, 2), _check(False, 1)]
    result = score_dimension("d", "D", checks)
    assert result.level == 3
