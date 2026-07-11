from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml


FRONT_MATTER_DELIMITER = "---"
RECORD_ENVELOPES = ("work_item", "work_packet", "evidence", "decision", "learning")


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=100,
    )


def parse_markdown_record(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != FRONT_MATTER_DELIMITER:
        raise ValueError(f"{path} must start with YAML front matter")

    closing_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONT_MATTER_DELIMITER:
            closing_index = index
            break
    if closing_index is None:
        raise ValueError(f"{path} has unterminated YAML front matter")

    raw_metadata = "".join(lines[1:closing_index])
    metadata = yaml.safe_load(raw_metadata) or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"{path} front matter must be a mapping")
    body = "".join(lines[closing_index + 1 :])
    return metadata, body


def write_markdown_record(path: Path, metadata: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = f"{FRONT_MATTER_DELIMITER}\n{dump_yaml(metadata)}{FRONT_MATTER_DELIMITER}\n"
    if body and not body.startswith("\n"):
        rendered += "\n"
    rendered += body
    if rendered and not rendered.endswith("\n"):
        rendered += "\n"
    path.write_text(rendered, encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def framework_root() -> Path:
    return Path(__file__).resolve().parents[1]


def locate_overlay(root: Path) -> tuple[Path, Path]:
    root = root.resolve()
    if (root / ".agentic" / "program.yaml").is_file():
        return root, root / ".agentic"
    if (root / "program.yaml").is_file():
        return root, root
    raise FileNotFoundError(
        f"No project manifest found below {root}; expected .agentic/program.yaml or program.yaml"
    )


def record_files(overlay: Path, kind: str) -> list[Path]:
    aliases = {
        "work": ["work", "work_items"],
        "packets": ["packets", "work_packets"],
        "evidence": ["evidence"],
        "decisions": ["decisions"],
        "learnings": ["learnings"],
    }.get(kind, [kind])
    directories = [
        directory
        for alias in aliases
        for directory in (overlay / "records" / alias, overlay / alias)
    ]
    files: list[Path] = []
    for directory in directories:
        if directory.exists():
            files.extend(directory.glob("*.md"))
            files.extend(directory.glob("*.yaml"))
            files.extend(directory.glob("*.yml"))
    return sorted(set(files))


def load_record(path: Path) -> tuple[dict[str, Any], str]:
    if path.suffix == ".md":
        data, body = parse_markdown_record(path)
    else:
        data, body = load_yaml(path), ""
    for envelope in RECORD_ENVELOPES:
        payload = data.get(envelope)
        if isinstance(payload, dict):
            normalized = dict(payload)
            normalized["_envelope"] = envelope
            normalized["_schema_version"] = data.get("schema_version")
            normalized["_framework_version"] = data.get("framework_version")
            return normalized, body
    return data, body


def principal_id(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        principal = value.get("principal") or value.get("id")
        if isinstance(principal, str) and principal.strip():
            return principal.strip()
    return None
