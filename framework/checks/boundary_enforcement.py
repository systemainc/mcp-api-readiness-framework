"""
Dimension 2 - Boundary Enforcement

An agent operating under one tenant's token must not be able to read or
mutate another tenant's data, even if it tries. This dimension checks that
tenant/role/scope isolation is present in source AND that adversarial
negative-case tests actually prove it.

Implementation without adversarial tests is Level 1 at best: the isolation
may exist, but there is no machine-readable proof that it was verified.
"""
from __future__ import annotations

from ..schema import CheckResult
from ._util import grep_files


def check_boundary_enforcement(target_dir: str, dim_config: dict) -> list[CheckResult]:
    results = []

    # Check 1: tenant isolation pattern in source
    tenant_hits = grep_files(
        target_dir,
        r"tenant_id|org_id|account_id|workspace_id|tenant\.id",
        "**/*.py",
    )
    results.append(CheckResult(
        id="boundary_enforcement.tenant_filter",
        description="Tenant/org/account ID filter present in source",
        passed=len(tenant_hits) > 0,
        evidence=(
            f"Found {len(tenant_hits)} reference(s): {tenant_hits[0][0]}:{tenant_hits[0][1]}"
            if tenant_hits
            else "No tenant-scoping filter found in source"
        ),
        score_contribution=2,
    ))

    # Check 2: role/permission check in source
    role_hits = grep_files(
        target_dir,
        r"require_permission|has_permission|check_permission|assert_role|require_scope|authorize",
        "**/*.py",
    )
    results.append(CheckResult(
        id="boundary_enforcement.role_check",
        description="Role/permission enforcement present in source",
        passed=len(role_hits) > 0,
        evidence=(
            f"Found {len(role_hits)} reference(s): {role_hits[0][0]}:{role_hits[0][1]}"
            if role_hits
            else "No permission/role enforcement found"
        ),
        score_contribution=2,
    ))

    # Check 3: adversarial negative tests (cross-tenant access attempt must be rejected)
    adversarial_hits = grep_files(
        target_dir,
        r"def test.*cross.tenant|def test.*forbidden|def test.*unauthorized|def test.*403|def test.*wrong.account|def test.*other.tenant",
        "**/*.py",
    )
    results.append(CheckResult(
        id="boundary_enforcement.adversarial_tests",
        description="Adversarial negative tests prove cross-tenant access is rejected",
        passed=len(adversarial_hits) > 0,
        evidence=(
            f"Found {len(adversarial_hits)} adversarial test(s): {adversarial_hits[0][0]}:{adversarial_hits[0][1]}"
            if adversarial_hits
            else "No adversarial cross-tenant tests found - isolation is asserted, not proven"
        ),
        score_contribution=2,
    ))

    # Check 4: scope validation on incoming token/credential
    scope_hits = grep_files(
        target_dir,
        r"validate_scope|check_scope|required_scope|token_scope|scope.*check|verify_scope",
        "**/*.py",
    )
    results.append(CheckResult(
        id="boundary_enforcement.scope_validation",
        description="Token/credential scope is validated at the handler level",
        passed=len(scope_hits) > 0,
        evidence=(
            f"Found {len(scope_hits)} reference(s): {scope_hits[0][0]}:{scope_hits[0][1]}"
            if scope_hits
            else "No scope validation found at handler level"
        ),
        score_contribution=1,
    ))

    # Check 5: direct object lookups (single-resource GET/PATCH/DELETE by ID)
    # verify ownership - the classic IDOR gap. Distinct from the list-scoping
    # pattern above: a list handler *includes* matching rows (tenant_id ==),
    # a single-resource handler must *reject* a non-owned one (tenant_id !=).
    object_ownership_hits = grep_files(
        target_dir,
        r"assert_owner|verify_ownership|check_ownership|owns_resource|belongs_to_tenant"
        r"|(account_id|tenant_id|org_id|workspace_id)\"?\]\s*!=\s*ctx"
        r"|(account_id|tenant_id|org_id|workspace_id)\s*!=\s*ctx\.",
        "**/*.py",
    )
    results.append(CheckResult(
        id="boundary_enforcement.object_ownership_check",
        description="Direct object lookups (single-resource GET/PATCH/DELETE) verify ownership",
        passed=len(object_ownership_hits) > 0,
        evidence=(
            f"Found {len(object_ownership_hits)} reference(s): {object_ownership_hits[0][0]}:{object_ownership_hits[0][1]}"
            if object_ownership_hits
            else "No ownership check found on single-resource handlers - an agent guessing/enumerating IDs may read another tenant's resource"
        ),
        score_contribution=2,
    ))

    # Check 6: bulk/export endpoints are scoped and capped - much faster
    # cross-tenant exfiltration path than iterating single lookups.
    bulk_export_hits = grep_files(
        target_dir,
        r"(bulk|export)\w*.{0,100}(tenant_id|org_id|account_id|max_rows|max_export_rows|limit\s*=)",
        "**/*.py",
    )
    results.append(CheckResult(
        id="boundary_enforcement.bulk_export_scoping",
        description="Bulk/export endpoints are tenant-scoped and row-capped",
        passed=len(bulk_export_hits) > 0,
        evidence=(
            f"Found {len(bulk_export_hits)} reference(s): {bulk_export_hits[0][0]}:{bulk_export_hits[0][1]}"
            if bulk_export_hits
            else "No bulk/export/batch handler found with tenant scoping and a row cap"
        ),
        score_contribution=1,
    ))

    return results
