from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from agentic_engineering.runtime.records import (
    create_decision,
    create_evidence,
    create_work_packet,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_ROOT = REPO_ROOT / "agentic_engineering"
OVERLAY_TEMPLATE = FRAMEWORK_ROOT / "templates" / "overlay" / ".agentic"


class RecordAuthoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(OVERLAY_TEMPLATE, self.root / ".agentic")
        program_path = self.root / ".agentic" / "program.yaml"
        program = yaml.safe_load(program_path.read_text(encoding="utf-8"))
        tailoring = program["program"]["tailoring"]
        tailoring.update(
            {
                "status": "confirmed",
                "answers": [
                    {"question": tailoring["questions"][0], "answer": "Tailored for record tests."}
                ],
                "confirmed_by": "human:owner",
                "confirmed_at": "2026-07-10T00:00:00Z",
            }
        )
        program_path.write_text(yaml.safe_dump(program, sort_keys=False), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_packet_decision_and_explicit_failed_evidence_are_linked(self) -> None:
        packet_path = create_work_packet(
            self.root,
            "AWP-NEW",
            work_id="WORK-0001",
            producer_id="agent:implementation",
            run_id="RUN-NEW",
            goal="Exercise the exact acceptance behavior without broadening its claim.",
            claims_requested=["acceptance:AC-1"],
            claims_forbidden=["production_ready"],
            output_kind="file",
            output_ref="src/example.py",
            output_summary="Bounded implementation output.",
            framework=FRAMEWORK_ROOT,
        )
        packet = yaml.safe_load(packet_path.read_text(encoding="utf-8"))["work_packet"]
        self.assertEqual("draft", packet["status"])
        self.assertEqual([], packet["verification_evidence_refs"])

        work_path = self.root / ".agentic" / "records" / "work_items" / "WORK-0001.yaml"
        work = yaml.safe_load(work_path.read_text(encoding="utf-8"))["work_item"]
        self.assertIn("AWP-NEW", work["work_packet_refs"])

        decision_path = create_decision(
            self.root,
            "DEC-NEW",
            decision_type="delivery",
            title="Approve the bounded implementation direction",
            subject_refs=["WORK-0001"],
            options=["OPTION-APPROVE=Approve the bounded direction."],
            outcome="approve",
            selected_option_ref="OPTION-APPROVE",
            rationale="The option is limited to the named acceptance criterion.",
            owner_id="human:owner",
            framework=FRAMEWORK_ROOT,
        )
        self.assertTrue(decision_path.is_file())
        work = yaml.safe_load(work_path.read_text(encoding="utf-8"))["work_item"]
        self.assertIn("DEC-NEW", work["decision_refs"])

        evidence_path = create_evidence(
            self.root,
            "EV-NEW",
            work_id="WORK-0001",
            packet_id="AWP-NEW",
            kind="deterministic_test",
            producer_id="agent:review",
            run_id="RUN-VERIFY-NEW",
            result="fail",
            observed_at="2026-07-10T12:00:00Z",
            acceptance_refs=["AC-1"],
            claims_authorized=["acceptance:AC-1"],
            subject={"ref": "src/example.py"},
            method={"command": "python -m unittest", "environment": "local"},
            framework=FRAMEWORK_ROOT,
        )
        evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))["evidence"]
        self.assertEqual("fail", evidence["result"])
        packet = yaml.safe_load(packet_path.read_text(encoding="utf-8"))["work_packet"]
        self.assertIn("EV-NEW", packet["verification_evidence_refs"])

    def test_evidence_claim_must_be_requested_by_packet(self) -> None:
        create_work_packet(
            self.root,
            "AWP-CLAIM",
            work_id="WORK-0001",
            producer_id="agent:implementation",
            run_id="RUN-CLAIM",
            goal="Bound one claim.",
            claims_requested=["acceptance:AC-1"],
            output_kind="file",
            output_ref="src/example.py",
            output_summary="Bounded output.",
            framework=FRAMEWORK_ROOT,
        )
        with self.assertRaisesRegex(ValueError, "not requested"):
            create_evidence(
                self.root,
                "EV-OVERCLAIM",
                work_id="WORK-0001",
                packet_id="AWP-CLAIM",
                kind="deterministic_test",
                producer_id="agent:review",
                run_id="RUN-OVERCLAIM",
                result="pass",
                observed_at="2026-07-10T12:00:00Z",
                acceptance_refs=["AC-1"],
                claims_authorized=["production_ready"],
                subject={"commit": "0000000000000000000000000000000000000000"},
                method={"command": "python -m unittest", "environment": "local"},
                framework=FRAMEWORK_ROOT,
            )

    def test_elevated_packet_requires_bound_decision_and_action_receipt(self) -> None:
        program_path = self.root / ".agentic" / "program.yaml"
        program = yaml.safe_load(program_path.read_text(encoding="utf-8"))
        for actor in program["program"]["actors"]:
            if actor["id"] == "agent:implementation":
                actor["permission_ceiling"] = "external_write"
        program_path.write_text(yaml.safe_dump(program, sort_keys=False), encoding="utf-8")

        work_path = self.root / ".agentic" / "records" / "work_items" / "WORK-0001.yaml"
        work_document = yaml.safe_load(work_path.read_text(encoding="utf-8"))
        work_document["work_item"]["change"]["external_write"] = True
        work_document["work_item"]["permission_classes"] = ["local_write", "external_write"]
        work_document["work_item"]["risk"] = {
            "declared_tier": "medium",
            "effective_tier": "medium",
            "assurance_level": "A1",
            "rule_refs": ["FACT-EXTERNAL-WRITE"],
        }
        work_document["work_item"]["evidence_plan"][0]["minimum_assurance"] = "A1"
        work_path.write_text(
            yaml.safe_dump(work_document, sort_keys=False), encoding="utf-8"
        )

        decision_path = create_decision(
            self.root,
            "DEC-AUTH",
            decision_type="delivery",
            title="Authorize one bounded external write",
            subject_refs=["WORK-0001"],
            options=["OPTION-AUTH=Authorize the named actor and action scope."],
            outcome="approve",
            selected_option_ref="OPTION-AUTH",
            rationale="The write is bounded to the named test fixture.",
            owner_id="human:owner",
            decided_at="2026-07-10T10:00:00Z",
            authorize_permissions=["external_write"],
            authorize_actors=["agent:implementation"],
            action_scope="Write the named external test fixture once.",
            authorization_expires_at="2099-01-01T00:00:00Z",
            framework=FRAMEWORK_ROOT,
        )
        self.assertTrue(decision_path.is_file())

        packet_path = create_work_packet(
            self.root,
            "AWP-AUTH",
            work_id="WORK-0001",
            producer_id="agent:implementation",
            run_id="RUN-AUTH",
            goal="Perform the one authorized external write.",
            claims_requested=["external_fixture_written"],
            output_kind="artifact",
            output_ref="fixture://external/result",
            output_summary="Receipt target for the authorized external write.",
            context_manifest_digest="sha256:" + "1" * 64,
            approval_refs=["DEC-AUTH"],
            framework=FRAMEWORK_ROOT,
        )
        packet = yaml.safe_load(packet_path.read_text(encoding="utf-8"))["work_packet"]
        self.assertIn("DEC-AUTH", packet["approval_refs"])

        evidence_path = create_evidence(
            self.root,
            "EV-ACTION",
            work_id="WORK-0001",
            packet_id="AWP-AUTH",
            kind="approval",
            producer_id="agent:implementation",
            run_id="RUN-ACTION",
            result="pass",
            observed_at="2026-07-10T12:00:00Z",
            acceptance_refs=["AC-1"],
            claims_authorized=["external_fixture_written"],
            subject={"ref": "fixture://external/result"},
            method={"description": "Record the authorized external action receipt."},
            context_manifest_digest="sha256:" + "2" * 64,
            authorization_ref="DEC-AUTH",
            framework=FRAMEWORK_ROOT,
        )
        self.assertTrue(evidence_path.is_file())
        packet = yaml.safe_load(packet_path.read_text(encoding="utf-8"))["work_packet"]
        self.assertIn("EV-ACTION", packet["action_receipt_refs"])
        self.assertNotIn("EV-ACTION", packet["verification_evidence_refs"])


if __name__ == "__main__":
    unittest.main()
