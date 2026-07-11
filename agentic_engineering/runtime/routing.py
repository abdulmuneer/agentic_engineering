from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from .catalog import Catalog


DEFAULT_RISK_ORDER = ["low", "medium", "high", "critical"]
DEFAULT_ASSURANCE_BY_RISK = {
    "low": "A0",
    "medium": "A1",
    "high": "A2",
    "critical": "A3",
}
DEFAULT_PERMISSION_ORDER = [
    "read-only",
    "local-write",
    "external-read",
    "external-write",
    "sensitive",
    "production",
]


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _normalized_tokens(*values: Any) -> set[str]:
    """Normalize user-facing fact labels without requiring one spelling convention."""
    result: set[str] = set()
    for value in values:
        for item in _strings(value):
            normalized = re.sub(r"[^a-z0-9]+", "_", item.strip().lower()).strip("_")
            if not normalized:
                continue
            result.add(normalized)
            result.update(part for part in normalized.split("_") if part)
    return result


def _normalized_label(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _work_facts(record: dict[str, Any]) -> dict[str, bool]:
    change = record.get("change") if isinstance(record.get("change"), dict) else {}
    raw_labels = (
        _strings(record.get("type"))
        + _strings(record.get("workflow"))
        + _strings(record.get("route"))
        + _strings(record.get("change_class"))
        + _strings(record.get("traits"))
        + _strings(record.get("risk_factors"))
        + _strings(record.get("surfaces"))
        + _strings(record.get("permission_classes"))
        + _strings(change.get("surfaces"))
    )
    labels = {label for item in raw_labels if (label := _normalized_label(item))}
    tokens = _normalized_tokens(raw_labels)
    blast_radius = str(change.get("blast_radius", "")).strip().lower().replace("-", "_")
    reversibility = str(change.get("reversibility", "")).strip().lower().replace("-", "_")

    def asserted(name: str) -> bool:
        return change.get(name) is True

    unknown = any(
        change.get(name) == "unknown"
        for name in (
            "production_affecting",
            "authentication",
            "authorization",
            "sensitive_data",
            "safety_impact",
            "regulated_impact",
            "destructive_migration",
            "external_write",
            "reversibility",
            "blast_radius",
        )
    )
    authentication = asserted("authentication") or bool(
        tokens & {"auth", "authentication", "login", "identity"}
    )
    authorization = asserted("authorization") or bool(
        tokens & {"authorization", "permission", "permissions", "rbac", "access_control"}
    )
    sensitive = asserted("sensitive_data") or bool(
        tokens
        & {
            "sensitive",
            "sensitive_data",
            "personal_data",
            "customer_data",
            "regulated_data",
            "secrets",
            "payments",
        }
    )
    release = bool(labels & {"release", "deployment", "deploy", "production_release"})
    incident = bool(labels & {"incident", "outage", "security_event", "data_event"})
    production = asserted("production_affecting") or release or incident or bool(
        tokens & {"production", "prod"}
    )
    user_interface = bool(
        tokens
        & {
            "ui",
            "gui",
            "web",
            "browser",
            "frontend",
            "graphical",
            "desktop",
            "mobile",
            "user_interface",
            "human_facing",
        }
    )
    api = bool(tokens & {"api", "endpoint", "rest", "graphql"})
    backend = authentication or authorization or api or bool(
        tokens & {"backend", "service", "server", "worker", "database", "storage"}
    )
    protocol = bool(
        tokens
        & {
            "protocol",
            "webhook",
            "queue",
            "grpc",
            "websocket",
            "transport",
            "message_bus",
        }
    )
    external_integration = bool(
        tokens & {"third_party", "vendor", "external_integration", "external_service"}
    )
    cross_component = blast_radius in {"multi_component", "customer_segment", "systemic"} or bool(
        tokens & {"integration", "cross_component", "distributed"}
    )
    integration = protocol or external_integration or cross_component
    research = bool(
        labels
        & {
            "research",
            "research_spike",
            "experiment",
            "benchmark",
            "model",
            "algorithm",
            "scientific_claim",
            "research_claim",
            "model_or_algorithm_change",
        }
    )
    regulated = asserted("regulated_impact") or bool(
        tokens & {"regulated", "regulatory", "compliance"}
    )
    destructive = asserted("destructive_migration") or reversibility in {
        "difficult",
        "irreversible",
    }

    return {
        "authentication": authentication,
        "authorization": authorization,
        "sensitive": sensitive,
        "release": release,
        "incident": incident,
        "production": production,
        "user_interface": user_interface,
        "api": api,
        "backend": backend,
        "protocol": protocol,
        "external_integration": external_integration,
        "cross_component": cross_component,
        "integration": integration,
        "research": research,
        "regulated": regulated,
        "destructive": destructive,
        "external_write": asserted("external_write") or "external_write" in labels,
        "unknown": unknown,
        "documentation": bool(tokens & {"documentation", "docs", "release_notes"}),
        "technical_debt": bool(tokens & {"technical_debt", "refactor"}),
    }


def _rules(policy: dict[str, Any]) -> list[dict[str, Any]]:
    value = policy.get(
        "forced_minimum_rules",
        policy.get("rules", policy.get("routing_rules", [])),
    )
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def risk_order(catalog: Catalog) -> list[str]:
    raw = catalog.risk_policy.get("risk_tiers", catalog.risk_policy.get("tiers"))
    if isinstance(raw, list):
        values: list[str] = []
        for item in raw:
            if isinstance(item, str):
                values.append(item)
            elif isinstance(item, dict) and isinstance(item.get("id"), str):
                values.append(item["id"])
        if values:
            return values
    if isinstance(raw, dict):
        ordered = sorted(
            (
                (int(value.get("rank", index)), str(key))
                for index, (key, value) in enumerate(raw.items())
                if isinstance(value, dict)
            ),
        )
        if ordered:
            return [item[1] for item in ordered]
    return DEFAULT_RISK_ORDER.copy()


def max_tier(tiers: Iterable[str], order: list[str]) -> str:
    ranks = {name: index for index, name in enumerate(order)}
    valid = [tier for tier in tiers if tier in ranks]
    return max(valid, key=lambda value: ranks[value]) if valid else order[0]


def minimum_assurance(catalog: Catalog, tier: str) -> str:
    policy = catalog.assurance_policy
    mapping = policy.get("minimum_by_risk", policy.get("assurance_by_risk"))
    if isinstance(mapping, dict) and isinstance(mapping.get(tier), str):
        return mapping[tier]
    levels = policy.get("levels")
    if isinstance(levels, dict):
        for level_id, level in levels.items():
            if isinstance(level, dict) and tier in _strings(level.get("risk_tiers")):
                return str(level_id)
    return DEFAULT_ASSURANCE_BY_RISK[tier]


def _dotted(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _condition_matches(record: dict[str, Any], condition: Any) -> bool:
    if isinstance(condition, str):
        factors = set(_strings(record.get("risk_factors"))) | set(_strings(record.get("traits")))
        return condition in factors
    if not isinstance(condition, dict) or not isinstance(condition.get("field"), str):
        return False
    actual = _dotted(record, condition["field"])
    if "equals" in condition:
        return actual == condition["equals"]
    if isinstance(condition.get("in"), list):
        return actual in condition["in"]
    if "exists" in condition:
        return (actual is not None) is bool(condition["exists"])
    return bool(actual)


def permission_order(catalog: Catalog) -> list[str]:
    raw = catalog.permission_policy.get("order")
    if isinstance(raw, list) and raw:
        return [item for item in raw if isinstance(item, str)]
    classes = catalog.permission_policy.get("classes")
    if isinstance(classes, list):
        ranked: list[tuple[int, str]] = []
        for index, item in enumerate(classes):
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                ranked.append((int(item.get("rank", index)), item["id"]))
        if ranked:
            return [item[1] for item in sorted(ranked)]
    return [item.replace("-", "_") for item in DEFAULT_PERMISSION_ORDER]


def assurance_rank(value: str | None) -> int:
    if not isinstance(value, str):
        return -1
    try:
        return int(value.removeprefix("A"))
    except ValueError:
        return -1


@dataclass(frozen=True)
class Route:
    declared_risk: str
    computed_risk: str
    effective_risk: str
    minimum_assurance: str
    required_capabilities: tuple[str, ...]
    required_evidence: tuple[str, ...]
    permissions: tuple[str, ...]
    permission_ceiling: str
    matched_rules: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "declared_risk": self.declared_risk,
            "computed_risk": self.computed_risk,
            "effective_risk": self.effective_risk,
            "minimum_assurance": self.minimum_assurance,
            "required_capabilities": list(self.required_capabilities),
            "required_evidence": list(self.required_evidence),
            "permissions": list(self.permissions),
            "permission_ceiling": self.permission_ceiling,
            "matched_rules": list(self.matched_rules),
        }


def route_record(record: dict[str, Any], catalog: Catalog) -> Route:
    order = risk_order(catalog)
    default_tier = record.get("_baseline_risk", catalog.risk_policy.get("default_tier", "low"))
    if default_tier not in order:
        default_tier = order[0]
    risk = record.get("risk") if isinstance(record.get("risk"), dict) else {}
    # A recorded effective tier is an output to audit, never an input to recomputation.
    declared = risk.get("declared_tier", record.get("risk_tier", default_tier))
    if declared not in order:
        declared = default_tier

    workflow_id = record.get("workflow")
    workflow = catalog.workflows.get(workflow_id, {}) if isinstance(workflow_id, str) else {}
    required_capabilities = set(_strings(workflow.get("required_capabilities")))
    required_capabilities.update(_strings(record.get("required_capabilities")))
    required_evidence = set(_strings(workflow.get("required_evidence")))
    evidence_plan = record.get("evidence_plan")
    if isinstance(evidence_plan, list):
        for item in evidence_plan:
            if isinstance(item, dict):
                required_evidence.update(_strings(item.get("kinds")))
    permissions = set(_strings(workflow.get("permissions")))
    permissions.update(_strings(record.get("permission_classes")))
    candidate_tiers = [default_tier, declared]
    matched: list[str] = []

    facts = _work_facts(record)
    normalized_workflow = _normalized_label(workflow_id)
    normalized_type = _normalized_label(record.get("type"))

    def force_fact(rule_id: str, minimum_tier: str) -> None:
        if minimum_tier in order:
            candidate_tiers.append(minimum_tier)
        matched.append(rule_id)

    program_defaults = (
        record.get("_program_risk_defaults")
        if isinstance(record.get("_program_risk_defaults"), dict)
        else {}
    )
    change = record.get("change") if isinstance(record.get("change"), dict) else {}
    preset_minima: list[tuple[str, bool]] = [
        ("production_release_minimum", normalized_workflow == "release"),
        ("destructive_local_action_minimum", facts["destructive"]),
        ("externally_published_claim_minimum", facts["research"] and facts["external_write"]),
        ("sensitive_dataset_minimum", facts["sensitive"]),
        (
            "safety_or_irreversible_consequence_minimum",
            facts["destructive"] or change.get("safety_impact") == "severe",
        ),
    ]
    for control, applies in preset_minima:
        tier = program_defaults.get(control)
        if applies and isinstance(tier, str):
            force_fact(f"PRESET-{control.upper().replace('_', '-')}", tier)

    if normalized_workflow or normalized_type:
        required_capabilities.update({"requirements", "code_quality", "verification"})

    if normalized_workflow == "discovery":
        required_capabilities.update({"product_outcomes", "product_discovery", "requirements"})
    elif normalized_workflow == "feature":
        required_capabilities.update({"requirements", "code_quality", "verification"})
        permissions.add("local_write")
    elif normalized_workflow == "bug_fix":
        required_capabilities.update({"code_quality", "verification"})
        permissions.add("local_write")
    elif normalized_workflow == "research_spike":
        required_capabilities.update({"research_assurance", "verification"})
    elif normalized_workflow == "release":
        required_capabilities.update(
            {"operability_release", "verification", "documentation_feedback"}
        )
    elif normalized_workflow == "incident":
        required_capabilities.update(
            {"incident_response", "operability_release", "verification", "documentation_feedback"}
        )

    if normalized_type == "operations":
        required_capabilities.add("operability_release")
        permissions.add("local_write")
    if facts["technical_debt"]:
        required_capabilities.update({"architecture", "code_quality", "verification"})
        permissions.add("local_write")
    if facts["unknown"]:
        force_fact("FACT-UNASSESSED", "high")
    if facts["documentation"]:
        required_capabilities.add("documentation_feedback")
        permissions.add("local_write")

    if facts["authentication"] or facts["authorization"]:
        required_capabilities.update({"backend_delivery", "security_privacy", "verification"})
        required_evidence.update({"security_test", "review"})
        permissions.add("sensitive")
        force_fact("FACT-IDENTITY", "high")
    if facts["sensitive"]:
        required_capabilities.update({"security_privacy", "verification"})
        required_evidence.update({"security_test", "review"})
        permissions.add("sensitive")
        force_fact("FACT-SENSITIVE", "high")
    if facts["regulated"]:
        required_capabilities.update({"regulatory_assurance", "security_privacy"})
        permissions.add("sensitive")
        force_fact("FACT-REGULATED", "high")
    if facts["user_interface"]:
        required_capabilities.update(
            {"experience_design", "frontend_delivery", "verification", "documentation_feedback"}
        )
        required_evidence.add("end_to_end_test")
        permissions.add("local_write")
        force_fact("FACT-USER-SURFACE", "medium")
    if facts["backend"]:
        required_capabilities.update({"backend_delivery", "verification"})
        required_evidence.add("integration_test")
        permissions.add("local_write")
    if facts["api"] or facts["protocol"]:
        required_capabilities.add("architecture")
    if facts["api"]:
        force_fact("FACT-API", "medium")
    if facts["integration"]:
        required_capabilities.update({"architecture", "integration_delivery", "verification"})
        required_evidence.add("integration_test")
        permissions.add("local_write")
        force_fact("FACT-CROSS-SYSTEM", "medium")
    if facts["external_integration"]:
        permissions.add("external_read")
    if facts["research"]:
        required_capabilities.update({"research_assurance", "verification"})
        required_evidence.update({"experiment_result", "review"})
        force_fact("FACT-RESEARCH", "medium")
    if facts["destructive"]:
        required_capabilities.update(
            {"architecture", "backend_delivery", "operability_release", "verification"}
        )
        force_fact("FACT-DESTRUCTIVE", "high")
    if facts["external_write"]:
        permissions.add("external_write")
        force_fact("FACT-EXTERNAL-WRITE", "medium")
    if facts["production"]:
        required_capabilities.update({"operability_release", "verification"})
        required_evidence.update(
            {"deployment_receipt", "monitoring_observation", "regression_test"}
        )
        permissions.add("production")
        force_fact("FACT-PRODUCTION", "high")
    if facts["release"]:
        required_capabilities.add("documentation_feedback")
    if facts["incident"]:
        required_capabilities.update(
            {"incident_response", "operability_release", "documentation_feedback"}
        )
        required_evidence.update({"monitoring_observation", "document"})
        permissions.add("production")
        force_fact("FACT-INCIDENT", "high")

    for index, rule in enumerate(_rules(catalog.risk_policy), start=1):
        raw_triggers = rule.get(
            "when_any",
            rule.get("match_any", rule.get("risk_factors", rule.get("triggers"))),
        )
        trigger_values = raw_triggers if isinstance(raw_triggers, list) else [raw_triggers]
        applies = any(_condition_matches(record, trigger) for trigger in trigger_values if trigger)
        when_all = rule.get("when_all")
        if isinstance(when_all, list) and when_all:
            applies = applies and all(_condition_matches(record, trigger) for trigger in when_all)
        if not applies:
            continue
        tier = rule.get("minimum_tier", rule.get("tier", rule.get("risk_tier")))
        if isinstance(tier, str) and tier in order:
            candidate_tiers.append(tier)
        required_capabilities.update(
            _strings(rule.get("required_capabilities", rule.get("capabilities")))
        )
        required_evidence.update(_strings(rule.get("required_evidence", rule.get("evidence"))))
        permissions.update(_strings(rule.get("permissions")))
        matched.append(str(rule.get("id", f"rule-{index}")))

    computed = max_tier(candidate_tiers, order)
    effective = computed
    required_assurance = minimum_assurance(catalog, effective)
    release_assurance = program_defaults.get("minimum_release_assurance")
    if (
        normalized_workflow == "release"
        and isinstance(release_assurance, str)
        and assurance_rank(release_assurance) > assurance_rank(required_assurance)
    ):
        required_assurance = release_assurance

    permission_order_values = permission_order(catalog)
    if not permissions:
        permissions.add(permission_order_values[0])
    permission_ceiling = max(
        permissions or {permission_order_values[0]},
        key=lambda value: permission_order_values.index(value)
        if value in permission_order_values
        else -1,
    )

    return Route(
        declared_risk=declared,
        computed_risk=computed,
        effective_risk=effective,
        minimum_assurance=required_assurance,
        required_capabilities=tuple(sorted(required_capabilities)),
        required_evidence=tuple(sorted(required_evidence)),
        permissions=tuple(
            sorted(
                permissions,
                key=lambda value: permission_order_values.index(value)
                if value in permission_order_values
                else len(permission_order_values),
            )
        ),
        permission_ceiling=permission_ceiling,
        matched_rules=tuple(matched),
    )
