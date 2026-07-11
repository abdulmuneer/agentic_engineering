from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from agentic_engineering.runtime.catalog import framework_fingerprint, load_catalog
from agentic_engineering.runtime.initialization import (
    confirm_tailoring,
    create_work_item,
    init_project,
    update_source_pin,
    upgrade_project,
)
from agentic_engineering.runtime.io import sha256_file
from agentic_engineering.runtime.records import create_decision, create_work_packet
from agentic_engineering.runtime.rendering import render_project
from agentic_engineering.runtime.routing import route_record
from agentic_engineering.runtime.transitions import TransitionError, transition_project
from agentic_engineering.runtime.validation import validate_framework, validate_project


REPO_ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_ROOT = REPO_ROOT / "agentic_engineering"
FORNAX_EXAMPLE = FRAMEWORK_ROOT / "examples" / "fornax"


def confirm_test_tailoring(root: Path) -> None:
    manifest_path = root / ".agentic" / "program.yaml"
    document = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    tailoring = document["program"]["tailoring"]
    tailoring["answers"] = [
        {"question": question, "answer": "Reviewed and tailored for this test project."}
        for question in tailoring["questions"]
    ]
    manifest_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    confirm_tailoring(root, actor="human:owner", framework=FRAMEWORK_ROOT)


class FrameworkValidationTests(unittest.TestCase):
    def test_framework_contracts_are_internally_consistent(self) -> None:
        report = validate_framework(FRAMEWORK_ROOT)
        self.assertTrue(report.ok, [issue.as_dict() for issue in report.issues])
        self.assertEqual([], report.warnings)

    def test_fornax_reference_example_is_valid(self) -> None:
        report = validate_project(FORNAX_EXAMPLE)
        self.assertTrue(report.ok, [issue.as_dict() for issue in report.issues])
        self.assertEqual([], report.warnings)

    def test_stale_fornax_manifest_is_rejected_for_one_specific_reason(self) -> None:
        report = validate_project(FORNAX_EXAMPLE / "invalid" / "stale-manifest")
        self.assertFalse(report.ok)
        self.assertEqual(["source-version-drift"], [issue.code for issue in report.errors])


class RoutingTests(unittest.TestCase):
    def test_authentication_change_forces_high_risk_and_a2(self) -> None:
        catalog = load_catalog(FRAMEWORK_ROOT)
        route = route_record(
            {
                "type": "feature",
                "workflow": "feature",
                "risk": {"declared_tier": "low", "effective_tier": "low"},
                "change": {
                    "authentication": True,
                    "authorization": False,
                    "production_affecting": False,
                    "sensitive_data": False,
                    "regulated_impact": False,
                    "destructive_migration": False,
                    "safety_impact": "none",
                    "reversibility": "easy",
                    "blast_radius": "component",
                },
                "required_capabilities": ["backend_delivery", "verification"],
                "permission_classes": ["local_write", "sensitive"],
                "_baseline_risk": "low",
            },
            catalog,
        )
        self.assertEqual("high", route.computed_risk)
        self.assertEqual("A2", route.minimum_assurance)
        self.assertEqual("sensitive", route.permission_ceiling)
        self.assertIn("RISK-IDENTITY", route.matched_rules)

    def test_fornax_route_preserves_domain_specific_capability_cell(self) -> None:
        catalog = load_catalog(FRAMEWORK_ROOT)
        work = yaml.safe_load((FORNAX_EXAMPLE / "work" / "WI-G2-001.yaml").read_text())[
            "work_item"
        ]
        work["_baseline_risk"] = "medium"
        route = route_record(work, catalog)
        self.assertEqual("high", route.effective_risk)
        self.assertEqual("A2", route.minimum_assurance)
        self.assertIn("research_assurance", route.required_capabilities)

    def test_regulated_release_uses_preset_a3_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# Regulated product\n", encoding="utf-8")
            init_project(root, preset_name="regulated_service", framework=FRAMEWORK_ROOT)
            path = create_work_item(
                root,
                "REL-NEW",
                title="Release the bounded regulated change",
                workflow_id="release",
                work_type="release",
                framework=FRAMEWORK_ROOT,
            )
            work = yaml.safe_load(path.read_text(encoding="utf-8"))["work_item"]
            self.assertEqual("high", work["risk"]["effective_tier"])
            self.assertEqual("A3", work["risk"]["assurance_level"])
            self.assertIn("deployment_receipt", work["evidence_plan"][0]["kinds"])


class ProjectLifecycleTests(unittest.TestCase):
    def test_init_preserves_root_agent_guidance_and_adds_one_managed_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            agents = root / "AGENTS.md"
            agents.write_text("# Product-specific guidance\n\nKeep this text.\n", encoding="utf-8")
            init_project(root, preset_name="cli_tool", framework=FRAMEWORK_ROOT)
            init_project(
                root, preset_name="cli_tool", framework=FRAMEWORK_ROOT, force=True
            )
            rendered = agents.read_text(encoding="utf-8")
            self.assertIn("Keep this text.", rendered)
            self.assertEqual(1, rendered.count("<!-- agentic-engineering:start -->"))

    def test_source_update_requires_and_records_bound_decision(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "README.md"
            source.write_text("# Version one\n", encoding="utf-8")
            init_project(
                root,
                preset_name="cli_tool",
                project_id="source-example",
                framework=FRAMEWORK_ROOT,
            )
            source.write_text("# Version two\n", encoding="utf-8")
            create_decision(
                root,
                "DEC-SOURCE-2",
                decision_type="product",
                title="Adopt authoritative source version two",
                subject_refs=["source-example"],
                options=["OPTION-ADOPT=Adopt the reviewed source update."],
                outcome="approve",
                selected_option_ref="OPTION-ADOPT",
                rationale="The accountable owner reviewed the source change.",
                owner_id="human:owner",
                source_update_path="README.md",
                source_update_version="2",
                source_update_sha256=sha256_file(source),
                framework=FRAMEWORK_ROOT,
            )
            manifest = update_source_pin(
                root,
                actor="human:owner",
                decision_ref="DEC-SOURCE-2",
                declared_version="2",
                framework=FRAMEWORK_ROOT,
            )
            program = yaml.safe_load(manifest.read_text(encoding="utf-8"))["program"]
            self.assertEqual("2", program["source_of_truth"]["declared_version"])
            self.assertEqual(sha256_file(source), program["source_of_truth"]["sha256"])
            self.assertEqual(
                "DEC-SOURCE-2", program["source_of_truth"]["update_decision_ref"]
            )
            self.assertEqual(
                "unversioned",
                program["source_of_truth"]["history"][0]["declared_version"],
            )
            with self.assertRaisesRegex(ValueError, "already been used"):
                update_source_pin(
                    root,
                    actor="human:owner",
                    decision_ref="DEC-SOURCE-2",
                    declared_version="2",
                    framework=FRAMEWORK_ROOT,
                )

    def test_fake_risk_waiver_does_not_suppress_computed_risk(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)
            work_path = root / "work" / "WI-G2-001.yaml"
            document = yaml.safe_load(work_path.read_text(encoding="utf-8"))
            document["work_item"]["risk"]["effective_tier"] = "medium"
            document["work_item"]["risk"]["waiver_ref"] = "DEC-DOES-NOT-EXIST"
            work_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            render_project(root, framework=FRAMEWORK_ROOT)
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertIn("risk-waiver-not-found", [issue.code for issue in report.errors])

    def test_packet_cannot_exceed_work_or_actor_permission_ceiling(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)
            packet_path = root / "work_packets" / "AWP-G2-001.yaml"
            document = yaml.safe_load(packet_path.read_text(encoding="utf-8"))
            document["work_packet"]["permission_classes"].append("production")
            packet_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            render_project(root, framework=FRAMEWORK_ROOT)
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            codes = [issue.code for issue in report.errors]
            self.assertIn("packet-permission-out-of-scope", codes)
            self.assertIn("packet-permission-ceiling", codes)

    def test_discovery_new_work_is_schema_valid_and_requires_discovery_section(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# Discovery example\n", encoding="utf-8")
            init_project(root, preset_name="cli_tool", framework=FRAMEWORK_ROOT)
            path = create_work_item(
                root,
                "DISC-NEW",
                title="Validate the product hypothesis",
                workflow_id="discovery",
                framework=FRAMEWORK_ROOT,
            )

            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertTrue(report.ok, [issue.as_dict() for issue in report.issues])
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual("discovery", document["work_item"]["type"])
            self.assertIn("discovery", document["work_item"])

            del document["work_item"]["discovery"]
            path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            missing = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertIn("json-schema", [issue.code for issue in missing.errors])

    def test_failed_fornax_evidence_cannot_satisfy_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)
            for evidence_id in ("EV-G2-001", "EV-G2-EXPERIMENT", "EV-G2-REVIEW"):
                evidence_path = root / "evidence" / f"{evidence_id}.yaml"
                document = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
                document["evidence"]["result"] = "fail"
                evidence_path.write_text(
                    yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
                )
            render_project(root, framework=FRAMEWORK_ROOT)

            report = validate_project(root, framework=FRAMEWORK_ROOT)
            codes = [issue.code for issue in report.errors]
            self.assertIn("packet-evidence-not-passing", codes)
            self.assertIn("acceptance-evidence-gap", codes)

    def test_work_evidence_coverage_aggregates_across_linked_packets(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)

            work_path = root / "work" / "WI-G2-001.yaml"
            work_document = yaml.safe_load(work_path.read_text(encoding="utf-8"))
            work = work_document["work_item"]
            work["work_packet_refs"].append("AWP-G2-002")
            work["evidence_plan"][0]["kinds"] = ["integration_test"]
            work["evidence_plan"][1]["kinds"] = ["experiment_result"]
            work["evidence_plan"][2]["kinds"] = ["review"]
            work_path.write_text(
                yaml.safe_dump(work_document, sort_keys=False), encoding="utf-8"
            )

            packet_path = root / "work_packets" / "AWP-G2-001.yaml"
            packet_document = yaml.safe_load(packet_path.read_text(encoding="utf-8"))
            packet = packet_document["work_packet"]
            packet["verification_evidence_refs"] = [
                "EV-G2-001",
                "EV-G2-EXPERIMENT",
                "EV-G2-REVIEW",
            ]
            packet_path.write_text(
                yaml.safe_dump(packet_document, sort_keys=False), encoding="utf-8"
            )

            second_packet_document = yaml.safe_load(
                yaml.safe_dump(packet_document, sort_keys=False)
            )
            second_packet = second_packet_document["work_packet"]
            second_packet["id"] = "AWP-G2-002"
            second_packet["permission_classes"] = ["local_write"]
            second_packet["approval_refs"] = []
            second_packet["action_receipt_refs"] = []
            second_packet["verification_evidence_refs"] = ["EV-G2-REVIEW-002"]
            second_packet["review_refs"] = ["EV-G2-REVIEW-002"]
            (root / "work_packets" / "AWP-G2-002.yaml").write_text(
                yaml.safe_dump(second_packet_document, sort_keys=False), encoding="utf-8"
            )

            evidence_acceptance = {
                "EV-G2-001": ["AC-G2-01"],
                "EV-G2-EXPERIMENT": ["AC-G2-02"],
                "EV-G2-REVIEW": ["AC-G2-01"],
            }
            for evidence_id, acceptance_refs in evidence_acceptance.items():
                evidence_path = root / "evidence" / f"{evidence_id}.yaml"
                evidence_document = yaml.safe_load(
                    evidence_path.read_text(encoding="utf-8")
                )
                evidence_document["evidence"]["acceptance_refs"] = acceptance_refs
                evidence_path.write_text(
                    yaml.safe_dump(evidence_document, sort_keys=False), encoding="utf-8"
                )

            review_path = root / "evidence" / "EV-G2-REVIEW.yaml"
            second_review_document = yaml.safe_load(
                review_path.read_text(encoding="utf-8")
            )
            second_review = second_review_document["evidence"]
            second_review["id"] = "EV-G2-REVIEW-002"
            second_review["packet_ref"] = "AWP-G2-002"
            second_review["acceptance_refs"] = ["AC-G2-03"]
            (root / "evidence" / "EV-G2-REVIEW-002.yaml").write_text(
                yaml.safe_dump(second_review_document, sort_keys=False), encoding="utf-8"
            )

            render_project(root, framework=FRAMEWORK_ROOT)
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertTrue(report.ok, [issue.as_dict() for issue in report.issues])

    def test_each_planned_evidence_kind_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)
            work_path = root / "work" / "WI-G2-001.yaml"
            work_document = yaml.safe_load(work_path.read_text(encoding="utf-8"))
            work_document["work_item"]["evidence_plan"][0]["kinds"].append("document")
            work_path.write_text(
                yaml.safe_dump(work_document, sort_keys=False), encoding="utf-8"
            )
            render_project(root, framework=FRAMEWORK_ROOT)

            report = validate_project(root, framework=FRAMEWORK_ROOT)
            plan_gaps = [
                issue for issue in report.errors if issue.code == "evidence-plan-unsatisfied"
            ]
            self.assertEqual(1, len(plan_gaps))
            self.assertIn(
                "(AC-G2-01, document, physical-two-node-lab)", plan_gaps[0].message
            )

    def test_undeclared_transition_actor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            init_project(root, preset_name="cli_tool", framework=FRAMEWORK_ROOT)
            create_work_item(
                root,
                "WORK-ACTOR",
                title="Bounded capability",
                workflow_id="feature",
                framework=FRAMEWORK_ROOT,
            )
            confirm_test_tailoring(root)

            with self.assertRaisesRegex(TransitionError, "is not declared by the program"):
                transition_project(
                    root,
                    "WORK-ACTOR",
                    "classified",
                    actor="agent:undeclared",
                    framework=FRAMEWORK_ROOT,
                )

    def test_incomplete_transition_history_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)
            work_path = root / "work" / "WI-G2-001.yaml"
            document = yaml.safe_load(work_path.read_text(encoding="utf-8"))
            del document["work_item"]["state"]["history"][0]
            work_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            render_project(root, framework=FRAMEWORK_ROOT)

            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertIn("transition-initial-state", [issue.code for issue in report.errors])

    def test_framework_lock_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            manifest = init_project(root, preset_name="cli_tool", framework=FRAMEWORK_ROOT)
            document = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            document["program"]["framework_lock"]["catalog_sha256"] = "0" * 64
            manifest.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            render_project(root, framework=FRAMEWORK_ROOT)

            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertIn("framework-lock-drift", [issue.code for issue in report.errors])

    def test_framework_behavior_fingerprint_is_root_stable_and_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            copied_framework = Path(raw) / "framework"
            for relative in ("catalog", "team", "schemas", "runtime", "presets"):
                shutil.copytree(FRAMEWORK_ROOT / relative, copied_framework / relative)

            expected = framework_fingerprint(FRAMEWORK_ROOT)
            copied = framework_fingerprint(copied_framework)
            self.assertEqual(expected, copied)

            runtime_path = copied_framework / "runtime" / "routing.py"
            runtime_path.write_text(
                runtime_path.read_text(encoding="utf-8") + "\n# fingerprint test\n",
                encoding="utf-8",
            )
            runtime_changed = framework_fingerprint(copied_framework)
            self.assertNotEqual(copied["behavior_sha256"], runtime_changed["behavior_sha256"])
            self.assertEqual(copied["catalog_sha256"], runtime_changed["catalog_sha256"])
            self.assertEqual(copied["schemas_sha256"], runtime_changed["schemas_sha256"])

            preset_path = copied_framework / "presets" / "cli_tool.yaml"
            preset_path.write_text(
                preset_path.read_text(encoding="utf-8") + "\n# fingerprint test\n",
                encoding="utf-8",
            )
            preset_changed = framework_fingerprint(copied_framework)
            self.assertNotEqual(
                runtime_changed["behavior_sha256"], preset_changed["behavior_sha256"]
            )

    def test_framework_behavior_lock_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            manifest = init_project(root, preset_name="cli_tool", framework=FRAMEWORK_ROOT)
            document = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                framework_fingerprint(FRAMEWORK_ROOT)["behavior_sha256"],
                document["program"]["framework_lock"]["behavior_sha256"],
            )
            document["program"]["framework_lock"]["behavior_sha256"] = "0" * 64
            manifest.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            render_project(root, framework=FRAMEWORK_ROOT)

            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertIn("framework-lock-drift", [issue.code for issue in report.errors])

    def test_framework_upgrade_adds_behavior_lock(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            manifest = init_project(root, preset_name="cli_tool", framework=FRAMEWORK_ROOT)
            document = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            del document["program"]["framework_lock"]["behavior_sha256"]
            manifest.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

            _, _, applied = upgrade_project(root, framework=FRAMEWORK_ROOT)
            self.assertFalse(applied)
            _, _, applied = upgrade_project(root, framework=FRAMEWORK_ROOT, apply=True)
            self.assertTrue(applied)

            upgraded = yaml.safe_load(manifest.read_text(encoding="utf-8"))
            self.assertEqual(
                framework_fingerprint(FRAMEWORK_ROOT)["behavior_sha256"],
                upgraded["program"]["framework_lock"]["behavior_sha256"],
            )
            self.assertTrue(validate_project(root, framework=FRAMEWORK_ROOT).ok)

    def test_new_work_is_valid_but_cannot_leave_draft_until_tailored(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            init_project(root, preset_name="cli_tool", framework=FRAMEWORK_ROOT)
            path = create_work_item(
                root,
                "WORK-NEW",
                title="Bounded capability",
                workflow_id="feature",
                framework=FRAMEWORK_ROOT,
            )
            self.assertTrue(validate_project(root, framework=FRAMEWORK_ROOT).ok)
            with self.assertRaisesRegex(TransitionError, "tailoring is pending"):
                transition_project(
                    root,
                    "WORK-NEW",
                    "classified",
                    actor="human:owner",
                    framework=FRAMEWORK_ROOT,
                )
            confirm_test_tailoring(root)
            with self.assertRaisesRegex(TransitionError, "objective_defined"):
                transition_project(
                    root,
                    "WORK-NEW",
                    "classified",
                    actor="human:owner",
                    framework=FRAMEWORK_ROOT,
                )
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            document["work_item"]["objective"] = "Expose a deterministic, observable capability."
            document["work_item"]["acceptance"][0]["statement"] = "The named behavior is observable."
            path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(TransitionError, "risk_facts_complete"):
                transition_project(
                    root,
                    "WORK-NEW",
                    "classified",
                    actor="human:owner",
                    framework=FRAMEWORK_ROOT,
                )
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            document["work_item"]["change"].update(
                {
                    "production_affecting": False,
                    "authentication": False,
                    "authorization": False,
                    "sensitive_data": False,
                    "safety_impact": "none",
                    "regulated_impact": False,
                    "destructive_migration": False,
                    "external_write": False,
                    "reversibility": "easy",
                    "blast_radius": "local",
                }
            )
            document["work_item"]["risk"] = {
                "declared_tier": "low",
                "effective_tier": "low",
                "assurance_level": "A0",
                "rule_refs": [],
            }
            document["work_item"]["evidence_plan"][0]["minimum_assurance"] = "A0"
            path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            transition_project(
                root,
                "WORK-NEW",
                "classified",
                actor="human:owner",
                framework=FRAMEWORK_ROOT,
            )

    def test_init_render_validate_and_source_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "README.md"
            source.write_text("# Example product\n", encoding="utf-8")
            init_project(
                root,
                preset_name="cli_tool",
                project_id="example-product",
                framework=FRAMEWORK_ROOT,
            )
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertTrue(report.ok, [issue.as_dict() for issue in report.issues])
            self.assertEqual(["tailoring-pending"], [issue.code for issue in report.warnings])
            confirm_test_tailoring(root)
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertTrue(report.ok, [issue.as_dict() for issue in report.issues])
            self.assertEqual([], report.warnings)

            source.write_text("# Materially changed product\n", encoding="utf-8")
            drift = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertIn("source-hash-drift", [issue.code for issue in drift.errors])

    def test_generated_view_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            init_project(root, preset_name="cli_tool", framework=FRAMEWORK_ROOT)
            generated = root / ".agentic" / "generated" / "AGENTS.md"
            generated.write_text("stale\n", encoding="utf-8")
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertIn("generated-view-drift", [issue.code for issue in report.errors])

    def test_canonical_yaml_work_item_can_transition(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            init_project(root, preset_name="cli_tool", framework=FRAMEWORK_ROOT)
            destination = root / ".agentic" / "records" / "work_items" / "WORK-0001.yaml"
            shutil.copy2(
                FRAMEWORK_ROOT
                / "templates"
                / "overlay"
                / ".agentic"
                / "records"
                / "work_items"
                / "WORK-0001.yaml",
                destination,
            )
            initial_document = yaml.safe_load(destination.read_text(encoding="utf-8"))
            manifest_document = yaml.safe_load(
                (root / ".agentic" / "program.yaml").read_text(encoding="utf-8")
            )
            initial_document["work_item"]["source_revision"] = manifest_document["program"][
                "source_of_truth"
            ]["declared_version"]
            initial_document["work_item"]["decision_refs"] = []
            initial_document["work_item"]["work_packet_refs"] = []
            destination.write_text(
                yaml.safe_dump(initial_document, sort_keys=False), encoding="utf-8"
            )
            confirm_test_tailoring(root)
            transition_project(
                root,
                "WORK-0001",
                "classified",
                actor="human:owner",
                framework=FRAMEWORK_ROOT,
            )
            data = yaml.safe_load(destination.read_text(encoding="utf-8"))["work_item"]
            self.assertEqual("classified", data["state"]["current"])
            self.assertEqual("draft", data["state"]["history"][-1]["from"])

            transition_project(
                root,
                "WORK-0001",
                "ready",
                actor="human:owner",
                framework=FRAMEWORK_ROOT,
            )
            with self.assertRaisesRegex(TransitionError, "review_capacity_available"):
                transition_project(
                    root,
                    "WORK-0001",
                    "in_progress",
                    actor="human:owner",
                    framework=FRAMEWORK_ROOT,
                )
            with self.assertRaisesRegex(TransitionError, "explicitly authorizes that guard"):
                transition_project(
                    root,
                    "WORK-0001",
                    "in_progress",
                    actor="human:owner",
                    confirm_guards=("review_capacity_available",),
                    framework=FRAMEWORK_ROOT,
                )
            decision_destination = (
                root / ".agentic" / "records" / "decisions" / "DEC-0001.yaml"
            )
            shutil.copy2(
                FRAMEWORK_ROOT
                / "templates"
                / "overlay"
                / ".agentic"
                / "records"
                / "decisions"
                / "DEC-0001.yaml",
                decision_destination,
            )
            decision_document = yaml.safe_load(decision_destination.read_text(encoding="utf-8"))
            decision_document["decision"]["subject_refs"] = ["WORK-0001"]
            decision_document["decision"]["guard_authorizations"] = []
            decision_destination.write_text(
                yaml.safe_dump(decision_document, sort_keys=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(TransitionError, "explicitly authorizes that guard"):
                transition_project(
                    root,
                    "WORK-0001",
                    "in_progress",
                    actor="human:owner",
                    confirm_guards=("review_capacity_available",),
                    approval_refs=("DEC-0001",),
                    framework=FRAMEWORK_ROOT,
                )
            decision_document["decision"]["guard_authorizations"] = [
                "review_capacity_available"
            ]
            decision_destination.write_text(
                yaml.safe_dump(decision_document, sort_keys=False), encoding="utf-8"
            )
            transition_project(
                root,
                "WORK-0001",
                "in_progress",
                actor="human:owner",
                confirm_guards=("review_capacity_available",),
                approval_refs=("DEC-0001",),
                framework=FRAMEWORK_ROOT,
            )
            data = yaml.safe_load(destination.read_text(encoding="utf-8"))["work_item"]
            self.assertIn("review_capacity_available", data["state"]["history"][-1]["guard_refs"])

            create_work_packet(
                root,
                "AWP-DRAFT",
                work_id="WORK-0001",
                producer_id="agent:delivery",
                run_id="RUN-DRAFT",
                goal="Produce the bounded sample output.",
                claims_requested=["acceptance:AC-1"],
                output_kind="file",
                output_ref="src/example.py",
                output_summary="Draft output awaiting review.",
                framework=FRAMEWORK_ROOT,
            )
            with self.assertRaisesRegex(TransitionError, "work_packet_complete"):
                transition_project(
                    root,
                    "WORK-0001",
                    "review",
                    actor="agent:delivery",
                    confirm_guards=("work_packet_complete", "producer_checks_recorded"),
                    framework=FRAMEWORK_ROOT,
                )

    def test_correlated_a2_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)
            evidence_path = root / "evidence" / "EV-G2-001.yaml"
            document = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
            document["evidence"]["producer"]["actor"] = "agent:runtime-integration"
            evidence_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            render_project(root, framework=FRAMEWORK_ROOT)
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertIn("assurance-correlated-producer", [issue.code for issue in report.errors])

    def test_evidence_subject_must_bind_to_declared_packet_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)
            evidence_path = root / "evidence" / "EV-G2-001.yaml"
            document = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
            document["evidence"]["subject"] = {"ref": "artifact://unrelated-output"}
            evidence_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            render_project(root, framework=FRAMEWORK_ROOT)
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertIn(
                "evidence-subject-packet-mismatch",
                [issue.code for issue in report.errors],
            )

    def test_action_receipt_must_follow_actor_bound_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)
            action_path = root / "evidence" / "EV-G2-ACTION.yaml"
            action = yaml.safe_load(action_path.read_text(encoding="utf-8"))
            action["evidence"]["observed_at"] = "2026-07-10T09:00:00Z"
            action_path.write_text(yaml.safe_dump(action, sort_keys=False), encoding="utf-8")
            work_path = root / "work" / "WI-G2-001.yaml"
            work = yaml.safe_load(work_path.read_text(encoding="utf-8"))
            work["work_item"]["state"]["history"][3]["actor"] = "agent:numerical-correctness"
            work_path.write_text(yaml.safe_dump(work, sort_keys=False), encoding="utf-8")
            render_project(root, framework=FRAMEWORK_ROOT)
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            codes = [issue.code for issue in report.errors]
            self.assertIn("action-receipt-before-authorization", codes)
            self.assertIn("transition-permission-authorization", codes)

    def test_guard_receipt_must_authorize_the_exact_guard(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)
            decision_path = root / "decisions" / "DEC-G2-PERMISSION.yaml"
            decision = yaml.safe_load(decision_path.read_text(encoding="utf-8"))
            decision["decision"]["guard_authorizations"] = ["different_guard"]
            decision_path.write_text(yaml.safe_dump(decision, sort_keys=False), encoding="utf-8")
            render_project(root, framework=FRAMEWORK_ROOT)
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            codes = [issue.code for issue in report.errors]
            self.assertIn("transition-guard-authorization", codes)
            self.assertIn("transition-permission-authorization", codes)

    def test_claims_cannot_exceed_evidence_authority(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "fornax"
            shutil.copytree(FORNAX_EXAMPLE, root)
            for evidence_id in ("EV-G2-001", "EV-G2-EXPERIMENT", "EV-G2-REVIEW"):
                evidence_path = root / "evidence" / f"{evidence_id}.yaml"
                document = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
                document["evidence"]["claims_authorized"].remove(
                    "numerical_equivalence_for_named_fixture"
                )
                evidence_path.write_text(
                    yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
                )
            render_project(root, framework=FRAMEWORK_ROOT)
            report = validate_project(root, framework=FRAMEWORK_ROOT)
            self.assertIn("claim-authority-gap", [issue.code for issue in report.errors])


if __name__ == "__main__":
    unittest.main()
