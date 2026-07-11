from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_engineering import __version__

from .catalog import (
    Catalog,
    framework_fingerprint,
    load_catalog,
    workflow_states,
    workflow_transitions,
)
from .io import (
    load_record,
    load_yaml,
    locate_overlay,
    parse_markdown_record,
    principal_id,
    record_files,
    sha256_file,
)
from .policy_validation import validate_policy_shapes
from .routing import assurance_rank, permission_order, risk_order, route_record


VALID_CAPABILITY_STATES = {"active", "not_applicable", "waived"}
REVIEW_STATES = {
    "ready-for-review",
    "evidence-review",
    "accepted",
    "integrated",
    "released",
    "resolved",
    "closed",
    "proceed",
    "narrow",
    "kill",
    "review",
    "verified",
    "release_ready",
    "observed",
    "evidence_ready",
    "decision_pending",
    "recovered",
    "postmortem",
    "actions_tracked",
}


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result = {"severity": self.severity, "code": self.code, "message": self.message}
        if self.path:
            result["path"] = self.path
        return result


@dataclass
class ValidationReport:
    issues: list[Issue] = field(default_factory=list)
    project_root: Path | None = None
    overlay: Path | None = None
    program: dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, severity: str, code: str, message: str, path: Path | str | None = None) -> None:
        self.issues.append(
            Issue(severity, code, message, str(path) if path is not None else None)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [issue.as_dict() for issue in self.issues],
        }


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _present(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return value is not None


def _validate_json_schema_if_available(
    document: dict[str, Any],
    schema_name: str,
    path: Path,
    catalog: Catalog,
    report: ValidationReport,
) -> None:
    try:
        import jsonschema
    except ImportError:
        report.add(
            "error",
            "schema-validator-missing",
            "jsonschema is required; install the project dependencies before validation",
            path,
        )
        return
    schema_path = catalog.root / "schemas" / "v1" / f"{schema_name}.schema.json"
    if not schema_path.is_file():
        report.add(
            "error",
            "schema-missing",
            f"Required schema {schema_name!r} is not installed",
            schema_path,
        )
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path)):
        field = ".".join(str(item) for item in error.absolute_path) or "<root>"
        report.add(
            "error",
            "json-schema",
            f"{schema_name}.{field}: {error.message}",
            path,
        )


def _program_payload(document: dict[str, Any]) -> dict[str, Any]:
    value = document.get("program")
    return value if isinstance(value, dict) else document


def _program_capabilities(program: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = _program_payload(program).get("capabilities", {})
    if isinstance(raw, dict):
        return {
            str(capability_id): (value if isinstance(value, dict) else {"status": value})
            for capability_id, value in raw.items()
        }
    if isinstance(raw, list):
        result: dict[str, dict[str, Any]] = {}
        for item in raw:
            if isinstance(item, str):
                result[item] = {"disposition": "active"}
            elif isinstance(item, dict) and isinstance(item.get("id"), str):
                result[item["id"]] = item
        return result
    return {}


def _project_traits(program: dict[str, Any]) -> set[str]:
    project = _program_payload(program)
    profile = project.get("profile", {}) if isinstance(project.get("profile"), dict) else {}
    traits: set[str] = set()
    for key in ("surfaces", "deployment_targets", "data_classes", "risk_domains"):
        traits.update(_strings(profile.get(key)))
    for key in ("product_type", "lifecycle_phase"):
        if isinstance(profile.get(key), str):
            traits.add(profile[key])
    traits.update(_strings(project.get("traits")))
    traits.update(_strings(program.get("traits")))
    traits.update(_strings(program.get("surfaces")))
    if traits & {"web", "desktop", "mobile", "gui", "operator_console"}:
        traits.update({"human_facing_surface", "graphical_surface", "user_visible_change"})
    if traits & {"cli", "operator_cli", "operator-console", "operator_console"}:
        traits.update({"human_facing_surface", "operator_workflow_change", "operator_change"})
    if traits & {"api", "service", "backend", "distributed-runtime", "stage-protocol"}:
        traits.add("backend_surface")
    if traits & {"hosted", "controlled_hosted", "production"}:
        traits.update({"runtime_change", "production_release"})
    if traits & {"customer_data", "regulated_data", "personal_data"}:
        traits.add("sensitive_data")
    if traits & {"regulated_service", "regulated_data", "compliance"}:
        traits.add("regulated_domain")
    if traits & {"research_platform", "research-system", "experiment"}:
        traits.add("research_claim")
    if "discovery" in traits:
        traits.add("new_product")
    return traits


def _capability_required(metadata: dict[str, Any], traits: set[str]) -> bool:
    if metadata.get("default") == "required":
        return True
    triggers = _strings(metadata.get("activation_triggers"))
    if "always" in triggers:
        return True
    if triggers:
        return bool(set(triggers) & traits)
    required_when = metadata.get("required_when", metadata.get("activation"))
    if isinstance(required_when, list):
        return bool(set(_strings(required_when)) & traits)
    if not isinstance(required_when, dict):
        return False
    any_traits = set(
        _strings(required_when.get("any", required_when.get("when_any", required_when.get("traits"))))
    )
    all_traits = set(_strings(required_when.get("all", required_when.get("when_all"))))
    return (bool(any_traits & traits) if any_traits else True) and all_traits <= traits


def _validate_program_shape(program: dict[str, Any], path: Path, report: ValidationReport) -> None:
    if program.get("schema_version") != 1:
        report.add("error", "schema-version", "program.schema_version must be 1", path)
    project = program.get("program")
    if not isinstance(project, dict):
        report.add("error", "program-missing", "The manifest must contain a program mapping", path)
        return
    for key in ("id", "name", "accountable_human", "governance_root"):
        if not isinstance(project.get(key), str) or not project[key].strip():
            report.add("error", "program-field", f"program.{key} is required", path)
    profile = project.get("profile")
    if not isinstance(profile, dict):
        report.add("error", "profile-missing", "program.profile must be a mapping", path)
    else:
        for key in (
            "product_type",
            "lifecycle_phase",
            "surfaces",
            "deployment_targets",
            "data_classes",
            "risk_domains",
        ):
            if key not in profile:
                report.add("error", "profile-field", f"program.profile.{key} is required", path)
    gate = project.get("current_gate")
    if not isinstance(gate, str) or not gate:
        report.add("error", "current-gate", "program.current_gate is required", path)
    if not isinstance(program.get("framework_version"), str):
        report.add("warning", "framework-version", "framework_version is not declared", path)
    tailoring = project.get("tailoring")
    if not isinstance(tailoring, dict) or tailoring.get("status") != "confirmed":
        report.add(
            "warning",
            "tailoring-pending",
            "Project tailoring is not confirmed; answer the persisted questions and run agentic tailor --confirm",
            path,
        )
    elif not _strings(tailoring.get("questions")):
        report.add(
            "error",
            "tailoring-questions",
            "Confirmed tailoring must retain the questions that were answered",
            path,
        )
    else:
        questions = set(_strings(tailoring.get("questions")))
        answers = {
            item.get("question")
            for item in tailoring.get("answers", [])
            if isinstance(item, dict)
            and isinstance(item.get("question"), str)
            and isinstance(item.get("answer"), str)
            and item.get("answer", "").strip()
        }
        if questions - answers:
            report.add(
                "error",
                "tailoring-answers",
                "Confirmed tailoring must answer every persisted question",
                path,
            )


def _source_version(path: Path) -> str | int | None:
    if path.suffix == ".md":
        try:
            metadata, _ = parse_markdown_record(path)
        except ValueError:
            metadata = {}
        return metadata.get("plan_version", metadata.get("version"))
    if path.suffix in {".yaml", ".yml"}:
        data = load_yaml(path)
        return data.get("plan_version", data.get("version"))
    return None


def _validate_framework_lock(
    program: dict[str, Any], catalog: Catalog, manifest_path: Path, report: ValidationReport
) -> None:
    payload = _program_payload(program)
    lock = payload.get("framework_lock")
    if not isinstance(lock, dict):
        report.add(
            "error",
            "framework-lock-missing",
            "program.framework_lock is required for reproducible validation",
            manifest_path,
        )
        return
    if lock.get("version") != program.get("framework_version"):
        report.add(
            "error",
            "framework-lock-version",
            "framework_lock.version must match the manifest framework_version",
            manifest_path,
        )
    expected = framework_fingerprint(catalog.root)
    for field, value in expected.items():
        if lock.get(field) != value:
            report.add(
                "error",
                "framework-lock-drift",
                f"{field} does not match the loaded framework; run agentic upgrade --apply",
                manifest_path,
            )


def _validate_program_catalog_refs(
    program: dict[str, Any], catalog: Catalog, manifest_path: Path, report: ValidationReport
) -> None:
    payload = _program_payload(program)
    policy_ids = {
        policy.get("id")
        for policy in (
            catalog.risk_policy,
            catalog.assurance_policy,
            catalog.permission_policy,
            catalog.evidence_policy,
        )
        if isinstance(policy.get("id"), str)
    }
    for policy_ref in sorted(set(_strings(payload.get("policy_refs"))) - policy_ids):
        report.add(
            "error",
            "program-policy-ref",
            f"Program policy_ref {policy_ref!r} cannot be resolved",
            manifest_path,
        )
    workflow_defaults = payload.get("workflow_defaults")
    if isinstance(workflow_defaults, dict):
        for workflow_id in workflow_defaults.values():
            if workflow_id not in catalog.workflows:
                report.add(
                    "error",
                    "program-workflow-ref",
                    f"Program workflow default {workflow_id!r} cannot be resolved",
                    manifest_path,
                )


def _validate_source(
    program: dict[str, Any], project_root: Path, manifest_path: Path, report: ValidationReport
) -> None:
    payload = _program_payload(program)
    source = payload.get("source_of_truth")
    if not isinstance(source, dict):
        report.add("error", "source-missing", "source_of_truth must be declared", manifest_path)
        return
    relative = source.get("path")
    if not isinstance(relative, str) or not relative:
        report.add("error", "source-path", "source_of_truth.path is required", manifest_path)
        return
    source_path = (project_root / relative).resolve()
    if not source_path.is_relative_to(project_root):
        report.add(
            "error",
            "source-outside-project",
            "The authoritative source must be inside the project root",
            source_path,
        )
        return
    if not source_path.is_file():
        report.add("error", "source-not-found", f"Authoritative source does not exist: {relative}", source_path)
        return

    expected_hash = source.get("sha256")
    if isinstance(expected_hash, str) and expected_hash:
        actual_hash = sha256_file(source_path)
        if expected_hash != actual_hash:
            report.add(
                "error",
                "source-hash-drift",
                f"Authoritative source hash changed: expected {expected_hash}, got {actual_hash}",
                source_path,
            )
    else:
        report.add(
            "error",
            "source-hash-missing",
            "source_of_truth.sha256 is missing; content drift cannot be detected",
            manifest_path,
        )

    declared_version = source.get("declared_version")
    actual_version = _source_version(source_path)
    if actual_version is not None and declared_version is not None:
        if str(actual_version).removeprefix("v") != str(declared_version).removeprefix("v"):
            report.add(
                "error",
                "source-version-drift",
                f"Manifest declares source version {declared_version}, but {relative} declares {actual_version}",
                source_path,
            )


def _validate_capabilities(
    program: dict[str, Any], catalog: Catalog, manifest_path: Path, report: ValidationReport
) -> None:
    assignments = _program_capabilities(program)
    raw_assignments = _program_payload(program).get("capabilities", [])
    if isinstance(raw_assignments, list):
        ids = [
            item.get("id")
            for item in raw_assignments
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        for duplicate in sorted({item for item in ids if ids.count(item) > 1}):
            report.add(
                "error",
                "duplicate-capability-assignment",
                f"Capability {duplicate!r} is assigned more than once",
                manifest_path,
            )
    traits = _project_traits(program)
    for capability_id, metadata in catalog.capabilities.items():
        assignment = assignments.get(capability_id)
        required = _capability_required(metadata, traits)
        if assignment is None:
            if required:
                report.add(
                    "error",
                    "capability-uncovered",
                    f"Required capability {capability_id!r} has no project disposition",
                    manifest_path,
                )
            continue
        status = assignment.get("disposition", assignment.get("status", "active"))
        if status not in VALID_CAPABILITY_STATES:
            report.add(
                "error",
                "capability-status",
                f"Capability {capability_id!r} has invalid status {status!r}",
                manifest_path,
            )
            continue
        if status == "not_applicable":
            rationale = assignment.get("rationale", assignment.get("reason"))
            if not isinstance(rationale, str) or not rationale.strip():
                report.add(
                    "error",
                    "capability-omission-reason",
                    f"Omitted capability {capability_id!r} needs a reason",
                    manifest_path,
                )
            if metadata.get("default") == "required":
                report.add(
                    "error",
                    "mandatory-capability-omitted",
                    f"Capability {capability_id!r} cannot be omitted",
                    manifest_path,
                )
            elif required:
                report.add(
                    "error",
                    "triggered-capability-omitted",
                    f"Capability {capability_id!r} is triggered by the project profile and must be active or formally waived",
                    manifest_path,
                )
            if not _strings(assignment.get("reconsider_when")):
                report.add(
                    "error",
                    "capability-reconsider-trigger",
                    f"Not-applicable capability {capability_id!r} needs reconsider_when",
                    manifest_path,
                )
        elif status == "waived":
            waiver = assignment.get("waiver")
            if not isinstance(waiver, dict) or not all(
                key in waiver
                for key in ("owner", "expires_at", "compensating_controls", "decision_ref")
            ):
                report.add(
                    "error",
                    "capability-waiver",
                    f"Waived capability {capability_id!r} needs owner, expiry, compensating controls, and decision_ref",
                    manifest_path,
                )
            elif not _unexpired(waiver.get("expires_at")):
                report.add(
                    "error",
                    "capability-waiver-expired",
                    f"Capability waiver {capability_id!r} is expired or has an invalid expiry",
                    manifest_path,
                )
        elif required and not (
            principal_id(assignment.get("accountable"))
            or principal_id(assignment.get("owner"))
            or principal_id(assignment.get("reviewer"))
        ):
            report.add(
                "warning",
                "capability-accountability",
                f"Active required capability {capability_id!r} has no accountable principal",
                manifest_path,
            )

    for capability_id in sorted(set(assignments) - set(catalog.capabilities)):
        assignment = assignments[capability_id]
        if assignment.get("disposition", assignment.get("status", "active")) == "active" and not principal_id(
            assignment.get("accountable") or assignment.get("owner") or assignment.get("reviewer")
        ):
            report.add(
                "warning",
                "custom-capability-accountability",
                f"Custom capability {capability_id!r} has no accountable principal",
                manifest_path,
            )


def _validate_actors(
    program: dict[str, Any], catalog: Catalog, manifest_path: Path, report: ValidationReport
) -> None:
    payload = _program_payload(program)
    raw_actors = payload.get("actors")
    if not isinstance(raw_actors, list) or not raw_actors:
        report.add("error", "actors-missing", "program.actors must not be empty", manifest_path)
        return
    actors: dict[str, dict[str, Any]] = {}
    for actor in raw_actors:
        if not isinstance(actor, dict) or not isinstance(actor.get("id"), str):
            report.add("error", "actor-id", "Every actor needs an id", manifest_path)
            continue
        actor_id = actor["id"]
        if actor_id in actors:
            report.add("error", "duplicate-actor", f"Duplicate actor {actor_id!r}", manifest_path)
        actors[actor_id] = actor
        if actor.get("kind") not in {"human", "agent", "automation"}:
            report.add("error", "actor-kind", f"Actor {actor_id!r} has invalid kind", manifest_path)
        if actor.get("permission_ceiling") not in permission_order(catalog):
            report.add(
                "error",
                "actor-permission",
                f"Actor {actor_id!r} has unknown permission ceiling {actor.get('permission_ceiling')!r}",
                manifest_path,
            )
        known_capabilities = set(catalog.capabilities) | set(_program_capabilities(program))
        for capability_id in sorted(set(_strings(actor.get("capabilities"))) - known_capabilities):
            report.add(
                "error",
                "actor-capability-unknown",
                f"Actor {actor_id!r} declares unknown capability {capability_id!r}",
                manifest_path,
            )

    accountable = payload.get("accountable_human")
    accountable_actor = actors.get(accountable) if isinstance(accountable, str) else None
    if accountable_actor is None or accountable_actor.get("kind") != "human":
        report.add(
            "error",
            "accountable-human",
            "program.accountable_human must reference a declared human actor",
            manifest_path,
        )
    tailoring = payload.get("tailoring")
    if isinstance(tailoring, dict) and tailoring.get("status") == "confirmed":
        confirmed_by = tailoring.get("confirmed_by")
        if confirmed_by != accountable or actors.get(confirmed_by, {}).get("kind") != "human":
            report.add(
                "error",
                "tailoring-confirmer",
                "Tailoring must be confirmed by the declared accountable human",
                manifest_path,
            )

    for capability_id, assignment in _program_capabilities(program).items():
        if assignment.get("disposition", assignment.get("status")) != "active":
            continue
        for key in ("owner",):
            actor_id = principal_id(assignment.get(key))
            if actor_id and actor_id not in actors:
                report.add(
                    "error",
                    "capability-actor",
                    f"Capability {capability_id!r} references unknown {key} {actor_id!r}",
                    manifest_path,
                )
            elif actor_id and capability_id not in set(
                _strings(actors.get(actor_id, {}).get("capabilities"))
            ):
                report.add(
                    "error",
                    "capability-actor-mismatch",
                    f"Capability {capability_id!r} {key} {actor_id!r} does not declare that capability",
                    manifest_path,
                )
        for key in ("executors", "reviewers"):
            for actor_id in _strings(assignment.get(key)):
                if actor_id not in actors:
                    report.add(
                        "error",
                        "capability-actor",
                        f"Capability {capability_id!r} references unknown {key[:-1]} {actor_id!r}",
                        manifest_path,
                    )
                elif capability_id not in set(_strings(actors[actor_id].get("capabilities"))):
                    report.add(
                        "error",
                        "capability-actor-mismatch",
                        f"Capability {capability_id!r} references {actor_id!r}, which does not declare that capability",
                        manifest_path,
                    )


def _resolve_evidence_reference(path: Path, value: str, overlay: Path, evidence_ids: set[str]) -> bool:
    if value in evidence_ids:
        return True
    candidate = (path.parent / value).resolve()
    if candidate.is_file():
        return True
    for directory in (overlay / "records" / "evidence", overlay / "evidence"):
        if any(candidate.is_file() for candidate in [directory / f"{value}.md", directory / f"{value}.yaml"]):
            return True
    return False


def _record_workflow_id(record: dict[str, Any]) -> str | None:
    value = record.get("workflow", record.get("route"))
    return value if isinstance(value, str) else None


def _record_risk(record: dict[str, Any]) -> str | None:
    risk = record.get("risk")
    if isinstance(risk, dict):
        value = risk.get("effective_tier", risk.get("declared_tier"))
    else:
        value = record.get("risk_tier", risk)
    return value if isinstance(value, str) else None


def _record_state(record: dict[str, Any]) -> str | None:
    state = record.get("state", record.get("status"))
    if isinstance(state, dict):
        state = state.get("current")
    return state if isinstance(state, str) else None


def _review_reached(record: dict[str, Any], workflow: dict[str, Any] | None = None) -> bool:
    state = _record_state(record)
    if not isinstance(state, str):
        return True
    assurance_states = _strings((workflow or {}).get("assurance_states"))
    return state in (set(assurance_states) if assurance_states else REVIEW_STATES)


def _validate_transition_history(
    record: dict[str, Any],
    workflow: dict[str, Any],
    path: Path,
    report: ValidationReport,
    *,
    evidence_ids: set[str],
    decision_ids: set[str],
    actor_ids: set[str],
    evidence_records: dict[str, dict[str, Any]],
    decision_records: dict[str, dict[str, Any]],
    packet_records: dict[str, dict[str, Any]],
) -> None:
    state_value = record.get("state")
    if isinstance(state_value, dict):
        history = state_value.get("history")
    else:
        history = record.get("transition_history")
    if not isinstance(history, list) or not history:
        report.add("error", "transition-history-missing", "Work item needs state history", path)
        return
    allowed = workflow_transitions(workflow)
    state_definitions = workflow.get("states", {})
    initial_state = workflow.get("initial_state")
    previous: str | None = None
    previous_at: datetime | None = None
    for index, event in enumerate(history):
        if not isinstance(event, dict) or not isinstance(event.get("to"), str):
            report.add("error", "transition-history", f"Invalid transition event {index}", path)
            continue
        source = event.get("from", previous)
        target = event["to"]
        sequence = event.get("sequence")
        if sequence != index + 1:
            report.add(
                "error",
                "transition-sequence",
                f"Transition sequence must be contiguous; expected {index + 1}, got {sequence!r}",
                path,
            )
        raw_at = event.get("at")
        try:
            event_at = (
                datetime.fromisoformat(raw_at.replace("Z", "+00:00"))
                if isinstance(raw_at, str)
                else None
            )
            if event_at is not None and event_at.tzinfo is None:
                event_at = event_at.replace(tzinfo=timezone.utc)
        except ValueError:
            event_at = None
        if event_at is None:
            report.add(
                "error",
                "transition-timestamp",
                f"Transition {index + 1} needs a valid timestamp",
                path,
            )
        elif previous_at is not None and event_at < previous_at:
            report.add(
                "error",
                "transition-time-order",
                f"Transition {index + 1} predates the prior event",
                path,
            )
        if index == 0:
            if source is not None or target != initial_state:
                report.add(
                    "error",
                    "transition-initial-state",
                    f"History must begin with null -> {initial_state!r}",
                    path,
                )
        elif source != previous:
            report.add(
                "error",
                "transition-history-gap",
                f"Transition {index + 1} starts at {source!r}; expected {previous!r}",
                path,
            )
        actor = event.get("actor")
        if not isinstance(actor, str) or actor not in actor_ids:
            report.add(
                "error",
                "transition-actor",
                f"Transition actor {actor!r} is not declared by the program",
                path,
            )
        event_evidence = set(_strings(event.get("evidence_refs")))
        event_approvals = set(_strings(event.get("approval_refs")))
        confirmed_guards = set(_strings(event.get("confirmed_guard_refs")))
        for reference in sorted(event_evidence - evidence_ids):
            report.add(
                "error",
                "transition-evidence-ref",
                f"Transition evidence {reference!r} cannot be resolved",
                path,
            )
        for reference in sorted(event_evidence & evidence_ids):
            receipt = evidence_records.get(reference, {})
            if receipt.get("result") != "pass" or receipt.get("work_item_ref") != record.get("id"):
                report.add(
                    "error",
                    "transition-evidence-invalid",
                    f"Transition evidence {reference!r} must be passing and bound to this work item",
                    path,
                )
        if event_at is not None:
            for reference in sorted(event_evidence & evidence_ids):
                raw_observed = evidence_records.get(reference, {}).get("observed_at")
                try:
                    observed = (
                        datetime.fromisoformat(raw_observed.replace("Z", "+00:00"))
                        if isinstance(raw_observed, str)
                        else None
                    )
                    if observed is not None and observed.tzinfo is None:
                        observed = observed.replace(tzinfo=timezone.utc)
                except ValueError:
                    observed = None
                if observed is not None and observed > event_at:
                    report.add(
                        "error",
                        "transition-evidence-from-future",
                        f"Transition cites evidence {reference!r} observed after the event",
                        path,
                    )
        for reference in sorted(event_approvals - decision_ids):
            report.add(
                "error",
                "transition-approval-ref",
                f"Transition approval {reference!r} is not a decision record",
                path,
            )
        for reference in sorted(event_approvals & decision_ids):
            decision = decision_records.get(reference, {})
            if (
                _decision_disposition(decision)
                not in {"approve", "go", "commit", "accept_risk"}
                or record.get("id") not in _strings(decision.get("subject_refs"))
            ):
                report.add(
                    "error",
                    "transition-approval-invalid",
                    f"Transition decision {reference!r} must be approving and bound to this work item",
                    path,
                )
        if event_at is not None:
            for reference in sorted(event_approvals & decision_ids):
                raw_decided = decision_records.get(reference, {}).get("decided_at")
                try:
                    decided = (
                        datetime.fromisoformat(raw_decided.replace("Z", "+00:00"))
                        if isinstance(raw_decided, str)
                        else None
                    )
                    if decided is not None and decided.tzinfo is None:
                        decided = decided.replace(tzinfo=timezone.utc)
                except ValueError:
                    decided = None
                if decided is not None and decided > event_at:
                    report.add(
                        "error",
                        "transition-approval-from-future",
                        f"Transition cites decision {reference!r} made after the event",
                        path,
                    )
        if isinstance(source, str) and allowed and target not in allowed.get(source, set()):
            report.add(
                "error",
                "illegal-transition",
                f"Workflow does not allow transition {source!r} -> {target!r}",
                path,
            )
        elif isinstance(source, str) and isinstance(state_definitions, dict):
            required_guards: list[str] = []
            state_definition = state_definitions.get(source)
            if isinstance(state_definition, dict) and isinstance(
                state_definition.get("transitions"), dict
            ):
                for transition in state_definition["transitions"].values():
                    if isinstance(transition, dict) and transition.get("to") == target:
                        required_guards = _strings(transition.get("guards"))
                        break
            recorded_guards = set(_strings(event.get("guard_refs")))
            unknown_confirmed = sorted(confirmed_guards - recorded_guards)
            if unknown_confirmed:
                report.add(
                    "error",
                    "transition-confirmed-guard",
                    "Confirmed guards are not required by this transition: "
                    + ", ".join(unknown_confirmed),
                    path,
                )
            missing_guards = [guard for guard in required_guards if guard not in recorded_guards]
            if missing_guards:
                report.add(
                    "error",
                    "transition-guard-receipt",
                    f"Transition {source!r} -> {target!r} lacks guard receipts: {', '.join(missing_guards)}",
                    path,
                )
            contracts = workflow.get("guard_contracts")
            for guard in required_guards:
                contract = contracts.get(guard) if isinstance(contracts, dict) else None
                if not isinstance(contract, dict) or not isinstance(contract.get("path"), str):
                    continue
                value = _dotted(record, contract["path"])
                predicate = contract.get("predicate")
                satisfied = (
                    value == contract["equals"]
                    if "equals" in contract
                    else _present(value)
                    if predicate in {"non_empty", "declared_actor"}
                    else value is not None
                    if predicate == "present"
                    else True
                )
                if not satisfied:
                    report.add(
                        "error",
                        "transition-guard-contract",
                        f"Guard {guard!r} is not supported by canonical field {contract['path']}",
                        path,
                    )
            evidence_guards = {
                guard
                for guard in required_guards
                if guard not in {"evidence_plan_defined"}
                if any(
                    token in guard
                    for token in (
                        "evidence",
                        "assurance",
                        "claims_",
                        "provenance",
                        "receipt",
                        "test",
                        "reproduction",
                        "smoke",
                        "monitoring",
                    )
                )
            }
            approval_guards = {
                guard
                for guard in required_guards
                if any(
                    token in guard
                    for token in (
                        "decision",
                        "approved",
                        "permissions_satisfied",
                        "review_capacity_available",
                        "release_gate_passed",
                        "risk_acceptance",
                    )
                )
            }
            elevated_permissions = set(_strings(record.get("permission_classes"))) & {
                "external_write",
                "sensitive",
                "production",
            }
            if not elevated_permissions:
                approval_guards.discard("permissions_satisfied")
            elif "permissions_satisfied" in required_guards:
                authorized = False
                for reference in event_approvals:
                    decision = decision_records.get(reference, {})
                    authorization = decision.get("authorization")
                    authorization = authorization if isinstance(authorization, dict) else {}
                    if elevated_permissions <= set(
                        _strings(authorization.get("permission_classes"))
                    ) and _unexpired(authorization.get("expires_at")) and actor in _strings(
                        authorization.get("actor_refs")
                    ) and any(
                        guard in _strings(decision.get("guard_authorizations"))
                        for guard in {"permissions_satisfied", "production_permission_valid"}
                        if guard in required_guards
                    ):
                        authorized = True
                        break
                if not authorized:
                    report.add(
                        "error",
                        "transition-permission-authorization",
                        "Elevated permission transition lacks a valid scoped authorization",
                        path,
                    )
            for guard in sorted(confirmed_guards):
                evidence_support = any(
                    guard in _strings(evidence_records.get(reference, {}).get("guard_authorizations"))
                    for reference in event_evidence
                )
                approval_support = any(
                    guard in _strings(decision_records.get(reference, {}).get("guard_authorizations"))
                    for reference in event_approvals
                )
                evidence_typed = any(
                    token in guard
                    for token in (
                        "evidence",
                        "assurance",
                        "claims_",
                        "provenance",
                        "receipt",
                        "test",
                        "reproduction",
                        "smoke",
                        "monitoring",
                        "observed",
                        "checked",
                    )
                )
                approval_typed = any(
                    token in guard
                    for token in (
                        "decision",
                        "approved",
                        "approval",
                        "permissions_satisfied",
                        "production_permission",
                        "release_gate",
                        "risk_acceptance",
                        "review_capacity",
                    )
                )
                supported = (
                    approval_support
                    if approval_typed
                    else evidence_support
                    if evidence_typed
                    else evidence_support or approval_support
                )
                if not supported:
                    report.add(
                        "error",
                        "transition-guard-authorization",
                        f"Manually confirmed guard {guard!r} lacks an explicitly scoped receipt",
                        path,
                    )
            if "work_packet_complete" in required_guards:
                packet_refs = _strings(record.get("work_packet_refs"))
                linked_packets = [packet_records.get(reference) for reference in packet_refs]
                if (
                    not packet_refs
                    or any(not isinstance(packet, dict) for packet in linked_packets)
                    or any(
                        packet.get("work_item_ref") != record.get("id")
                        or packet.get("status") not in {"ready_for_review", "accepted"}
                        for packet in linked_packets
                        if isinstance(packet, dict)
                    )
                ):
                    report.add(
                        "error",
                        "transition-work-packet-incomplete",
                        "work_packet_complete requires every linked packet to be ready for review or accepted",
                        path,
                    )
            if "provenance_present" in required_guards:
                packet_refs = _strings(record.get("work_packet_refs"))
                linked_packets = [packet_records.get(reference) for reference in packet_refs]
                if (
                    not packet_refs
                    or any(not isinstance(packet, dict) for packet in linked_packets)
                    or any(
                        not isinstance(packet.get("producer"), dict)
                        or not _present(packet["producer"].get("actor"))
                        or not _present(packet["producer"].get("run_id"))
                        or not _present(packet.get("changes_or_outputs"))
                        for packet in linked_packets
                        if isinstance(packet, dict)
                    )
                ):
                    report.add(
                        "error",
                        "transition-provenance-missing",
                        "provenance_present requires linked packets with producer/run and outputs",
                        path,
                    )
            if evidence_guards and not event_evidence:
                report.add(
                    "error",
                    "transition-evidence-receipt",
                    "Transition guards require evidence_refs: "
                    + ", ".join(sorted(evidence_guards)),
                    path,
                )
            if approval_guards and not event_approvals:
                report.add(
                    "error",
                    "transition-approval-receipt",
                    "Transition guards require approval_refs: "
                    + ", ".join(sorted(approval_guards)),
                    path,
                )
        previous = target
        if event_at is not None:
            previous_at = event_at
    state = _record_state(record)
    if isinstance(state, str) and previous and state != previous:
        report.add(
            "error",
            "transition-state-drift",
            f"Current state {state!r} does not match transition history {previous!r}",
            path,
        )


def _validate_assurance(
    record: dict[str, Any],
    path: Path,
    catalog: Catalog,
    report: ValidationReport,
    *,
    require_actor_separation: bool = True,
    workflow: dict[str, Any] | None = None,
) -> None:
    normalized = dict(record)
    risk_details = record.get("risk") if isinstance(record.get("risk"), dict) else {}
    declared_risk = risk_details.get("declared_tier", record.get("risk_tier"))
    if isinstance(declared_risk, str):
        normalized["risk_tier"] = declared_risk
    workflow_id = _record_workflow_id(record)
    if workflow_id:
        normalized["workflow"] = workflow_id
    route = route_record(normalized, catalog)
    stated_effective = risk_details.get("effective_tier")
    if (
        isinstance(stated_effective, str)
        and stated_effective != route.computed_risk
        and not risk_details.get("waiver_ref")
    ):
        report.add(
            "error",
            "risk-classification-drift",
            f"Recorded effective risk {stated_effective!r} does not match computed {route.computed_risk!r}",
            path,
        )
    declared_assurance = record.get(
        "assurance", record.get("assurance_level", risk_details.get("assurance_level"))
    )
    if isinstance(declared_assurance, dict):
        declared_assurance = declared_assurance.get("level")
    if declared_assurance is not None and assurance_rank(declared_assurance) < assurance_rank(
        route.minimum_assurance
    ):
        report.add(
            "error",
            "assurance-too-low",
            f"Risk {route.effective_risk!r} requires {route.minimum_assurance}, got {declared_assurance}",
            path,
        )

    producer_value = record.get("producer")
    if isinstance(producer_value, dict) and "actor" in producer_value:
        producer = principal_id(producer_value.get("actor"))
    else:
        producer = principal_id(producer_value)
    validator = principal_id(record.get("validator") or record.get("reviewer"))
    approver = principal_id(record.get("approver") or record.get("accountable_human"))
    minimum_rank = assurance_rank(route.minimum_assurance)
    review_reached = _review_reached(record, workflow)
    if require_actor_separation and review_reached and minimum_rank >= 1:
        review_receipts = _strings(record.get("review_refs"))
        if not review_receipts and not validator:
            report.add(
                "error",
                "review-receipt-missing",
                f"{route.minimum_assurance} requires a separate review receipt or named validator",
                path,
            )
    if require_actor_separation and review_reached and minimum_rank >= 2:
        if not producer or not validator:
            report.add(
                "error",
                "independent-validator-missing",
                f"{route.minimum_assurance} requires named producer and validator",
                path,
            )
        elif producer == validator:
            report.add(
                "error",
                "self-validation",
                f"{route.minimum_assurance} does not allow the producer to validate its own work",
                path,
            )
    if require_actor_separation and review_reached and minimum_rank >= 3:
        if not approver or not approver.startswith("human:"):
            report.add(
                "error",
                "human-approval-missing",
                "A3 requires a named human approver",
                path,
            )
        elif approver in {producer, validator}:
            report.add(
                "error",
                "approval-independence",
                "A3 approver must be distinct from producer and validator",
                path,
            )

def _producer_actor(record: dict[str, Any]) -> str | None:
    value = record.get("producer")
    if isinstance(value, dict):
        return principal_id(value.get("actor"))
    return principal_id(value)


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _unexpired(value: Any) -> bool:
    parsed = _parse_datetime(value)
    return parsed is not None and parsed > datetime.now(timezone.utc)


def _evidence_subject_matches_packet(
    evidence: dict[str, Any], packet: dict[str, Any]
) -> bool:
    subject = evidence.get("subject") if isinstance(evidence.get("subject"), dict) else {}
    outputs = [
        item for item in packet.get("changes_or_outputs", []) if isinstance(item, dict)
    ]
    output_refs = {
        item["ref"] for item in outputs if isinstance(item.get("ref"), str)
    }
    reference = subject.get("ref")
    if isinstance(reference, str):
        if reference in output_refs:
            return True
        if evidence.get("kind") in {"review", "document", "user_research"}:
            return reference in {packet.get("id"), packet.get("work_item_ref")}
        return False
    artifact_digest = subject.get("artifact_digest")
    if isinstance(artifact_digest, str):
        if any(item.get("digest") == artifact_digest for item in outputs):
            return True
        raw_digest = artifact_digest.removeprefix("sha256:")
        return any(
            artifact.get("uri") in output_refs and artifact.get("sha256") == raw_digest
            for artifact in evidence.get("artifacts", [])
            if isinstance(artifact, dict)
        )
    commit = subject.get("commit")
    if isinstance(commit, str):
        return any(item.get("kind") == "commit" and item.get("ref") == commit for item in outputs)
    release_ref = subject.get("release_ref")
    return isinstance(release_ref, str) and release_ref in output_refs


def _decision_disposition(record: dict[str, Any]) -> str | None:
    outcome = record.get("outcome")
    value = outcome.get("disposition") if isinstance(outcome, dict) else None
    return value if isinstance(value, str) else None


def _highest_permission(values: list[str], catalog: Catalog) -> str | None:
    order = permission_order(catalog)
    known = [value for value in values if value in order]
    return max(known, key=order.index) if known else None


def _validate_records(
    program: dict[str, Any], overlay: Path, catalog: Catalog, report: ValidationReport
) -> None:
    parsed: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    seen_ids: dict[str, Path] = {}
    for kind in ("work", "packets", "evidence", "decisions", "learnings"):
        parsed[kind] = []
        for path in record_files(overlay, kind):
            if path.suffix == ".md":
                report.add(
                    "error",
                    "canonical-record-format",
                    "Canonical .agentic records must be YAML; Markdown is a generated or legacy view",
                    path,
                )
            try:
                record, _ = load_record(path)
            except (OSError, ValueError) as error:
                report.add("error", "record-parse", str(error), path)
                continue
            envelope = record.get("_envelope")
            if isinstance(envelope, str) and path.suffix in {".yaml", ".yml"}:
                _validate_json_schema_if_available(
                    load_yaml(path), envelope, path, catalog, report
                )
            record_id = record.get("id")
            if not isinstance(record_id, str) or not record_id:
                report.add("error", "record-id", "Record id is required", path)
            elif record_id in seen_ids:
                report.add(
                    "error",
                    "duplicate-id",
                    f"Record id {record_id!r} duplicates {seen_ids[record_id]}",
                    path,
                )
            else:
                seen_ids[record_id] = path
            schema_version = record.get("_schema_version", record.get("schema_version"))
            if schema_version != 1:
                report.add("error", "record-schema-version", "schema_version must be 1", path)
            if record.get("_envelope") == "work_packet":
                if not _strings(record.get("claims_requested")):
                    report.add(
                        "error",
                        "packet-claims-missing",
                        "Work packet must declare claims_requested",
                        path,
                    )
                if "claims_forbidden" not in record:
                    report.add(
                        "error",
                        "packet-claim-boundary-missing",
                        "Work packet must declare claims_forbidden",
                        path,
                    )
            if record.get("_envelope") == "evidence":
                if not _strings(record.get("claims_authorized")):
                    report.add(
                        "error",
                        "evidence-claims-missing",
                        "Evidence must declare claims_authorized",
                        path,
                    )
                if "claims_forbidden" not in record:
                    report.add(
                        "error",
                        "evidence-claim-boundary-missing",
                        "Evidence must declare claims_forbidden",
                        path,
                    )
            parsed[kind].append((path, record))

    evidence_ids = {
        record["id"]
        for _, record in parsed["evidence"]
        if isinstance(record.get("id"), str)
    }
    decision_ids = {
        record["id"]
        for _, record in parsed["decisions"]
        if isinstance(record.get("id"), str)
    }
    work_by_id = {
        record["id"]: (path, record)
        for path, record in parsed["work"]
        if isinstance(record.get("id"), str)
    }
    packets_by_id = {
        record["id"]: (path, record)
        for path, record in parsed["packets"]
        if isinstance(record.get("id"), str)
    }
    evidence_by_id = {
        record["id"]: (path, record)
        for path, record in parsed["evidence"]
        if isinstance(record.get("id"), str)
    }
    decisions_by_id = {
        record["id"]: (path, record)
        for path, record in parsed["decisions"]
        if isinstance(record.get("id"), str)
    }

    program_payload = _program_payload(program)
    actor_ids = {
        actor["id"]
        for actor in program_payload.get("actors", [])
        if isinstance(actor, dict) and isinstance(actor.get("id"), str)
    }
    actors_by_id = {
        actor["id"]: actor
        for actor in program_payload.get("actors", [])
        if isinstance(actor, dict) and isinstance(actor.get("id"), str)
    }
    capability_assignments = _program_capabilities(program)
    for capability_id, assignment in capability_assignments.items():
        if assignment.get("disposition", assignment.get("status")) != "waived":
            continue
        waiver = assignment.get("waiver") if isinstance(assignment.get("waiver"), dict) else {}
        decision_ref = waiver.get("decision_ref")
        decision_entry = decisions_by_id.get(decision_ref) if isinstance(decision_ref, str) else None
        if decision_entry is None:
            report.add(
                "error",
                "capability-waiver-decision-not-found",
                f"Capability waiver {capability_id!r} must resolve an approval decision",
                overlay / "program.yaml",
            )
            continue
        _, decision = decision_entry
        owner = principal_id(waiver.get("owner"))
        if (
            _decision_disposition(decision) not in {"approve", "accept_risk"}
            or capability_id not in _strings(decision.get("subject_refs"))
            or decision.get("owner") != owner
            or actors_by_id.get(owner or "", {}).get("kind") != "human"
        ):
            report.add(
                "error",
                "capability-waiver-decision",
                f"Capability waiver {capability_id!r} is not backed by its human-owned approval decision",
                decision_entry[0],
            )
    source = program_payload.get("source_of_truth")
    if isinstance(source, dict) and source.get("update_decision_ref"):
        current_update_ref = source.get("update_decision_ref")
        if current_update_ref not in decision_ids:
            report.add(
                "error",
                "source-update-decision-not-found",
                f"Source update decision {current_update_ref!r} cannot be resolved",
                overlay / "program.yaml",
            )
        else:
            update_decision = decisions_by_id[current_update_ref][1]
            expected_update = {
                "path": source.get("path"),
                "declared_version": str(source.get("declared_version")),
                "sha256": source.get("sha256"),
            }
            if update_decision.get("source_update") != expected_update:
                report.add(
                    "error",
                    "source-update-decision-scope",
                    "Current source pin is not backed by a decision scoped to its exact path, version, and digest",
                    decisions_by_id[current_update_ref][0],
                )
        if source.get("updated_by") not in actor_ids:
            report.add(
                "error",
                "source-update-actor-not-found",
                f"Source updater {source.get('updated_by')!r} is not declared",
                overlay / "program.yaml",
            )
        seen_history_decisions: set[str] = set()
        for item in source.get("history", []):
            if not isinstance(item, dict):
                continue
            history_ref = item.get("decision_ref")
            if not isinstance(history_ref, str) or history_ref not in decision_ids:
                report.add(
                    "error",
                    "source-history-decision-not-found",
                    f"Source history decision {history_ref!r} cannot be resolved",
                    overlay / "program.yaml",
                )
            elif history_ref in seen_history_decisions:
                report.add(
                    "error",
                    "source-history-decision-reused",
                    f"Source update decision {history_ref!r} is reused in source history",
                    overlay / "program.yaml",
                )
            if isinstance(history_ref, str):
                seen_history_decisions.add(history_ref)
    declared_version = program_payload.get("source_of_truth", {}).get("declared_version")
    source_history = program_payload.get("source_of_truth", {}).get("history", [])
    known_source_versions = {
        str(value).removeprefix("v")
        for value in [
            declared_version,
            *[
                item.get("declared_version")
                for item in source_history
                if isinstance(item, dict)
            ],
        ]
        if value is not None
    }
    for kind in ("work", "packets"):
        for path, record in parsed[kind]:
            risk_defaults = program_payload.get("risk_defaults", {})
            if isinstance(risk_defaults, dict):
                record["_program_risk_defaults"] = risk_defaults
                if isinstance(risk_defaults.get("baseline"), str):
                    record["_baseline_risk"] = risk_defaults["baseline"]
            route = route_record(record, catalog)
            if kind == "work":
                accountable = principal_id(record.get("accountable_human"))
                if accountable not in actor_ids or actors_by_id.get(accountable or "", {}).get("kind") != "human":
                    report.add(
                        "error",
                        "work-accountable-human",
                        f"Work accountable_human {accountable!r} must resolve to a human actor",
                        path,
                    )
                acceptance_ids = {
                    item["id"]
                    for item in record.get("acceptance", [])
                    if isinstance(item, dict) and isinstance(item.get("id"), str)
                }
                acceptance_list = [
                    item.get("id")
                    for item in record.get("acceptance", [])
                    if isinstance(item, dict) and isinstance(item.get("id"), str)
                ]
                for duplicate in sorted(
                    {item for item in acceptance_list if acceptance_list.count(item) > 1}
                ):
                    report.add(
                        "error",
                        "duplicate-acceptance-id",
                        f"Acceptance criterion {duplicate!r} is declared more than once",
                        path,
                    )
                planned_acceptance = [
                    item.get("acceptance_ref")
                    for item in record.get("evidence_plan", [])
                    if isinstance(item, dict) and isinstance(item.get("acceptance_ref"), str)
                ]
                work_assurance = (
                    record.get("risk", {}).get("assurance_level")
                    if isinstance(record.get("risk"), dict)
                    else None
                )
                for plan in record.get("evidence_plan", []):
                    if isinstance(plan, dict) and assurance_rank(
                        plan.get("minimum_assurance")
                    ) < assurance_rank(work_assurance):
                        report.add(
                            "error",
                            "evidence-plan-assurance",
                            f"Evidence plan for {plan.get('acceptance_ref')!r} is below work assurance {work_assurance}",
                            path,
                        )
                for acceptance_ref in sorted(set(planned_acceptance) - acceptance_ids):
                    report.add(
                        "error",
                        "evidence-plan-acceptance-not-found",
                        f"Evidence plan references unknown acceptance criterion {acceptance_ref!r}",
                        path,
                    )
                for acceptance_ref in sorted(acceptance_ids - set(planned_acceptance)):
                    report.add(
                        "error",
                        "acceptance-plan-missing",
                        f"Acceptance criterion {acceptance_ref!r} has no evidence plan",
                        path,
                    )
                for packet_ref in _strings(record.get("work_packet_refs")):
                    if packet_ref not in packets_by_id:
                        report.add(
                            "error",
                            "work-packet-not-found",
                            f"Work packet {packet_ref!r} cannot be resolved",
                            path,
                        )
                for decision_ref in _strings(record.get("decision_refs")):
                    if decision_ref not in decisions_by_id:
                        report.add(
                            "error",
                            "work-decision-not-found",
                            f"Decision {decision_ref!r} cannot be resolved",
                            path,
                        )
                for dependency_ref in _strings(record.get("dependency_refs")):
                    if dependency_ref not in work_by_id:
                        report.add(
                            "error",
                            "work-dependency-not-found",
                            f"Work dependency {dependency_ref!r} cannot be resolved",
                            path,
                        )
                declared_capabilities = set(_strings(record.get("required_capabilities")))
                routed_capabilities = set(route.required_capabilities)
                missing_capabilities = sorted(routed_capabilities - declared_capabilities)
                if missing_capabilities:
                    report.add(
                        "error",
                        "work-capability-routing-gap",
                        "Work item omits capabilities derived from its facts: "
                        + ", ".join(missing_capabilities),
                        path,
                    )
                for capability_id in sorted(routed_capabilities):
                    assignment = capability_assignments.get(capability_id)
                    disposition = (
                        assignment.get("disposition", assignment.get("status"))
                        if isinstance(assignment, dict)
                        else None
                    )
                    if disposition != "active":
                        report.add(
                            "error",
                            "work-capability-not-active",
                            f"Derived capability {capability_id!r} must be active for this work",
                            path,
                        )
                        continue
                    executors = _strings(assignment.get("executors"))
                    if not executors:
                        report.add(
                            "error",
                            "work-capability-unstaffed",
                            f"Active capability {capability_id!r} has no executor",
                            path,
                        )
                    for executor in executors:
                        actor_capabilities = set(_strings(actors_by_id.get(executor, {}).get("capabilities")))
                        if executor not in actors_by_id or capability_id not in actor_capabilities:
                            report.add(
                                "error",
                                "work-capability-actor-mismatch",
                                f"Executor {executor!r} is not declared with capability {capability_id!r}",
                                path,
                            )

                routed_permissions = set(route.permissions)
                declared_permissions = set(_strings(record.get("permission_classes")))
                missing_permissions = sorted(routed_permissions - declared_permissions)
                if missing_permissions:
                    report.add(
                        "error",
                        "work-permission-routing-gap",
                        "Work item omits permissions derived from its facts: "
                        + ", ".join(missing_permissions),
                        path,
                    )
                planned_kinds = {
                    kind_name
                    for plan in record.get("evidence_plan", [])
                    if isinstance(plan, dict)
                    for kind_name in _strings(plan.get("kinds"))
                }
                missing_evidence_kinds = sorted(
                    set(route.required_evidence) - planned_kinds
                )
                if missing_evidence_kinds:
                    report.add(
                        "error",
                        "work-evidence-routing-gap",
                        "Evidence plan omits kinds derived from work facts: "
                        + ", ".join(missing_evidence_kinds),
                        path,
                    )

                discovery = record.get("discovery")
                if isinstance(discovery, dict):
                    experiment = (
                        discovery.get("experiment")
                        if isinstance(discovery.get("experiment"), dict)
                        else {}
                    )
                    owner = principal_id(experiment.get("owner"))
                    if owner not in actor_ids:
                        report.add(
                            "error",
                            "discovery-owner-not-found",
                            f"Discovery experiment owner {owner!r} is not declared",
                            path,
                        )
                    nested_evidence: list[str] = []
                    for section_name in ("problem", "experiment", "decision"):
                        section = discovery.get(section_name)
                        if isinstance(section, dict):
                            nested_evidence.extend(_strings(section.get("evidence_refs")))
                    for evidence_ref in sorted(set(nested_evidence) - evidence_ids):
                        report.add(
                            "error",
                            "discovery-evidence-not-found",
                            f"Discovery evidence {evidence_ref!r} cannot be resolved",
                            path,
                        )

                risk_details = record.get("risk") if isinstance(record.get("risk"), dict) else {}
                stated_effective = risk_details.get("effective_tier")
                waiver_ref = risk_details.get("waiver_ref")
                if isinstance(stated_effective, str) and stated_effective != route.computed_risk:
                    order = risk_order(catalog)
                    if (
                        route.computed_risk == "critical"
                        and stated_effective in order
                        and order.index(stated_effective) < order.index("critical")
                    ):
                        report.add(
                            "error",
                            "critical-risk-downgrade",
                            "Critical risk cannot be downgraded",
                            path,
                        )
                    if not isinstance(waiver_ref, str):
                        pass  # _validate_assurance reports the classification drift.
                    else:
                        waiver_entry = decisions_by_id.get(waiver_ref)
                        if waiver_entry is None:
                            report.add(
                                "error",
                                "risk-waiver-not-found",
                                f"Risk waiver {waiver_ref!r} is not a decision record",
                                path,
                            )
                        else:
                            waiver_path, waiver = waiver_entry
                            details = waiver.get("risk_acceptance")
                            details = details if isinstance(details, dict) else {}
                            owner = principal_id(waiver.get("owner"))
                            owner_actor = actors_by_id.get(owner or "", {})
                            subject_refs = set(_strings(waiver.get("subject_refs")))
                            if waiver.get("type") != "risk_acceptance" or _decision_disposition(waiver) != "accept_risk":
                                report.add(
                                    "error",
                                    "risk-waiver-type",
                                    "A downgrade must reference an accept_risk decision",
                                    waiver_path,
                                )
                            if record.get("id") not in subject_refs:
                                report.add(
                                    "error",
                                    "risk-waiver-subject",
                                    "Risk waiver is not bound to this work item",
                                    waiver_path,
                                )
                            if owner != record.get("accountable_human") or owner_actor.get("kind") != "human":
                                report.add(
                                    "error",
                                    "risk-waiver-owner",
                                    "Risk waiver owner must be the work item's accountable human",
                                    waiver_path,
                                )
                            if details.get("from_tier") != route.computed_risk or details.get("to_tier") != stated_effective:
                                report.add(
                                    "error",
                                    "risk-waiver-tiers",
                                    "Risk waiver tiers do not match computed and recorded risk",
                                    waiver_path,
                                )
                            if not _unexpired(details.get("expires_at")):
                                report.add(
                                    "error",
                                    "risk-waiver-expired",
                                    "Risk waiver must have a future expiry",
                                    waiver_path,
                                )
                            if not _strings(details.get("compensating_controls")):
                                report.add(
                                    "error",
                                    "risk-waiver-controls",
                                    "Risk waiver must name compensating controls",
                                    waiver_path,
                                )
            workflow_id = _record_workflow_id(record)
            workflow = catalog.workflows.get(workflow_id or "", {})
            if workflow_id and not workflow:
                report.add(
                    "error",
                    "unknown-workflow",
                    f"Workflow {workflow_id!r} is not defined by the locked framework",
                    path,
                )
            if workflow:
                state = _record_state(record)
                states = workflow_states(workflow)
                if isinstance(state, str) and states and state not in states:
                    report.add(
                        "error",
                        "invalid-workflow-state",
                        f"State {state!r} is not valid for workflow {workflow_id!r}",
                        path,
                    )
                _validate_transition_history(
                    record,
                    workflow,
                    path,
                    report,
                    evidence_ids=evidence_ids,
                    decision_ids=decision_ids,
                    actor_ids=actor_ids,
                    evidence_records={
                        record_id: entry[1] for record_id, entry in evidence_by_id.items()
                    },
                    decision_records={
                        record_id: entry[1] for record_id, entry in decisions_by_id.items()
                    },
                    packet_records={
                        record_id: entry[1] for record_id, entry in packets_by_id.items()
                    },
                )
            _validate_assurance(
                record,
                path,
                catalog,
                report,
                require_actor_separation=kind == "packets",
                workflow=workflow,
            )

            source_revision = record.get("source_revision")
            if source_revision is not None and known_source_versions:
                if str(source_revision).removeprefix("v") not in known_source_versions:
                    report.add(
                        "error",
                        "record-source-unknown",
                        f"Record source revision {source_revision!r} is not current or retained in source history",
                        path,
                    )
            references = (
                _strings(record.get("evidence"))
                + _strings(record.get("required_evidence"))
                + _strings(record.get("verification_evidence_refs"))
            )
            for reference in references:
                if not _resolve_evidence_reference(path, reference, overlay, evidence_ids):
                    report.add(
                        "error",
                        "evidence-not-found",
                        f"Evidence reference {reference!r} cannot be resolved",
                        path,
                    )

    for path, record in parsed["evidence"]:
        work_ref = record.get("work_item_ref")
        work_entry = work_by_id.get(work_ref) if isinstance(work_ref, str) else None
        if work_entry is None:
            report.add(
                "error",
                "evidence-work-item-not-found",
                f"Evidence work_item_ref {work_ref!r} cannot be resolved",
                path,
            )
        else:
            _, work = work_entry
            acceptance_ids = {
                item["id"]
                for item in work.get("acceptance", [])
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            }
            for acceptance_ref in sorted(set(_strings(record.get("acceptance_refs"))) - acceptance_ids):
                report.add(
                    "error",
                    "evidence-acceptance-not-found",
                    f"Evidence acceptance_ref {acceptance_ref!r} is not defined by {work_ref}",
                    path,
                )
        evidence_id = record.get("id")
        packet_ref = record.get("packet_ref")
        packet_entry = packets_by_id.get(packet_ref) if isinstance(packet_ref, str) else None
        linked_packets: list[dict[str, Any]] = []
        if packet_entry is None:
            report.add(
                "error",
                "evidence-packet-not-found",
                f"Evidence packet_ref {packet_ref!r} cannot be resolved",
                path,
            )
        else:
            _, packet = packet_entry
            linked_packets = [packet]
            expected_refs = (
                _strings(packet.get("action_receipt_refs"))
                if record.get("kind") in {"approval", "deployment_receipt"}
                else _strings(packet.get("verification_evidence_refs"))
            )
            if evidence_id not in expected_refs:
                report.add(
                    "error",
                    "evidence-packet-backlink",
                    f"Evidence is not linked from its declared packet {packet_ref!r}",
                    path,
                )
            if packet.get("work_item_ref") != work_ref:
                report.add(
                    "error",
                    "evidence-packet-work-mismatch",
                    "Evidence packet_ref belongs to a different work item",
                    path,
                )
            if not _evidence_subject_matches_packet(record, packet):
                report.add(
                    "error",
                    "evidence-subject-packet-mismatch",
                    "Evidence subject is not bound to an output of its declared packet",
                    path,
                )
        reverse_packets = [
            packet
            for _, packet in parsed["packets"]
            if evidence_id
            in (
                _strings(packet.get("verification_evidence_refs"))
                + _strings(packet.get("action_receipt_refs"))
            )
        ]
        if not reverse_packets:
            report.add(
                "error",
                "evidence-orphan",
                "Evidence must be linked from a work packet",
                path,
            )
        elif any(packet.get("id") != packet_ref for packet in reverse_packets):
            report.add(
                "error",
                "evidence-multiple-packets",
                "Evidence may only be linked from its declared packet_ref",
                path,
            )
        authorized_claims = set(_strings(record.get("claims_authorized")))
        forbidden_claims = set(_strings(record.get("claims_forbidden")))
        if authorized_claims & forbidden_claims:
            report.add(
                "error",
                "evidence-claim-conflict",
                "Evidence cannot both authorize and forbid the same claim",
                path,
            )
        if record.get("kind") not in {"approval", "deployment_receipt"}:
            requested_claims = {
                claim
                for packet in linked_packets
                for claim in _strings(packet.get("claims_requested"))
            }
            excess_claims = sorted(authorized_claims - requested_claims)
            if excess_claims:
                report.add(
                    "error",
                    "evidence-claim-out-of-scope",
                    "Evidence authorizes claims no linked packet requested: "
                    + ", ".join(excess_claims),
                    path,
                )
        producer_value = record.get("producer")
        producer = _producer_actor(record)
        linked_assurance = (
            work_entry[1].get("risk", {}).get("assurance_level")
            if work_entry is not None and isinstance(work_entry[1].get("risk"), dict)
            else None
        )
        if assurance_rank(linked_assurance) >= 1 and (
            not isinstance(producer_value, dict)
            or not producer_value.get("context_manifest_digest")
        ):
            report.add(
                "error",
                "evidence-run-context",
                f"{linked_assurance} evidence requires a context_manifest_digest",
                path,
            )
        producer_actor = actors_by_id.get(producer or "")
        if producer_actor is None:
            report.add(
                "error",
                "evidence-producer-not-found",
                f"Evidence producer {producer!r} is not a declared actor",
                path,
            )
        elif isinstance(producer_value, dict) and producer_value.get("type") != producer_actor.get("kind"):
            report.add(
                "error",
                "evidence-producer-kind",
                "Evidence producer type does not match the declared actor kind",
                path,
            )
        validator_value = record.get("validator")
        validator = (
            principal_id(validator_value.get("actor"))
            if isinstance(validator_value, dict)
            else principal_id(validator_value)
        )
        if producer and validator and producer == validator:
            report.add(
                "error",
                "evidence-self-validation",
                "Evidence producer and validator must be different",
                path,
            )
        if not isinstance(record.get("kind"), str):
            report.add("warning", "evidence-kind", "Evidence kind is not declared", path)
        approval = principal_id(record.get("approval_ref"))
        if approval:
            approval_actor = actors_by_id.get(approval)
            if approval_actor is None or approval_actor.get("kind") != "human":
                report.add(
                    "error",
                    "evidence-approval-actor",
                    f"Evidence approval_ref {approval!r} must resolve to a human actor",
                    path,
                )
        authorization_ref = record.get("authorization_ref")
        if isinstance(authorization_ref, str):
            authorization_entry = decisions_by_id.get(authorization_ref)
            if authorization_entry is None:
                report.add(
                    "error",
                    "evidence-authorization-not-found",
                    f"Evidence authorization {authorization_ref!r} cannot be resolved",
                    path,
                )
            else:
                _, authorization_decision = authorization_entry
                authorization = authorization_decision.get("authorization")
                authorization = authorization if isinstance(authorization, dict) else {}
                if (
                    _decision_disposition(authorization_decision) not in {"approve", "go", "commit"}
                    or record.get("work_item_ref")
                    not in _strings(authorization_decision.get("subject_refs"))
                    or producer not in _strings(authorization.get("actor_refs"))
                ):
                    report.add(
                        "error",
                        "evidence-authorization-invalid",
                        "Evidence authorization is not approving, subject-bound, and producer-bound",
                        path,
                    )
                if record.get("kind") in {"approval", "deployment_receipt"}:
                    observed = _parse_datetime(record.get("observed_at"))
                    decided = _parse_datetime(authorization_decision.get("decided_at"))
                    expires = _parse_datetime(authorization.get("expires_at"))
                    declared_packet = packet_entry[1] if packet_entry is not None else {}
                    if (
                        packet_entry is None
                        or authorization_ref not in _strings(declared_packet.get("approval_refs"))
                    ):
                        report.add(
                            "error",
                            "action-receipt-packet",
                            "Action receipt authorization must be attached to its declared packet",
                            path,
                        )
                    if record.get("action_scope") != authorization.get("action_scope"):
                        report.add(
                            "error",
                            "action-receipt-scope",
                            "Action receipt scope must exactly match its authorization",
                            path,
                        )
                    if observed is None or decided is None or observed < decided:
                        report.add(
                            "error",
                            "action-receipt-before-authorization",
                            "Action receipt cannot predate its authorization decision",
                            path,
                        )
                    if observed is None or expires is None or observed > expires:
                        report.add(
                            "error",
                            "action-receipt-after-expiry",
                            "Action receipt must be observed before authorization expiry",
                            path,
                        )
                    if observed is not None and observed > datetime.now(timezone.utc):
                        report.add(
                            "error",
                            "action-receipt-from-future",
                            "Action receipt observed_at cannot be in the future",
                            path,
                        )
        subject = record.get("subject") if isinstance(record.get("subject"), dict) else {}
        artifact_digest = subject.get("artifact_digest")
        if isinstance(artifact_digest, str):
            artifact_hashes = {
                f"sha256:{artifact.get('sha256')}"
                for artifact in record.get("artifacts", [])
                if isinstance(artifact, dict) and isinstance(artifact.get("sha256"), str)
            }
            if artifact_hashes and artifact_digest not in artifact_hashes:
                report.add(
                    "error",
                    "evidence-subject-digest",
                    "Evidence subject digest is not present in its artifact receipts",
                    path,
                )
        if record.get("result") in {"not_run", "inconclusive"}:
            linked_risk = (
                work_entry[1].get("risk", {}).get("effective_tier")
                if work_entry is not None and isinstance(work_entry[1].get("risk"), dict)
                else None
            )
            if linked_risk == "critical" and _strings(record.get("acceptance_refs")):
                report.add(
                    "error",
                    "critical-evidence-skip",
                    "Critical work cannot waive required acceptance evidence",
                    path,
                )
            risk_ref = record.get("risk_acceptance_ref")
            decision_entry = decisions_by_id.get(risk_ref) if isinstance(risk_ref, str) else None
            if decision_entry is None or decision_entry[1].get("type") != "risk_acceptance":
                report.add(
                    "error",
                    "evidence-nonpass-waiver",
                    "not_run or inconclusive evidence requires a resolved risk-acceptance decision",
                    path,
                )

    action_required = set(
        _strings(catalog.permission_policy.get("rules", {}).get("action_receipt_required_for"))
        if isinstance(catalog.permission_policy.get("rules"), dict)
        else []
    ) or {"external_write", "sensitive", "production"}
    order = permission_order(catalog)
    for packet_path, packet in parsed["packets"]:
        work_ref = packet.get("work_item_ref")
        work_entry = work_by_id.get(work_ref) if isinstance(work_ref, str) else None
        if work_entry is None:
            report.add(
                "error",
                "packet-work-item-not-found",
                f"Work packet work_item_ref {work_ref!r} cannot be resolved",
                packet_path,
            )
            continue
        _, work = work_entry
        producer = _producer_actor(packet)
        producer_value = packet.get("producer")
        work_assurance = (
            work.get("risk", {}).get("assurance_level")
            if isinstance(work.get("risk"), dict)
            else None
        )
        if assurance_rank(work_assurance) >= 1 and (
            not isinstance(producer_value, dict)
            or not producer_value.get("context_manifest_digest")
        ):
            report.add(
                "error",
                "packet-run-context",
                f"{work_assurance} packet requires a context_manifest_digest",
                packet_path,
            )
        actor = actors_by_id.get(producer or "")
        if actor is None:
            report.add(
                "error",
                "packet-producer-not-found",
                f"Work packet producer {producer!r} is not a declared actor",
                packet_path,
            )
        elif isinstance(producer_value, dict) and producer_value.get("actor_kind") != actor.get("kind"):
            report.add(
                "error",
                "packet-producer-kind",
                "Work packet producer kind does not match the declared actor kind",
                packet_path,
            )
        packet_capabilities = set(_strings(packet.get("capability_refs")))
        work_capabilities = set(_strings(work.get("required_capabilities")))
        for capability_id in sorted(packet_capabilities - work_capabilities):
            report.add(
                "error",
                "packet-capability-out-of-scope",
                f"Packet capability {capability_id!r} is not authorized by the work item",
                packet_path,
            )
        actor_capabilities = set(_strings((actor or {}).get("capabilities")))
        for capability_id in sorted(packet_capabilities - actor_capabilities):
            report.add(
                "error",
                "packet-producer-capability",
                f"Producer {producer!r} does not provide packet capability {capability_id!r}",
                packet_path,
            )

        requested = _strings(packet.get("permission_classes"))
        for approval_ref in _strings(packet.get("approval_refs")):
            if approval_ref not in decisions_by_id:
                report.add(
                    "error",
                    "packet-approval-not-found",
                    f"Packet approval {approval_ref!r} cannot be resolved",
                    packet_path,
                )
        for action_ref in _strings(packet.get("action_receipt_refs")):
            if action_ref not in evidence_by_id:
                report.add(
                    "error",
                    "packet-action-receipt-not-found",
                    f"Packet action receipt {action_ref!r} cannot be resolved",
                    packet_path,
                )
        for review_ref in _strings(packet.get("review_refs")):
            if review_ref not in evidence_by_id:
                report.add(
                    "error",
                    "packet-review-receipt-not-found",
                    f"Packet review receipt {review_ref!r} must resolve to evidence",
                    packet_path,
                )
        outside_work_permissions = sorted(
            set(requested) - set(_strings(work.get("permission_classes")))
        )
        if outside_work_permissions:
            report.add(
                "error",
                "packet-permission-out-of-scope",
                "Packet permissions are not authorized by the work item: "
                + ", ".join(outside_work_permissions),
                packet_path,
            )
        highest_requested = _highest_permission(requested, catalog)
        ceiling = (actor or {}).get("permission_ceiling")
        if highest_requested in order and ceiling in order and order.index(highest_requested) > order.index(ceiling):
            report.add(
                "error",
                "packet-permission-ceiling",
                f"Packet requests {highest_requested!r} above producer ceiling {ceiling!r}",
                packet_path,
            )
        elevated = set(requested) & action_required
        if elevated:
            valid_authorization = False
            for approval_ref in _strings(packet.get("approval_refs")):
                decision_entry = decisions_by_id.get(approval_ref)
                if decision_entry is None:
                    continue
                _, decision = decision_entry
                authorization = decision.get("authorization")
                authorization = authorization if isinstance(authorization, dict) else {}
                if (
                    _decision_disposition(decision) in {"approve", "go", "commit"}
                    and work_ref in _strings(decision.get("subject_refs"))
                    and producer in _strings(authorization.get("actor_refs"))
                    and elevated <= set(_strings(authorization.get("permission_classes")))
                    and (
                        _unexpired(authorization.get("expires_at"))
                        or packet.get("status") in {"ready_for_review", "accepted"}
                    )
                ):
                    valid_authorization = True
                    break
            if not valid_authorization:
                report.add(
                    "error",
                    "packet-permission-approval",
                    "External-write, sensitive, or production work requires an unexpired subject- and actor-bound approval decision",
                    packet_path,
                )
            action_refs = _strings(packet.get("action_receipt_refs"))
            if packet.get("status") in {"ready_for_review", "accepted"} and not action_refs:
                report.add(
                    "error",
                    "packet-action-receipt-missing",
                    "Executed elevated-permission work requires an action receipt",
                    packet_path,
                )
            for action_ref in action_refs:
                action_entry = evidence_by_id.get(action_ref)
                if action_entry is None:
                    report.add(
                        "error",
                        "packet-action-receipt-not-found",
                        f"Action receipt {action_ref!r} cannot be resolved",
                        packet_path,
                    )
                    continue
                action_path, action = action_entry
                action_authorization_ref = action.get("authorization_ref")
                authorization_entry = (
                    decisions_by_id.get(action_authorization_ref)
                    if isinstance(action_authorization_ref, str)
                    else None
                )
                authorization_decision = authorization_entry[1] if authorization_entry else {}
                authorization = (
                    authorization_decision.get("authorization")
                    if isinstance(authorization_decision.get("authorization"), dict)
                    else {}
                )
                observed = _parse_datetime(action.get("observed_at"))
                decided = _parse_datetime(authorization_decision.get("decided_at"))
                expires = _parse_datetime(authorization.get("expires_at"))
                if (
                    action.get("work_item_ref") != work_ref
                    or action.get("packet_ref") != packet.get("id")
                    or action.get("result") != "pass"
                    or action.get("kind") not in {"approval", "deployment_receipt"}
                    or _producer_actor(action) != producer
                    or action_authorization_ref not in _strings(packet.get("approval_refs"))
                    or action.get("action_scope") != authorization.get("action_scope")
                    or decided is None
                    or observed is None
                    or expires is None
                    or observed < decided
                    or observed > expires
                    or observed > datetime.now(timezone.utc)
                ):
                    report.add(
                        "error",
                        "packet-action-receipt-invalid",
                        "Action receipt must be passing, packet/output/producer-bound, scope-matched, and observed within its authorization window",
                        action_path,
                    )

        assurance = (
            work.get("risk", {}).get("assurance_level")
            if isinstance(work.get("risk"), dict)
            else None
        )
        if packet.get("status") == "accepted" and assurance_rank(assurance) >= 1:
            review_refs = _strings(packet.get("review_refs"))
            valid_review = False
            producer_run = producer_value.get("run_id") if isinstance(producer_value, dict) else None
            producer_context = (
                producer_value.get("context_manifest_digest")
                if isinstance(producer_value, dict)
                else None
            )
            for review_ref in review_refs:
                review_entry = evidence_by_id.get(review_ref)
                if review_entry is None:
                    continue
                _, review = review_entry
                review_producer = review.get("producer")
                review_run = review_producer.get("run_id") if isinstance(review_producer, dict) else None
                review_context = (
                    review_producer.get("context_manifest_digest")
                    if isinstance(review_producer, dict)
                    else None
                )
                if (
                    review.get("result") == "pass"
                    and review.get("work_item_ref") == work_ref
                    and review_run
                    and review_run != producer_run
                    and producer_context
                    and review_context
                    and producer_context != review_context
                ):
                    valid_review = True
                    break
            if not valid_review:
                report.add(
                    "error",
                    "packet-isolated-review-missing",
                    f"{assurance} accepted packet requires a passing review receipt from a distinct run and context",
                    packet_path,
                )

    for decision_path, decision in parsed["decisions"]:
        owner = principal_id(decision.get("owner"))
        if actors_by_id.get(owner or "", {}).get("kind") != "human":
            report.add(
                "error",
                "decision-human-owner",
                "Decision owner must resolve to a human actor",
                decision_path,
            )
        for actor_ref in [principal_id(decision.get("owner"))] + _strings(decision.get("reviewers")):
            if actor_ref and actor_ref not in actor_ids:
                report.add(
                    "error",
                    "decision-actor-not-found",
                    f"Decision actor {actor_ref!r} is not declared",
                    decision_path,
                )
        for evidence_ref in _strings(decision.get("evidence_refs")):
            if evidence_ref not in evidence_ids:
                report.add(
                    "error",
                    "decision-evidence-not-found",
                    f"Decision evidence {evidence_ref!r} cannot be resolved",
                    decision_path,
                )
            elif (
                _decision_disposition(decision)
                in {"commit", "approve", "go", "accept_risk"}
                and evidence_by_id[evidence_ref][1].get("result") != "pass"
            ):
                report.add(
                    "error",
                    "decision-nonpassing-evidence",
                    f"Approving decision cites non-passing evidence {evidence_ref!r}",
                    decision_path,
                )
        outcome = decision.get("outcome") if isinstance(decision.get("outcome"), dict) else {}
        selected = outcome.get("selected_option_ref")
        option_ids = {
            option.get("id")
            for option in decision.get("options", [])
            if isinstance(option, dict) and isinstance(option.get("id"), str)
        }
        if isinstance(selected, str) and selected not in option_ids:
            report.add(
                "error",
                "decision-option-not-found",
                f"Selected option {selected!r} is not declared",
                decision_path,
            )
        resolvable_subjects = (
            set(work_by_id)
            | set(packets_by_id)
            | set(evidence_by_id)
            | set(decisions_by_id)
            | set(catalog.capabilities)
            | {str(program_payload.get("id"))}
        )
        for subject_ref in sorted(set(_strings(decision.get("subject_refs"))) - resolvable_subjects):
            report.add(
                "error",
                "decision-subject-not-found",
                f"Decision subject {subject_ref!r} cannot be resolved",
                decision_path,
            )

    learning_ids = {
        record["id"]
        for _, record in parsed["learnings"]
        if isinstance(record.get("id"), str)
    }
    learning_sources = (
        set(work_by_id)
        | set(packets_by_id)
        | set(evidence_by_id)
        | set(decisions_by_id)
        | learning_ids
    )
    for learning_path, learning in parsed["learnings"]:
        owner = principal_id(learning.get("owner"))
        if owner not in actor_ids:
            report.add(
                "error",
                "learning-owner-not-found",
                f"Learning owner {owner!r} is not declared",
                learning_path,
            )
        for source_ref in sorted(set(_strings(learning.get("source_refs"))) - learning_sources):
            report.add(
                "error",
                "learning-source-not-found",
                f"Learning source {source_ref!r} cannot be resolved",
                learning_path,
            )
        for evidence_ref in sorted(set(_strings(learning.get("evidence_refs"))) - evidence_ids):
            report.add(
                "error",
                "learning-evidence-not-found",
                f"Learning evidence {evidence_ref!r} cannot be resolved",
                learning_path,
            )

    for work_path, work in parsed["work"]:
        risk = work.get("risk") if isinstance(work.get("risk"), dict) else {}
        assurance = risk.get("assurance_level")
        workflow = catalog.workflows.get(_record_workflow_id(work) or "", {})
        if assurance_rank(assurance) < 0 or not _review_reached(work, workflow):
            continue
        packet_refs = _strings(work.get("work_packet_refs"))
        if not packet_refs:
            report.add(
                "error",
                "assurance-packet-missing",
                f"{assurance} work reaching review requires a linked work packet",
                work_path,
            )
            continue
        passing_evidence_by_id: dict[str, dict[str, Any]] = {}
        for packet_ref in packet_refs:
            packet_entry = packets_by_id.get(packet_ref)
            if packet_entry is None:
                report.add(
                    "error",
                    "work-packet-not-found",
                    f"Linked work packet {packet_ref!r} cannot be resolved",
                    work_path,
                )
                continue
            packet_path, packet = packet_entry
            producer_value = packet.get("producer")
            producer = (
                principal_id(producer_value.get("actor"))
                if isinstance(producer_value, dict)
                else principal_id(producer_value)
            )
            packet_context = (
                producer_value.get("context_manifest_digest")
                if isinstance(producer_value, dict)
                else None
            )
            packet_evidence_refs = _strings(packet.get("verification_evidence_refs"))
            if not packet_evidence_refs:
                report.add(
                    "error",
                    "assurance-evidence-missing",
                    f"{assurance} work packet has no verification evidence",
                    packet_path,
                )
            claims_authorized: set[str] = set()
            evidence_forbidden: set[str] = set()
            for evidence_ref in packet_evidence_refs:
                evidence_entry = evidence_by_id.get(evidence_ref)
                if evidence_entry is None:
                    continue
                evidence_path, evidence = evidence_entry
                if evidence.get("work_item_ref") != work.get("id"):
                    report.add(
                        "error",
                        "packet-evidence-work-mismatch",
                        f"Evidence {evidence_ref!r} belongs to a different work item",
                        evidence_path,
                    )
                    continue
                if evidence.get("result") != "pass":
                    report.add(
                        "error",
                        "packet-evidence-not-passing",
                        f"Evidence {evidence_ref!r} has result {evidence.get('result')!r} and cannot satisfy acceptance",
                        evidence_path,
                    )
                    continue
                passing_evidence_by_id[evidence_ref] = evidence
                claims_authorized.update(_strings(evidence.get("claims_authorized")))
                evidence_forbidden.update(_strings(evidence.get("claims_forbidden")))
                evidence_producer_value = evidence.get("producer")
                evidence_producer = (
                    principal_id(evidence_producer_value.get("actor"))
                    if isinstance(evidence_producer_value, dict)
                    else principal_id(evidence_producer_value)
                )
                evidence_context = (
                    evidence_producer_value.get("context_manifest_digest")
                    if isinstance(evidence_producer_value, dict)
                    else None
                )
                if (
                    assurance_rank(assurance) >= 2
                    and producer
                    and evidence_producer
                    and producer == evidence_producer
                ):
                    report.add(
                        "error",
                        "assurance-correlated-producer",
                        f"{assurance} verification evidence must be produced independently from the work packet",
                        evidence_path,
                    )
                if assurance_rank(assurance) >= 2 and (
                    not packet_context
                    or not evidence_context
                    or packet_context == evidence_context
                ):
                    report.add(
                        "error",
                        "assurance-context-isolation",
                        f"{assurance} verification requires distinct producer and evidence context digests",
                        evidence_path,
                    )
                if assurance_rank(assurance) >= 2:
                    approval = principal_id(evidence.get("approval_ref"))
                    if (
                        not approval
                        or actors_by_id.get(approval, {}).get("kind") != "human"
                        or approval != work.get("accountable_human")
                    ):
                        report.add(
                            "error",
                            "assurance-human-acceptance",
                            f"{assurance} evidence requires acceptance by the work item's accountable human",
                            evidence_path,
                        )
                    elif assurance_rank(assurance) >= 3:
                        approver = actors_by_id.get(approval, {})
                        if approval in {producer, evidence_producer}:
                            report.add(
                                "error",
                                "assurance-separate-approver",
                                "A3 approver must be separate from producer and validator",
                                evidence_path,
                            )
                        if approver.get("kind") != "human" or not _strings(
                            approver.get("specialist_domains")
                        ):
                            report.add(
                                "error",
                                "assurance-specialist-approval",
                                "A3 evidence requires a declared specialist human approver",
                                evidence_path,
                            )
            claims_requested = set(_strings(packet.get("claims_requested")))
            claims_forbidden = set(_strings(packet.get("claims_forbidden"))) | evidence_forbidden
            unsupported_claims = sorted(claims_requested - claims_authorized)
            if unsupported_claims:
                report.add(
                    "error",
                    "claim-authority-gap",
                    "Work packet requests claims not authorized by evidence: "
                    + ", ".join(unsupported_claims),
                    packet_path,
                )
            conflicting_claims = sorted(claims_requested & claims_forbidden)
            if conflicting_claims:
                report.add(
                    "error",
                    "claim-boundary-conflict",
                    "Work packet requests explicitly forbidden claims: "
                    + ", ".join(conflicting_claims),
                    packet_path,
                )

        passing_evidence = list(passing_evidence_by_id.values())
        observed_acceptance = {
            acceptance_ref
            for evidence in passing_evidence
            for acceptance_ref in _strings(evidence.get("acceptance_refs"))
        }
        acceptance_ids = {
            item["id"]
            for item in work.get("acceptance", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        missing_acceptance = sorted(acceptance_ids - observed_acceptance)
        if missing_acceptance:
            report.add(
                "error",
                "acceptance-evidence-gap",
                "No linked evidence observes acceptance criteria: "
                + ", ".join(missing_acceptance),
                work_path,
            )

        observed_kinds = {
            evidence["kind"]
            for evidence in passing_evidence
            if isinstance(evidence.get("kind"), str)
        }
        normalized_work = dict(work)
        normalized_work["_baseline_risk"] = program_payload.get("risk_defaults", {}).get(
            "baseline", "medium"
        )
        routed_evidence = set(route_record(normalized_work, catalog).required_evidence)
        missing_routed_evidence = sorted(routed_evidence - observed_kinds)
        if missing_routed_evidence:
            report.add(
                "error",
                "required-evidence-kind-missing",
                "No passing receipt supplies routed evidence kinds: "
                + ", ".join(missing_routed_evidence),
                work_path,
            )

        for plan in work.get("evidence_plan", []):
            if not isinstance(plan, dict) or not isinstance(plan.get("acceptance_ref"), str):
                continue
            acceptance_ref = plan["acceptance_ref"]
            expected_environment = plan.get("environment")
            for expected_kind in _strings(plan.get("kinds")):
                planned_match = any(
                    evidence.get("work_item_ref") == work.get("id")
                    and evidence.get("kind") == expected_kind
                    and acceptance_ref in _strings(evidence.get("acceptance_refs"))
                    and (
                        not isinstance(expected_environment, str)
                        or (
                            evidence.get("method", {}).get("environment")
                            if isinstance(evidence.get("method"), dict)
                            else None
                        )
                        == expected_environment
                    )
                    for evidence in passing_evidence
                )
                if not planned_match:
                    report.add(
                        "error",
                        "evidence-plan-unsatisfied",
                        "No passing evidence matches planned tuple "
                        f"({acceptance_ref}, {expected_kind}, {expected_environment})",
                        work_path,
                    )


def validate_project(
    root: Path,
    *,
    catalog: Catalog | None = None,
    framework: Path | None = None,
) -> ValidationReport:
    report = ValidationReport()
    try:
        project_root, overlay = locate_overlay(root)
    except FileNotFoundError as error:
        report.add("error", "manifest-not-found", str(error), root)
        return report
    report.project_root = project_root
    report.overlay = overlay
    manifest_path = overlay / "program.yaml"
    try:
        program = load_yaml(manifest_path)
    except (OSError, ValueError) as error:
        report.add("error", "manifest-parse", str(error), manifest_path)
        return report
    report.program = program
    try:
        catalog = catalog or load_catalog(framework)
    except (OSError, ValueError) as error:
        report.add("error", "catalog-load", str(error), framework)
        return report

    _validate_program_shape(program, manifest_path, report)
    _validate_json_schema_if_available(program, "program", manifest_path, catalog, report)
    _validate_framework_lock(program, catalog, manifest_path, report)
    _validate_program_catalog_refs(program, catalog, manifest_path, report)
    _validate_source(program, project_root, manifest_path, report)
    _validate_capabilities(program, catalog, manifest_path, report)
    _validate_actors(program, catalog, manifest_path, report)
    _validate_records(program, overlay, catalog, report)
    try:
        from .rendering import expected_rendered

        generated_root, expected = expected_rendered(root, catalog=catalog)
        for name, content in expected.items():
            path = generated_root / name
            normalized = content.rstrip() + "\n"
            if not path.exists():
                report.add(
                    "warning",
                    "generated-view-missing",
                    f"Generated view {name} is missing; run agentic render",
                    path,
                )
            elif path.read_text(encoding="utf-8") != normalized:
                report.add(
                    "error",
                    "generated-view-drift",
                    f"Generated view {name} is stale; run agentic render",
                    path,
                )
    except (OSError, ValueError) as error:
        report.add("error", "render-check", str(error), overlay / "generated")
    return report


def validate_framework(root: Path) -> ValidationReport:
    root = root.resolve()
    if not (root / "catalog").is_dir() and (root / "agentic_engineering" / "catalog").is_dir():
        root = root / "agentic_engineering"
    report = ValidationReport(project_root=root, overlay=root)
    try:
        catalog = load_catalog(root)
    except (OSError, ValueError) as error:
        report.add("error", "catalog-load", str(error), root / "catalog")
        return report

    for issue in validate_policy_shapes(catalog):
        report.add("error", issue.code, issue.message, root / "catalog" / issue.filename)

    framework_yaml = list((root / "catalog").rglob("*.yaml")) + list(
        (root / "presets").glob("*.yaml")
    )
    for path in sorted(framework_yaml):
        try:
            document = load_yaml(path)
        except (OSError, ValueError):
            continue
        if document.get("framework_version") != __version__:
            report.add(
                "error",
                "framework-asset-version",
                f"Asset framework_version must match package version {__version__}",
                path,
            )

    if not catalog.capabilities:
        report.add("error", "capability-catalog-empty", "No capabilities are defined", root)
    for capability_id, metadata in catalog.capabilities.items():
        path = root / "catalog" / "capabilities.yaml"
        if metadata.get("default") not in {"required", "conditional"}:
            report.add(
                "error",
                "capability-default",
                f"Capability {capability_id!r} has an invalid default disposition",
                path,
            )
        if not _strings(metadata.get("activation_triggers")):
            report.add(
                "error",
                "capability-activation",
                f"Capability {capability_id!r} needs activation_triggers",
                path,
            )
        if not _strings(metadata.get("expected_outputs")):
            report.add(
                "error",
                "capability-outputs",
                f"Capability {capability_id!r} needs expected_outputs",
                path,
            )
    role_ids: set[str] = set()
    provided_capabilities: set[str] = set()
    for path in sorted((root / "team").glob("*.md")):
        if path.name == "README.md":
            continue
        try:
            metadata, _ = parse_markdown_record(path)
        except ValueError as error:
            report.add("error", "role-metadata", str(error), path)
            continue
        role_id = metadata.get("id")
        if not isinstance(role_id, str) or not role_id:
            report.add("error", "role-id", "Role id is required", path)
        elif role_id in role_ids:
            report.add("error", "duplicate-role-id", f"Duplicate role id {role_id!r}", path)
        else:
            role_ids.add(role_id)
        provides = _strings(metadata.get("provides"))
        if not provides:
            report.add("error", "role-capabilities", "Role must provide capabilities", path)
        for capability_id in provides:
            provided_capabilities.add(capability_id)
            if capability_id not in catalog.capabilities:
                report.add(
                    "error",
                    "role-capability-unknown",
                    f"Role provides unknown capability {capability_id!r}",
                    path,
                )
        if metadata.get("independent_when_risk_at_least") not in {
            "low",
            "medium",
            "high",
            "critical",
        }:
            report.add(
                "error",
                "role-independence",
                "independent_when_risk_at_least must be a known risk tier",
                path,
            )
        triggers = metadata.get("activation_triggers")
        if not isinstance(triggers, list) or not triggers or not all(
            isinstance(trigger, str) and trigger.strip() for trigger in triggers
        ):
            report.add(
                "error",
                "role-activation-triggers",
                "activation_triggers must be a non-empty list of strings",
                path,
            )
        if metadata.get("permission_ceiling") not in permission_order(catalog):
            report.add(
                "error",
                "role-permission-ceiling",
                f"Unknown role permission ceiling {metadata.get('permission_ceiling')!r}",
                path,
            )

    for capability_id in sorted(set(catalog.capabilities) - provided_capabilities):
        report.add(
            "error",
            "capability-role-provider-missing",
            f"No default role lens provides capability {capability_id!r}",
            root / "team",
        )

    for workflow_id, workflow in catalog.workflows.items():
        path = Path(str(workflow.get("_path", root / "catalog" / "workflows" / workflow_id)))
        states = workflow_states(workflow)
        if not states:
            report.add("error", "workflow-states", "Workflow has no states", path)
            continue
        transitions = workflow_transitions(workflow)
        initial_state = workflow.get("initial_state")
        if initial_state not in states:
            report.add(
                "error",
                "workflow-initial-state",
                f"Workflow initial_state {initial_state!r} is not declared",
                path,
            )
        else:
            reachable = {initial_state}
            frontier = [initial_state]
            while frontier:
                source = frontier.pop()
                for target in transitions.get(source, set()):
                    if target not in reachable:
                        reachable.add(target)
                        frontier.append(target)
            for state in sorted(set(states) - reachable):
                report.add(
                    "error",
                    "workflow-unreachable-state",
                    f"Workflow state {state!r} is unreachable from {initial_state!r}",
                    path,
                )
        for state in _strings(workflow.get("assurance_states")):
            if state not in states:
                report.add(
                    "error",
                    "workflow-assurance-state",
                    f"Assurance state {state!r} is not declared by the workflow",
                    path,
                )
        for source, targets in transitions.items():
            if source not in states:
                report.add(
                    "error",
                    "workflow-transition-source",
                    f"Transition source {source!r} is not a workflow state",
                    path,
                )
            for target in targets:
                if target not in states:
                    report.add(
                        "error",
                        "workflow-transition-target",
                        f"Transition target {target!r} is not a workflow state",
                        path,
                    )

    order = risk_order(catalog)
    if order != ["low", "medium", "high", "critical"]:
        report.add(
            "warning",
            "risk-order",
            f"Risk order is {order}; expected low, medium, high, critical",
            root / "catalog" / "risk_policy.yaml",
        )

    schema_root = root / "schemas" / "v1"
    required_schemas = {"program", "work_item", "work_packet", "evidence", "decision", "learning"}
    for schema_name in sorted(required_schemas):
        path = schema_root / f"{schema_name}.schema.json"
        if not path.is_file():
            report.add("error", "schema-missing", f"Missing {path.name}", path)
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            report.add("error", "schema-parse", str(error), path)
            continue
        if not isinstance(data, dict) or data.get("type") != "object":
            report.add("error", "schema-root", "Schema root must describe an object", path)
            continue
        framework_property = data.get("properties", {}).get("framework_version", {})
        if framework_property.get("const") != __version__:
            report.add(
                "error",
                "schema-framework-version",
                f"Schema framework_version const must match package version {__version__}",
                path,
            )
        try:
            import jsonschema

            jsonschema.Draft202012Validator.check_schema(data)
        except ImportError:
            report.add(
                "error",
                "schema-validator-missing",
                "jsonschema is required to validate framework schemas",
                path,
            )
        except jsonschema.exceptions.SchemaError as error:
            report.add("error", "schema-invalid", error.message, path)

    for path in sorted((root / "presets").glob("*.yaml")):
        try:
            data = load_yaml(path)
        except (OSError, ValueError) as error:
            report.add("error", "preset-parse", str(error), path)
            continue
        program = data.get("program", data)
        if not isinstance(program, dict):
            report.add("error", "preset-shape", "Preset must contain a mapping", path)
            continue
        preset = data.get("preset", data)
        if not isinstance(preset, dict) or not isinstance(preset.get("id"), str):
            report.add("error", "preset-id", "Preset must declare preset.id", path)
            continue
        capability_defaults = preset.get("capability_defaults")
        if not isinstance(capability_defaults, dict):
            report.add(
                "error", "preset-capabilities", "Preset needs capability_defaults", path
            )
        else:
            active = set(_strings(capability_defaults.get("active")))
            conditional = set(_strings(capability_defaults.get("conditional")))
            for capability_id in sorted((active | conditional) - set(catalog.capabilities)):
                report.add(
                    "error",
                    "preset-capability-unknown",
                    f"Preset references unknown capability {capability_id!r}",
                    path,
                )
            for capability_id in sorted(active & conditional):
                report.add(
                    "error",
                    "preset-capability-conflict",
                    f"Preset marks capability {capability_id!r} both active and conditional",
                    path,
                )
        questions = _strings(preset.get("required_tailoring_questions"))
        if not questions:
            report.add(
                "error",
                "preset-tailoring-questions",
                "Preset must declare required_tailoring_questions",
                path,
            )
        workflow_defaults = preset.get("workflow_defaults")
        if isinstance(workflow_defaults, dict):
            for workflow_id in workflow_defaults.values():
                if workflow_id not in catalog.workflows:
                    report.add(
                        "error",
                        "preset-workflow-unknown",
                        f"Preset references unknown workflow {workflow_id!r}",
                        path,
                    )
        risk_defaults = preset.get("risk_defaults")
        if not isinstance(risk_defaults, dict) or risk_defaults.get("baseline") not in order:
            report.add(
                "error",
                "preset-risk-baseline",
                "Preset must declare a known risk_defaults.baseline",
                path,
            )
    return report


def render_report(report: ValidationReport, *, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(report.as_dict(), indent=2, sort_keys=True)
    lines = [
        f"Validation {'passed' if report.ok else 'failed'}: "
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)"
    ]
    for issue in report.issues:
        location = f" [{issue.path}]" if issue.path else ""
        lines.append(f"- {issue.severity.upper()} {issue.code}: {issue.message}{location}")
    return "\n".join(lines)
