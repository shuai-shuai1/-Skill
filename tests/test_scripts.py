from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skill" / "research-paper" / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"
GOLDEN = ROOT / "tests" / "golden_outputs"


def run_script(name: str, *args: object) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPTS / name), *map(str, args)]
    return subprocess.run(command, text=True, capture_output=True, encoding="utf-8")


class EvidenceLedgerTests(unittest.TestCase):
    def test_valid_ledger_matches_golden_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            result = run_script(
                "audit_evidence_ledger.py",
                FIXTURES / "evidence_valid.csv",
                "--json",
                report_path,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            golden = json.loads(
                (GOLDEN / "evidence_valid_summary.json").read_text(encoding="utf-8")
            )
            actual = {
                "status": report["status"],
                "record_count": report["record_count"],
                "summary": report["summary"],
            }
            self.assertEqual(actual, golden)

    def test_invalid_ledger_fails_with_required_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            result = run_script(
                "audit_evidence_ledger.py",
                FIXTURES / "evidence_invalid.csv",
                "--json",
                report_path,
            )
            self.assertEqual(result.returncode, 1)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            actual_codes = {item["code"] for item in report["issues"]}
            golden = json.loads(
                (GOLDEN / "evidence_invalid_required_codes.json").read_text(encoding="utf-8")
            )
            self.assertTrue(set(golden["required_codes"]).issubset(actual_codes))


class ManuscriptTests(unittest.TestCase):
    def test_valid_manuscript_passes(self) -> None:
        result = run_script(
            "audit_manuscript.py",
            FIXTURES / "manuscript_valid.md",
            "--ledger",
            FIXTURES / "evidence_valid.csv",
            "--claims",
            FIXTURES / "claims_valid.csv",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("PASS", result.stdout)

    def test_invalid_manuscript_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            result = run_script(
                "audit_manuscript.py",
                FIXTURES / "manuscript_invalid.md",
                "--ledger",
                FIXTURES / "evidence_valid.csv",
                "--json",
                report_path,
            )
            self.assertEqual(result.returncode, 1)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            codes = {item["code"] for item in report["issues"]}
            self.assertIn("UNRESOLVED_PLACEHOLDER", codes)
            self.assertIn("HIGH_RISK_CLAIM", codes)
            self.assertIn("UNKNOWN_EVIDENCE_TAG", codes)

    def test_context_dependent_engineering_claims_are_warned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manuscript = Path(tmp) / "claim.md"
            report_path = Path(tmp) / "report.json"
            manuscript.write_text(
                "该方法获得最优结果，并满足工程实时性要求。\n", encoding="utf-8"
            )
            result = run_script(
                "audit_manuscript.py",
                manuscript,
                "--json",
                report_path,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            findings = [
                item
                for item in report["issues"]
                if item["code"] == "CONTEXT_DEPENDENT_CLAIM"
            ]
            self.assertGreaterEqual(len(findings), 2)


class ReviewPackageTests(unittest.TestCase):
    def test_valid_full_review_ledger_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "review.json"
            result = run_script(
                "audit_review_package.py",
                FIXTURES / "review_valid.csv",
                "--recommendation",
                "MAJOR_REVISION",
                "--require-perspectives",
                3,
                "--json",
                report_path,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["perspective_count"], 3)
            self.assertEqual(report["unresolved_blocking_count"], 1)

    def test_invalid_review_ledger_blocks_ready_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "review.json"
            result = run_script(
                "audit_review_package.py",
                FIXTURES / "review_invalid.csv",
                "--recommendation",
                "READY",
                "--json",
                report_path,
            )
            self.assertEqual(result.returncode, 1)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            codes = {item["code"] for item in report["issues"]}
            for code in (
                "DUPLICATE_REVIEW_ID",
                "MINOR_CANNOT_BLOCK",
                "REVIEW_FIELD_MISSING",
                "INVALID_REVIEW_AXIS",
                "READY_WITH_OPEN_MAJOR",
                "RECOMMENDATION_WITH_BLOCKER",
            ):
                self.assertIn(code, codes)


class WorkspaceTests(unittest.TestCase):
    def test_workspace_initializer_is_non_destructive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "paper-workspace"
            first = run_script(
                "init_paper_workspace.py", workspace, "--title", "Synthetic Test Paper"
            )
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            brief = workspace / "paper" / "paper_brief.md"
            review_ledger = workspace / "reviews" / "review_issue_ledger.csv"
            self.assertIn("Synthetic Test Paper", brief.read_text(encoding="utf-8"))
            self.assertTrue(review_ledger.exists())
            brief.write_text("user content\n", encoding="utf-8")
            second = run_script(
                "init_paper_workspace.py", workspace, "--update-missing"
            )
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            self.assertEqual(brief.read_text(encoding="utf-8"), "user content\n")


@unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow is not installed")
class FigureTests(unittest.TestCase):
    def test_identical_render_comparison_is_zero(self) -> None:
        from PIL import Image, ImageDraw

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            reference = base / "reference.png"
            candidate = base / "candidate.png"
            image = Image.new("RGB", (1200, 800), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle((100, 100, 1100, 700), fill="#0077BB")
            image.save(reference, dpi=(300, 300))
            image.save(candidate, dpi=(300, 300))
            report_path = base / "compare.json"
            result = run_script(
                "compare_figure_renders.py",
                reference,
                candidate,
                "--output",
                report_path,
                "--diff",
                base / "diff.png",
                "--overlay",
                base / "overlay.png",
                "--max-mae",
                0,
                "--max-differing-ratio",
                0,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["metrics"]["normalized_mae"], 0)
            self.assertEqual(report["metrics"]["differing_pixel_ratio"], 0)

    def test_difference_threshold_can_block_acceptance(self) -> None:
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            reference = base / "reference.png"
            candidate = base / "candidate.png"
            Image.new("RGB", (1200, 800), "white").save(reference)
            Image.new("RGB", (1200, 800), "black").save(candidate)
            result = run_script(
                "compare_figure_renders.py",
                reference,
                candidate,
                "--max-mae",
                0.04,
                "--max-differing-ratio",
                0.15,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("FAIL", result.stdout)

    def test_figure_qa_accepts_sufficient_raster(self) -> None:
        from PIL import Image, ImageDraw

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "figure.png"
            image = Image.new("RGB", (1200, 800), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 599, 799), fill="black")
            image.save(path, dpi=(300, 300))
            result = run_script("figure_qa.py", path, "--strict")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


class StyleTests(unittest.TestCase):
    def test_style_cli_outputs_json(self) -> None:
        result = run_script("figure_style.py", "--preset", "engineering")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["savefig.dpi"], 300)

    def test_synthetic_provenance_requires_disclosure(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        try:
            import figure_style

            provenance = figure_style.FigureProvenance(
                figure_id="Fig-S1",
                evidence_type="SYNTHETIC",
                source_files=["synthetic.csv"],
            )
            with self.assertRaises(ValueError):
                provenance.validate()
        finally:
            sys.path.remove(str(SCRIPTS))


if __name__ == "__main__":
    unittest.main()
