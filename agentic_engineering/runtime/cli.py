from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from agentic_engineering import __version__

from .catalog import load_catalog
from .initialization import (
    confirm_tailoring,
    create_work_item,
    init_project,
    update_source_pin,
    upgrade_project,
)
from .io import load_record, load_yaml, locate_overlay
from .rendering import render_project
from .records import (
    CONTEXT_KINDS,
    DECISION_OUTCOMES,
    DECISION_TYPES,
    EVIDENCE_KINDS,
    OUTPUT_KINDS,
    PACKET_LOOP_TYPES,
    PERMISSION_CLASSES,
    create_decision,
    create_evidence,
    create_work_packet,
)
from .routing import route_record
from .transitions import TransitionError, find_work_record, transition_project
from .validation import render_report, validate_framework, validate_project


def _path(value: str | None) -> Path | None:
    return Path(value).resolve() if value else None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic",
        description="Tailor, route, validate, and render an Agentic Engineering project overlay.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Initialize a .agentic project overlay")
    init.add_argument("target", nargs="?", default=".")
    init.add_argument("--preset", default="cli_tool")
    init.add_argument("--project-id")
    init.add_argument("--project-name")
    init.add_argument("--source", default="README.md")
    init.add_argument("--framework-root")
    init.add_argument("--force", action="store_true")

    tailor = subparsers.add_parser(
        "tailor", help="Confirm that the project-specific operating model has been reviewed"
    )
    tailor.add_argument("root", nargs="?", default=".")
    tailor.add_argument("--actor", required=True)
    tailor.add_argument("--confirm", action="store_true", required=True)
    tailor.add_argument("--framework-root")

    source_update = subparsers.add_parser(
        "source-update", help="Rebaseline the authoritative source through an accountable decision"
    )
    source_update.add_argument("root", nargs="?", default=".")
    source_update.add_argument("--actor", required=True)
    source_update.add_argument("--decision-ref", required=True)
    source_update.add_argument("--declared-version")
    source_update.add_argument("--framework-root")

    validate = subparsers.add_parser("validate", help="Validate project controls and records")
    validate.add_argument("root", nargs="?", default=".")
    validate.add_argument("--framework-root")
    validate.add_argument("--json", action="store_true")
    validate.add_argument(
        "--strict",
        action="store_true",
        help="Return failure when warnings are present as well as errors",
    )

    validate_framework_parser = subparsers.add_parser(
        "validate-framework", help="Validate the reusable catalogs, workflows, roles, and schemas"
    )
    validate_framework_parser.add_argument("root", nargs="?", default="agentic_engineering")
    validate_framework_parser.add_argument("--json", action="store_true")
    validate_framework_parser.add_argument("--strict", action="store_true")

    route = subparsers.add_parser("route", help="Compute controls for a work record")
    route.add_argument("item")
    route.add_argument("--root", default=".")
    route.add_argument("--framework-root")
    route.add_argument("--json", action="store_true")

    new_work = subparsers.add_parser("new-work", help="Create a schema-backed draft work item")
    new_work.add_argument("item")
    new_work.add_argument("--title", required=True)
    new_work.add_argument("--workflow", default="feature")
    new_work.add_argument("--type", default="feature")
    new_work.add_argument("--root", default=".")
    new_work.add_argument("--framework-root")

    new_packet = subparsers.add_parser(
        "new-packet", help="Create a schema-backed draft work packet and link it to work"
    )
    new_packet.add_argument("packet")
    new_packet.add_argument("--work", required=True)
    new_packet.add_argument("--producer", required=True)
    new_packet.add_argument("--run-id", required=True)
    new_packet.add_argument("--goal", required=True)
    new_packet.add_argument("--claim", action="append", required=True)
    new_packet.add_argument("--forbid-claim", action="append", default=[])
    new_packet.add_argument("--output-kind", choices=OUTPUT_KINDS, default="file")
    new_packet.add_argument("--output-ref", required=True)
    new_packet.add_argument("--output-summary", required=True)
    new_packet.add_argument("--output-digest")
    new_packet.add_argument("--loop-type", choices=PACKET_LOOP_TYPES)
    new_packet.add_argument("--capability", action="append", default=[])
    new_packet.add_argument(
        "--permission", action="append", choices=PERMISSION_CLASSES, default=[]
    )
    new_packet.add_argument(
        "--context",
        action="append",
        default=[],
        metavar="KIND=REF",
        help=f"Additional context ({', '.join(CONTEXT_KINDS)})",
    )
    new_packet.add_argument("--skill", action="append", default=[])
    new_packet.add_argument("--tool", action="append", default=[])
    new_packet.add_argument("--context-digest")
    new_packet.add_argument("--approval-ref", action="append", default=[])
    new_packet.add_argument("--action-receipt-ref", action="append", default=[])
    new_packet.add_argument("--root", default=".")
    new_packet.add_argument("--framework-root")

    new_decision = subparsers.add_parser(
        "new-decision", help="Record an explicit schema-backed decision and update backlinks"
    )
    new_decision.add_argument("decision")
    new_decision.add_argument("--type", choices=DECISION_TYPES, required=True)
    new_decision.add_argument("--title", required=True)
    new_decision.add_argument("--subject", action="append", required=True)
    new_decision.add_argument(
        "--option", action="append", required=True, metavar="ID=SUMMARY"
    )
    new_decision.add_argument("--outcome", choices=DECISION_OUTCOMES, required=True)
    new_decision.add_argument("--selected-option", required=True)
    new_decision.add_argument("--successor-ref")
    new_decision.add_argument("--custom-value")
    new_decision.add_argument("--rationale", required=True)
    new_decision.add_argument("--owner", required=True)
    new_decision.add_argument("--reviewer", action="append", default=[])
    new_decision.add_argument("--evidence-ref", action="append", default=[])
    new_decision.add_argument(
        "--authorize-guard", action="append", default=[], metavar="GUARD"
    )
    new_decision.add_argument("--decided-at")
    new_decision.add_argument("--revisit-at")
    new_decision.add_argument("--revisit-when", action="append", default=[])
    new_decision.add_argument(
        "--authorize-permission", action="append", choices=PERMISSION_CLASSES, default=[]
    )
    new_decision.add_argument("--authorize-actor", action="append", default=[])
    new_decision.add_argument("--action-scope")
    new_decision.add_argument("--authorization-expires-at")
    new_decision.add_argument("--source-path")
    new_decision.add_argument("--source-version")
    new_decision.add_argument("--source-sha256")
    new_decision.add_argument("--from-tier", choices=("low", "medium", "high", "critical"))
    new_decision.add_argument("--to-tier", choices=("low", "medium", "high", "critical"))
    new_decision.add_argument("--risk-expires-at")
    new_decision.add_argument("--compensating-control", action="append", default=[])
    new_decision.add_argument("--root", default=".")
    new_decision.add_argument("--framework-root")

    new_evidence = subparsers.add_parser(
        "new-evidence", help="Create an explicit evidence receipt and link it to a packet"
    )
    new_evidence.add_argument("evidence")
    new_evidence.add_argument("--work", required=True)
    new_evidence.add_argument("--packet", required=True)
    new_evidence.add_argument("--kind", choices=EVIDENCE_KINDS, required=True)
    new_evidence.add_argument("--producer", required=True)
    new_evidence.add_argument("--run-id", required=True)
    new_evidence.add_argument(
        "--result", choices=("pass", "fail", "inconclusive", "not_run"), required=True
    )
    new_evidence.add_argument("--observed-at", required=True)
    new_evidence.add_argument("--acceptance-ref", action="append", default=[])
    new_evidence.add_argument("--claim", action="append", required=True)
    new_evidence.add_argument("--forbid-claim", action="append", default=[])
    subject = new_evidence.add_mutually_exclusive_group(required=True)
    subject.add_argument("--subject-ref")
    subject.add_argument("--commit")
    subject.add_argument("--artifact-digest")
    subject.add_argument("--release-ref")
    method = new_evidence.add_mutually_exclusive_group(required=True)
    method.add_argument("--command", dest="method_command")
    method.add_argument("--description")
    new_evidence.add_argument("--environment")
    new_evidence.add_argument(
        "--artifact", action="append", default=[], metavar="URI=SHA256_HEX"
    )
    new_evidence.add_argument("--context-digest")
    new_evidence.add_argument("--approval-ref")
    new_evidence.add_argument("--authorization-ref")
    new_evidence.add_argument(
        "--authorize-guard", action="append", default=[], metavar="GUARD"
    )
    new_evidence.add_argument("--rationale")
    new_evidence.add_argument("--owner")
    new_evidence.add_argument("--risk-acceptance-ref")
    new_evidence.add_argument("--root", default=".")
    new_evidence.add_argument("--framework-root")

    transition = subparsers.add_parser("transition", help="Move a record through its workflow")
    transition.add_argument("item")
    transition.add_argument("state")
    transition.add_argument("--root", default=".")
    transition.add_argument("--actor", required=True)
    transition.add_argument("--confirm-guard", action="append", default=[])
    transition.add_argument("--approval-ref", action="append", default=[])
    transition.add_argument("--evidence-ref", action="append", default=[])
    transition.add_argument("--framework-root")

    render = subparsers.add_parser("render", help="Render disposable human-readable views")
    render.add_argument("root", nargs="?", default=".")
    render.add_argument("--framework-root")

    upgrade = subparsers.add_parser("upgrade", help="Check or update the framework version pin")
    upgrade.add_argument("root", nargs="?", default=".")
    upgrade.add_argument("--framework-root")
    upgrade.add_argument("--apply", action="store_true")
    return parser


def _print_route(data: dict[str, object]) -> None:
    print(f"Declared risk: {data['declared_risk']}")
    print(f"Computed risk: {data['computed_risk']}")
    print(f"Effective risk: {data['effective_risk']}")
    print(f"Minimum assurance: {data['minimum_assurance']}")
    print(f"Permission ceiling: {data['permission_ceiling']}")
    for label, key in (
        ("Required capabilities", "required_capabilities"),
        ("Required evidence", "required_evidence"),
        ("Permissions", "permissions"),
        ("Matched rules", "matched_rules"),
    ):
        values = data[key]
        rendered = ", ".join(values) if isinstance(values, list) and values else "none"
        print(f"{label}: {rendered}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            path = init_project(
                Path(args.target),
                preset_name=args.preset,
                project_id=args.project_id,
                project_name=args.project_name,
                source_path=args.source,
                framework=_path(args.framework_root),
                force=args.force,
            )
            print(f"Initialized {path}")
            document = load_yaml(path)
            program = document.get("program", {})
            tailoring = program.get("tailoring", {}) if isinstance(program, dict) else {}
            print("\nTailoring questions:")
            for question in tailoring.get("questions", []):
                print(f"- {question}")
            target = Path(args.target).resolve()
            print("\nNext:")
            print(f"1. Edit {path} and answer the questions above.")
            print(
                "2. Confirm the tailored model: "
                f"agentic tailor {target} --actor {program.get('accountable_human', 'human:owner')} --confirm"
            )
            print(f"3. Validate it: agentic validate {target} --strict")
            print(
                "4. Create bounded work: "
                f"agentic new-work WORK-0001 --title \"First outcome\" --root {target}"
            )
            return 0

        if args.command == "tailor":
            path = confirm_tailoring(
                Path(args.root), actor=args.actor, framework=_path(args.framework_root)
            )
            print(f"Confirmed project tailoring in {path}")
            return 0

        if args.command == "source-update":
            path = update_source_pin(
                Path(args.root),
                actor=args.actor,
                decision_ref=args.decision_ref,
                declared_version=args.declared_version,
                framework=_path(args.framework_root),
            )
            print(f"Updated authoritative source pin in {path}")
            return 0

        if args.command == "validate":
            report = validate_project(
                Path(args.root),
                framework=_path(args.framework_root),
            )
            print(render_report(report, as_json=args.json))
            return 1 if not report.ok or (args.strict and report.warnings) else 0

        if args.command == "validate-framework":
            report = validate_framework(Path(args.root))
            print(render_report(report, as_json=args.json))
            return 1 if not report.ok or (args.strict and report.warnings) else 0

        if args.command == "route":
            _, overlay = locate_overlay(Path(args.root))
            path = find_work_record(overlay, args.item)
            record, _ = load_record(path)
            program_document = load_yaml(overlay / "program.yaml")
            program = (
                program_document.get("program", {})
                if isinstance(program_document.get("program"), dict)
                else program_document
            )
            risk_defaults = program.get("risk_defaults", {})
            if isinstance(risk_defaults, dict):
                record["_program_risk_defaults"] = risk_defaults
                if isinstance(risk_defaults.get("baseline"), str):
                    record["_baseline_risk"] = risk_defaults["baseline"]
            if "risk_tier" not in record and isinstance(record.get("risk"), str):
                record["risk_tier"] = record["risk"]
            if "workflow" not in record and isinstance(record.get("route"), str):
                record["workflow"] = record["route"]
            catalog = load_catalog(_path(args.framework_root))
            data = route_record(record, catalog).as_dict()
            data["item"] = args.item
            data["record"] = str(path)
            if args.json:
                print(json.dumps(data, indent=2, sort_keys=True))
            else:
                print(f"Work item: {args.item}")
                _print_route(data)
            return 0

        if args.command == "new-work":
            path = create_work_item(
                Path(args.root),
                args.item,
                title=args.title,
                workflow_id=args.workflow,
                work_type=args.type,
                framework=_path(args.framework_root),
            )
            print(f"Created {path}")
            return 0

        if args.command == "new-packet":
            path = create_work_packet(
                Path(args.root),
                args.packet,
                work_id=args.work,
                producer_id=args.producer,
                run_id=args.run_id,
                goal=args.goal,
                claims_requested=args.claim,
                claims_forbidden=args.forbid_claim,
                output_kind=args.output_kind,
                output_ref=args.output_ref,
                output_summary=args.output_summary,
                output_digest=args.output_digest,
                loop_type=args.loop_type,
                capability_refs=args.capability or None,
                permission_classes=args.permission or None,
                contexts=args.context,
                skill_refs=args.skill,
                tooling=args.tool,
                context_manifest_digest=args.context_digest,
                approval_refs=args.approval_ref,
                action_receipt_refs=args.action_receipt_ref,
                framework=_path(args.framework_root),
            )
            print(f"Created draft work packet {path}")
            return 0

        if args.command == "new-decision":
            path = create_decision(
                Path(args.root),
                args.decision,
                decision_type=args.type,
                title=args.title,
                subject_refs=args.subject,
                options=args.option,
                outcome=args.outcome,
                selected_option_ref=args.selected_option,
                successor_ref=args.successor_ref,
                custom_value=args.custom_value,
                rationale=args.rationale,
                owner_id=args.owner,
                reviewer_ids=args.reviewer,
                evidence_refs=args.evidence_ref,
                guard_authorizations=args.authorize_guard,
                decided_at=args.decided_at,
                revisit_at=args.revisit_at,
                revisit_when=args.revisit_when,
                authorize_permissions=args.authorize_permission,
                authorize_actors=args.authorize_actor,
                action_scope=args.action_scope,
                authorization_expires_at=args.authorization_expires_at,
                source_update_path=args.source_path,
                source_update_version=args.source_version,
                source_update_sha256=args.source_sha256,
                from_tier=args.from_tier,
                to_tier=args.to_tier,
                risk_expires_at=args.risk_expires_at,
                compensating_controls=args.compensating_control,
                framework=_path(args.framework_root),
            )
            print(f"Created decision {path}")
            return 0

        if args.command == "new-evidence":
            subject_record = {
                key: value
                for key, value in (
                    ("ref", args.subject_ref),
                    ("commit", args.commit),
                    ("artifact_digest", args.artifact_digest),
                    ("release_ref", args.release_ref),
                )
                if value is not None
            }
            method_record = {
                key: value
                for key, value in (
                    ("command", args.method_command),
                    ("description", args.description),
                    ("environment", args.environment),
                )
                if value is not None
            }
            path = create_evidence(
                Path(args.root),
                args.evidence,
                work_id=args.work,
                packet_id=args.packet,
                kind=args.kind,
                producer_id=args.producer,
                run_id=args.run_id,
                result=args.result,
                observed_at=args.observed_at,
                acceptance_refs=args.acceptance_ref,
                claims_authorized=args.claim,
                claims_forbidden=args.forbid_claim,
                subject=subject_record,
                method=method_record,
                artifacts=args.artifact,
                context_manifest_digest=args.context_digest,
                approval_ref=args.approval_ref,
                authorization_ref=args.authorization_ref,
                guard_authorizations=args.authorize_guard,
                rationale=args.rationale,
                owner_id=args.owner,
                risk_acceptance_ref=args.risk_acceptance_ref,
                framework=_path(args.framework_root),
            )
            print(f"Created evidence receipt {path}")
            return 0

        if args.command == "transition":
            path = transition_project(
                Path(args.root),
                args.item,
                args.state,
                actor=args.actor,
                confirm_guards=tuple(args.confirm_guard),
                approval_refs=tuple(args.approval_ref),
                evidence_refs=tuple(args.evidence_ref),
                framework=_path(args.framework_root),
            )
            print(f"Transitioned {args.item} to {args.state} in {path}")
            return 0

        if args.command == "render":
            paths = render_project(Path(args.root), framework=_path(args.framework_root))
            for path in paths:
                print(path)
            return 0

        if args.command == "upgrade":
            current, available, changed = upgrade_project(
                Path(args.root), framework=_path(args.framework_root), apply=args.apply
            )
            if changed:
                print(f"Updated framework pin {current} -> {available}")
            elif current == available:
                print(f"Framework is current at {available}")
            else:
                print(f"Framework update available: {current} -> {available}; rerun with --apply")
            return 0
    except (FileNotFoundError, FileExistsError, ValueError, TransitionError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
