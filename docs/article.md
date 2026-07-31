# Do you think your APIs are ready for MCP exposure?

The MCP API Readiness Framework is a tool I built and am open-sourcing.
It scores your API against six dimensions and tells you exactly which gaps
you need to close before you expose it as callable MCP tools in production.
This post walks through a real scored example, explains what the scoring
actually checks, and shows you what the gaps look like in code.

**Code: [github.com/systemainc/mcp-api-readiness-framework](https://github.com/systemainc/mcp-api-readiness-framework)** — MIT licensed, full scorer and dashboard, no waitlist.

You wrapped your API in an MCP server.
The demo worked.
You shipped it.

Six weeks later, an agent created 47 duplicate invoices during a retry storm
and nobody could figure out which calls caused it because the audit log only
records successes.

This is the conversation I keep having with engineering teams doing the right
thing -- building agent-callable interfaces to their APIs -- who still get
bitten because these gaps are invisible until an agent, not a human, starts
calling the API.

The problem is not the MCP wrapper.
It is almost never the MCP wrapper.
The problem is a set of properties that every production API needs before an
agent can safely call it, which OpenAPI specs do not capture, which existing
tests do not cover, and which are genuinely invisible until an agent -
with its retry loops, parallel calls, and lack of human judgment - hits them.

---

## The pattern every team hits

The sequence goes like this.

A developer discovers that their existing REST API, already documented with
OpenAPI, can be turned into a set of callable tools with relatively little
effort.
They write an MCP server (or use an auto-generated one), test it manually,
and the happy path works great.
The agent creates invoices, submits expenses, reads reports.
Demos are clean.
The team ships it.

Then one of a small number of predictable things happens:

**The retry incident.**
The agent calls `POST /invoices` and the response times out at the network
level.
The request actually landed - the invoice was created - but the agent doesn't
know that.
It retries.
Now there are two invoices.
The agent retries again because it still got no confirmation.
Finance notices a week later.

**The scope-creep incident.**
An agent authorized to read one customer's expense reports turns out to also
be able to read every other customer's expense reports, because the endpoint
was filtering by user session (which was always scoped) but the API token
issued to the agent was not, and nobody tested what happened when you used
a token to call an endpoint that was designed to be called with a session.

**The error storm.**
The agent hits a validation error.
The error message says `Unprocessable entity.`
The agent has no idea whether it should retry with different parameters, retry
later, or stop.
It retries with the same parameters, in a loop, for twenty minutes.

None of these are MCP problems.
None of them are agent problems.
They are API properties - missing idempotency enforcement, missing cross-token
scope tests, missing structured error codes - that were always there, but
only visible to an automated caller that doesn't slow down when it's confused.

---

## The caller has changed

Your API was built for two kinds of callers: a human clicking through a UI, or a script a developer wrote and tested for a specific integration.

In the UI case, a human was present on every response.
They looked at what came back before anything happened next.
When something seemed off, they stopped.
The edge cases that were never quite right stayed hidden, because a human would have noticed before clicking again.

In the script case, a developer wrote exactly the calls the integration needed, in the order they tested, and the script ran that sequence.
It didn't improvise.
It called what the developer told it to call.

An agent does neither.

It generates calls dynamically, based on its current understanding of the task, which may be incomplete or just wrong in ways that only surface several calls in.
It doesn't follow a fixed sequence.
It decides what to call next from what the previous response said, and it can reach endpoints in orders and combinations no one scripted or tested.

When a call times out, it doesn't know whether the write landed.
It retries.
Not because it checked, because retrying is what it does.

When a response comes back with a status it doesn't recognize, it doesn't pause to ask anyone.
It interprets what it can and keeps going, at machine speed, potentially running the same bad call hundreds of times before anything triggers an alert.

The parameters it passes may include content it retrieved earlier in the task, from a search result, a document, or a user's message.
Content you don't control, that may have been crafted to influence what the agent does next.

That's a different caller than the ones your API was designed for.
The gaps this framework checks for are exactly the ones that stay invisible until this kind of caller shows up.

---

## Why "just add OpenAPI" isn't enough

OpenAPI specs are necessary and good.
They tell the agent what parameters a tool accepts, what responses look like,
and what security scheme is in use.
That is a lot of information that was previously implicit.

But a spec is a contract, not a proof.
It tells you what the API is supposed to do.
It does not tell you:

- What happens when a write call is retried after a timeout.
- Whether the scope encoded in a bearer token is actually enforced at the
  handler level, or whether it was only enforced at the session level and
  nobody tested the token path.
- Whether `403 Forbidden` in the response body includes an error code that
  an agent can act on, or just a message string written for a human to read.
- Whether there is any per-tool timeout, so that a slow tool call can be
  aborted rather than blocking an agent's execution indefinitely.

These are not documentation gaps.
They are implementation gaps.
The framework checks for them mechanically, in code.

---

## Scoring the Clario Example

The framework ships with a Clario Example, a fictional B2B
expense-management and invoicing API.
Clario is a deliberate teaching tool - it has an OpenAPI spec, scoped tokens,
tenant isolation, and an audit log.
It also has four specific gaps that a team building agent tooling would
typically miss, because they are invisible to human callers but hazardous
to automated ones.

Here is the scorecard:

```
  MCP API Readiness: Clario Expense & Invoicing API
  Overall Level: 1/4 — Not Ready

  Write Safety
    Level 2/4 — Partial (weighted score)   Checks passed: 1/6
         [PASS] Idempotency-Key header referenced in source
           Found 5 reference(s): api/expenses.py:7
         [FAIL] Deduplication store or window present
           No deduplication window found - retried writes may be applied twice
         [FAIL] Conditional-request guard (ETag / If-Match / optimistic lock) present
           No conditional-request guard found; concurrent agent writes may corrupt state
         [FAIL] Tests explicitly cover duplicate / idempotent request behavior
           No idempotency/duplicate-request tests found
         [FAIL] Deduplication window has a bounded TTL/expiry
           No TTL/expiry found on the dedup store - it can grow unbounded and never ages out old keys
         [FAIL] Multi-step writes have compensating/rollback handling
           No transaction/rollback/compensation handling found - a write spanning multiple resources can fail halfway with no recovery

  Boundary Enforcement
    Level 3/4 — Capable (weighted score)   Checks passed: 4/6
         [PASS] Tenant/org/account ID filter present in source
           Found 22 reference(s): tests/test_expenses.py:14
         [PASS] Role/permission enforcement present in source
           Found 12 reference(s): api/auth.py:49
         [FAIL] Adversarial negative tests prove cross-tenant access is rejected
           No adversarial cross-tenant tests found - isolation is asserted, not proven
         [PASS] Token/credential scope is validated at the handler level
           Found 3 reference(s): api/auth.py:57
         [PASS] Direct object lookups (single-resource GET/PATCH/DELETE) verify ownership
           Found 4 reference(s): api/expenses.py:65
         [FAIL] Bulk/export endpoints are tenant-scoped and row-capped
           No bulk/export/batch handler found with tenant scoping and a row cap

  Consent & Auth Surface
    Level 3/4 — Capable (weighted score)   Checks passed: 3/6
         [PASS] Scoped / least-privilege token pattern present
           Found 2 reference(s): api/auth.py:57
         [PASS] Auth metadata is machine-discoverable (OpenAPI securitySchemes or equivalent)
           Found auth metadata in: openapi.yaml
         [PASS] Per-tool or per-endpoint permission declaration present
           Found 8 reference(s): api/expenses.py:29
         [FAIL] Token expiry or rotation mechanism present
           No token expiry or rotation mechanism found
         [FAIL] Explicit token/session revocation mechanism present
           No revocation mechanism found - a compromised token can only be waited out, not killed
         [FAIL] Step-up confirmation required before destructive actions
           No step-up/reauth pattern found - destructive actions require no more confirmation than a routine read

  Forensics
    Level 3/4 — Capable (weighted score)   Checks passed: 4/6
         [PASS] Correlation/trace/request ID propagated in source
           Found 4 reference(s): api/audit.py:5
         [PASS] Audit log or event emission present on write paths
           Found 9 reference(s): tests/test_invoices.py:63
         [FAIL] Failure and rejection paths are also captured in audit trail
           No audit entries on failure paths; audit trail covers only successes
         [PASS] Actor identity (agent/user/service) recorded alongside each audited action
           Found 8 reference(s): api/expenses.py:50
         [FAIL] Sensitive reads are audit-logged, not just writes
           No audit entries on read paths; an agent that reads and exfiltrates sensitive data leaves no trace
         [PASS] Audit trail storage exposes no update/delete path (append-only)
           No update/delete calls found against audit log storage - consistent with append-only

  Interface Legibility
    Level 3/4 — Capable (weighted score)   Checks passed: 3/6
         [PASS] OpenAPI or tool schema file present
           Found schema at: openapi.yaml
         [PASS] Operation descriptions present in schema (not just names/summaries)
           Descriptions found in: openapi.yaml
         [PASS] Structured error schema with machine-readable error codes present
           Found 10 reference(s): api/expenses.py:64
         [FAIL] Deprecation or versioning signals present (agents can detect breaking changes)
           No versioning or deprecation signals found
         [FAIL] Request/response examples present in schema
           No example/examples blocks found in schema; agent has only prose to infer valid request shapes
         [FAIL] Machine-readable parameter constraints (enum/minimum/maximum/pattern) present on request parameters
           No enum/minimum/maximum/pattern constraints found on request parameters; validation rules exist only in prose

  Operational Containment
    Level 1/4 — Not Ready (weighted score)   Checks passed: 0/6
         [FAIL] Timeout configuration present at tool/endpoint level
           No timeout configuration found; runaway agent calls have no ceiling
         [FAIL] Rate limiting or quota enforcement present
           No rate limiting or quota found; a looping agent can exhaust resources
         [FAIL] Input size cap or payload size validation present
           No input size cap found; agent-interpolated context could be arbitrarily large
         [FAIL] Awareness of untrusted / agent-interpolated input surfaces (sanitization, content validation)
           No untrusted-input handling found; agent-interpolated strings accepted verbatim
         [FAIL] Retry-After signal set alongside throttled/429 responses
           No Retry-After header found on throttled responses; a throttled agent has no signal for how long to back off
         [FAIL] Pagination or result-size ceiling present on list/query endpoints
           No page_size/limit ceiling found on list endpoints; an agent can pull unbounded data in one call
```

The overall Level 1 is not because Clario is badly built.
It is because the scoring rule is: overall level equals the minimum across
all six dimensions.
Operational Containment is 1, so the overall score is 1.
This is intentional.
A codebase with perfect Forensics and Consent scores but no per-tool timeouts
is not "mostly ready" - it is one looping agent call away from a production
incident.

Let me walk through the gaps in order of severity.

---

### Gap 1: No deduplication window (Write Safety: 2/4)

Clario's `POST /invoices` accepts an `Idempotency-Key` header.
That is the right instinct.
But here is what the implementation actually does:

```python
# from examples/clario/api/invoices.py
idempotency_key = request.get("headers", {}).get("Idempotency-Key")
# TODO: check _seen_idempotency_keys before proceeding

invoice_id = f"inv_{uuid.uuid4().hex[:8]}"
invoice = { ... }
_invoices[invoice_id] = invoice
```

The key is read.
It is logged.
It is never checked against anything.
A retry with the same key creates a second invoice with a different ID.

The fix is a dedup store - a cache keyed on the idempotency key that returns
the original response if the same key is seen again within a time window.
The framework checks for this with a pattern that looks for actual store
initialization (`idempotency_store =`, `dedup_store =`, etc.), not just a
mention of the concept.

The second Write Safety gap is test coverage.
Clario's test suite has `test_create_invoice_returns_201`.
It does not have `test_create_invoice_duplicate_idempotent`.
The distinction matters: you cannot know your idempotency logic is correct
without a test that actually sends the same idempotency key twice and asserts
the response is identical.

---

### Gap 2: Tenant isolation asserted, not proven (Boundary Enforcement: 3/4)

Clario filters by `account_id` on every data access endpoint.
That is correct.
The issue is that this is true in the source code but not proven in the test
suite.

```python
# from examples/clario/tests/test_invoices.py

def test_get_invoice_returns_data():
    # ... creates an invoice, retrieves it with the same token
    assert get_resp["status"] == 200
```

There is no test that creates an invoice under account A and attempts to
retrieve it with a token issued to account B.
Without that test, the boundary enforcement check passes linting and code
review but has no machine-verified proof.

The framework looks for test functions whose names match patterns like
`def test_cross_tenant_*` or `def test_unauthorized_*`.
Clario has none.
Level 3 is the right score here: the mechanism is present, but the proof is
absent.

---

### Gap 3: Failure paths not audited (Forensics: 3/4)

Clario's audit log correctly records actor ID, action, resource ID, and
outcome for every successful mutation.
Here is what it does not record:

```python
# from examples/clario/api/invoices.py
if invoice["status"] == "paid":
    # Gap: failure path - no audit event emitted here
    return {
        "status": 422,
        "error": "Something went wrong with the void operation",
    }
```

When a `POST /invoices/{id}/void` fails because the invoice is already paid,
no audit entry is written.
This means that if an agent attempts to void the same invoice fifty times in
a retry loop, the audit log shows nothing.
You know the agent existed.
You do not know what it tried.

The fix is to call `audit_log(outcome="failure")` on every rejected mutation,
not just the successful ones.
The framework checks for this with patterns that require the `outcome=` field
to be explicitly set to a failure value, rather than just checking that the
`audit_log` function is called somewhere.

---

### Gap 4: No timeouts, quotas, or size caps (Operational Containment: 1/4)

Clario has none of the six Operational Containment checks.
No per-tool timeout.
No rate limit per token.
No cap on the `notes` field in expense submissions.
No sanitization of content that an agent might interpolate from its context.
No Retry-After signal telling a throttled agent how long to back off.
No pagination or result-size ceiling on the list endpoints.

```python
# from examples/clario/api/expenses.py
expense = {
    ...
    "notes": body.get("notes", ""),  # no max_length enforcement
    ...
}
```

This is the most common gap in APIs that were designed for human callers and
are being adapted for agents.
A human writing an expense note writes a sentence.
An agent interpolating from a retrieval context might write ten thousand tokens.
Without a cap, every one of those tokens goes into the database.

The timeout gap is the more dangerous one.
An agent that calls a slow endpoint has no way to know when to give up unless
the endpoint enforces a deadline itself.
Without a server-side timeout, one slow operation can block an entire agent
session indefinitely.

---

## How the scoring works

The framework is built around two ideas: deterministic checks for anything
that is mechanically verifiable, and one bounded LLM pass for the one thing
that is not.

**Deterministic checks** scan the target codebase with patterns that require
actual implementation evidence, not just keyword presence.
The idempotency store check requires a variable assignment like `idempotency_store =`
or `dedup_store =`, not just the word "idempotency" appearing somewhere in a comment.
The adversarial test check requires a function definition like `def test_cross_tenant_*`,
not just a mention of cross-tenant access in a docstring.
This specificity is deliberate: the goal is to surface real gaps, not false
positives from documentation that describes what a feature should do but does
not implement it.

**The LLM pass** (off by default) reads the tool descriptions and error
response descriptions from your OpenAPI spec and assesses whether they
contain enough information for an agent to act on them correctly without
guessing.
It is bounded: the model sees only what is in the spec, not your source code
or business logic.
Its job is to phrase an observation, not to decide a score.
The score is already determined by the deterministic checks; the LLM note
is a human-readable summary of what specifically an agent would struggle with
when reading these descriptions.

**The minimum rule** is the most important architectural decision in the
scoring engine.
A 1 on any dimension caps the overall score at 1.
This is not a mathematical convenience - it reflects the actual risk profile.
An API that is perfectly described and perfectly audited but has no per-tool
timeouts will have incidents.
The scorecard should make that visible, not average it away.

---

## What to fix first

If you run the scorer against your own codebase and get a low score, the
priority order follows the overall minimum rule: fix the dimension that is
pulling your score down before improving dimensions that are already higher.

For most APIs that were built before agent tooling was in scope:

1. **Operational Containment** is almost always the lowest.
   Per-tool timeouts and rate limits can often be added at the middleware
   or gateway layer without touching business logic.
   Start there.

2. **Write Safety** is the second most common gap.
   If your API has any write operations, the idempotency store is the first
   thing to add.
   The test coverage is the second.

3. **Boundary Enforcement** at Level 3 (mechanism present, no adversarial
   tests) is a paper gap - the code is right, you just need to prove it.
   Add the cross-tenant rejection tests and the score will go up.

4. **Forensics** gaps on failure paths are easy to miss because failures are
   rare in development.
   Audit every mutation outcome, not just the successes.

---

## Running it

```bash
git clone https://github.com/systemainc/mcp-api-readiness-framework
cd mcp-api-readiness-framework
pip install -r requirements.txt

# Score the Clario Example
python -m framework.cli scan \
  --config examples/clario/config.yaml \
  --target examples/clario
```

To point it at your own codebase, copy `examples/clario/config.yaml`,
update `target_name` and `openapi_paths`, and run the scan against your
API directory.

The test suite runs without credentials:

```bash
python -m pytest tests/ -v
```

---

## The pattern that makes this useful

The reason this framework exists as a scored checklist rather than a
document is the same reason the sibling frameworks in this series exist as
code rather than slide decks: a score is an artifact.
You can track it over sprints.
You can gate on it in CI.
You can compare it before and after a migration.
A document that says "ensure your API is idempotent" is advice.
A check that fails because your test suite has no `def test_cross_tenant_`
function is a pull request.

The goal is not to reach Level 4 on every dimension before shipping agents.
Some APIs will never need Level 4 Operational Containment because they are
only ever called by one internal agent under controlled conditions.
The goal is to know your score, know why, and make a deliberate decision
about which gaps to close before which agent use cases go to production.

The alternative - discovering the gaps when the first agent causes an incident
in production - is the thing this framework exists to prevent.

**Code: [github.com/systemainc/mcp-api-readiness-framework](https://github.com/systemainc/mcp-api-readiness-framework)** — MIT licensed, full scorer and dashboard, no waitlist.
