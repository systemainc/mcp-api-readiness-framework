"""
Dimension 4 - Forensics

When an agent takes a write action that causes a problem, you need to be
able to reconstruct exactly what happened: which tool call, from which
agent session, with which inputs, at what time, and whether it succeeded
or failed. Missing correlation IDs or write-only audit logs that omit
failures are common gaps here.
"""
from __future__ import annotations

from ..schema import CheckResult
from ._util import grep_files


def check_forensics(target_dir: str, dim_config: dict) -> list[CheckResult]:
    results = []

    # Check 1: correlation / trace ID propagation
    correlation_hits = grep_files(
        target_dir,
        r"correlation_id|trace_id|request_id|X-Request-Id|X-Correlation-Id|span_id",
        "**/*.py",
    )
    results.append(CheckResult(
        id="forensics.correlation_id",
        description="Correlation/trace/request ID propagated in source",
        passed=len(correlation_hits) > 0,
        evidence=(
            f"Found {len(correlation_hits)} reference(s): {correlation_hits[0][0]}:{correlation_hits[0][1]}"
            if correlation_hits
            else "No correlation/trace ID found - agent actions cannot be correlated across services"
        ),
        score_contribution=2,
    ))

    # Check 2: audit log or event emission on mutating operations
    audit_hits = grep_files(
        target_dir,
        r"audit_log|AuditLog|audit_event|emit_event|write_audit|record_action|AuditRecord",
        "**/*.py",
    )
    results.append(CheckResult(
        id="forensics.audit_log",
        description="Audit log or event emission present on write paths",
        passed=len(audit_hits) > 0,
        evidence=(
            f"Found {len(audit_hits)} reference(s): {audit_hits[0][0]}:{audit_hits[0][1]}"
            if audit_hits
            else "No audit log or event emission found on write paths"
        ),
        score_contribution=2,
    ))

    # Check 3: failure / error paths are also audited (not just successes)
    failure_audit_hits = grep_files(
        target_dir,
        r"audit_log.*outcome.*fail|audit_log.*error|outcome=\"failure\"|outcome='failure'|emit.*failure|record_failure.*audit",
        "**/*.py",
    )
    results.append(CheckResult(
        id="forensics.failure_auditing",
        description="Failure and rejection paths are also captured in audit trail",
        passed=len(failure_audit_hits) > 0,
        evidence=(
            f"Found {len(failure_audit_hits)} reference(s): {failure_audit_hits[0][0]}:{failure_audit_hits[0][1]}"
            if failure_audit_hits
            else "No audit entries on failure paths; audit trail covers only successes"
        ),
        score_contribution=2,
    ))

    # Check 4: actor identity recorded alongside action (who did what)
    actor_hits = grep_files(
        target_dir,
        r"actor_id|performed_by|initiated_by|agent_id|caller_id|user_id.*audit|audit.*user_id",
        "**/*.py",
    )
    results.append(CheckResult(
        id="forensics.actor_identity",
        description="Actor identity (agent/user/service) recorded alongside each audited action",
        passed=len(actor_hits) > 0,
        evidence=(
            f"Found {len(actor_hits)} reference(s): {actor_hits[0][0]}:{actor_hits[0][1]}"
            if actor_hits
            else "No actor identity field found in audit records"
        ),
        score_contribution=1,
    ))

    # Check 5: sensitive reads are audit-logged too, not just writes - an agent
    # that reads and exfiltrates data leaves no trace if only mutations are audited.
    read_audit_hits = grep_files(
        target_dir,
        r"audit_log\(.*action=.*(read|view|get|fetch|access)"
        r"|audit_event\(.*(read|view|get|fetch|access)"
        r"|action=\"[\w.]*\.(read|view|get|fetch|access)\"",
        "**/*.py",
    )
    results.append(CheckResult(
        id="forensics.read_audit_logging",
        description="Sensitive reads are audit-logged, not just writes",
        passed=len(read_audit_hits) > 0,
        evidence=(
            f"Found {len(read_audit_hits)} reference(s): {read_audit_hits[0][0]}:{read_audit_hits[0][1]}"
            if read_audit_hits
            else "No audit entries on read paths; an agent that reads and exfiltrates sensitive data leaves no trace"
        ),
        score_contribution=2,
    ))

    # Check 6: audit trail is append-only - a log that can be updated or
    # deleted is not forensic evidence. Only counts as a pass if audit storage
    # actually exists (absence of a mutating function proves nothing on its own).
    audit_storage_hits = grep_files(
        target_dir,
        r"audit_log|AuditLog|audit_event|AuditRecord",
        "**/*.py",
    )
    audit_mutation_hits = grep_files(
        target_dir,
        r"(audit_log|AuditLog|audit_event|AuditRecord)\w*\.(update|delete|remove)\("
        r"|def (update|delete)_audit"
        r"|DELETE FROM audit|UPDATE audit_log",
        "**/*.py",
    )
    append_only_passed = len(audit_storage_hits) > 0 and len(audit_mutation_hits) == 0
    results.append(CheckResult(
        id="forensics.append_only_audit",
        description="Audit trail storage exposes no update/delete path (append-only)",
        passed=append_only_passed,
        evidence=(
            f"Found {len(audit_mutation_hits)} mutating audit call(s): {audit_mutation_hits[0][0]}:{audit_mutation_hits[0][1]} - audit trail is not append-only"
            if audit_mutation_hits
            else (
                "No audit log or event emission found - cannot confirm append-only guarantees"
                if not audit_storage_hits
                else "No update/delete calls found against audit log storage - consistent with append-only"
            )
        ),
        score_contribution=2,
    ))

    return results
