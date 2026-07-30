"""
Result schema for the mcp-api-readiness scorer.

CheckResult is what every deterministic check returns.
DimensionResult aggregates the checks for one of the six dimensions into a
1-4 score and a set of evidence strings. ScorecardResult is the final output
of a full scan.

None on a numeric field always means "could not determine" - never silently
zero.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CheckResult:
    id: str
    description: str
    passed: bool
    evidence: str
    score_contribution: int   # 0, 1, or 2 - weight of this check toward dimension score


@dataclass
class DimensionResult:
    id: str
    name: str
    level: int                         # 1-4
    check_results: list[CheckResult] = field(default_factory=list)
    legibility_note: Optional[str] = None   # only set for interface_legibility dimension, from LLM pass
    insufficient_data: bool = False


@dataclass
class ScorecardResult:
    target: str
    dimensions: list[DimensionResult] = field(default_factory=list)
    overall_level: Optional[int] = None
    scan_errors: list[str] = field(default_factory=list)
    legibility_enabled: bool = False
