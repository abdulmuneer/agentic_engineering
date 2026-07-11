from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from agentic_engineering import __version__

from .catalog import Catalog, load_catalog
from .io import dump_yaml, framework_root, load_record, load_yaml, locate_overlay, record_files
from .rendering import render_project
from .routing import assurance_rank, permission_order, route_record


PERMISSION_CLASSES = (
    "read_only",
    "local_write",
    "external_read",
    "external_write",
    "sensitive",
    "production",
)
PACKET_LOOP_TYPES = (
    "discovery",
    "requirements",
    "design",
    "implementation",
    "review",
    "test",
    "release",
    "incident",
    "learning",
    "research_spike",
)
EVIDENCE_KINDS = (
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
)
DECISION_TYPES = (
    "discovery",
    "product",
    "requirements",
    "experience",
    "architecture",
    "security",
    "delivery",
    "release",
    "risk_acceptance",
    "incident",
    "learning",
)
DECISION_OUTCOMES = (
    "commit",
    "narrow",
    "kill",
    "park",
    "approve",
    "reject",
    "go",
    "no_go",
    "accept_risk",
    "mitigate",
    "custom",
)
OUTPUT_KINDS = ("file", "commit", "artifact", "document", "decision", "finding", "other")
CONTEXT_KINDS = ("file", "document", "ticket", "log", "command", "source", "assumption", "other")


@dataclass(frozen=True)
class ProjectContext:
    project_root: Path
    overlay: Path
    document: dict[str, Any]
    program: dict[str, Any]
    actors: dict[str, dict[str, Any]]
    framework: Path
    catalog: Catalog


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _decision_authorizes(
    decision: dict[str, Any], *, work_id: str, actor_id: str, permissions: set[str]
) -> bool:
    outcome = decision.get("outcome") if isinstance(decision.get("outcome"), dict) else {}
    authorization = (
        decision.get("authorization") if isinstance(decision.get("authorization"), dict) else {}
    )
    return (
        outcome.get("disposition") in {"approve", "go", "commit"}
        and work_id in decision.get("subject_refs", [])
        and actor_id in authorization.get("actor_refs", [])
        and permissions <= set(authorization.get("permission_classes", []))
        and _unexpired(authorization.get("expires_at"))
    )


def _project_context(target: Path, framework: Path | None) -> ProjectContext:
    project_root, overlay = locate_overlay(target.resolve())
    document = load_yaml(overlay / "program.yaml")
    program = document.get("program", document)
    if not isinstance(program, dict):
        raise ValueError("program.yaml does not contain a program mapping")
    actors = {
        item.get("id"): item
        for item in program.get("actors", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    resolved_framework = (framework or framework_root()).resolve()
    return ProjectContext(
        project_root=project_root,
        overlay=overlay,
        document=document,
        program=program,
        actors=actors,
        framework=resolved_framework,
        catalog=load_catalog(resolved_framework),
    )


def _actor(context: ProjectContext, actor_id: str, *, human: bool = False) -> dict[str, Any]:
    actor = context.actors.get(actor_id)
    if actor is None:
        raise ValueError(f"Actor {actor_id!r} is not declared in program.yaml")
    if human and actor.get("kind") != "human":
        raise ValueError(f"Actor {actor_id!r} must be a declared human")
    return actor


def _require_tailored(context: ProjectContext) -> None:
    tailoring = context.program.get("tailoring")
    if not isinstance(tailoring, dict) or tailoring.get("status") != "confirmed":
        raise ValueError(
            "Project tailoring is pending; confirm the operating model before execution records"
        )


def _find_record(context: ProjectContext, kind: str, record_id: str) -> tuple[Path, dict[str, Any]]:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in record_files(context.overlay, kind):
        record, _ = load_record(path)
        if record.get("id") == record_id:
            matches.append((path, record))
    if not matches:
        raise FileNotFoundError(f"No {kind} record has id {record_id!r}")
    if len(matches) > 1:
        raise ValueError(f"Record id {record_id!r} is ambiguous: {', '.join(str(p) for p, _ in matches)}")
    return matches[0]


def _record_index(context: ProjectContext) -> dict[str, tuple[str, Path, dict[str, Any]]]:
    result: dict[str, tuple[str, Path, dict[str, Any]]] = {}
    for kind in ("work", "packets", "evidence", "decisions", "learnings"):
        for path in record_files(context.overlay, kind):
            record, _ = load_record(path)
            record_id = record.get("id")
            if not isinstance(record_id, str):
                continue
            if record_id in result:
                raise ValueError(f"Duplicate record id {record_id!r} prevents safe authoring")
            result[record_id] = (kind, path, record)
    return result


def _destination(context: ProjectContext, kind: str, record_id: str) -> Path:
    aliases = {
        "packets": ("work_packets", "packets"),
        "decisions": ("decisions",),
        "evidence": ("evidence",),
    }[kind]
    candidates = [context.overlay / "records" / aliases[0]] + [
        context.overlay / alias for alias in aliases
    ]
    directory = next((candidate for candidate in candidates if candidate.is_dir()), candidates[0])
    return directory / f"{record_id}.yaml"


def _raw_envelope(path: Path, envelope: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if path.suffix not in {".yaml", ".yml"}:
        raise ValueError(f"Safe backlink updates require a canonical YAML record: {path}")
    document = load_yaml(path)
    payload = document.get(envelope)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} does not contain a {envelope} envelope")
    return document, payload


def _append_unique(payload: dict[str, Any], key: str, value: str) -> None:
    current = payload.setdefault(key, [])
    if not isinstance(current, list):
        raise ValueError(f"{key} must be a list before it can be updated")
    if value not in current:
        current.append(value)


def _validate_schema(
    context: ProjectContext, document: dict[str, Any], schema_name: str, path: Path
) -> None:
    try:
        import jsonschema
    except ImportError as error:
        raise ValueError("jsonschema is required to author canonical records") from error
    schema_path = context.framework / "schemas" / "v1" / f"{schema_name}.schema.json"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Canonical schema is not installed: {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    if errors:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors[:5]
        )
        raise ValueError(f"Refusing to write schema-invalid {schema_name} record {path}: {details}")


def _commit_documents(documents: dict[Path, dict[str, Any]], *, new_path: Path) -> None:
    if new_path.exists():
        raise FileExistsError(f"Record already exists: {new_path}")
    originals = {path: path.read_bytes() if path.exists() else None for path in documents}
    staged: list[tuple[Path, Path]] = []
    replaced: list[Path] = []
    try:
        for path, document in documents.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            handle, raw_temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
            temp = Path(raw_temp)
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(dump_yaml(document))
            staged.append((temp, path))
        for temp, path in staged:
            os.replace(temp, path)
            replaced.append(path)
    except Exception:
        for path in reversed(replaced):
            original = originals[path]
            if original is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(original)
        raise
    finally:
        for temp, _ in staged:
            temp.unlink(missing_ok=True)


def _relative(project_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _parse_pairs(values: Iterable[str], *, label: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for value in values:
        if "=" not in value:
            raise ValueError(f"{label} must use KEY=VALUE syntax: {value!r}")
        key, item = value.split("=", 1)
        if not key.strip() or not item.strip():
            raise ValueError(f"{label} must contain non-empty KEY and VALUE: {value!r}")
        result.append((key.strip(), item.strip()))
    return result


def _parse_artifacts(values: Iterable[str]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for value in values:
        if "=" not in value:
            raise ValueError(f"Artifact must use URI=SHA256_HEX syntax: {value!r}")
        uri, digest = value.rsplit("=", 1)
        result.append({"uri": uri.strip(), "sha256": digest.strip()})
    return result


def _subject_matches_packet(
    subject: dict[str, str],
    packet: dict[str, Any],
    artifacts: list[dict[str, str]],
    *,
    kind: str,
) -> bool:
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
        if kind in {"review", "document", "user_research"}:
            return reference in {packet.get("id"), packet.get("work_item_ref")}
        return False
    artifact_digest = subject.get("artifact_digest")
    if isinstance(artifact_digest, str):
        if any(item.get("digest") == artifact_digest for item in outputs):
            return True
        raw_digest = artifact_digest.removeprefix("sha256:")
        return any(
            artifact.get("uri") in output_refs and artifact.get("sha256") == raw_digest
            for artifact in artifacts
        )
    commit = subject.get("commit")
    if isinstance(commit, str):
        return any(item.get("kind") == "commit" and item.get("ref") == commit for item in outputs)
    release_ref = subject.get("release_ref")
    if isinstance(release_ref, str):
        return release_ref in output_refs
    return False


def _permission_subset(
    context: ProjectContext, actor: dict[str, Any], permissions: Iterable[str]
) -> None:
    order = permission_order(context.catalog)
    ceiling = actor.get("permission_ceiling")
    if ceiling not in order:
        raise ValueError(f"Actor {actor.get('id')!r} has an invalid permission ceiling")
    invalid = [permission for permission in permissions if permission not in order]
    if invalid:
        raise ValueError(f"Unknown permission classes: {', '.join(invalid)}")
    excessive = [permission for permission in permissions if order.index(permission) > order.index(ceiling)]
    if excessive:
        raise ValueError(
            f"Requested permission exceeds actor {actor.get('id')!r} ceiling {ceiling!r}: "
            + ", ".join(excessive)
        )


def create_work_packet(
    target: Path,
    packet_id: str,
    *,
    work_id: str,
    producer_id: str,
    run_id: str,
    goal: str,
    claims_requested: list[str],
    output_kind: str,
    output_ref: str,
    output_summary: str,
    claims_forbidden: list[str] | None = None,
    output_digest: str | None = None,
    loop_type: str | None = None,
    capability_refs: list[str] | None = None,
    permission_classes: list[str] | None = None,
    contexts: list[str] | None = None,
    skill_refs: list[str] | None = None,
    tooling: list[str] | None = None,
    context_manifest_digest: str | None = None,
    approval_refs: list[str] | None = None,
    action_receipt_refs: list[str] | None = None,
    framework: Path | None = None,
) -> Path:
    context = _project_context(target, framework)
    _require_tailored(context)
    index = _record_index(context)
    if packet_id in index:
        raise FileExistsError(f"Record id already exists: {packet_id}")
    work_path, work = _find_record(context, "work", work_id)
    producer = _actor(context, producer_id)
    accountable = work.get("accountable_human")
    if not isinstance(accountable, str):
        raise ValueError(f"Work item {work_id!r} has no accountable_human")
    _actor(context, accountable, human=True)

    routed_work = dict(work)
    risk_defaults = context.program.get("risk_defaults", {})
    if isinstance(risk_defaults, dict):
        routed_work["_program_risk_defaults"] = risk_defaults
        if isinstance(risk_defaults.get("baseline"), str):
            routed_work["_baseline_risk"] = risk_defaults["baseline"]
    route = route_record(routed_work, context.catalog)
    work_risk = work.get("risk") if isinstance(work.get("risk"), dict) else {}
    if work_risk.get("effective_tier") != route.computed_risk:
        raise ValueError(
            f"Work item {work_id!r} records risk {work_risk.get('effective_tier')!r}, "
            f"but routing computes {route.computed_risk!r}; reconcile it before creating a packet"
        )
    if assurance_rank(work_risk.get("assurance_level")) < assurance_rank(
        route.minimum_assurance
    ):
        raise ValueError(
            f"Work item {work_id!r} records assurance {work_risk.get('assurance_level')!r}, "
            f"but routing requires {route.minimum_assurance}"
        )
    actor_capabilities = {
        item for item in producer.get("capabilities", []) if isinstance(item, str)
    }
    required = {
        item for item in work.get("required_capabilities", []) if isinstance(item, str)
    }
    missing_routed_capabilities = set(route.required_capabilities) - required
    if missing_routed_capabilities:
        raise ValueError(
            f"Work item {work_id!r} is missing capabilities derived by routing: "
            + ", ".join(sorted(missing_routed_capabilities))
            + ". Update and review the work item before creating an execution packet."
        )
    selected_capabilities = list(dict.fromkeys(capability_refs or sorted(required & actor_capabilities)))
    if not selected_capabilities:
        raise ValueError(
            f"Producer {producer_id!r} provides none of the capabilities required by {work_id!r}"
        )
    unknown_capabilities = set(selected_capabilities) - required
    unavailable_capabilities = set(selected_capabilities) - actor_capabilities
    if unknown_capabilities:
        raise ValueError(
            "Packet capabilities are outside the routed work scope: "
            + ", ".join(sorted(unknown_capabilities))
        )
    if unavailable_capabilities:
        raise ValueError(
            f"Producer {producer_id!r} does not provide: "
            + ", ".join(sorted(unavailable_capabilities))
        )

    work_permissions = {
        item for item in work.get("permission_classes", []) if isinstance(item, str)
    }
    missing_routed_permissions = set(route.permissions) - work_permissions
    if missing_routed_permissions:
        raise ValueError(
            f"Work item {work_id!r} is missing permissions derived by routing: "
            + ", ".join(sorted(missing_routed_permissions))
            + ". Update and approve the work item before creating an execution packet."
        )
    planned_kinds = {
        kind_name
        for plan in work.get("evidence_plan", [])
        if isinstance(plan, dict)
        for kind_name in plan.get("kinds", [])
        if isinstance(kind_name, str)
    }
    missing_evidence = set(route.required_evidence) - planned_kinds
    if missing_evidence:
        raise ValueError(
            f"Work item {work_id!r} is missing routed evidence kinds: "
            + ", ".join(sorted(missing_evidence))
        )
    selected_permissions = list(dict.fromkeys(permission_classes or sorted(work_permissions)))
    outside_work_permissions = set(selected_permissions) - work_permissions
    if outside_work_permissions:
        raise ValueError(
            "Packet permissions are outside the authorized work scope: "
            + ", ".join(sorted(outside_work_permissions))
        )
    _permission_subset(context, producer, selected_permissions)
    if output_kind not in OUTPUT_KINDS:
        raise ValueError(f"Unknown output kind {output_kind!r}")
    workflow_id = work.get("workflow", work.get("route"))
    derived_loop = {
        "discovery": "discovery",
        "research_spike": "research_spike",
        "feature": "implementation",
        "bug_fix": "implementation",
        "incident": "incident",
        "release": "release",
    }.get(workflow_id, "implementation")
    selected_loop = loop_type or derived_loop
    if selected_loop not in PACKET_LOOP_TYPES:
        raise ValueError(f"Unknown packet loop type {selected_loop!r}")
    work_mode = {
        "human": "human_led",
        "agent": "agent_executed_human_review",
        "automation": "agent_assisted",
    }.get(producer.get("kind"))
    if work_mode is None:
        raise ValueError(f"Actor {producer_id!r} has an invalid kind")
    if (
        assurance_rank(route.minimum_assurance) >= 1
        and not context_manifest_digest
    ):
        raise ValueError(
            f"{route.minimum_assurance} packets require --context-digest"
        )

    resolved_approvals = list(dict.fromkeys(approval_refs or []))
    for approval in resolved_approvals:
        entry = index.get(approval)
        if entry is None or entry[0] != "decisions":
            raise ValueError(f"Packet approval decision {approval!r} cannot be resolved")
    elevated = set(selected_permissions) & {"external_write", "sensitive", "production"}
    if elevated and not any(
        _decision_authorizes(
            index[approval][2],
            work_id=work_id,
            actor_id=producer_id,
            permissions=elevated,
        )
        for approval in resolved_approvals
    ):
        raise ValueError(
            "Elevated packet permissions require an unexpired decision bound to the work, "
            "producer, and requested permission classes"
        )
    resolved_actions = list(dict.fromkeys(action_receipt_refs or []))
    for receipt in resolved_actions:
        entry = index.get(receipt)
        if entry is None or entry[0] != "evidence":
            raise ValueError(f"Packet action receipt {receipt!r} cannot be resolved")

    producer_record: dict[str, Any] = {
        "actor": producer_id,
        "actor_kind": producer["kind"],
        "run_id": run_id,
        "skill_refs": list(dict.fromkeys(skill_refs or [])),
        "tooling": list(dict.fromkeys(tooling or [])),
    }
    if context_manifest_digest:
        producer_record["context_manifest_digest"] = context_manifest_digest
    output: dict[str, Any] = {
        "kind": output_kind,
        "ref": output_ref,
        "summary": output_summary,
    }
    if output_digest:
        output["digest"] = output_digest
    context_items: list[dict[str, str]] = [
        {"kind": "file", "ref": _relative(context.project_root, work_path)}
    ]
    for kind, reference in _parse_pairs(contexts or [], label="Context"):
        if kind not in CONTEXT_KINDS:
            raise ValueError(f"Unknown context kind {kind!r}")
        context_items.append({"kind": kind, "ref": reference})

    document = {
        "schema_version": 1,
        "framework_version": __version__,
        "work_packet": {
            "id": packet_id,
            "work_item_ref": work_id,
            "date": datetime.now(timezone.utc).date().isoformat(),
            "work_mode": work_mode,
            "loop_type": selected_loop,
            "accountable_human": accountable,
            "producer": producer_record,
            "capability_refs": selected_capabilities,
            "permission_classes": selected_permissions,
            "approval_refs": resolved_approvals,
            "action_receipt_refs": resolved_actions,
            "status": "draft",
            "goal": goal,
            "context": context_items,
            "assumptions": [],
            "changes_or_outputs": [output],
            "verification_evidence_refs": [],
            "claims_requested": list(dict.fromkeys(claims_requested)),
            "claims_forbidden": list(dict.fromkeys(claims_forbidden or [])),
            "skipped_checks": [],
            "risks": [],
            "open_questions": [],
            "review_refs": [],
            "promotion_candidates": [],
        },
    }
    destination = _destination(context, "packets", packet_id)
    work_document, work_payload = _raw_envelope(work_path, "work_item")
    _append_unique(work_payload, "work_packet_refs", packet_id)
    _validate_schema(context, document, "work_packet", destination)
    _validate_schema(context, work_document, "work_item", work_path)
    _commit_documents({destination: document, work_path: work_document}, new_path=destination)
    render_project(context.project_root, catalog=context.catalog)
    return destination


def create_decision(
    target: Path,
    decision_id: str,
    *,
    decision_type: str,
    title: str,
    subject_refs: list[str],
    options: list[str],
    outcome: str,
    selected_option_ref: str,
    rationale: str,
    owner_id: str,
    reviewer_ids: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    guard_authorizations: list[str] | None = None,
    decided_at: str | None = None,
    successor_ref: str | None = None,
    custom_value: str | None = None,
    revisit_at: str | None = None,
    revisit_when: list[str] | None = None,
    authorize_permissions: list[str] | None = None,
    authorize_actors: list[str] | None = None,
    action_scope: str | None = None,
    authorization_expires_at: str | None = None,
    source_update_path: str | None = None,
    source_update_version: str | None = None,
    source_update_sha256: str | None = None,
    from_tier: str | None = None,
    to_tier: str | None = None,
    risk_expires_at: str | None = None,
    compensating_controls: list[str] | None = None,
    framework: Path | None = None,
) -> Path:
    context = _project_context(target, framework)
    index = _record_index(context)
    if decision_id in index:
        raise FileExistsError(f"Record id already exists: {decision_id}")
    if decision_type not in DECISION_TYPES:
        raise ValueError(f"Unknown decision type {decision_type!r}")
    if outcome not in DECISION_OUTCOMES:
        raise ValueError(f"Unknown decision outcome {outcome!r}")
    _actor(context, owner_id, human=True)
    reviewers = list(dict.fromkeys(reviewer_ids or []))
    for reviewer in reviewers:
        _actor(context, reviewer)
    evidence_ids = list(dict.fromkeys(evidence_refs or []))
    for evidence_id in evidence_ids:
        _find_record(context, "evidence", evidence_id)

    subjects: list[tuple[str, Path | None, dict[str, Any] | None]] = []
    for subject in dict.fromkeys(subject_refs):
        if subject == context.program.get("id"):
            subjects.append(("program", None, context.program))
            continue
        if subject in context.catalog.capabilities:
            subjects.append(("capability", None, context.catalog.capabilities[subject]))
            continue
        entry = index.get(subject)
        if entry is None:
            raise ValueError(f"Decision subject {subject!r} cannot be resolved")
        subjects.append(entry)
    parsed_options = [
        {"id": option_id, "summary": summary}
        for option_id, summary in _parse_pairs(options, label="Option")
    ]
    option_ids = {option["id"] for option in parsed_options}
    if selected_option_ref not in option_ids:
        raise ValueError(f"Selected option {selected_option_ref!r} is not declared by --option")
    outcome_record: dict[str, Any] = {
        "disposition": outcome,
        "selected_option_ref": selected_option_ref,
    }
    if outcome == "narrow":
        if not successor_ref:
            raise ValueError("A narrow decision requires --successor-ref")
        outcome_record["successor_ref"] = successor_ref
    if outcome == "custom":
        if not custom_value:
            raise ValueError("A custom decision requires --custom-value")
        outcome_record["custom_value"] = custom_value

    decision: dict[str, Any] = {
        "id": decision_id,
        "type": decision_type,
        "title": title,
        "subject_refs": list(dict.fromkeys(subject_refs)),
        "options": parsed_options,
        "outcome": outcome_record,
        "rationale": rationale,
        "owner": owner_id,
        "reviewers": reviewers,
        "evidence_refs": evidence_ids,
        "decided_at": decided_at or _now(),
    }
    if guard_authorizations:
        decision["guard_authorizations"] = list(dict.fromkeys(guard_authorizations))
    if revisit_at:
        decision["revisit_at"] = revisit_at
    if revisit_when:
        decision["revisit_when"] = list(dict.fromkeys(revisit_when))

    authorization_values = (
        authorize_permissions,
        authorize_actors,
        action_scope,
        authorization_expires_at,
    )
    if any(authorization_values):
        if not all(authorization_values):
            raise ValueError(
                "Authorization requires --authorize-permission, --authorize-actor, "
                "--action-scope, and --authorization-expires-at"
            )
        if not _unexpired(authorization_expires_at):
            raise ValueError("Authorization expiry must be a valid future date-time")
        authorized_actors = list(dict.fromkeys(authorize_actors or []))
        authorized_permissions = list(dict.fromkeys(authorize_permissions or []))
        for actor_id in authorized_actors:
            actor = _actor(context, actor_id)
            _permission_subset(context, actor, authorized_permissions)
        decision["authorization"] = {
            "permission_classes": authorized_permissions,
            "actor_refs": authorized_actors,
            "action_scope": action_scope,
            "expires_at": authorization_expires_at,
        }

    source_update_values = (
        source_update_path,
        source_update_version,
        source_update_sha256,
    )
    if any(source_update_values):
        if not all(source_update_values):
            raise ValueError(
                "Source-update approval requires --source-path, --source-version, "
                "and --source-sha256"
            )
        decision["source_update"] = {
            "path": source_update_path,
            "declared_version": source_update_version,
            "sha256": source_update_sha256,
        }

    if decision_type == "risk_acceptance":
        if outcome != "accept_risk":
            raise ValueError("A risk_acceptance decision must use --outcome accept_risk")
        if not all((from_tier, to_tier, risk_expires_at, compensating_controls)):
            raise ValueError(
                "Risk acceptance requires --from-tier, --to-tier, --risk-expires-at, "
                "and --compensating-control"
            )
        order = ["low", "medium", "high", "critical"]
        if from_tier not in order or to_tier not in order:
            raise ValueError("Risk tiers must be low, medium, high, or critical")
        if from_tier == "critical" and order.index(to_tier) < order.index(from_tier):
            raise ValueError("Critical risk cannot be downgraded")
        if not _unexpired(risk_expires_at):
            raise ValueError("Risk acceptance expiry must be a valid future date-time")
        decision["risk_acceptance"] = {
            "from_tier": from_tier,
            "to_tier": to_tier,
            "expires_at": risk_expires_at,
            "compensating_controls": list(dict.fromkeys(compensating_controls or [])),
        }

    document = {
        "schema_version": 1,
        "framework_version": __version__,
        "decision": decision,
    }
    destination = _destination(context, "decisions", decision_id)
    documents: dict[Path, dict[str, Any]] = {destination: document}
    approving = outcome in {"commit", "approve", "go", "accept_risk"}
    for kind, path, _ in subjects:
        if path is None:
            continue
        if kind == "work":
            linked_document, payload = _raw_envelope(path, "work_item")
            _append_unique(payload, "decision_refs", decision_id)
            documents[path] = linked_document
            _validate_schema(context, linked_document, "work_item", path)
        elif kind == "packets" and approving:
            linked_document, payload = _raw_envelope(path, "work_packet")
            _append_unique(payload, "approval_refs", decision_id)
            documents[path] = linked_document
            _validate_schema(context, linked_document, "work_packet", path)
    _validate_schema(context, document, "decision", destination)
    _commit_documents(documents, new_path=destination)
    render_project(context.project_root, catalog=context.catalog)
    return destination


def create_evidence(
    target: Path,
    evidence_id: str,
    *,
    work_id: str,
    packet_id: str,
    kind: str,
    producer_id: str,
    run_id: str,
    result: str,
    observed_at: str,
    acceptance_refs: list[str],
    claims_authorized: list[str],
    subject: dict[str, str],
    method: dict[str, str],
    claims_forbidden: list[str] | None = None,
    artifacts: list[str] | None = None,
    context_manifest_digest: str | None = None,
    approval_ref: str | None = None,
    authorization_ref: str | None = None,
    guard_authorizations: list[str] | None = None,
    rationale: str | None = None,
    owner_id: str | None = None,
    risk_acceptance_ref: str | None = None,
    framework: Path | None = None,
) -> Path:
    context = _project_context(target, framework)
    _require_tailored(context)
    index = _record_index(context)
    if evidence_id in index:
        raise FileExistsError(f"Record id already exists: {evidence_id}")
    if kind not in EVIDENCE_KINDS:
        raise ValueError(f"Unknown evidence kind {kind!r}")
    if result not in {"pass", "fail", "inconclusive", "not_run"}:
        raise ValueError("Evidence result must be pass, fail, inconclusive, or not_run")
    work_path, work = _find_record(context, "work", work_id)
    packet_path, packet = _find_record(context, "packets", packet_id)
    if packet.get("work_item_ref") != work_id:
        raise ValueError(f"Packet {packet_id!r} is not linked to work item {work_id!r}")
    producer = _actor(context, producer_id)
    action_receipt = kind in {"approval", "deployment_receipt"}
    acceptance_ids = {
        item.get("id")
        for item in work.get("acceptance", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    unknown_acceptance = set(acceptance_refs) - acceptance_ids
    if unknown_acceptance:
        raise ValueError(
            f"Evidence references acceptance criteria absent from {work_id!r}: "
            + ", ".join(sorted(unknown_acceptance))
        )
    if not action_receipt:
        plans = [item for item in work.get("evidence_plan", []) if isinstance(item, dict)]
        for acceptance_ref in acceptance_refs:
            matches = [
                plan for plan in plans if plan.get("acceptance_ref") == acceptance_ref
            ]
            if not any(
                kind in plan.get("kinds", [])
                and (
                    not isinstance(plan.get("environment"), str)
                    or method.get("environment") == plan.get("environment")
                )
                for plan in matches
            ):
                raise ValueError(
                    f"Evidence kind/environment does not match the plan for {acceptance_ref!r}"
                )
    requested_claims = {
        item for item in packet.get("claims_requested", []) if isinstance(item, str)
    }
    unauthorized_claims = (
        set() if action_receipt else set(claims_authorized) - requested_claims
    )
    if unauthorized_claims:
        raise ValueError(
            f"Evidence claims were not requested by packet {packet_id!r}: "
            + ", ".join(sorted(unauthorized_claims))
        )
    forbidden = set(
        item for item in packet.get("claims_forbidden", []) if isinstance(item, str)
    ) | set(claims_forbidden or [])
    conflict = set(claims_authorized) & forbidden
    if conflict:
        raise ValueError("Claims cannot be both authorized and forbidden: " + ", ".join(sorted(conflict)))

    routed_work = dict(work)
    risk_defaults = context.program.get("risk_defaults", {})
    if isinstance(risk_defaults, dict) and isinstance(risk_defaults.get("baseline"), str):
        routed_work["_baseline_risk"] = risk_defaults["baseline"]
    assurance_level = route_record(routed_work, context.catalog).minimum_assurance
    packet_producer = packet.get("producer", {})
    packet_producer_id = (
        packet_producer.get("actor") if isinstance(packet_producer, dict) else None
    )
    if action_receipt and producer_id != packet_producer_id:
        raise ValueError(f"{kind} evidence must be produced by the packet producer")
    if action_receipt and result != "pass":
        raise ValueError(f"{kind} evidence must explicitly record --result pass")
    if (
        not action_receipt
        and assurance_rank(assurance_level) >= 2
        and packet_producer_id == producer_id
    ):
        raise ValueError(f"{assurance_level} evidence producer must differ from packet producer")
    if not action_receipt and assurance_rank(assurance_level) >= 2:
        if not approval_ref:
            raise ValueError(f"{assurance_level} evidence requires --approval-ref")
        _actor(context, approval_ref, human=True)
        if approval_ref != work.get("accountable_human"):
            raise ValueError(
                f"{assurance_level} evidence approval must be the work item's accountable human"
            )
    elif approval_ref:
        _actor(context, approval_ref, human=True)
    resolved_authorization: dict[str, Any] | None = None
    authorization_decision: dict[str, Any] | None = None
    if authorization_ref:
        entry = index.get(authorization_ref)
        if entry is None or entry[0] != "decisions":
            raise ValueError(f"Authorization decision {authorization_ref!r} cannot be resolved")
        authorization = entry[2].get("authorization")
        if not isinstance(authorization, dict):
            raise ValueError(f"Decision {authorization_ref!r} does not contain an authorization")
        if authorization_ref not in packet.get("approval_refs", []):
            raise ValueError(
                f"Authorization decision {authorization_ref!r} is not attached to packet {packet_id!r}"
            )
        packet_permissions = {
            item for item in packet.get("permission_classes", []) if isinstance(item, str)
        } & {"external_write", "sensitive", "production"}
        if not _decision_authorizes(
            entry[2],
            work_id=work_id,
            actor_id=producer_id,
            permissions=packet_permissions,
        ):
            raise ValueError(
                f"Authorization decision {authorization_ref!r} is not valid for this work, "
                "actor, and permission scope"
            )
        resolved_authorization = authorization
        authorization_decision = entry[2]

    if (
        assurance_rank(assurance_level) >= 1
        and not context_manifest_digest
    ):
        raise ValueError(
            f"{assurance_level} evidence requires --context-digest"
        )
    if result in {"not_run", "inconclusive"}:
        if not all((rationale, owner_id, risk_acceptance_ref)):
            raise ValueError(
                f"{result} evidence requires --rationale, --owner, and --risk-acceptance-ref"
            )
        _actor(context, owner_id or "", human=True)
        entry = index.get(risk_acceptance_ref or "")
        if (
            entry is None
            or entry[0] != "decisions"
            or entry[2].get("type") != "risk_acceptance"
        ):
            raise ValueError(f"Risk acceptance {risk_acceptance_ref!r} cannot be resolved")

    producer_record: dict[str, Any] = {
        "actor": producer_id,
        "run_id": run_id,
        "type": producer["kind"],
    }
    if context_manifest_digest:
        producer_record["context_manifest_digest"] = context_manifest_digest
    parsed_artifacts = _parse_artifacts(artifacts or [])
    artifact_subject = subject.get("artifact_digest")
    if isinstance(artifact_subject, str):
        observed_digests = {f"sha256:{artifact['sha256']}" for artifact in parsed_artifacts}
        if artifact_subject not in observed_digests:
            raise ValueError(
                "An --artifact-digest subject requires a matching --artifact URI=SHA256_HEX receipt"
            )
    if not _subject_matches_packet(subject, packet, parsed_artifacts, kind=kind):
        raise ValueError(
            f"Evidence subject is not bound to an output of packet {packet_id!r}"
        )
    if action_receipt and not authorization_ref:
        raise ValueError(f"{kind} evidence requires --authorization-ref")
    if action_receipt:
        observed = _parse_datetime(observed_at)
        decided = _parse_datetime(
            authorization_decision.get("decided_at")
            if isinstance(authorization_decision, dict)
            else None
        )
        expires = _parse_datetime(
            resolved_authorization.get("expires_at")
            if isinstance(resolved_authorization, dict)
            else None
        )
        now = datetime.now(timezone.utc)
        if observed is None:
            raise ValueError("Action receipt observed_at must be a valid date-time")
        if decided is None or observed < decided:
            raise ValueError("Action receipt cannot predate its authorization decision")
        if expires is None or observed > expires:
            raise ValueError("Action receipt was observed after its authorization expired")
        if observed > now:
            raise ValueError("Action receipt observed_at cannot be in the future")

    evidence: dict[str, Any] = {
        "id": evidence_id,
        "work_item_ref": work_id,
        "packet_ref": packet_id,
        "acceptance_refs": list(dict.fromkeys(acceptance_refs)),
        "kind": kind,
        "subject": subject,
        "producer": producer_record,
        "method": method,
        "result": result,
        "observed_at": observed_at,
        "artifacts": parsed_artifacts,
        "claims_authorized": list(dict.fromkeys(claims_authorized)),
        "claims_forbidden": sorted(forbidden),
    }
    if approval_ref:
        evidence["approval_ref"] = approval_ref
    if authorization_ref:
        evidence["authorization_ref"] = authorization_ref
    if action_receipt and isinstance(resolved_authorization, dict):
        evidence["action_scope"] = resolved_authorization["action_scope"]
    if guard_authorizations:
        evidence["guard_authorizations"] = list(dict.fromkeys(guard_authorizations))
    if result in {"not_run", "inconclusive"}:
        evidence.update(
            {
                "rationale": rationale,
                "owner": owner_id,
                "risk_acceptance_ref": risk_acceptance_ref,
            }
        )
    document = {
        "schema_version": 1,
        "framework_version": __version__,
        "evidence": evidence,
    }
    destination = _destination(context, "evidence", evidence_id)
    packet_document, packet_payload = _raw_envelope(packet_path, "work_packet")
    if action_receipt:
        _append_unique(packet_payload, "action_receipt_refs", evidence_id)
    else:
        _append_unique(packet_payload, "verification_evidence_refs", evidence_id)
    _validate_schema(context, document, "evidence", destination)
    _validate_schema(context, packet_document, "work_packet", packet_path)
    _commit_documents({destination: document, packet_path: packet_document}, new_path=destination)
    render_project(context.project_root, catalog=context.catalog)
    return destination
