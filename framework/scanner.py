"""
Scanner orchestrator: config + target_dir -> ScorecardResult.

One broken check set should not take down the whole scan. Each dimension
runs independently; failures are collected and reported in scan_errors
rather than aborting. A dimension that raises an unexpected error is
reported as Level 1 with insufficient_data=True.

The LLM pass (legibility assessment) follows the same policy: if it fails
or is disabled, the deterministic legibility checks still report their
findings. The note field is simply absent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from .checks import DIMENSION_CHECKS
from .config import Config, load_config
from .legibility import build_provider
from .legibility.prompt import build_legibility_prompt
from .schema import DimensionResult, ScorecardResult
from .scoring.engine import score_dimension, compute_overall


def _extract_openapi_samples(target_dir: str, config: Config):
    """Pull a sample of operation and error descriptions from OpenAPI files."""
    operation_samples = []
    error_samples = []
    try:
        import yaml
    except ImportError:
        return operation_samples, error_samples

    for rel_path in config.openapi_paths:
        path = Path(target_dir) / rel_path
        if not path.exists():
            # also try glob
            matches = list(Path(target_dir).glob(rel_path))
            if not matches:
                continue
            path = matches[0]
        try:
            with open(path) as f:
                spec = yaml.safe_load(f)
        except Exception:
            continue

        paths = spec.get("paths", {})
        for path_str, methods in paths.items():
            for method, op in methods.items():
                if not isinstance(op, dict):
                    continue
                operation_samples.append({
                    "path": f"{method.upper()} {path_str}",
                    "operationId": op.get("operationId"),
                    "summary": op.get("summary"),
                    "description": op.get("description"),
                })
                for status, resp in op.get("responses", {}).items():
                    if str(status).startswith(("4", "5")):
                        error_samples.append({
                            "status": status,
                            "description": resp.get("description") if isinstance(resp, dict) else None,
                        })

    return operation_samples, error_samples


def run_scan(config_path: str, target_dir: str) -> ScorecardResult:
    config = load_config(config_path)
    scorecard = ScorecardResult(
        target=config.target_name,
        legibility_enabled=config.legibility.enabled,
    )

    dim_config_by_id = {d.id: d for d in config.dimensions}

    for dim_id, check_fn in DIMENSION_CHECKS.items():
        dim_config = dim_config_by_id.get(dim_id, None)
        dim_name = dim_config.name if dim_config else dim_id.replace("_", " ").title()
        try:
            checks = check_fn(target_dir, dim_config.__dict__ if dim_config else {})
            dim_result = score_dimension(dim_id, dim_name, checks)
        except Exception as e:  # noqa: BLE001
            msg = f"{dim_id}: {e}"
            scorecard.scan_errors.append(msg)
            print(f"[warn] dimension scan failed, reporting as Level 1 - {msg}", file=sys.stderr)
            dim_result = DimensionResult(
                id=dim_id,
                name=dim_name,
                level=1,
                insufficient_data=True,
            )
        scorecard.dimensions.append(dim_result)

    # LLM pass for interface legibility (optional)
    if config.legibility.enabled:
        try:
            provider = build_provider(
                config.legibility.provider,
                {
                    "model": config.legibility.model,
                    "api_key_env": config.legibility.api_key_env,
                    "max_tokens": config.legibility.max_tokens,
                },
            )
            op_samples, err_samples = _extract_openapi_samples(target_dir, config)
            prompt = build_legibility_prompt(config.target_name, op_samples, err_samples)
            note = provider.assess(prompt)
            leg_dim = next(
                (d for d in scorecard.dimensions if d.id == "interface_legibility"), None
            )
            if leg_dim:
                leg_dim.legibility_note = note
        except Exception as e:  # noqa: BLE001
            msg = f"legibility LLM pass: {e}"
            scorecard.scan_errors.append(msg)
            print(f"[warn] legibility assessment skipped - {msg}", file=sys.stderr)

    scorecard.overall_level = compute_overall(scorecard)
    return scorecard
