"""
Config loader for mcp-api-readiness-framework.

One YAML file is the only thing you change to point the scorer at a different
codebase. All thresholds, patterns, and the LLM pass toggle live here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class PatternConfig:
    """A grep pattern used by a deterministic check."""
    pattern: str
    description: str
    file_glob: str = "**/*"


@dataclass
class DimensionConfig:
    id: str
    name: str
    checks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class LegibilityConfig:
    enabled: bool = False
    provider: str = "anthropic"
    model: str = "claude-sonnet-5"
    api_key_env: str = "ANTHROPIC_API_KEY"
    max_tokens: int = 300


@dataclass
class Config:
    target_name: str
    dimensions: list[DimensionConfig]
    legibility: LegibilityConfig
    openapi_paths: list[str] = field(default_factory=list)
    test_path_glob: str = "tests/**/*.py"
    source_path_glob: str = "**/*.py"


def load_config(path: str) -> Config:
    with open(path) as f:
        raw = yaml.safe_load(f)

    leg_raw = raw.get("legibility", {})
    legibility = LegibilityConfig(
        enabled=leg_raw.get("enabled", False),
        provider=leg_raw.get("provider", "anthropic"),
        model=leg_raw.get("model", "claude-sonnet-5"),
        api_key_env=leg_raw.get("api_key_env", "ANTHROPIC_API_KEY"),
        max_tokens=leg_raw.get("max_tokens", 300),
    )

    dimensions = []
    for dim in raw.get("dimensions", []):
        dimensions.append(DimensionConfig(
            id=dim["id"],
            name=dim["name"],
            checks=dim.get("checks", []),
        ))

    return Config(
        target_name=raw.get("target_name", "unknown"),
        dimensions=dimensions,
        legibility=legibility,
        openapi_paths=raw.get("openapi_paths", []),
        test_path_glob=raw.get("test_path_glob", "tests/**/*.py"),
        source_path_glob=raw.get("source_path_glob", "**/*.py"),
    )
