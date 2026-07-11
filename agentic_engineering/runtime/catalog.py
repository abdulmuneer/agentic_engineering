from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import framework_root, load_yaml


def _indexed(value: Any, key: str = "id") -> dict[str, dict[str, Any]]:
    if isinstance(value, dict):
        if all(isinstance(item, dict) for item in value.values()):
            return {
                str(item_id): ({key: str(item_id), **item} if key not in item else item)
                for item_id, item in value.items()
            }
        return {}
    if isinstance(value, list):
        result: dict[str, dict[str, Any]] = {}
        for item in value:
            if isinstance(item, dict) and isinstance(item.get(key), str):
                result[item[key]] = item
        return result
    return {}


@dataclass(frozen=True)
class Catalog:
    root: Path
    capabilities: dict[str, dict[str, Any]]
    workflows: dict[str, dict[str, Any]]
    risk_policy: dict[str, Any]
    assurance_policy: dict[str, Any]
    permission_policy: dict[str, Any]
    evidence_policy: dict[str, Any]


def framework_fingerprint(root: Path) -> dict[str, str]:
    root = root.resolve()

    def digest(paths: list[Path]) -> str:
        value = hashlib.sha256()
        entries = sorted(
            (
                (path.relative_to(root).as_posix(), path)
                for path in paths
                if path.is_file()
            ),
            key=lambda item: item[0],
        )
        for relative, path in entries:
            value.update(relative.encode("utf-8"))
            value.update(b"\0")
            value.update(path.read_bytes())
            value.update(b"\0")
        return value.hexdigest()

    catalog_paths = list((root / "catalog").rglob("*.yaml")) + list(
        (root / "team").glob("*.md")
    )
    schema_paths = list((root / "schemas" / "v1").glob("*.json"))
    behavior_paths = list((root / "runtime").rglob("*.py")) + list(
        (root / "presets").rglob("*.yaml")
    )
    return {
        "catalog_sha256": digest(catalog_paths),
        "schemas_sha256": digest(schema_paths),
        "behavior_sha256": digest(behavior_paths),
    }


def load_catalog(root: Path | None = None) -> Catalog:
    root = (root or framework_root()).resolve()
    catalog_root = root / "catalog"

    capability_data = load_yaml(catalog_root / "capabilities.yaml")
    capability_catalog = capability_data.get("catalog", capability_data)
    if not isinstance(capability_catalog, dict):
        capability_catalog = {}
    capabilities = _indexed(
        capability_catalog.get("capabilities", capability_catalog),
    )

    workflows: dict[str, dict[str, Any]] = {}
    for path in sorted((catalog_root / "workflows").glob("*.yaml")):
        data = load_yaml(path)
        workflow = data.get("workflow", data)
        workflow_id = workflow.get("id") if isinstance(workflow, dict) else None
        if not isinstance(workflow_id, str) or not workflow_id:
            raise ValueError(f"{path} does not define workflow.id")
        workflow["_path"] = str(path)
        workflows[workflow_id] = workflow

    def policy(name: str) -> dict[str, Any]:
        data = load_yaml(catalog_root / f"{name}.yaml")
        value = data.get(name, data)
        return value if isinstance(value, dict) else {}

    return Catalog(
        root=root,
        capabilities=capabilities,
        workflows=workflows,
        risk_policy=policy("risk_policy"),
        assurance_policy=policy("assurance_policy"),
        permission_policy=policy("permission_policy"),
        evidence_policy=policy("evidence_policy"),
    )


def workflow_states(workflow: dict[str, Any]) -> list[str]:
    states = workflow.get("states", [])
    terminal_states = [
        item for item in workflow.get("terminal_states", []) if isinstance(item, str)
    ]
    if isinstance(states, dict):
        return list(dict.fromkeys([*(str(item) for item in states), *terminal_states]))
    result: list[str] = []
    if isinstance(states, list):
        for item in states:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict) and isinstance(item.get("id"), str):
                result.append(item["id"])
    return list(dict.fromkeys([*result, *terminal_states]))


def workflow_transitions(workflow: dict[str, Any]) -> dict[str, set[str]]:
    raw = workflow.get("transitions", {})
    result: dict[str, set[str]] = {}
    states = workflow.get("states")
    if isinstance(states, dict):
        for source, state in states.items():
            if not isinstance(state, dict):
                continue
            events = state.get("transitions", {})
            if not isinstance(events, dict):
                continue
            for transition in events.values():
                if isinstance(transition, str):
                    result.setdefault(str(source), set()).add(transition)
                elif isinstance(transition, dict) and isinstance(transition.get("to"), str):
                    result.setdefault(str(source), set()).add(transition["to"])
        if result:
            return result
    if isinstance(raw, dict):
        for source, targets in raw.items():
            if isinstance(targets, str):
                result[str(source)] = {targets}
            elif isinstance(targets, list):
                normalized: set[str] = set()
                for target in targets:
                    if isinstance(target, str):
                        normalized.add(target)
                    elif isinstance(target, dict) and isinstance(target.get("to"), str):
                        normalized.add(target["to"])
                result[str(source)] = normalized
        return result
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            source = item.get("from")
            target = item.get("to")
            targets = target if isinstance(target, list) else [target]
            if isinstance(source, str):
                result.setdefault(source, set()).update(
                    str(value) for value in targets if isinstance(value, str)
                )
    return result
