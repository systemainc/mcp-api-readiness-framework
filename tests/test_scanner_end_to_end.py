"""End-to-end scan tests against the Clario example - no live credentials."""
import os
import pytest
from framework.scanner import run_scan

CLARIO_CONFIG = os.path.join(
    os.path.dirname(__file__), "..", "examples", "clario", "config.yaml"
)
CLARIO_DIR = os.path.join(os.path.dirname(__file__), "..", "examples", "clario")


def _dim(scorecard, dim_id):
    return next(d for d in scorecard.dimensions if d.id == dim_id)


def test_scan_produces_all_six_dimensions():
    scorecard = run_scan(CLARIO_CONFIG, CLARIO_DIR)
    dim_ids = {d.id for d in scorecard.dimensions}
    assert dim_ids == {
        "write_safety",
        "boundary_enforcement",
        "consent_auth",
        "forensics",
        "interface_legibility",
        "operational_containment",
    }


def test_scan_has_no_scan_errors():
    scorecard = run_scan(CLARIO_CONFIG, CLARIO_DIR)
    assert scorecard.scan_errors == []


def test_overall_level_is_minimum():
    scorecard = run_scan(CLARIO_CONFIG, CLARIO_DIR)
    dim_levels = [d.level for d in scorecard.dimensions]
    assert scorecard.overall_level == min(dim_levels)


def test_all_dimension_levels_in_range():
    scorecard = run_scan(CLARIO_CONFIG, CLARIO_DIR)
    for dim in scorecard.dimensions:
        assert 1 <= dim.level <= 4, f"{dim.id} level {dim.level} out of range"


def test_write_safety_not_level_4():
    """Clario's write safety has gaps (no dedup store, no idempotency tests)."""
    scorecard = run_scan(CLARIO_CONFIG, CLARIO_DIR)
    ws = _dim(scorecard, "write_safety")
    assert ws.level < 4


def test_boundary_enforcement_not_level_4():
    """Clario has no adversarial cross-tenant tests."""
    scorecard = run_scan(CLARIO_CONFIG, CLARIO_DIR)
    be = _dim(scorecard, "boundary_enforcement")
    assert be.level < 4


def test_operational_containment_is_low():
    """Clario has no timeouts, rate limits, size caps, or untrusted-input handling."""
    scorecard = run_scan(CLARIO_CONFIG, CLARIO_DIR)
    oc = _dim(scorecard, "operational_containment")
    assert oc.level <= 2


def test_legibility_not_enabled_means_no_note():
    """LLM pass is off in Clario config; legibility_note stays None."""
    scorecard = run_scan(CLARIO_CONFIG, CLARIO_DIR)
    leg = _dim(scorecard, "interface_legibility")
    assert leg.legibility_note is None
