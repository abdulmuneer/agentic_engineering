from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .catalog import Catalog


CORE_RISK_RANKS = {"low": 1, "medium": 2, "high": 3, "critical": 4}
CORE_ASSURANCE_RANKS = {"A0": 0, "A1": 1, "A2": 2, "A3": 3}
CORE_PERMISSION_RANKS = {
    "read_only": 1,
    "local_write": 2,
    "external_read": 3,
    "external_write": 4,
    "sensitive": 5,
    "production": 6,
}
RUNTIME_EVIDENCE_KINDS = {
    "deterministic_test",
    "integration_test",
    "end_to_end_test",
    "regression_test",
    "security_test",
    "static_analysis",
    "manual_observation",
    "user_research",
    "experiment_result",
    "benchmark",
    "review",
    "approval",
    "deployment_receipt",
    "monitoring_observation",
    "document",
}


@dataclass(frozen=True)
class PolicyShapeIssue:
    code: str
    message: str
    filename: str


def _add(
    issues: list[PolicyShapeIssue], filename: str, code: str, message: str
) -> None:
    issues.append(PolicyShapeIssue(code, message, filename))


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _validate_id(
    policy: dict[str, Any], name: str, expected: str, filename: str, issues: list[PolicyShapeIssue]
) -> None:
    if policy.get("id") != expected:
        _add(issues, filename, f"{name}-policy-id", f"{name}_policy.id must be {expected!r}")


def _ranked_entries(
    policy: dict[str, Any],
    *,
    name: str,
    section: str,
    singular: str,
    expected: dict[str, int],
    filename: str,
    issues: list[PolicyShapeIssue],
) -> dict[str, dict[str, Any]]:
    raw = policy.get(section)
    section_code = f"{name}-policy-{section}"
    if not isinstance(raw, list) or not raw:
        _add(issues, filename, section_code, f"{name}_policy.{section} must be a non-empty list")
        return {}

    entries: dict[str, dict[str, Any]] = {}
    seen_ranks: set[int] = set()
    for index, entry in enumerate(raw):
        location = f"{name}_policy.{section}[{index}]"
        if not isinstance(entry, dict):
            _add(issues, filename, section_code, f"{location} must be a mapping")
            continue
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id.strip() or entry_id in entries:
            _add(
                issues,
                filename,
                f"{name}-policy-{singular}-id",
                f"{location}.id must be a unique non-empty string",
            )
            continue
        entries[entry_id] = entry
        rank = entry.get("rank")
        if (
            not isinstance(rank, int)
            or isinstance(rank, bool)
            or rank < 0
            or rank in seen_ranks
        ):
            _add(
                issues,
                filename,
                f"{name}-policy-{singular}-rank",
                f"{location}.rank must be a unique non-negative integer",
            )
        else:
            seen_ranks.add(rank)

    missing = sorted(set(expected) - set(entries))
    if missing:
        _add(
            issues,
            filename,
            section_code,
            f"{name}_policy.{section} is missing runtime-required ids: {', '.join(missing)}",
        )
    for entry_id, rank in expected.items():
        if entry_id in entries and entries[entry_id].get("rank") != rank:
            _add(
                issues,
                filename,
                f"{name}-policy-{singular}-rank",
                f"{singular.capitalize()} {entry_id!r} must have rank {rank}",
            )
    return entries


def _risk(policy: dict[str, Any]) -> list[PolicyShapeIssue]:
    filename = "risk_policy.yaml"
    issues: list[PolicyShapeIssue] = []
    _validate_id(policy, "risk", "core-risk-policy", filename, issues)
    tiers = _ranked_entries(
        policy,
        name="risk",
        section="tiers",
        singular="tier",
        expected=CORE_RISK_RANKS,
        filename=filename,
        issues=issues,
    )
    if policy.get("default_tier") not in tiers:
        _add(
            issues,
            filename,
            "risk-policy-default-tier",
            "risk_policy.default_tier must reference a declared tier",
        )

    rules = policy.get("forced_minimum_rules")
    if not isinstance(rules, list) or not rules:
        _add(
            issues,
            filename,
            "risk-policy-rules",
            "risk_policy.forced_minimum_rules must be a non-empty list",
        )
    else:
        rule_ids: set[str] = set()
        for index, rule in enumerate(rules):
            location = f"risk_policy.forced_minimum_rules[{index}]"
            if not isinstance(rule, dict):
                _add(issues, filename, "risk-policy-rule-shape", f"{location} must be a mapping")
                continue
            rule_id = rule.get("id")
            if not isinstance(rule_id, str) or not rule_id.strip() or rule_id in rule_ids:
                _add(
                    issues,
                    filename,
                    "risk-policy-rule-id",
                    f"{location}.id must be a unique non-empty string",
                )
            else:
                rule_ids.add(rule_id)
            if rule.get("minimum_tier") not in tiers:
                _add(
                    issues,
                    filename,
                    "risk-policy-rule-tier",
                    f"{location}.minimum_tier must reference a declared tier",
                )
            conditions = rule.get("when_any")
            if not isinstance(conditions, list) or not conditions:
                _add(
                    issues,
                    filename,
                    "risk-policy-rule-conditions",
                    f"{location}.when_any must be a non-empty list",
                )
                continue
            for condition in conditions:
                operator_valid = isinstance(condition, dict) and (
                    "equals" in condition
                    or (isinstance(condition.get("in"), list) and bool(condition["in"]))
                    or isinstance(condition.get("exists"), bool)
                )
                if (
                    not isinstance(condition, dict)
                    or not isinstance(condition.get("field"), str)
                    or not condition["field"].strip()
                    or not operator_valid
                ):
                    _add(
                        issues,
                        filename,
                        "risk-policy-rule-condition",
                        f"{location} conditions need a field and an equals, in, or exists operator",
                    )
                    break
    evaluation = policy.get("evaluation")
    if not isinstance(evaluation, dict) or evaluation.get("unknown_fact_behavior") != "fail_closed":
        _add(
            issues,
            filename,
            "risk-policy-unknown-facts",
            "risk_policy.evaluation.unknown_fact_behavior must be 'fail_closed'",
        )
    return issues


def _assurance(policy: dict[str, Any]) -> list[PolicyShapeIssue]:
    filename = "assurance_policy.yaml"
    issues: list[PolicyShapeIssue] = []
    _validate_id(policy, "assurance", "core-assurance-policy", filename, issues)
    levels = _ranked_entries(
        policy,
        name="assurance",
        section="levels",
        singular="level",
        expected=CORE_ASSURANCE_RANKS,
        filename=filename,
        issues=issues,
    )
    minimums = policy.get("minimum_by_risk")
    if not isinstance(minimums, dict) or not minimums:
        _add(
            issues,
            filename,
            "assurance-policy-minimums",
            "assurance_policy.minimum_by_risk must be a non-empty mapping",
        )
    else:
        for tier in CORE_RISK_RANKS:
            if minimums.get(tier) not in levels:
                _add(
                    issues,
                    filename,
                    "assurance-policy-minimum",
                    f"minimum_by_risk.{tier} must reference a declared assurance level",
                )
    if policy.get("run_receipt_required_from") not in levels:
        _add(
            issues,
            filename,
            "assurance-policy-run-receipt-level",
            "run_receipt_required_from must reference a declared assurance level",
        )
    required_fields = {"run_id", "actor", "actor_kind", "context_manifest_digest"}
    missing = sorted(required_fields - set(_strings(policy.get("run_receipt_fields"))))
    if missing:
        _add(
            issues,
            filename,
            "assurance-policy-run-receipt-fields",
            f"run_receipt_fields is missing runtime-required fields: {', '.join(missing)}",
        )
    return issues


def _permission(policy: dict[str, Any]) -> list[PolicyShapeIssue]:
    filename = "permission_policy.yaml"
    issues: list[PolicyShapeIssue] = []
    _validate_id(policy, "permission", "core-permission-policy", filename, issues)
    classes = _ranked_entries(
        policy,
        name="permission",
        section="classes",
        singular="class",
        expected=CORE_PERMISSION_RANKS,
        filename=filename,
        issues=issues,
    )
    rules = policy.get("rules")
    if not isinstance(rules, dict) or not rules:
        _add(
            issues,
            filename,
            "permission-policy-rules",
            "permission_policy.rules must be a non-empty mapping",
        )
        return issues
    receipt_classes = set(_strings(rules.get("action_receipt_required_for")))
    unknown = sorted(receipt_classes - set(classes))
    missing = sorted({"external_write", "sensitive", "production"} - receipt_classes)
    if unknown:
        _add(
            issues,
            filename,
            "permission-policy-action-receipt-class",
            f"action_receipt_required_for references unknown classes: {', '.join(unknown)}",
        )
    if missing:
        _add(
            issues,
            filename,
            "permission-policy-action-receipts",
            f"action_receipt_required_for is missing elevated classes: {', '.join(missing)}",
        )
    return issues


def _evidence(policy: dict[str, Any]) -> list[PolicyShapeIssue]:
    filename = "evidence_policy.yaml"
    issues: list[PolicyShapeIssue] = []
    _validate_id(policy, "evidence", "core-evidence-policy", filename, issues)
    kinds = _strings(policy.get("kinds"))
    missing = sorted(RUNTIME_EVIDENCE_KINDS - set(kinds))
    if not kinds or missing:
        suffix = f"; missing: {', '.join(missing)}" if missing else ""
        _add(
            issues,
            filename,
            "evidence-policy-kinds",
            f"evidence_policy.kinds must contain all runtime-supported kinds{suffix}",
        )
    elif len(kinds) != len(set(kinds)):
        _add(
            issues,
            filename,
            "evidence-policy-kind-duplicate",
            "evidence_policy.kinds must contain unique values",
        )

    required = {"id", "work_item_ref", "kind", "subject", "producer", "method", "result", "observed_at"}
    missing = sorted(required - set(_strings(policy.get("required_fields"))))
    if missing:
        _add(
            issues,
            filename,
            "evidence-policy-required-fields",
            f"evidence_policy.required_fields is missing: {', '.join(missing)}",
        )
    missing = sorted(
        {"pass", "fail", "inconclusive", "not_run"}
        - set(_strings(policy.get("result_values")))
    )
    if missing:
        _add(
            issues,
            filename,
            "evidence-policy-result-values",
            f"evidence_policy.result_values is missing: {', '.join(missing)}",
        )
    bindings = policy.get("subject_binding")
    required_bindings = {
        "code_evidence_requires_commit",
        "artifact_evidence_requires_digest",
        "release_evidence_requires_release_ref",
    }
    missing = sorted(
        required_bindings
        if not isinstance(bindings, dict)
        else {key for key in required_bindings if not isinstance(bindings.get(key), bool)}
    )
    if missing:
        _add(
            issues,
            filename,
            "evidence-policy-subject-binding",
            f"subject_binding needs boolean rules: {', '.join(missing)}",
        )
    return issues


def validate_policy_shapes(catalog: Catalog) -> list[PolicyShapeIssue]:
    """Validate policy semantics used by routing, authoring, and evidence checks."""
    return [
        *_risk(catalog.risk_policy),
        *_assurance(catalog.assurance_policy),
        *_permission(catalog.permission_policy),
        *_evidence(catalog.evidence_policy),
    ]
