"""
Scoring engine: turns a list of CheckResults into a 1-4 dimension level.

The score is driven by the weighted sum of passed checks versus the maximum
possible score. That ratio is mapped to 1-4:

  < 25%  -> Level 1 (Not Ready)
  25-49% -> Level 2 (Partial)
  50-74% -> Level 3 (Capable)
  >= 75% -> Level 4 (Robust)

The thresholds are defined here and are intentionally not in the config -
they are part of the framework's definition of the maturity scale and should
not vary between target codebases. What varies is the check set, not the
level math.

Overall level is the minimum across all six dimensions, not an average.
A codebase with a perfect score on five dimensions but a zero on Boundary
Enforcement is not "mostly ready" - it is a liability.
"""
from __future__ import annotations

from ..schema import CheckResult, DimensionResult, ScorecardResult


_THRESHOLDS = [
    (0.75, 4),
    (0.50, 3),
    (0.25, 2),
    (0.0,  1),
]


def _level_from_ratio(ratio: float) -> int:
    for threshold, level in _THRESHOLDS:
        if ratio >= threshold:
            return level
    return 1


def score_dimension(
    dim_id: str,
    dim_name: str,
    checks: list[CheckResult],
) -> DimensionResult:
    max_score = sum(c.score_contribution for c in checks)
    if max_score == 0:
        return DimensionResult(
            id=dim_id,
            name=dim_name,
            level=1,
            check_results=checks,
            insufficient_data=True,
        )
    earned = sum(c.score_contribution for c in checks if c.passed)
    ratio = earned / max_score
    level = _level_from_ratio(ratio)
    return DimensionResult(
        id=dim_id,
        name=dim_name,
        level=level,
        check_results=checks,
    )


def compute_overall(scorecard: ScorecardResult) -> int:
    levels = [d.level for d in scorecard.dimensions]
    if not levels:
        return 1
    return min(levels)
