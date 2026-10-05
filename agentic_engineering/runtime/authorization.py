from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

APPROVING_DISPOSITIONS = {"approve", "go", "commit", "accept_risk"}
ELEVATED_PERMISSIONS = {"external_write", "sensitive", "production"}


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def authorization_of(decision: dict[str, Any]) -> dict[str, Any]:
    value = decision.get("authorization")
    return value if isinstance(value, dict) else {}


def is_standing(decision: dict[str, Any]) -> bool:
    return authorization_of(decision).get("standing") is True


def standing_expired(decision: dict[str, Any], at: datetime | None = None) -> bool:
    """True when a standing authorization has no future expiry relative to `at` (default now)."""
    expires = parse_datetime(authorization_of(decision).get("expires_at"))
    return expires is None or expires <= (at or datetime.now(timezone.utc))


def standing_applies(decision: dict[str, Any], work_id: str, workflow_id: str | None) -> bool:
    targets = set(_strings(authorization_of(decision).get("applies_to")))
    return bool(targets & {"*", work_id, workflow_id or ""})


def decision_covers(
    decision: dict[str, Any],
    work: dict[str, Any],
    *,
    actor: str | None = None,
    at: datetime | None = None,
) -> bool:
    """A decision covers a work item by subject binding or by an unexpired standing authorization.

    Standing coverage needs the work item to match applies_to, the actor (when given) to be in
    actor_refs, and the item's elevated permissions to sit inside the authorized permission classes.
    """
    work_id = work.get("id")
    if not isinstance(work_id, str):
        return False
    if work_id in _strings(decision.get("subject_refs")):
        return True
    if work.get("_envelope") != "work_item" or not is_standing(decision):
        return False
    if standing_expired(decision, at):
        return False
    workflow_id = work.get("workflow", work.get("route"))
    if not standing_applies(decision, work_id, workflow_id if isinstance(workflow_id, str) else None):
        return False
    authorization = authorization_of(decision)
    if actor is not None and actor not in _strings(authorization.get("actor_refs")):
        return False
    elevated = set(_strings(work.get("permission_classes"))) & ELEVATED_PERMISSIONS
    return elevated <= set(_strings(authorization.get("permission_classes")))
