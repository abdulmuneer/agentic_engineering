from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

import yaml

from agentic_engineering.runtime.authorization import decision_covers
from agentic_engineering.runtime.catalog import load_catalog
from agentic_engineering.runtime.cli import main
from agentic_engineering.runtime.initialization import create_work_item, init_project
from agentic_engineering.runtime.records import create_decision
from agentic_engineering.runtime.rendering import render_project
from agentic_engineering.runtime.routing import route_record
from agentic_engineering.runtime.transitions import TransitionError, transition_project
from agentic_engineering.runtime.validation import (
    ValidationReport,
    _review_reached,
    render_report,
    validate_framework,
    validate_project,
)

from tests.test_runtime import confirm_test_tailoring


REPO_ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_ROOT = REPO_ROOT / "agentic_engineering"
LEAN_EXAMPLE = FRAMEWORK_ROOT / "examples" / "lean-research"
FORNAX_EXAMPLE = FRAMEWORK_ROOT / "examples" / "fornax"
STANDING = "DEC-RESUME-AFTER-CHECKPOINT"


def read(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write(path: Path, document: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def edit(path: Path, change: Callable[[dict[str, Any]], None]) -> None:
    document = read(path)
    change(document)
    write(path, document)


def codes(issues: list[Any]) -> list[str]:
    return [issue.code for issue in issues]


def run_cli(*argv: str) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        status = main(list(argv))
    return status, buffer.getvalue()


class LeanCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.tmp = Path(self.temporary.name)

    def lean_copy(self) -> Path:
        root = self.tmp / "lean"
        shutil.copytree(LEAN_EXAMPLE, root)
        return root

    def validate(self, root: Path) -> ValidationReport:
        render_project(root, framework=FRAMEWORK_ROOT)
        return validate_project(root, framework=FRAMEWORK_ROOT)

    def second_run(self, root: Path, run_id: str = "RUN-0002") -> Path:
        """Copy RUN-0001 as a fresh draft run with no results."""
        document = read(root / "work" / "RUN-0001.yaml")
        work = document["work_item"]
        work["id"] = run_id
        work["state"] = {"current": "draft", "history": [work["state"]["history"][0]]}
        work["decision_refs"] = []
        work.pop("results")
        work.pop("budget")
        path = root / "work" / f"{run_id}.yaml"
        write(path, document)
        return path


class LedgerWorkflowTests(LeanCase):
    def test_lean_example_and_framework_validate_strictly(self) -> None:
        report = validate_project(LEAN_EXAMPLE, framework=FRAMEWORK_ROOT)
        self.assertEqual([], [issue.as_dict() for issue in report.issues])
        framework = validate_framework(FRAMEWORK_ROOT)
        self.assertEqual([], [issue.as_dict() for issue in framework.issues])

    def test_run_goes_draft_to_closed_without_packets_or_evidence(self) -> None:
        root = self.tmp / "project"
        root.mkdir()
        (root / "README.md").write_text("# Research\n", encoding="utf-8")
        init_project(root, preset_name="research_platform", framework=FRAMEWORK_ROOT)
        confirm_test_tailoring(root)
        path = create_work_item(
            root, "RUN-1", title="Baseline", workflow_id="run", framework=FRAMEWORK_ROOT
        )

        def assess(document: dict[str, Any]) -> None:
            work = document["work_item"]
            work["objective"] = "Measure the baseline on the held-out set."
            work["acceptance"][0]["statement"] = "A results file reports the metric."
            work["change"].update(
                production_affecting=False,
                authentication=False,
                authorization=False,
                sensitive_data=False,
                safety_impact="none",
                regulated_impact=False,
                destructive_migration=False,
                external_write=False,
                reversibility="easy",
                blast_radius="local",
            )
            work["risk"].update(declared_tier="low", effective_tier="low", assurance_level="A0")

        edit(path, assess)
        self.assertNotIn("evidence_plan", read(path)["work_item"])
        transition_project(root, "RUN-1", "running", actor="human:owner", framework=FRAMEWORK_ROOT)
        with self.assertRaisesRegex(TransitionError, "results_recorded"):
            transition_project(root, "RUN-1", "closed", actor="human:owner", framework=FRAMEWORK_ROOT)
        edit(
            path,
            lambda document: document["work_item"].update(
                results={
                    "ref": "runs/RUN-1/results.md",
                    "not_established": ["Out-of-domain behaviour."],
                    "receipts": [{"uri": "gs://bucket/RUN-1/bundle.tar"}],
                }
            ),
        )
        transition_project(root, "RUN-1", "closed", actor="human:owner", framework=FRAMEWORK_ROOT)
        report = validate_project(root, framework=FRAMEWORK_ROOT)
        self.assertEqual([], [issue.as_dict() for issue in report.issues])
        self.assertEqual("closed", read(path)["work_item"]["state"]["current"])

    def test_new_run_with_unassessed_facts_is_rejected_as_consequential(self) -> None:
        root = self.tmp / "project"
        root.mkdir()
        (root / "README.md").write_text("# Research\n", encoding="utf-8")
        init_project(root, preset_name="research_platform", framework=FRAMEWORK_ROOT)
        create_work_item(root, "RUN-1", title="Baseline", workflow_id="run", framework=FRAMEWORK_ROOT)
        report = validate_project(root, framework=FRAMEWORK_ROOT)
        self.assertIn("ledger-consequential-risk", codes(report.errors))

    def test_high_risk_run_is_rejected_and_medium_is_allowed(self) -> None:
        root = self.lean_copy()
        path = root / "work" / "RUN-0001.yaml"
        edit(path, lambda d: d["work_item"]["risk"].update(declared_tier="medium", effective_tier="medium"))
        report = self.validate(root)
        self.assertNotIn("ledger-consequential-risk", codes(report.errors))
        self.assertEqual([], codes(report.errors))

        edit(path, lambda d: d["work_item"]["change"].update(production_affecting=True))
        edit(path, lambda d: d["work_item"]["risk"].update(effective_tier="high"))
        report = self.validate(root)
        errors = [issue for issue in report.errors if issue.code == "ledger-consequential-risk"]
        self.assertEqual(1, len(errors))
        self.assertIn("gated workflow", errors[0].message)

    def test_empty_assurance_states_means_no_review_states(self) -> None:
        self.assertFalse(_review_reached({"state": "closed"}, {"assurance_states": []}))
        self.assertTrue(_review_reached({"state": "closed"}, {}))
        self.assertTrue(_review_reached({"state": "accepted"}, {"assurance_states": ["accepted"]}))

    def test_research_no_longer_forces_medium_and_ledger_routes_no_evidence(self) -> None:
        catalog = load_catalog(FRAMEWORK_ROOT)
        change = {
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
            "surfaces": ["experiment"],
        }
        record = {"type": "research", "change": change, "_baseline_risk": "low"}
        gated = route_record({**record, "workflow": "research_spike"}, catalog)
        self.assertEqual("low", gated.computed_risk)
        self.assertIn("experiment_result", gated.required_evidence)
        ledger = route_record({**record, "workflow": "run"}, catalog)
        self.assertEqual("low", ledger.computed_risk)
        self.assertEqual((), ledger.required_evidence)
        published = route_record(
            {
                **record,
                "workflow": "run",
                "change": {**change, "external_write": True},
                "_program_risk_defaults": {"externally_published_claim_minimum": "high"},
            },
            catalog,
        )
        self.assertEqual("high", published.computed_risk)

    def test_research_platform_preset_defaults(self) -> None:
        preset = read(FRAMEWORK_ROOT / "presets" / "research_platform.yaml")["preset"]
        self.assertEqual("low", preset["risk_defaults"]["baseline"])
        self.assertEqual("run", preset["workflow_defaults"]["research_question"])
        self.assertEqual("release", preset["workflow_defaults"]["publication_or_distribution"])
        self.assertNotIn("product_discovery", preset["capability_defaults"]["active"])
        self.assertIn("product_discovery", preset["capability_defaults"]["conditional"])
        self.assertEqual(
            2,
            len([q for q in preset["required_tailoring_questions"] if "consequential" in q or "tiers" in q]),
        )


class ActorTierTests(LeanCase):
    def program(self, root: Path) -> Path:
        return root / "program.yaml"

    def actor(self, document: dict[str, Any], actor_id: str) -> dict[str, Any]:
        return next(a for a in document["program"]["actors"] if a["id"] == actor_id)

    def test_executor_above_local_write_is_an_error(self) -> None:
        root = self.lean_copy()
        edit(self.program(root), lambda d: self.actor(d, "agent:exec").update(permission_ceiling="external_write"))
        self.assertIn("executor-permission-ceiling", codes(self.validate(root).errors))

    def test_executor_may_not_own_or_review_a_capability(self) -> None:
        root = self.lean_copy()

        def make_reviewer(document: dict[str, Any]) -> None:
            capability = next(c for c in document["program"]["capabilities"] if c["id"] == "verification")
            capability["reviewers"] = ["agent:exec"]

        edit(self.program(root), make_reviewer)
        self.assertIn("executor-capability-role", codes(self.validate(root).errors))

    def test_tier_on_a_human_is_an_error(self) -> None:
        root = self.lean_copy()
        edit(self.program(root), lambda d: self.actor(d, "human:owner").update(tier="planner"))
        self.assertIn("actor-tier-kind", codes(self.validate(root).errors))

    def test_resource_owner_must_resolve(self) -> None:
        root = self.lean_copy()
        edit(
            self.program(root),
            lambda d: d["program"]["resources"][0].update(owner="agent:nobody"),
        )
        self.assertIn("resource-owner", codes(self.validate(root).errors))

    def test_budget_fields_are_typed(self) -> None:
        root = self.lean_copy()
        edit(self.program(root), lambda d: self.actor(d, "agent:worker").update(turn_cap=0))
        edit(self.program(root), lambda d: d["program"]["budgets"].update(per_run_tokens="many"))
        found = codes(self.validate(root).errors)
        self.assertIn("actor-budget", found)
        self.assertIn("program-budget", found)


class StandingAuthorizationTests(LeanCase):
    def decision_path(self, root: Path) -> Path:
        return root / "decisions" / f"{STANDING}.yaml"

    def test_standing_decision_satisfies_another_item(self) -> None:
        root = self.lean_copy()
        self.second_run(root)
        self.validate(root)
        transition_project(
            root,
            "RUN-0002",
            "running",
            actor="agent:planner",
            approval_refs=(STANDING,),
            framework=FRAMEWORK_ROOT,
        )
        history = read(root / "work" / "RUN-0002.yaml")["work_item"]["state"]["history"]
        self.assertEqual([STANDING], history[-1]["approval_refs"])
        report = validate_project(root, framework=FRAMEWORK_ROOT)
        self.assertEqual([], [issue.as_dict() for issue in report.issues])

    def test_standing_decision_stays_valid_in_history_after_it_expires(self) -> None:
        root = self.lean_copy()
        self.second_run(root)
        self.validate(root)
        transition_project(
            root, "RUN-0002", "running", actor="agent:planner",
            approval_refs=(STANDING,), framework=FRAMEWORK_ROOT,
        )
        edit(self.decision_path(root), lambda d: d["decision"]["authorization"].update(expires_at="2026-10-03T00:00:00Z"))
        edit(
            root / "work" / "RUN-0002.yaml",
            lambda d: d["work_item"]["state"]["history"][-1].update(at="2026-10-02T10:00:00Z"),
        )
        report = self.validate(root)
        self.assertNotIn("transition-approval-invalid", codes(report.errors))
        self.assertEqual([], codes(report.errors))

    def test_expired_standing_decision_satisfies_nothing_and_warns_while_open(self) -> None:
        root = self.lean_copy()
        path = self.second_run(root)
        edit(self.decision_path(root), lambda d: d["decision"]["authorization"].update(expires_at="2026-01-01T00:00:00Z"))
        edit(self.decision_path(root), lambda d: d["decision"].update(decided_at="2025-12-01T00:00:00Z"))
        self.validate(root)
        with self.assertRaisesRegex(TransitionError, "not bound"):
            transition_project(
                root, "RUN-0002", "running", actor="agent:planner",
                approval_refs=(STANDING,), framework=FRAMEWORK_ROOT,
            )
        self.assertEqual("draft", read(path)["work_item"]["state"]["current"])
        edit(path, lambda d: d["work_item"].update(decision_refs=[STANDING]))
        report = self.validate(root)
        warnings = [issue for issue in report.warnings if issue.code == "standing-authorization-expired"]
        self.assertEqual(1, len(warnings))
        self.assertIn("RUN-0002", warnings[0].message)
        self.assertNotIn("RUN-0001", warnings[0].message)

    def test_standing_decision_does_not_cover_other_workflows_actors_or_permissions(self) -> None:
        decision = read(LEAN_EXAMPLE / "decisions" / f"{STANDING}.yaml")["decision"]
        run = {"id": "RUN-X", "_envelope": "work_item", "workflow": "run", "permission_classes": ["local_write"]}
        self.assertTrue(decision_covers(decision, run, actor="agent:planner"))
        self.assertFalse(decision_covers(decision, run, actor="agent:worker"))
        self.assertFalse(decision_covers(decision, {**run, "workflow": "release", "id": "REL-X"}, actor="agent:planner"))
        production = {**run, "permission_classes": ["local_write", "production"]}
        self.assertFalse(decision_covers(decision, production, actor="agent:planner"))
        packet = {**run, "_envelope": "work_packet"}
        self.assertFalse(decision_covers(decision, packet, actor="agent:planner"))
        wildcard = {**decision, "authorization": {**decision["authorization"], "applies_to": ["*"]}}
        self.assertTrue(decision_covers(wildcard, {**run, "workflow": "release"}, actor="agent:planner"))

    def test_release_item_is_not_covered_by_a_run_standing_decision(self) -> None:
        root = self.lean_copy()
        self.validate(root)
        with self.assertRaisesRegex(TransitionError, "not bound"):
            transition_project(
                root, "REL-0001", "scope_locked", actor="agent:planner",
                approval_refs=(STANDING,), framework=FRAMEWORK_ROOT,
            )

    def test_standing_requires_applies_to_and_known_targets(self) -> None:
        root = self.lean_copy()
        edit(self.decision_path(root), lambda d: d["decision"]["authorization"].update(applies_to=["no-such-workflow"]))
        self.assertIn("standing-applies-to-unknown", codes(self.validate(root).errors))
        edit(self.decision_path(root), lambda d: d["decision"]["authorization"].pop("applies_to"))
        self.assertIn("standing-applies-to-missing", codes(self.validate(root).errors))

    def test_create_decision_records_a_standing_authorization(self) -> None:
        root = self.tmp / "project"
        root.mkdir()
        (root / "README.md").write_text("# Research\n", encoding="utf-8")
        init_project(root, preset_name="research_platform", project_id="proj", framework=FRAMEWORK_ROOT)
        confirm_test_tailoring(root)
        path = create_decision(
            root,
            "DEC-STANDING",
            decision_type="delivery",
            title="Resume from checkpoints",
            subject_refs=["proj"],
            options=["YES=Resume without asking."],
            outcome="approve",
            selected_option_ref="YES",
            rationale="Routine and bounded.",
            owner_id="human:owner",
            authorize_permissions=["local_write"],
            authorize_actors=["agent:delivery"],
            action_scope="Resume a paused run.",
            authorization_expires_at="2099-01-01T00:00:00Z",
            standing=True,
            applies_to=["run"],
            framework=FRAMEWORK_ROOT,
        )
        authorization = read(path)["decision"]["authorization"]
        self.assertTrue(authorization["standing"])
        self.assertEqual(["run"], authorization["applies_to"])
        self.assertEqual([], codes(validate_project(root, framework=FRAMEWORK_ROOT).errors))


class IndependentEvidenceTests(LeanCase):
    CLAIM = "physical_two_node_protocol_correctness_for_named_fixture"

    def fornax_copy(self) -> Path:
        root = self.tmp / "fornax"
        shutil.copytree(FORNAX_EXAMPLE, root)
        return root

    def correlate(self, root: Path, independence: dict[str, Any] | None, *, approval: bool = True) -> list[str]:
        """Make EV-G2-001 come from the packet producer in the packet context."""

        def change(document: dict[str, Any]) -> None:
            evidence = document["evidence"]
            evidence["producer"]["actor"] = "agent:runtime-integration"
            evidence["producer"]["context_manifest_digest"] = (
                "sha256:1111111111111111111111111111111111111111111111111111111111111111"
            )
            if independence is not None:
                evidence["independence"] = independence
            if not approval:
                evidence.pop("approval_ref")

        edit(root / "evidence" / "EV-G2-001.yaml", change)
        return codes(self.validate(root).errors)

    def test_same_agent_evidence_is_correlated_without_independence(self) -> None:
        found = self.correlate(self.fornax_copy(), None)
        self.assertEqual(["assurance-context-isolation", "assurance-correlated-producer"], sorted(found))

    def test_gold_set_readback_and_fixed_bar_satisfy_distinctness(self) -> None:
        for independence in (
            {"kind": "gold_set", "ref": "gold://fornax/g2/reference"},
            {"kind": "readback", "ref": "gcs://fornax/g2/readback"},
            {"kind": "preregistered_bar", "ref": "bar://fornax/g2", "fixed_before_read": True},
        ):
            with self.subTest(kind=independence["kind"]):
                self.setUp()
                self.assertEqual([], self.correlate(self.fornax_copy(), independence))

    def test_weak_independence_does_not_count(self) -> None:
        for independence in (
            {"kind": "preregistered_bar", "ref": "bar://fornax/g2"},
            {"kind": "preregistered_bar", "ref": "bar://fornax/g2", "fixed_before_read": False},
            {"kind": "second_reader", "ref": "reader://x"},
            {"kind": "deterministic_check", "ref": "check://x"},
            {"kind": "gold_set"},
        ):
            with self.subTest(independence=independence):
                self.setUp()
                found = self.correlate(self.fornax_copy(), independence)
                self.assertIn("assurance-correlated-producer", found)

    def test_independence_does_not_replace_human_acceptance(self) -> None:
        found = self.correlate(
            self.fornax_copy(), {"kind": "gold_set", "ref": "gold://fornax/g2/reference"}, approval=False
        )
        self.assertEqual(["assurance-human-acceptance"], found)

    def test_claims_without_coverage_warn_at_a1_and_above(self) -> None:
        root = self.fornax_copy()
        edit(
            root / "work" / "WI-G2-001.yaml",
            lambda d: d["work_item"].update(results={"claims": [self.CLAIM, "tool_call_feature"]}),
        )
        edit(root / "evidence" / "EV-G2-001.yaml", lambda d: d["evidence"].update(coverage=[self.CLAIM]))
        report = self.validate(root)
        self.assertEqual([], codes(report.errors))
        uncovered = [issue for issue in report.warnings if issue.code == "claim-not-covered"]
        self.assertEqual(1, len(uncovered))
        self.assertIn("tool_call_feature", uncovered[0].message)
        edit(
            root / "evidence" / "EV-G2-001.yaml",
            lambda d: d["evidence"].update(coverage=[self.CLAIM, "tool_call_feature"]),
        )
        self.assertEqual([], [i for i in self.validate(root).warnings if i.code == "claim-not-covered"])


class CliViewTests(LeanCase):
    def test_route_write_records_the_computed_risk(self) -> None:
        root = self.tmp / "project"
        root.mkdir()
        (root / "README.md").write_text("# Research\n", encoding="utf-8")
        init_project(root, preset_name="research_platform", framework=FRAMEWORK_ROOT)
        path = create_work_item(root, "RUN-1", title="Baseline", workflow_id="run", framework=FRAMEWORK_ROOT)

        def assess(document: dict[str, Any]) -> None:
            change = document["work_item"]["change"]
            for key in (
                "production_affecting",
                "authentication",
                "authorization",
                "sensitive_data",
                "regulated_impact",
                "destructive_migration",
                "external_write",
            ):
                change[key] = False
            change.update(safety_impact="none", reversibility="easy", blast_radius="local")

        edit(path, assess)
        self.assertEqual("high", read(path)["work_item"]["risk"]["effective_tier"])
        status, _ = run_cli("route", "RUN-1", "--root", str(root), "--write")
        self.assertEqual(0, status)
        risk = read(path)["work_item"]["risk"]
        self.assertEqual("low", risk["effective_tier"])
        self.assertEqual("A0", risk["assurance_level"])
        report = validate_project(root, framework=FRAMEWORK_ROOT)
        self.assertNotIn("ledger-consequential-risk", codes(report.errors))
        self.assertNotIn("risk-classification-drift", codes(report.errors))

    def test_max_issues_limits_output_and_counts_the_rest(self) -> None:
        report = ValidationReport()
        report.add("warning", "w-1", "first warning")
        for index in range(4):
            report.add("error", f"e-{index}", f"error {index}")
        limited = render_report(report, max_issues=2).splitlines()
        self.assertEqual(4, len(limited))
        self.assertIn("4 error(s), 1 warning(s)", limited[0])
        self.assertTrue(all("ERROR" in line for line in limited[1:3]))
        self.assertEqual("... 3 more issue(s) not shown (showing 2 of 5)", limited[3])
        self.assertEqual(7, len(render_report(report).splitlines()) + 1)
        self.assertEqual(7, len(render_report(report, max_issues=5).splitlines()) + 1)

    def test_validate_cli_accepts_max_issues(self) -> None:
        root = self.lean_copy()
        edit(
            root / "program.yaml",
            lambda d: [
                a.update(permission_ceiling="production") for a in d["program"]["actors"] if a["id"] == "agent:exec"
            ],
        )
        edit(
            root / "program.yaml",
            lambda d: next(a for a in d["program"]["actors"] if a["id"] == "human:owner").update(tier="planner"),
        )
        render_project(root, framework=FRAMEWORK_ROOT)
        status, full = run_cli("validate", str(root))
        self.assertEqual(1, status)
        status, limited = run_cli("validate", str(root), "--max-issues", "1")
        self.assertEqual(1, status)
        self.assertGreater(len(full.splitlines()), 3)
        self.assertEqual(3, len(limited.splitlines()))
        self.assertIn("more issue(s) not shown", limited)

    def test_status_prints_one_terse_line_per_item_and_dated_decision(self) -> None:
        root = self.lean_copy()
        status, output = run_cli("status", str(root))
        self.assertEqual(0, status)
        self.assertEqual(
            [
                "REL-0001 release draft tier=high gates=none",
                "RUN-0001 run closed tier=low gates=none",
                f"revisit {STANDING} at=2026-12-01T00:00:00Z",
                f"standing {STANDING} expires=2027-01-01T00:00:00Z applies_to=run",
            ],
            output.splitlines(),
        )

    def test_status_lists_open_human_gates_and_marks_expired_standing(self) -> None:
        root = self.lean_copy()
        edit(root / "work" / "REL-0001.yaml", lambda d: d["work_item"]["state"].update(current="approved"))
        edit(
            root / "decisions" / f"{STANDING}.yaml",
            lambda d: d["decision"]["authorization"].update(expires_at="2026-01-01T00:00:00Z"),
        )
        _, output = run_cli("status", str(root))
        lines = output.splitlines()
        self.assertTrue(lines[0].startswith("REL-0001 release approved tier=high gates="))
        self.assertIn("approval_not_expired", lines[0])
        self.assertIn("production_permission_valid", lines[0])
        self.assertIn(f"standing {STANDING} expires=2026-01-01T00:00:00Z EXPIRED applies_to=run", lines)

    def test_render_writes_decisions_view_dated_first(self) -> None:
        root = self.lean_copy()
        base = read(root / "decisions" / f"{STANDING}.yaml")
        for decision_id, revisit in (("DEC-A-UNDATED", None), ("DEC-B-EARLY", "2026-11-01T00:00:00Z")):
            document = {**base, "decision": {**base["decision"], "id": decision_id}}
            document["decision"].pop("authorization")
            document["decision"].pop("guard_authorizations")
            document["decision"].pop("revisit_at")
            if revisit:
                document["decision"]["revisit_at"] = revisit
            write(root / "decisions" / f"{decision_id}.yaml", document)
        edit(root / "work" / "RUN-0001.yaml", lambda d: d["work_item"].update(decision_refs=[STANDING, "DEC-B-EARLY"]))
        paths = render_project(root, framework=FRAMEWORK_ROOT)
        view = next(path for path in paths if path.name == "decisions.md")
        text = view.read_text(encoding="utf-8")
        self.assertIn(
            f"| `{STANDING}` | approve | human:owner | yes | run | "
            "expires 2027-01-01T00:00:00Z; revisit 2026-12-01T00:00:00Z | RUN-0001 |",
            text,
        )
        self.assertIn("| `DEC-B-EARLY` | approve | human:owner | no | — | revisit 2026-11-01T00:00:00Z | RUN-0001 |", text)
        self.assertLess(text.index("DEC-B-EARLY"), text.index(STANDING))
        self.assertLess(text.index(STANDING), text.index("DEC-A-UNDATED"))
        self.assertEqual([], codes(validate_project(root, framework=FRAMEWORK_ROOT).errors))


if __name__ == "__main__":
    unittest.main()
