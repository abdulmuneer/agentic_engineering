from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentic_engineering.runtime.initialization import init_project
from agentic_engineering.runtime.validation import validate_project


REPO_ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_ROOT = REPO_ROOT / "agentic_engineering"


class PresetInitializationTests(unittest.TestCase):
    def test_triggered_capabilities_are_active_in_specialized_presets(self) -> None:
        for preset in ("research_platform", "regulated_service"):
            with self.subTest(preset=preset), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                (root / "README.md").write_text("# Test product\n", encoding="utf-8")
                init_project(root, preset_name=preset, framework=FRAMEWORK_ROOT)

                report = validate_project(root, framework=FRAMEWORK_ROOT)

                self.assertEqual([], report.errors)
                self.assertEqual(
                    ["tailoring-pending"], [issue.code for issue in report.warnings]
                )


if __name__ == "__main__":
    unittest.main()
