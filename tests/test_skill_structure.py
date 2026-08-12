from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skill" / "research-paper"


class SkillStructureTests(unittest.TestCase):
    def test_skill_router_is_thin_and_frontmatter_is_minimal(self) -> None:
        path = SKILL_DIR / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        self.assertLess(len(text.splitlines()), 500)
        parts = text.split("---", 2)
        self.assertEqual(len(parts), 3)
        keys = {
            line.split(":", 1)[0].strip()
            for line in parts[1].splitlines()
            if line.strip() and ":" in line
        }
        self.assertEqual(keys, {"name", "description"})

    def test_all_skill_links_resolve(self) -> None:
        skill_path = SKILL_DIR / "SKILL.md"
        text = skill_path.read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        self.assertGreaterEqual(len(links), 10)
        missing = [link for link in links if not (SKILL_DIR / link).exists()]
        self.assertEqual(missing, [])

    def test_ppt_pixel_route_has_current_implementation_contract(self) -> None:
        text = (SKILL_DIR / "references" / "ppt-pixel-reproduction.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "GPT Image 2",
            "@oai/artifact-tool",
            "compare_figure_renders.py",
            "pixel",
            "版权",
        ):
            self.assertIn(phrase, text)

    def test_initializer_placeholders_are_removed(self) -> None:
        self.assertFalse((SKILL_DIR / "scripts" / "example.py").exists())
        self.assertFalse((SKILL_DIR / "references" / "api_reference.md").exists())
        self.assertFalse((SKILL_DIR / "assets" / "example_asset.txt").exists())

    def test_polishing_and_review_contracts_are_linked(self) -> None:
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for relative in (
            "references/polishing-and-style-profiles.md",
            "references/peer-review-and-rereview.md",
            "assets/templates/review_issue_ledger.csv",
            "assets/templates/reviewer_report.md",
        ):
            self.assertIn(relative, skill)

        review = (SKILL_DIR / "references" / "peer-review-and-rereview.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("相互盲审", review)
        self.assertIn("FULLY_ADDRESSED", review)
        self.assertIn("resolution_test", review)


if __name__ == "__main__":
    unittest.main()
