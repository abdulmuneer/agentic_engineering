from __future__ import annotations

import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "agentic-engineering"


class AgenticEngineeringSkillTests(unittest.TestCase):
    def test_skill_metadata_and_references_are_complete(self) -> None:
        skill_path = SKILL_ROOT / "SKILL.md"
        text = skill_path.read_text(encoding="utf-8")
        self.assertNotIn("TODO", text)
        self.assertLessEqual(len(text.splitlines()), 500)

        _, frontmatter, body = text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        self.assertEqual({"name", "description"}, set(metadata))
        self.assertEqual("agentic-engineering", metadata["name"])

        references = sorted((SKILL_ROOT / "references").glob("*.md"))
        self.assertEqual(3, len(references))
        for reference in references:
            self.assertIn(f"references/{reference.name}", body)
            self.assertNotIn("TODO", reference.read_text(encoding="utf-8"))

    def test_openai_interface_matches_skill(self) -> None:
        interface_document = yaml.safe_load(
            (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        )
        interface = interface_document["interface"]
        self.assertEqual("Agentic Engineering", interface["display_name"])
        self.assertGreaterEqual(len(interface["short_description"]), 25)
        self.assertLessEqual(len(interface["short_description"]), 64)
        self.assertIn("$agentic-engineering", interface["default_prompt"])


if __name__ == "__main__":
    unittest.main()
