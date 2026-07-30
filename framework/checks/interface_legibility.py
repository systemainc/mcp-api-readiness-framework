"""
Dimension 5 - Interface Legibility

Tool descriptions and error messages need to work for an agent, not a
human reading documentation. An agent acts on what it can read. Vague
descriptions cause hallucinated parameters; generic error messages cause
retry storms or silent wrong-path execution.

This dimension has two layers:
- Deterministic: checks that OpenAPI descriptions exist and that a machine-
  readable error schema is present.
- LLM pass (optional): reads the actual tool descriptions and error messages
  from the spec and judges whether they are specific enough for an agent to
  act on correctly. The model phrases - it does not decide.
"""
from __future__ import annotations

from pathlib import Path

from ..schema import CheckResult
from ._util import grep_files, glob_exists


def check_interface_legibility(target_dir: str, dim_config: dict) -> list[CheckResult]:
    results = []

    # Check 1: OpenAPI / tool schema present
    openapi_files = (
        glob_exists(target_dir, "openapi.yaml")
        + glob_exists(target_dir, "openapi.json")
        + glob_exists(target_dir, "**/openapi.yaml")
        + glob_exists(target_dir, "**/openapi.json")
        + glob_exists(target_dir, "**/*openapi*.yaml")
        + glob_exists(target_dir, "**/*openapi*.json")
    )
    # deduplicate
    seen = set()
    openapi_files = [f for f in openapi_files if not (f in seen or seen.add(f))]

    results.append(CheckResult(
        id="interface_legibility.openapi_present",
        description="OpenAPI or tool schema file present",
        passed=len(openapi_files) > 0,
        evidence=(
            f"Found schema at: {openapi_files[0]}"
            if openapi_files
            else "No OpenAPI/tool schema found; agent has no machine-readable interface contract"
        ),
        score_contribution=2,
    ))

    # Check 2: operation descriptions present (not just names/summaries)
    description_hits = []
    for rel_path in openapi_files:
        try:
            content = (Path(target_dir) / rel_path).read_text(errors="replace")
            if "description:" in content or '"description"' in content:
                description_hits.append(rel_path)
        except OSError:
            pass

    results.append(CheckResult(
        id="interface_legibility.operation_descriptions",
        description="Operation descriptions present in schema (not just names/summaries)",
        passed=len(description_hits) > 0,
        evidence=(
            f"Descriptions found in: {description_hits[0]}"
            if description_hits
            else "Schema files present but no operation descriptions found"
        ),
        score_contribution=2,
    ))

    # Check 3: structured error schema with error codes
    error_schema_hits = grep_files(
        target_dir,
        r"error_code|error\.code|\"code\".*error|errorCode|ErrorCode|machine_readable",
        "**/*.py",
    ) + grep_files(
        target_dir,
        r"error_code|errorCode|\"code\"",
        "**/*.yaml",
    )
    results.append(CheckResult(
        id="interface_legibility.structured_errors",
        description="Structured error schema with machine-readable error codes present",
        passed=len(error_schema_hits) > 0,
        evidence=(
            f"Found {len(error_schema_hits)} reference(s): {error_schema_hits[0][0]}:{error_schema_hits[0][1]}"
            if error_schema_hits
            else "No structured error codes found; agents receive only human-readable error strings"
        ),
        score_contribution=2,
    ))

    # Check 4: versioning / deprecation signals
    version_hits = grep_files(
        target_dir,
        r"deprecated|Deprecated|x-deprecated|sunset|X-Sunset|api.version|version.*header",
        "**/*.py",
    ) + grep_files(
        target_dir,
        r"deprecated|x-sunset|x-deprecation",
        "**/*.yaml",
    )
    results.append(CheckResult(
        id="interface_legibility.versioning",
        description="Deprecation or versioning signals present (agents can detect breaking changes)",
        passed=len(version_hits) > 0,
        evidence=(
            f"Found {len(version_hits)} reference(s): {version_hits[0][0]}:{version_hits[0][1]}"
            if version_hits
            else "No versioning or deprecation signals found"
        ),
        score_contribution=1,
    ))

    return results
