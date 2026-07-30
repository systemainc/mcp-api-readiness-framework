# MCP API Readiness Framework

A config-driven tool that scores whether an API's write and read surface is
actually ready to be called by an AI agent - not just whether it has an
OpenAPI spec.

This is the third entry in a series on measurable AI engineering maturity.
See also: [ai-engineering-maturity-metrics-framework](https://github.com/systemainc/ai-engineering-maturity-metrics-framework)
and [loop-engineering-tutorial](https://github.com/systemainc/loop-engineering-tutorial).

---

## The problem

Most API teams discover their agent-readiness gap the first time an agent
causes an incident - a duplicate invoice created by a retry, a cross-account
data leak from a missing scope check, a support ticket storm from an error
message that reads `Something went wrong` and tells an agent nothing.

The pattern is predictable: the team wraps the API in an MCP server, the
demo works, and six weeks later something breaks in production in a way that
the existing test suite did not and could not have caught.

The root cause is almost never the MCP wrapper.
It is always a property of the underlying API that was invisible until an
agent - with its retry loops, parallel calls, untrusted input interpolation,
and lack of human judgment about "does this seem right?" - started calling it.

## Why OpenAPI alone is not enough

Adding an OpenAPI spec is the right first move.
It is not the last.

A spec tells an agent what parameters a tool accepts.
It does not tell the agent what happens if it retries a write call that timed out.
It does not prove that a token issued to agent A cannot access agent B's data.
It does not guarantee that a `422 Unprocessable Entity` response contains
enough information for the agent to decide whether to fix its input, escalate,
or abort the workflow.

These gaps are not addressable at the wrapper layer.
They require changes to the underlying API.
The framework gives you a scorecard that identifies exactly which changes are
missing and provides evidence to back the finding.

## Architecture

```
config.yaml + target codebase
        │
        ▼
  six dimension checks (deterministic grep-based scans)
        │
        ├─▶ Write Safety
        ├─▶ Boundary Enforcement
        ├─▶ Consent & Auth Surface
        ├─▶ Forensics
        ├─▶ Interface Legibility  ──▶  optional: one bounded LLM pass
        └─▶ Operational Containment
        │
        ▼
  scoring engine (weighted pass/fail → 1-4 per dimension)
        │
        ▼
  scorecard (overall level = minimum across all six dimensions)
```

**Deterministic checks** grep the target codebase for patterns that are
mechanically verifiable: is an idempotency store referenced?
Does a test function explicitly test cross-tenant access rejection?
Is an OpenAPI `securitySchemes` block present?

**One bounded LLM pass** (optional, off by default) reads the actual tool
descriptions and error messages from the OpenAPI spec and assesses whether
they are specific enough for an agent to act on correctly.
The model phrases observations - it does not invent scores or facts it was not given.

**Scoring** maps the weighted sum of passed checks to a 1-4 level per
dimension.
The overall score is the minimum across all six - a score of 4 on five
dimensions with a 1 on Boundary Enforcement is not "mostly ready," it is a
liability.

## The six dimensions

| # | Dimension | The agent-specific risk if this is missing |
|---|-----------|-------------------------------------------|
| 1 | **Write Safety** | A retry creates a duplicate record, charge, or notification |
| 2 | **Boundary Enforcement** | An agent using tenant A's token reads or modifies tenant B's data |
| 3 | **Consent & Auth Surface** | An agent cannot acquire minimum-necessary permission; it either gets admin rights or nothing |
| 4 | **Forensics** | When an agent causes an incident, you cannot reconstruct what it called or why |
| 5 | **Interface Legibility** | Vague tool descriptions cause hallucinated parameters; generic errors cause retry storms |
| 6 | **Operational Containment** | A looping agent DoS's a shared API; untrusted input passes unchecked into storage |

## Maturity levels

| Level | Label | What it means |
|-------|-------|---------------|
| 1 | Not Ready | Critical gaps that will cause incidents in production |
| 2 | Partial | Core mechanisms present but unverified or inconsistently applied |
| 3 | Capable | Solid foundation with known gaps that limit safe agent scope |
| 4 | Robust | Proactively defended; agent calls are safe, auditable, and bounded |

The level for each dimension is determined by the weighted fraction of checks
that pass.
The overall level is the minimum across all dimensions.

## Quick start

```bash
git clone https://github.com/systemainc/mcp-api-readiness-framework
cd mcp-api-readiness-framework
pip install -r requirements.txt

# Run against the Clario Example (no credentials needed)
python -m framework.cli scan \
  --config examples/clario/config.yaml \
  --target examples/clario

# Validate a config file
python -m framework.cli validate --config examples/clario/config.yaml

# Write scorecard to JSON
python -m framework.cli scan \
  --config examples/clario/config.yaml \
  --target examples/clario \
  --output out/clario-scorecard.json
```

## Point it at your own codebase

1. Copy `examples/clario/config.yaml` to your project root as `agent-readiness.yaml`.
2. Set `target_name` to your API's name.
3. Set `openapi_paths` to the relative path of your OpenAPI spec (or leave
   empty to skip spec-based checks).
4. Run: `python -m framework.cli scan --config agent-readiness.yaml --target /path/to/your/api`

The scanner expects Python source files by default.
The `source_path_glob` and `test_path_glob` fields in the config control
which files are searched.
The patterns are tuned for common conventions; see `framework/checks/` for
the full set and extend as needed for your stack.

## The optional LLM pass

To enable the legibility assessment:

```yaml
legibility:
  enabled: true
  provider: anthropic
  model: claude-sonnet-5
  api_key_env: ANTHROPIC_API_KEY
  max_tokens: 300
```

Then: `export ANTHROPIC_API_KEY=your_key`

The model is given only what is in your OpenAPI spec's operation descriptions
and error response descriptions.
It cannot see your source code, your business logic, or anything beyond what
you provide.
Its output appears as a `[Legibility assessment]` note under the Interface
Legibility dimension.

## Clario Example

`examples/clario/` is a deliberately minimal fictional B2B expense-management
and invoicing API with realistic gaps across several dimensions.
Running the scorer against it produces:

```
  [2/4] Write Safety
         [PASS] Idempotency-Key header referenced in source
         [FAIL] Deduplication store or window present
         [FAIL] Conditional-request guard (ETag / If-Match / optimistic lock) present
         [FAIL] Tests explicitly cover duplicate / idempotent request behavior

  [3/4] Boundary Enforcement
         [PASS] Tenant/org/account ID filter present in source
         [PASS] Role/permission enforcement present in source
         [FAIL] Adversarial negative tests prove cross-tenant access is rejected
         [PASS] Token/credential scope is validated at the handler level

  [4/4] Consent & Auth Surface
  [3/4] Forensics
         [PASS] Correlation/trace/request ID propagated in source
         [PASS] Audit log or event emission present on write paths
         [FAIL] Failure and rejection paths are also captured in audit trail
         [PASS] Actor identity (agent/user/service) recorded alongside each audited action

  [4/4] Interface Legibility

  [1/4] Operational Containment
         [FAIL] Timeout configuration present at tool/endpoint level
         [FAIL] Rate limiting or quota enforcement present
         [FAIL] Input size cap or payload size validation present
         [FAIL] Awareness of untrusted / agent-interpolated input surfaces (sanitization, content validation)

  Overall Level: 1/4 — Not Ready
```

The overall score is 1 because Operational Containment is 1 - the minimum
rule prevents a good score on other dimensions from masking a critical gap.
The Clario Example is documented in detail in `docs/article.md`.

## Running the tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

No credentials required.
All tests use fixture-driven data in `tests/fixtures/` and the
Clario Example in `examples/clario/`.

## Extending the framework

To add or tighten a check within an existing dimension:

1. Edit `framework/checks/<dimension>.py` - add a `CheckResult` to the list.
2. Add a matching fixture (pass case and fail case) to `tests/fixtures/`.
3. Add a test in `tests/test_<dimension>.py`.

To add a new dimension:

1. Create `framework/checks/my_dimension.py` with a `check_my_dimension(target_dir, dim_config)` function.
2. Register it in `framework/checks/__init__.py`.
3. Add it to your config under `dimensions:`.

The scorer picks up the new dimension automatically - the config's `dimensions`
list controls which checks run and what they're called in the scorecard.
