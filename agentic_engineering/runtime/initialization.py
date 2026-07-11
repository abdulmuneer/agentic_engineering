from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_engineering import __version__

from .io import (
    dump_yaml,
    framework_root,
    load_record,
    load_yaml,
    locate_overlay,
    parse_markdown_record,
    record_files,
    sha256_file,
)
from .catalog import framework_fingerprint, load_catalog
from .rendering import render_project
from .routing import assurance_rank, minimum_assurance, risk_order, route_record


AGENTS_BLOCK_START = "<!-- agentic-engineering:start -->"
AGENTS_BLOCK_END = "<!-- agentic-engineering:end -->"


def _write_agents_pointer(target: Path) -> Path:
    path = target / "AGENTS.md"
    block = (
        f"{AGENTS_BLOCK_START}\n"
        "## Agentic Engineering control plane\n\n"
        "Read [`.agentic/generated/AGENTS.md`](.agentic/generated/AGENTS.md) before "
        "starting or accepting delegated work. `.agentic/program.yaml` and "
        "`.agentic/records/` are canonical; generated files are disposable views.\n"
        f"{AGENTS_BLOCK_END}"
    )
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Project Agent Guidance\n"
    if AGENTS_BLOCK_START in existing and AGENTS_BLOCK_END in existing:
        prefix, remainder = existing.split(AGENTS_BLOCK_START, 1)
        _, suffix = remainder.split(AGENTS_BLOCK_END, 1)
        updated = prefix.rstrip() + "\n\n" + block + suffix
    else:
        updated = existing.rstrip() + "\n\n" + block + "\n"
    path.write_text(updated.rstrip() + "\n", encoding="utf-8")
    return path


def _source_version(path: Path) -> str | int | None:
    if path.suffix == ".md":
        try:
            metadata, _ = parse_markdown_record(path)
        except ValueError:
            return None
        return metadata.get("plan_version", metadata.get("version"))
    if path.suffix in {".yaml", ".yml"}:
        data = load_yaml(path)
        return data.get("plan_version", data.get("version"))
    return None


def _preset_path(name: str, root: Path) -> Path:
    candidates = {
        name,
        name.replace("-", "_"),
        name.replace("_", "-"),
    }
    for candidate in sorted(candidates):
        path = root / "presets" / f"{candidate}.yaml"
        if path.is_file():
            return path
    available = ", ".join(path.stem for path in sorted((root / "presets").glob("*.yaml")))
    raise FileNotFoundError(f"Unknown preset {name!r}; available: {available}")


def init_project(
    target: Path,
    *,
    preset_name: str,
    project_id: str | None = None,
    project_name: str | None = None,
    source_path: str = "README.md",
    framework: Path | None = None,
    force: bool = False,
) -> Path:
    target = target.resolve()
    framework = (framework or framework_root()).resolve()
    source = (target / source_path).resolve()
    if not source.is_relative_to(target):
        raise ValueError("The authoritative source must be inside the target project")
    if not source.is_file():
        raise FileNotFoundError(
            f"Authoritative source {source_path!r} does not exist below {target}; "
            "pass --source with a project-relative file"
        )
    source_relative = str(source.relative_to(target))

    overlay = target / ".agentic"
    manifest_path = overlay / "program.yaml"
    if manifest_path.exists() and not force:
        raise FileExistsError(f"{manifest_path} already exists; pass --force to replace it")
    if manifest_path.exists() and force and any(
        record_files(overlay, kind)
        for kind in ("work", "packets", "evidence", "decisions", "learnings")
    ):
        raise ValueError("Refusing --force because the existing overlay contains canonical records")

    preset_document = load_yaml(_preset_path(preset_name, framework))
    preset = preset_document.get("preset", preset_document)
    if not isinstance(preset, dict):
        raise ValueError(f"Preset {preset_name!r} must contain a mapping")

    source_version = _source_version(source)
    capability_defaults = preset.get("capability_defaults", {})
    if not isinstance(capability_defaults, dict):
        capability_defaults = {}
    active = [item for item in capability_defaults.get("active", []) if isinstance(item, str)]
    conditional = [
        item for item in capability_defaults.get("conditional", []) if isinstance(item, str)
    ]
    capabilities: list[dict[str, Any]] = [
        {
            "id": capability_id,
            "disposition": "active",
            "owner": "human:owner",
            "executors": ["agent:delivery"],
            "reviewers": [
                "agent:review"
                if capability_id
                in {
                    "code_quality",
                    "verification",
                    "security_privacy",
                    "research_assurance",
                    "regulatory_assurance",
                }
                else "human:owner"
            ],
        }
        for capability_id in active
    ]
    capabilities.extend(
        {
            "id": capability_id,
            "disposition": "not_applicable",
            "rationale": "This preset leaves the capability inactive until its trigger enters scope.",
            "reconsider_when": [f"{capability_id}_activation_trigger_enters_scope"],
        }
        for capability_id in conditional
    )
    profile_defaults = preset.get("profile_defaults", {})
    if not isinstance(profile_defaults, dict):
        profile_defaults = {}
    profile = {
        "product_type": profile_defaults.get("product_type", preset.get("id", preset_name)),
        "lifecycle_phase": "discovery",
        "surfaces": profile_defaults.get("surfaces", []),
        "deployment_targets": profile_defaults.get("deployment_targets", []),
        "data_classes": profile_defaults.get("data_classes", []),
        "risk_domains": profile_defaults.get("risk_domains", []),
    }
    base: dict[str, Any] = {
        "schema_version": 1,
        "framework_version": __version__,
        "program": {
            "id": project_id or target.name,
            "name": project_name or (project_id or target.name).replace("-", " ").title(),
            "framework_preset": preset.get("id", preset_name),
            "accountable_human": "human:owner",
            "source_roots": ["."],
            "governance_root": ".agentic",
            "current_gate": "G0",
            "framework_lock": {
                "version": __version__,
                **framework_fingerprint(framework),
            },
            "source_of_truth": {
                "path": source_relative,
                "sha256": sha256_file(source),
                "declared_version": str(source_version)
                if source_version is not None
                else "unversioned",
            },
            "profile": profile,
            "capabilities": capabilities,
            "actors": [
                {
                    "id": "human:owner",
                    "kind": "human",
                    "name": "Accountable owner",
                    "capabilities": active,
                    "permission_ceiling": "production",
                },
                {
                    "id": "agent:delivery",
                    "kind": "agent",
                    "name": "Bounded delivery agent",
                    "capabilities": active,
                    "permission_ceiling": "local_write",
                },
                {
                    "id": "agent:review",
                    "kind": "agent",
                    "name": "Independent review agent",
                    "capabilities": [
                        capability_id
                        for capability_id in active
                        if capability_id
                        in {
                            "code_quality",
                            "verification",
                            "security_privacy",
                            "research_assurance",
                            "regulatory_assurance",
                        }
                    ]
                    or ["verification"],
                    "permission_ceiling": "read_only",
                },
            ],
            "workflow_defaults": preset.get("workflow_defaults", {}),
            "risk_defaults": preset.get("risk_defaults", {"baseline": "medium"}),
            "tailoring": {
                "status": "pending",
                "questions": [
                    question
                    for question in preset.get("required_tailoring_questions", [])
                    if isinstance(question, str) and question.strip()
                ]
                or ["Which project-specific risks, capabilities, actors, and permissions apply?"],
            },
            "policy_refs": [
                "core-risk-policy",
                "core-assurance-policy",
                "core-permission-policy",
                "core-evidence-policy",
            ],
        },
    }
    program = base
    program["schema_version"] = 1
    program["framework_version"] = __version__
    project = program["program"]
    project["id"] = project_id or project.get("id") or target.name
    project["name"] = project_name or project.get("name") or str(project["id"]).replace("-", " ").title()

    for directory in (
        overlay / "records" / "work_items",
        overlay / "records" / "work_packets",
        overlay / "records" / "evidence",
        overlay / "records" / "decisions",
        overlay / "records" / "learnings",
        overlay / "generated",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    overlay.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(dump_yaml(program), encoding="utf-8")
    readme = overlay / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Project Agentic Control Plane\n\n"
            "`program.yaml` and `records/` are authoritative. Files in `generated/` are views.\n\n"
            "Run `agentic validate .`, `agentic route <ID> --root .`, and `agentic render .`.\n",
            encoding="utf-8",
        )
    render_project(target, framework=framework)
    _write_agents_pointer(target)
    return manifest_path


def confirm_tailoring(
    target: Path, *, actor: str, framework: Path | None = None
) -> Path:
    target = target.resolve()
    manifest = target / ".agentic" / "program.yaml"
    if not manifest.is_file() and (target / "program.yaml").is_file():
        manifest = target / "program.yaml"
    if not manifest.is_file():
        raise FileNotFoundError("No project program.yaml found")
    document = load_yaml(manifest)
    program = document.get("program")
    if not isinstance(program, dict):
        raise ValueError("program.yaml does not contain a program mapping")
    actors = {
        item.get("id"): item
        for item in program.get("actors", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if actor != program.get("accountable_human") or actors.get(actor, {}).get("kind") != "human":
        raise ValueError("Tailoring must be confirmed by the declared accountable human")
    tailoring = program.get("tailoring")
    if not isinstance(tailoring, dict) or not tailoring.get("questions"):
        raise ValueError("The program has no persisted tailoring questions")
    questions = {
        question for question in tailoring.get("questions", []) if isinstance(question, str)
    }
    answers = {
        item.get("question"): item.get("answer")
        for item in tailoring.get("answers", [])
        if isinstance(item, dict)
        and isinstance(item.get("question"), str)
        and isinstance(item.get("answer"), str)
        and item.get("answer", "").strip()
    }
    missing = sorted(question for question in questions if question not in answers)
    if missing:
        raise ValueError(
            "Answer every persisted tailoring question before confirmation: "
            + "; ".join(missing)
        )
    original = manifest.read_text(encoding="utf-8")
    tailoring["status"] = "confirmed"
    tailoring["confirmed_by"] = actor
    tailoring["confirmed_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    manifest.write_text(dump_yaml(document), encoding="utf-8")
    render_project(target, framework=framework)
    from .validation import validate_project

    report = validate_project(target, framework=framework)
    if report.errors or report.warnings:
        manifest.write_text(original, encoding="utf-8")
        render_project(target, framework=framework)
        details = "; ".join(
            f"{issue.code}: {issue.message}" for issue in [*report.errors, *report.warnings]
        )
        raise ValueError(f"Tailoring confirmation was rolled back: {details}")
    _write_agents_pointer(target)
    return manifest


def update_source_pin(
    target: Path,
    *,
    actor: str,
    decision_ref: str,
    declared_version: str | None = None,
    framework: Path | None = None,
) -> Path:
    project_root, overlay = locate_overlay(target.resolve())
    manifest = overlay / "program.yaml"
    document = load_yaml(manifest)
    program = document.get("program")
    if not isinstance(program, dict):
        raise ValueError("program.yaml does not contain a program mapping")
    actors = {
        item.get("id"): item
        for item in program.get("actors", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if actor != program.get("accountable_human") or actors.get(actor, {}).get("kind") != "human":
        raise ValueError("The source pin can only be updated by the accountable human")
    source = program.get("source_of_truth")
    if not isinstance(source, dict) or not isinstance(source.get("path"), str):
        raise ValueError("program.source_of_truth is not configured")
    source_path = (project_root / source["path"]).resolve()
    if not source_path.is_relative_to(project_root):
        raise ValueError("The authoritative source must remain inside the project root")
    if not source_path.is_file():
        raise FileNotFoundError(f"Authoritative source does not exist: {source_path}")
    observed_version = _source_version(source_path)
    next_version = declared_version or (
        str(observed_version) if observed_version is not None else None
    )
    if not next_version:
        raise ValueError("The source does not declare a version; pass --declared-version")
    if observed_version is not None and str(observed_version).removeprefix("v") != str(
        next_version
    ).removeprefix("v"):
        raise ValueError(
            f"Requested version {next_version!r} does not match source-declared version {observed_version!r}"
        )
    next_digest = sha256_file(source_path)
    decision: dict[str, Any] | None = None
    for path in record_files(overlay, "decisions"):
        if path.suffix not in {".yaml", ".yml"}:
            continue
        candidate, _ = load_record(path)
        if candidate.get("id") == decision_ref:
            decision = candidate
            break
    if decision is None:
        raise ValueError(f"Source update decision {decision_ref!r} cannot be resolved")
    outcome = decision.get("outcome") if isinstance(decision.get("outcome"), dict) else {}
    approved_source = (
        decision.get("source_update")
        if isinstance(decision.get("source_update"), dict)
        else {}
    )
    expected_source = {
        "path": source["path"],
        "declared_version": str(next_version),
        "sha256": next_digest,
    }
    used_decisions = {
        item.get("decision_ref")
        for item in source.get("history", [])
        if isinstance(item, dict)
    }
    if isinstance(source.get("update_decision_ref"), str):
        used_decisions.add(source["update_decision_ref"])
    try:
        decided_at = datetime.fromisoformat(
            str(decision.get("decided_at", "")).replace("Z", "+00:00")
        )
        if decided_at.tzinfo is None:
            decided_at = decided_at.replace(tzinfo=timezone.utc)
    except ValueError:
        decided_at = None
    if (
        decision.get("owner") != actor
        or outcome.get("disposition") not in {"approve", "go", "commit"}
        or program.get("id") not in decision.get("subject_refs", [])
        or approved_source != expected_source
        or decided_at is None
        or decided_at > datetime.now(timezone.utc)
    ):
        raise ValueError(
            "Source update decision must be accountable, approving, program-bound, "
            "already decided, and scoped to the exact source path, version, and digest"
        )
    if decision_ref in used_decisions:
        raise ValueError(f"Source update decision {decision_ref!r} has already been used")
    from .validation import validate_project

    preflight = validate_project(project_root, framework=framework)
    allowed_preflight_errors = {
        "source-hash-drift",
        "source-version-drift",
        "record-source-drift",
        "record-source-unknown",
        "generated-view-drift",
    }
    blocking = [
        issue for issue in preflight.errors if issue.code not in allowed_preflight_errors
    ]
    if blocking:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in blocking)
        raise ValueError(f"Source update preflight failed: {details}")
    updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    history = source.setdefault("history", [])
    if not isinstance(history, list):
        raise ValueError("program.source_of_truth.history must be a list")
    history.append(
        {
            "path": source["path"],
            "declared_version": str(source["declared_version"]),
            "sha256": source["sha256"],
            "superseded_by": actor,
            "superseded_at": updated_at,
            "decision_ref": decision_ref,
        }
    )
    source.update(
        {
            "declared_version": str(next_version),
            "sha256": next_digest,
            "updated_by": actor,
            "update_decision_ref": decision_ref,
            "updated_at": updated_at,
        }
    )
    manifest.write_text(dump_yaml(document), encoding="utf-8")
    render_project(project_root, framework=framework)
    return manifest


def upgrade_project(
    target: Path, *, framework: Path | None = None, apply: bool = False
) -> tuple[str, str, bool]:
    target = target.resolve()
    manifest = target / ".agentic" / "program.yaml"
    if not manifest.is_file() and (target / "program.yaml").is_file():
        manifest = target / "program.yaml"
    if not manifest.is_file():
        raise FileNotFoundError("No program.yaml found")
    program = load_yaml(manifest)
    current = str(program.get("framework_version", "unknown"))
    resolved_framework = (framework or framework_root()).resolve()
    payload = program.get("program") if isinstance(program.get("program"), dict) else program
    expected_lock = {"version": __version__, **framework_fingerprint(resolved_framework)}
    lock_current = isinstance(payload, dict) and payload.get("framework_lock") == expected_lock
    if current == __version__ and lock_current:
        return current, __version__, False
    if apply:
        if program.get("schema_version") != 1:
            raise ValueError("Automatic upgrade only supports schema_version 1")
        original = manifest.read_text(encoding="utf-8")
        program["framework_version"] = __version__
        if not isinstance(payload, dict):
            raise ValueError("program.yaml does not contain a program mapping")
        payload["framework_lock"] = expected_lock
        manifest.write_text(dump_yaml(program), encoding="utf-8")
        from .validation import validate_project

        report = validate_project(target, framework=resolved_framework)
        blocking = [
            issue
            for issue in report.errors
            if issue.code not in {"generated-view-drift", "generated-view-missing"}
        ]
        if blocking:
            manifest.write_text(original, encoding="utf-8")
            details = "; ".join(f"{issue.code}: {issue.message}" for issue in blocking)
            raise ValueError(f"Framework upgrade was rolled back: {details}")
        render_project(target, framework=resolved_framework)
        return current, __version__, True
    reported_current = current if current != __version__ else f"{current} (lock drift)"
    return reported_current, __version__, False


def create_work_item(
    target: Path,
    work_id: str,
    *,
    title: str,
    workflow_id: str,
    work_type: str = "feature",
    framework: Path | None = None,
) -> Path:
    target = target.resolve()
    manifest = target / ".agentic" / "program.yaml"
    overlay = target / ".agentic"
    if not manifest.is_file() and (target / "program.yaml").is_file():
        manifest = target / "program.yaml"
        overlay = target
    if not manifest.is_file():
        raise FileNotFoundError("No project program.yaml found")
    document = load_yaml(manifest)
    program = document.get("program", document)
    if not isinstance(program, dict):
        raise ValueError("program.yaml does not contain a program mapping")
    catalog = load_catalog(framework)
    workflow = catalog.workflows.get(workflow_id)
    if workflow is None:
        raise ValueError(f"Unknown workflow {workflow_id!r}")
    initial_state = workflow.get("initial_state")
    if not isinstance(initial_state, str):
        raise ValueError(f"Workflow {workflow_id!r} has no initial_state")
    if work_type == "feature":
        work_type = {
            "discovery": "discovery",
            "research_spike": "research",
            "bug_fix": "bug",
            "incident": "incident",
            "release": "release",
        }.get(workflow_id, work_type)

    risk_defaults = program.get("risk_defaults", {})
    baseline = risk_defaults.get("baseline", "medium") if isinstance(risk_defaults, dict) else "medium"
    if workflow_id == "release" and isinstance(risk_defaults, dict):
        release_minimum = risk_defaults.get("production_release_minimum")
        order = risk_order(catalog)
        if release_minimum in order and baseline in order:
            baseline = max((baseline, release_minimum), key=order.index)
    active_capabilities = {
        item.get("id")
        for item in program.get("capabilities", [])
        if isinstance(item, dict) and item.get("disposition") == "active"
    }
    preferred = ["requirements", "code_quality", "verification"]
    required_capabilities = [item for item in preferred if item in active_capabilities]
    if not required_capabilities:
        required_capabilities = sorted(item for item in active_capabilities if isinstance(item, str))[:1]
    profile = program.get("profile", {}) if isinstance(program.get("profile"), dict) else {}
    surfaces = [item for item in profile.get("surfaces", []) if isinstance(item, str)] or ["local"]
    environments = [
        item for item in profile.get("deployment_targets", []) if isinstance(item, str)
    ] or ["local"]
    accountable = program.get("accountable_human", "human:owner")
    acceptance_id = f"AC-{work_id}-1"
    work_item = {
        "schema_version": 1,
        "framework_version": __version__,
        "work_item": {
            "id": work_id,
            "title": title,
            "type": work_type,
            "workflow": workflow_id,
            "state": {
                "current": initial_state,
                "history": [
                    {
                        "sequence": 1,
                        "event": "create",
                        "from": None,
                        "to": initial_state,
                        "at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                        "actor": accountable,
                        "guard_refs": [],
                        "confirmed_guard_refs": [],
                    }
                ],
            },
            "source_refs": [f"program:{program.get('id', 'project')}"],
            "source_revision": str(
                program.get("source_of_truth", {}).get("declared_version", "unversioned")
            ),
            "objective": f"Define and deliver the observable outcome for {work_id}.",
            "accountable_human": accountable,
            "required_capabilities": required_capabilities,
            "change": {
                "surfaces": surfaces,
                "changed_paths": [],
                "production_affecting": "unknown",
                "authentication": "unknown",
                "authorization": "unknown",
                "sensitive_data": "unknown",
                "safety_impact": "unknown",
                "regulated_impact": "unknown",
                "destructive_migration": "unknown",
                "external_write": "unknown",
                "reversibility": "unknown",
                "blast_radius": "unknown",
            },
            "risk": {
                "declared_tier": baseline,
                "effective_tier": baseline,
                "assurance_level": minimum_assurance(catalog, baseline),
                "rule_refs": [],
            },
            "route": workflow_id,
            "acceptance": [
                {
                    "id": acceptance_id,
                    "statement": "Replace with observable acceptance evidence before leaving draft.",
                }
            ],
            "evidence_plan": [
                {
                    "acceptance_ref": acceptance_id,
                    "kinds": ["deterministic_test"],
                    "environment": environments[0],
                    "minimum_assurance": minimum_assurance(catalog, baseline),
                }
            ],
            "permission_classes": ["local_write"],
            "dependency_refs": [],
            "decision_refs": [],
            "work_packet_refs": [],
        },
    }
    payload = work_item["work_item"]
    if workflow_id == "discovery":
        payload["type"] = "discovery"
        payload["permission_classes"] = ["read_only"]
        payload["discovery"] = {
            "problem": {
                "statement": "Replace with the observed problem and its evidence boundary."
            },
            "actor": {
                "id": "TARGET-ACTOR-UNKNOWN",
                "description": "Replace with the affected user, operator, or system actor.",
            },
            "hypothesis": {
                "statement": "Replace with the falsifiable value hypothesis.",
                "expected_outcome": "Replace with the observable expected outcome.",
                "assumptions": [],
            },
            "falsification": {
                "criterion": "Replace with the observation that would falsify the hypothesis.",
                "evaluation_method": "Replace with the evaluation method.",
            },
            "experiment": {
                "id": f"EXP-{work_id}",
                "method": "Replace with the bounded experiment protocol.",
                "owner": accountable,
                "status": "planned",
                "evidence_refs": [],
                "unknowns": [],
            },
            "decision": {"status": "pending"},
        }
    payload["_baseline_risk"] = baseline
    payload["_program_risk_defaults"] = risk_defaults if isinstance(risk_defaults, dict) else {}
    routed = route_record(payload, catalog)
    payload.pop("_baseline_risk", None)
    payload.pop("_program_risk_defaults", None)
    inactive_required = sorted(set(routed.required_capabilities) - active_capabilities)
    if inactive_required:
        raise ValueError(
            "Activate the routed capabilities before creating this work: "
            + ", ".join(inactive_required)
        )
    payload["required_capabilities"] = list(routed.required_capabilities)
    payload["permission_classes"] = list(routed.permissions)
    assurance = routed.minimum_assurance
    if workflow_id == "release" and isinstance(risk_defaults, dict):
        release_assurance = risk_defaults.get("minimum_release_assurance")
        if isinstance(release_assurance, str) and assurance_rank(release_assurance) > assurance_rank(
            assurance
        ):
            assurance = release_assurance
    payload["risk"] = {
        "declared_tier": baseline,
        "effective_tier": routed.computed_risk,
        "assurance_level": assurance,
        "rule_refs": list(routed.matched_rules),
    }
    for plan in payload["evidence_plan"]:
        plan["kinds"] = list(routed.required_evidence)
        plan["minimum_assurance"] = assurance
    output = overlay / "records" / "work_items" / f"{work_id}.yaml"
    for kind in ("work", "packets", "evidence", "decisions", "learnings"):
        for existing in record_files(overlay, kind):
            record, _ = load_record(existing)
            if record.get("id") == work_id:
                raise FileExistsError(f"Record id {work_id!r} already exists in {existing}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(dump_yaml(work_item), encoding="utf-8")
    render_project(target, catalog=catalog)
    return output
