"""
Dimension 6 - Operational Containment

Agents don't slow down when they're confused - they retry. Without
per-tool timeouts, per-token rate limits, and size caps on inputs, one
poorly-prompted agent session can DoS a shared API surface. This dimension
checks that every tool call is bounded, and that the API is aware it may
be receiving untrusted input via an agent's interpolated context.
"""
from __future__ import annotations

from ..schema import CheckResult
from ._util import grep_files


def check_operational_containment(target_dir: str, dim_config: dict) -> list[CheckResult]:
    results = []

    # Check 1: per-endpoint/tool timeout configuration
    timeout_hits = grep_files(
        target_dir,
        r"timeout|TIMEOUT|request_timeout|tool_timeout|deadline|max_duration",
        "**/*.py",
    )
    results.append(CheckResult(
        id="operational_containment.timeouts",
        description="Timeout configuration present at tool/endpoint level",
        passed=len(timeout_hits) > 0,
        evidence=(
            f"Found {len(timeout_hits)} reference(s): {timeout_hits[0][0]}:{timeout_hits[0][1]}"
            if timeout_hits
            else "No timeout configuration found; runaway agent calls have no ceiling"
        ),
        score_contribution=2,
    ))

    # Check 2: rate limiting / quota per token or per agent session
    ratelimit_hits = grep_files(
        target_dir,
        r"RateLimiter|rate_limiter\(|@rate_limit|RateLimit\(|apply_throttle|check_quota|enforce_quota|requests_per_minute|rpm_limit",
        "**/*.py",
    )
    results.append(CheckResult(
        id="operational_containment.rate_limits",
        description="Rate limiting or quota enforcement present",
        passed=len(ratelimit_hits) > 0,
        evidence=(
            f"Found {len(ratelimit_hits)} reference(s): {ratelimit_hits[0][0]}:{ratelimit_hits[0][1]}"
            if ratelimit_hits
            else "No rate limiting or quota found; a looping agent can exhaust resources"
        ),
        score_contribution=2,
    ))

    # Check 3: input size cap / payload validation
    size_cap_hits = grep_files(
        target_dir,
        r"max_length=|MAX_LENGTH\s*=|max_size=|MAX_SIZE\s*=|max_body_size|content_length_limit|payload_size_limit|MAX_PAYLOAD",
        "**/*.py",
    )
    results.append(CheckResult(
        id="operational_containment.input_size_cap",
        description="Input size cap or payload size validation present",
        passed=len(size_cap_hits) > 0,
        evidence=(
            f"Found {len(size_cap_hits)} reference(s): {size_cap_hits[0][0]}:{size_cap_hits[0][1]}"
            if size_cap_hits
            else "No input size cap found; agent-interpolated context could be arbitrarily large"
        ),
        score_contribution=1,
    ))

    # Check 4: untrusted-input surface awareness (prompt injection / content validation)
    untrusted_hits = grep_files(
        target_dir,
        r"sanitize|sanitise|strip_html|validate_content|content.filter|injection|prompt.injection|untrusted.input",
        "**/*.py",
    )
    results.append(CheckResult(
        id="operational_containment.untrusted_input",
        description="Awareness of untrusted / agent-interpolated input surfaces (sanitization, content validation)",
        passed=len(untrusted_hits) > 0,
        evidence=(
            f"Found {len(untrusted_hits)} reference(s): {untrusted_hits[0][0]}:{untrusted_hits[0][1]}"
            if untrusted_hits
            else "No untrusted-input handling found; agent-interpolated strings accepted verbatim"
        ),
        score_contribution=1,
    ))

    return results
