from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .catalog import Catalog, load_catalog, workflow_states, workflow_transitions
from .io import (
    dump_yaml,
    load_record,
    load_yaml,
    locate_overlay,
    record_files,
)
from .routing import permission_order
from .validation import validate_project


class TransitionError(ValueError):
    pass


EVIDENCE_GUARD_TOKENS = (
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
APPROVAL_GUARD_TOKENS = (
    "decision",
    "approved",
    "approval",
    "permissions_satisfied",
    "production_permission",
    "release_gate",
    "risk_acceptance",
    "review_capacity",
)


def _transition_guards(
    workflow: dict[str, Any], current_state: str, new_state: str
) -> list[str]:
    states = workflow.get("states")
    if not isinstance(states, dict):
        return []
    state = states.get(current_state)
    if not isinstance(state, dict) or not isinstance(state.get("transitions"), dict):
        return []
    for transition in state["transitions"].values():
        if isinstance(transition, dict) and transition.get("to") == new_state:
            guards = transition.get("guards", [])
            return [guard for guard in guards if isinstance(guard, str)]
    return []


def _present(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return value is not None


def _dotted(data: dict[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _auto_guard_satisfied(
    guard: str,
    record: dict[str, Any],
    workflow: dict[str, Any] | None = None,
    packets_by_id: dict[str, dict[str, Any]] | None = None,
) -> bool:
    contracts = (workflow or {}).get("guard_contracts")
    contract = contracts.get(guard) if isinstance(contracts, dict) else None
    if isinstance(contract, dict) and isinstance(contract.get("path"), str):
        exists, value = _dotted(record, contract["path"])
        if "equals" in contract:
            return exists and value == contract["equals"]
        predicate = contract.get("predicate")
        if predicate in {"non_empty", "declared_actor"}:
            return exists and _present(value)
        if predicate == "present":
            return exists
        if predicate in {"non_empty_resolved_refs", "resolved_ref"}:
            return False
    if guard == "objective_defined":
        objective = record.get("objective")
        return (
            isinstance(objective, str)
            and bool(objective.strip())
            and not objective.startswith("Define and deliver the observable outcome for")
        )
    if guard == "acceptance_defined":
        acceptance = record.get("acceptance")
        if not isinstance(acceptance, list) or not acceptance:
            return False
        statements = [
            item.get("statement")
            for item in acceptance
            if isinstance(item, dict) and isinstance(item.get("statement"), str)
        ]
        return bool(statements) and all(
            not statement.startswith("Replace with") for statement in statements
        )
    direct_fields = {
        "source_ref_present": "source_refs",
        "accountable_human_named": "accountable_human",
        "route_selected": "route",
        "evidence_plan_defined": "evidence_plan",
        "capability_coverage_complete": "required_capabilities",
        "decision_recorded": "decision_refs",
        "evidence_receipts_present": "evidence_refs",
        "review_refs_present": "review_refs",
    }
    field = direct_fields.get(guard)
    if field:
        return _present(record.get(field))
    if guard in {"work_packet_complete", "provenance_present"}:
        packet_refs = [
            value for value in record.get("work_packet_refs", []) if isinstance(value, str)
        ]
        packets = packets_by_id or {}
        linked = [packets.get(reference) for reference in packet_refs]
        if not packet_refs or any(not isinstance(packet, dict) for packet in linked):
            return False
        if any(packet.get("work_item_ref") != record.get("id") for packet in linked):
            return False
        if guard == "work_packet_complete":
            return all(
                packet.get("status") in {"ready_for_review", "accepted"}
                for packet in linked
            )
        return all(
            isinstance(packet.get("producer"), dict)
            and _present(packet["producer"].get("actor"))
            and _present(packet["producer"].get("run_id"))
            and _present(packet.get("changes_or_outputs"))
            for packet in linked
        )
    if guard == "risk_facts_complete":
        change = record.get("change")
        risk = record.get("risk")
        required_change_fields = {
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
        }
        return (
            isinstance(change, dict)
            and required_change_fields <= set(change)
            and all(change.get(field) != "unknown" for field in required_change_fields)
            and isinstance(risk, dict)
            and _present(risk.get("effective_tier"))
            and _present(risk.get("assurance_level"))
        )
    return False


def _record_index(overlay: Path, kind: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in record_files(overlay, kind):
        try:
            record, _ = load_record(path)
        except (OSError, ValueError):
            continue
        record_id = record.get("id")
        if isinstance(record_id, str):
            result[record_id] = record
    return result


def _guard_receipt_kind(guard: str) -> str:
    if any(token in guard for token in APPROVAL_GUARD_TOKENS):
        return "approval"
    if any(token in guard for token in EVIDENCE_GUARD_TOKENS):
        return "evidence"
    return "either"


def _future_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed > datetime.now(timezone.utc)


def _permissions_satisfied(
    record: dict[str, Any], actor: dict[str, Any], catalog: Catalog
) -> bool:
    order = permission_order(catalog)
    ceiling = actor.get("permission_ceiling")
    requested = [
        value
        for value in record.get("permission_classes", [])
        if isinstance(value, str) and value in order
    ]
    if ceiling not in order or not requested:
        return False
    highest = max(requested, key=order.index)
    return order.index(highest) <= order.index(ceiling) and highest in {
        "read_only",
        "local_write",
        "external_read",
    }


def find_work_record(overlay: Path, record_id: str) -> Path:
    for kind in ("work", "packets"):
        for path in record_files(overlay, kind):
            try:
                record, _ = load_record(path)
            except (OSError, ValueError):
                continue
            if record.get("id") == record_id:
                return path
    raise FileNotFoundError(f"No work or packet record has id {record_id!r}")


def _workflow_for(
    record: dict[str, Any], catalog: Catalog
) -> tuple[str, dict[str, Any]]:
    workflow_id = record.get("workflow", record.get("route"))
    if not isinstance(workflow_id, str):
        raise TransitionError("Record does not declare workflow or route")
    workflow = catalog.workflows.get(workflow_id)
    if workflow is None:
        raise TransitionError(f"Workflow {workflow_id!r} is not defined")
    return workflow_id, workflow


def transition_project(
    root: Path,
    record_id: str,
    new_state: str,
    *,
    actor: str,
    confirm_guards: tuple[str, ...] = (),
    approval_refs: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (),
    catalog: Catalog | None = None,
    framework: Path | None = None,
) -> Path:
    project_root, overlay = locate_overlay(root)
    catalog = catalog or load_catalog(framework)
    program = load_yaml(overlay / "program.yaml")
    program_payload = (
        program.get("program", {})
        if isinstance(program.get("program"), dict)
        else program
    )
    tailoring = program_payload.get("tailoring")
    if not isinstance(tailoring, dict) or tailoring.get("status") != "confirmed":
        raise TransitionError(
            "Project tailoring is pending; answer the persisted questions and confirm it before transitions"
        )
    actors = {
        candidate["id"]: candidate
        for candidate in program_payload.get("actors", [])
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
    }
    actor_record = actors.get(actor)
    if actor_record is None:
        raise TransitionError(f"Transition actor {actor!r} is not declared by the program")
    path = find_work_record(overlay, record_id)
    if path.suffix == ".md":
        raise TransitionError("Canonical work records must be YAML, not Markdown")
    record, _ = load_record(path)
    _, workflow = _workflow_for(record, catalog)

    state_value = record.get("state")
    if isinstance(state_value, dict):
        current_state = state_value.get("current")
    else:
        state_key = "state" if "state" in record else "status"
        current_state = record.get(state_key)
    if not isinstance(current_state, str):
        raise TransitionError("Record does not have a current state/status")
    states = workflow_states(workflow)
    if states and new_state not in states:
        raise TransitionError(f"State {new_state!r} is not part of this workflow")
    allowed = workflow_transitions(workflow)
    if allowed and new_state not in allowed.get(current_state, set()):
        expected = ", ".join(sorted(allowed.get(current_state, set()))) or "none"
        raise TransitionError(
            f"Workflow does not allow {current_state!r} -> {new_state!r}; allowed: {expected}"
        )
    required_guards = _transition_guards(workflow, current_state, new_state)
    confirmed = set(confirm_guards)
    unknown_confirmations = sorted(confirmed - set(required_guards))
    if unknown_confirmations:
        raise TransitionError(
            "Confirmed guards are not part of this transition: "
            + ", ".join(unknown_confirmations)
        )
    evidence_by_id = _record_index(overlay, "evidence")
    decisions_by_id = _record_index(overlay, "decisions")
    packets_by_id = _record_index(overlay, "packets")
    unresolved_evidence = sorted(set(evidence_refs) - set(evidence_by_id))
    unresolved_approvals = sorted(set(approval_refs) - set(decisions_by_id))
    if unresolved_evidence:
        raise TransitionError(
            "Evidence receipts cannot be resolved: " + ", ".join(unresolved_evidence)
        )
    if unresolved_approvals:
        raise TransitionError(
            "Approval decisions cannot be resolved: " + ", ".join(unresolved_approvals)
        )
    for reference in evidence_refs:
        if evidence_by_id[reference].get("result") != "pass":
            raise TransitionError(f"Evidence receipt {reference!r} is not passing")
        if evidence_by_id[reference].get("work_item_ref") != record_id:
            raise TransitionError(
                f"Evidence receipt {reference!r} is not bound to work item {record_id!r}"
            )
    for reference in approval_refs:
        decision = decisions_by_id[reference]
        if record_id not in decision.get("subject_refs", []):
            raise TransitionError(
                f"Decision {reference!r} is not bound to work item {record_id!r}"
            )
        disposition = decision.get("outcome", {})
        disposition = disposition.get("disposition") if isinstance(disposition, dict) else None
        if disposition not in {"approve", "go", "commit", "accept_risk"}:
            raise TransitionError(
                f"Decision {reference!r} does not carry an approving disposition"
            )

    auto_satisfied = {
        guard
        for guard in required_guards
        if _auto_guard_satisfied(guard, record, workflow, packets_by_id)
        or (
            guard == "permissions_satisfied"
            and _permissions_satisfied(record, actor_record, catalog)
        )
    }
    unsatisfied = [
        guard
        for guard in required_guards
        if guard not in auto_satisfied
        and (guard not in confirmed or guard in {"work_packet_complete", "provenance_present"})
    ]
    if unsatisfied:
        raise TransitionError(
            "Transition guards are not satisfied: "
            + ", ".join(unsatisfied)
            + ". Supply the missing canonical record fields or --confirm-guard with evidence."
        )
    for guard in sorted(confirmed - auto_satisfied):
        receipt_kind = _guard_receipt_kind(guard)
        authorized_evidence = [
            reference
            for reference in evidence_refs
            if guard in evidence_by_id[reference].get("guard_authorizations", [])
        ]
        authorized_approvals = [
            reference
            for reference in approval_refs
            if guard in decisions_by_id[reference].get("guard_authorizations", [])
        ]
        if receipt_kind == "evidence" and not authorized_evidence:
            raise TransitionError(
                f"Guard {guard!r} requires an --evidence-ref that explicitly authorizes that guard"
            )
        if receipt_kind == "approval" and not authorized_approvals:
            raise TransitionError(
                f"Guard {guard!r} requires an --approval-ref that explicitly authorizes that guard"
            )
        if receipt_kind == "either" and not (authorized_evidence or authorized_approvals):
            raise TransitionError(
                f"Guard {guard!r} requires a typed receipt that explicitly authorizes that guard"
            )
        if guard in {"permissions_satisfied", "production_permission_valid"}:
            requested = set(
                value for value in record.get("permission_classes", []) if isinstance(value, str)
            ) & {"external_write", "sensitive", "production"}
            if not any(
                requested
                <= set(
                    decision.get("authorization", {}).get("permission_classes", [])
                    if isinstance(decision.get("authorization"), dict)
                    else []
                )
                and _future_datetime(
                    decision.get("authorization", {}).get("expires_at")
                    if isinstance(decision.get("authorization"), dict)
                    else None
                )
                and actor
                in (
                    decision.get("authorization", {}).get("actor_refs", [])
                    if isinstance(decision.get("authorization"), dict)
                    else []
                )
                for reference in authorized_approvals
                for decision in [decisions_by_id[reference]]
            ):
                raise TransitionError(
                    f"Guard {guard!r} requires an unexpired authorization covering the requested permissions"
                )

    original = path.read_text(encoding="utf-8")
    if isinstance(state_value, dict):
        state_value["current"] = new_state
        history = state_value.setdefault("history", [])
    else:
        record[state_key] = new_state
        history = record.setdefault("transition_history", [])
    if not isinstance(history, list):
        raise TransitionError("transition_history must be a list")
    event = {
        "from": current_state,
        "to": new_state,
        "actor": actor,
        "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    if isinstance(state_value, dict):
        event["sequence"] = len(history) + 1
        event["event"] = f"transition_to_{new_state}"
        event["guard_refs"] = required_guards
        event["confirmed_guard_refs"] = sorted(confirmed - auto_satisfied)
        if approval_refs:
            event["approval_refs"] = list(approval_refs)
        if evidence_refs:
            event["evidence_refs"] = list(evidence_refs)
    history.append(event)
    envelope = record.pop("_envelope", None)
    schema_version = record.pop("_schema_version", 1)
    framework_version = record.pop("_framework_version", "0.1.0")
    if not isinstance(envelope, str):
        raise TransitionError("YAML work records must use a recognized envelope")
    path.write_text(
        dump_yaml(
            {
                "schema_version": schema_version,
                "framework_version": framework_version,
                envelope: record,
            }
        ),
        encoding="utf-8",
    )

    report = validate_project(project_root, catalog=catalog)
    path_errors = [
        issue for issue in report.errors if issue.path and Path(issue.path).resolve() == path.resolve()
    ]
    if path_errors:
        path.write_text(original, encoding="utf-8")
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in path_errors)
        raise TransitionError(f"Transition violates project controls: {details}")
    from .rendering import render_project

    render_project(project_root, catalog=catalog)
    return path
