from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TriggerCaseTests(unittest.TestCase):
    def test_trigger_case_catalog_has_balanced_coverage(self) -> None:
        path = ROOT / "tests" / "trigger_cases" / "cases.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(cases["positive"]), 8)
        self.assertGreaterEqual(len(cases["negative"]), 5)
        self.assertTrue(any("GPT Image 2" in case for case in cases["positive"]))
        self.assertTrue(any("PowerPoint" in case for case in cases["positive"]))
        self.assertTrue(any("润色" in case for case in cases["positive"]))
        self.assertTrue(any("复审" in case for case in cases["positive"]))

    def test_skill_description_mentions_critical_routes(self) -> None:
        skill = (ROOT / "skill" / "research-paper" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        frontmatter = skill.split("---", 2)[1].lower()
        for phrase in (
            "evidence-driven",
            "experiment-to-paper",
            "GPT Image 2",
            "PowerPoint",
            "reviewer-response",
            "simulated peer review",
            "polishing",
        ):
            self.assertIn(phrase.lower(), frontmatter)


if __name__ == "__main__":
    unittest.main()
