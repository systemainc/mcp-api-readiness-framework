"""
Shared utilities for deterministic checks.

grep_files returns all matching lines (with file paths) for a pattern across
the target directory, filtered by a glob. Used by every dimension check.
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Optional


def grep_files(
    target_dir: str,
    pattern: str,
    file_glob: str = "**/*",
    max_results: int = 200,
) -> list[tuple[str, int, str]]:
    """Return [(rel_path, line_no, line)] for every match."""
    root = Path(target_dir)
    matches: list[tuple[str, int, str]] = []
    try:
        compiled = re.compile(pattern)
    except re.error:
        return []

    for path in root.glob(file_glob):
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if compiled.search(line):
                matches.append((str(path.relative_to(root)), i, line.strip()))
                if len(matches) >= max_results:
                    return matches
    return matches


def file_exists(target_dir: str, *rel_paths: str) -> Optional[str]:
    """Return the first path that exists relative to target_dir, or None."""
    root = Path(target_dir)
    for rel in rel_paths:
        candidate = root / rel
        if candidate.exists():
            return str(candidate.relative_to(root))
    return None


def glob_exists(target_dir: str, glob: str) -> list[str]:
    """Return relative paths for all files matching glob under target_dir."""
    root = Path(target_dir)
    return [str(p.relative_to(root)) for p in root.glob(glob) if p.is_file()]
