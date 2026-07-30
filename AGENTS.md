# AGENTS.md

## What this repo is

A config-driven scorer that evaluates whether an API's write and read surface
is ready for AI agent use, across six dimensions.
See `README.md` for the full description and `docs/article.md` for the
editorial treatment.

## Essential commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run scorer against the Clario Example (no credentials needed)
python -m framework.cli scan \
  --config examples/clario/config.yaml \
  --target examples/clario

# Validate a config without scanning
python -m framework.cli validate --config examples/clario/config.yaml

# Run tests (no credentials needed)
python -m pytest tests/ -v
```

## Where things live

- `framework/checks/` - one file per dimension; each exports a `check_<dim>(target_dir, dim_config)` function that returns a `list[CheckResult]`.
- `framework/scoring/engine.py` - maps check results to 1-4 levels; overall level is the minimum across all dimensions.
- `framework/legibility/` - optional LLM pass for Interface Legibility; off by default, requires `ANTHROPIC_API_KEY` when enabled.
- `framework/scanner.py` - orchestrates the full scan and applies the legibility pass if configured.
- `framework/cli.py` - `scan` and `validate` commands. `scan --dashboard-data <path>` emits the scorecard as `window.MCP_READINESS_DATA = {...};` for `docs/dashboard.html`.
- `examples/clario/` - fictional Clario Example with deliberate, documented gaps.
- `tests/` - fixture-driven tests; `tests/fixtures/full_coverage/` and `tests/fixtures/no_coverage/` are synthetic codebases used by unit tests.
- `docs/dashboard.html` - single-file, no-build dashboard for the scorecard; ships with the Clario Example's real scorecard baked in as sample data, overridden by a sibling `docs/dashboard-data.js` if present (not committed - generated via `scan --dashboard-data`). `index.html` at repo root redirects to it.

## Key design rules

- `conftest.py` at repo root excludes `tests/fixtures/**` and `examples/**` from pytest collection.
- Deterministic check patterns must require actual implementation evidence (e.g., a variable assignment), not just a keyword in a comment. False positives in the check patterns are the main source of test failures.
- The minimum rule is intentional and must not be changed to an average: overall level = `min(dimension levels)`.
- The LLM pass receives only OpenAPI spec content; it never sees source code.

## Adding checks

1. Edit `framework/checks/<dimension>.py` and append a `CheckResult` to the returned list.
2. Add `full_coverage` and `no_coverage` fixture files that demonstrate pass and fail.
3. Add a test in `tests/test_<dimension>.py`.
4. Run `python -m pytest tests/ -v` before committing.

## Maintaining this file

Update this file when:
- New dimensions are added or renamed.
- The CLI interface changes (new commands or flags).
- The overall architecture changes (e.g., new check types or scoring strategies).

Do not duplicate content already in `README.md` - link to it instead.
Do not record ephemeral state (in-progress branches, recent fixes) here.
