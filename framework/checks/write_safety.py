"""
Dimension 1 - Write Safety

Checks whether mutating tool calls are safe for agent retries:
idempotency-key headers, deduplication windows, and conditional-request
patterns. An agent that retries a timed-out write call MUST NOT accidentally
double-charge, double-book, or double-send.
"""
from __future__ import annotations

from ..schema import CheckResult
from ._util import grep_files, glob_exists


def check_write_safety(target_dir: str, dim_config: dict) -> list[CheckResult]:
    results = []

    # Check 1: idempotency key header on mutating routes
    idempotency_hits = grep_files(
        target_dir,
        r"[Ii]dempotency[_-]?[Kk]ey|idempotency_key|IdempotencyKey",
        "**/*.py",
    )
    results.append(CheckResult(
        id="write_safety.idempotency_key",
        description="Idempotency-Key header referenced in source",
        passed=len(idempotency_hits) > 0,
        evidence=(
            f"Found {len(idempotency_hits)} reference(s): {idempotency_hits[0][0]}:{idempotency_hits[0][1]}"
            if idempotency_hits
            else "No Idempotency-Key references found in source"
        ),
        score_contribution=2,
    ))

    # Check 2: deduplication window / dedup store
    dedup_hits = grep_files(
        target_dir,
        r"idempotency_store\s*=|dedup_store\s*=|idempotency_cache\s*=|seen_keys\s*=|_dedup_window\s*=|already_processed\s*=",
        "**/*.py",
    )
    results.append(CheckResult(
        id="write_safety.dedup_window",
        description="Deduplication store or window present",
        passed=len(dedup_hits) > 0,
        evidence=(
            f"Found {len(dedup_hits)} reference(s): {dedup_hits[0][0]}:{dedup_hits[0][1]}"
            if dedup_hits
            else "No deduplication window found - retried writes may be applied twice"
        ),
        score_contribution=2,
    ))

    # Check 3: conditional request guards (ETag / If-Match / optimistic locking)
    conditional_hits = grep_files(
        target_dir,
        r"If-Match|ETag|etag|optimistic.lock|version_check|precondition",
        "**/*.py",
    )
    results.append(CheckResult(
        id="write_safety.conditional_requests",
        description="Conditional-request guard (ETag / If-Match / optimistic lock) present",
        passed=len(conditional_hits) > 0,
        evidence=(
            f"Found {len(conditional_hits)} reference(s): {conditional_hits[0][0]}:{conditional_hits[0][1]}"
            if conditional_hits
            else "No conditional-request guard found; concurrent agent writes may corrupt state"
        ),
        score_contribution=1,
    ))

    # Check 4: tests cover the duplicate-request path
    dedup_test_hits = grep_files(
        target_dir,
        r"def test.*duplicate|def test.*idempotent|def test.*retry_safe|def test.*same_key",
        "**/*.py",
    )
    results.append(CheckResult(
        id="write_safety.idempotency_tests",
        description="Tests explicitly cover duplicate / idempotent request behavior",
        passed=len(dedup_test_hits) > 0,
        evidence=(
            f"Found {len(dedup_test_hits)} test(s): {dedup_test_hits[0][0]}:{dedup_test_hits[0][1]}"
            if dedup_test_hits
            else "No idempotency/duplicate-request tests found"
        ),
        score_contribution=1,
    ))

    return results
