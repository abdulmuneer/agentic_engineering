from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml

from agentic_engineering.runtime.validation import validate_framework


REPO_ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_ROOT = REPO_ROOT / "agentic_engineering"


class PolicyShapeValidationTests(unittest.TestCase):
    def _validate_replacement(self, policy_name: str, replacement: Any):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "agentic_engineering"
            shutil.copytree(FRAMEWORK_ROOT, root)
            path = root / "catalog" / f"{policy_name}.yaml"
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            document[policy_name] = replacement
            path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            return validate_framework(root)

    def test_empty_assurance_policy_fails_closed(self) -> None:
        report = self._validate_replacement("assurance_policy", {})

        self.assertFalse(report.ok)
        codes = {issue.code for issue in report.errors}
        self.assertIn("assurance-policy-id", codes)
        self.assertIn("assurance-policy-levels", codes)
        self.assertIn("assurance-policy-minimums", codes)

    def test_empty_evidence_policy_fails_closed(self) -> None:
        report = self._validate_replacement("evidence_policy", {})

        self.assertFalse(report.ok)
        codes = {issue.code for issue in report.errors}
        self.assertIn("evidence-policy-id", codes)
        self.assertIn("evidence-policy-kinds", codes)
        self.assertIn("evidence-policy-required-fields", codes)
        self.assertIn("evidence-policy-result-values", codes)

    def test_malformed_risk_rule_is_rejected(self) -> None:
        policy = yaml.safe_load(
            (FRAMEWORK_ROOT / "catalog" / "risk_policy.yaml").read_text(encoding="utf-8")
        )["risk_policy"]
        policy["forced_minimum_rules"][0]["minimum_tier"] = "imaginary"
        policy["forced_minimum_rules"][0]["when_any"] = {}

        report = self._validate_replacement("risk_policy", policy)

        codes = {issue.code for issue in report.errors}
        self.assertIn("risk-policy-rule-tier", codes)
        self.assertIn("risk-policy-rule-conditions", codes)

    def test_permission_ranks_and_action_receipt_classes_are_validated(self) -> None:
        policy = yaml.safe_load(
            (FRAMEWORK_ROOT / "catalog" / "permission_policy.yaml").read_text(
                encoding="utf-8"
            )
        )["permission_policy"]
        policy["classes"][1]["rank"] = 1
        policy["rules"]["action_receipt_required_for"] = ["unknown_class"]

        report = self._validate_replacement("permission_policy", policy)

        codes = {issue.code for issue in report.errors}
        self.assertIn("permission-policy-class-rank", codes)
        self.assertIn("permission-policy-action-receipt-class", codes)
        self.assertIn("permission-policy-action-receipts", codes)


if __name__ == "__main__":
    unittest.main()
