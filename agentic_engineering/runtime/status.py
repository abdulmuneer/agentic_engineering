from __future__ import annotations

from pathlib import Path
from typing import Any

from .authorization import authorization_of, is_standing, standing_expired
from .catalog import Catalog, load_catalog
from .io import load_record, locate_overlay, record_files
from .transitions import _auto_guard_satisfied, _guard_receipt_kind, _record_index

ELEVATED = {"external_write", "sensitive", "production"}
EXIT_STATES = {"aborted", "cancelled", "rolled_back", "stopped", "killed"}


def _strings(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _tier(record: dict[str, Any]) -> str:
    risk = record.get("risk")
    if isinstance(risk, dict):
        return str(risk.get("effective_tier", risk.get("declared_tier", "-")))
    return str(record.get("risk_tier", risk or "-"))


def _open_human_gates(
    record: dict[str, Any],
    workflow: dict[str, Any],
    state: str,
    packets: dict[str, dict[str, Any]],
) -> list[str]:
    definition = (workflow.get("states") or {}).get(state)
    transitions = definition.get("transitions") if isinstance(definition, dict) else None
    if not isinstance(transitions, dict):
        return []
    elevated = bool(set(_strings(record.get("permission_classes"))) & ELEVATED)
    gates: set[str] = set()
    for transition in transitions.values():
        if isinstance(transition, dict) and transition.get("to") in EXIT_STATES:
            continue  # exits (abort, cancel, rollback) are not gates on forward progress
        for guard in _strings(transition.get("guards") if isinstance(transition, dict) else None):
            if _guard_receipt_kind(guard) != "approval":
                continue
            if guard == "permissions_satisfied" and not elevated:
                continue
            if not _auto_guard_satisfied(guard, record, workflow, packets):
                gates.add(guard)
    return sorted(gates)


def status_lines(
    root: Path, *, catalog: Catalog | None = None, framework: Path | None = None
) -> list[str]:
    """One terse line per work item, standing authorization, and decision with a revisit date."""
    _, overlay = locate_overlay(root)
    catalog = catalog or load_catalog(framework)
    packets = _record_index(overlay, "packets")
    lines: list[str] = []
    for path in record_files(overlay, "work"):
        try:
            record, _ = load_record(path)
        except (OSError, ValueError):
            continue
        state_value = record.get("state", record.get("status", "-"))
        state = state_value.get("current", "-") if isinstance(state_value, dict) else state_value
        workflow_id = str(record.get("workflow", record.get("route", "-")))
        gates = _open_human_gates(
            record, catalog.workflows.get(workflow_id, {}), str(state), packets
        )
        lines.append(
            f"{record.get('id', path.stem)} {workflow_id} {state} "
            f"tier={_tier(record)} gates={','.join(gates) if gates else 'none'}"
        )
    for path in record_files(overlay, "decisions"):
        try:
            decision, _ = load_record(path)
        except (OSError, ValueError):
            continue
        decision_id = decision.get("id", path.stem)
        authorization = authorization_of(decision)
        if is_standing(decision):
            expired = " EXPIRED" if standing_expired(decision) else ""
            lines.append(
                f"standing {decision_id} expires={authorization.get('expires_at', '-')}{expired} "
                f"applies_to={','.join(_strings(authorization.get('applies_to'))) or '-'}"
            )
        if decision.get("revisit_at"):
            lines.append(f"revisit {decision_id} at={decision['revisit_at']}")
    return sorted(lines, key=lambda line: (line.startswith(("standing ", "revisit ")), line))
