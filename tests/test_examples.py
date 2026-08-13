from __future__ import annotations

import subprocess
import sys
import unittest
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skill" / "research-paper" / "scripts"
EXAMPLES = ROOT / "examples"


def run_script(name: str, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *map(str, args)],
        text=True,
        capture_output=True,
        encoding="utf-8",
    )


class PublicExampleTests(unittest.TestCase):
    def test_readme_local_links_resolve(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme)
        local = [
            link.split("#", 1)[0]
            for link in links
            if link and not link.startswith(("http://", "https://", "#"))
        ]
        missing = [link for link in local if not (ROOT / link).exists()]
        self.assertEqual(missing, [])

    def test_evidence_audit_example_is_executable(self) -> None:
        example = EXAMPLES / "01-evidence-audit"
        ledger = run_script("audit_evidence_ledger.py", example / "evidence_ledger.csv")
        self.assertEqual(ledger.returncode, 0, ledger.stderr + ledger.stdout)
        manuscript = run_script(
            "audit_manuscript.py",
            example / "manuscript.md",
            "--ledger",
            example / "evidence_ledger.csv",
            "--claims",
            example / "claim_evidence_matrix.csv",
        )
        self.assertEqual(manuscript.returncode, 0, manuscript.stderr + manuscript.stdout)

    def test_peer_review_example_matches_major_revision(self) -> None:
        example = EXAMPLES / "03-peer-review" / "review_issue_ledger.csv"
        result = run_script(
            "audit_review_package.py",
            example,
            "--recommendation",
            "MAJOR_REVISION",
            "--require-perspectives",
            3,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_peer_review_example_rejects_ready(self) -> None:
        example = EXAMPLES / "03-peer-review" / "review_issue_ledger.csv"
        result = run_script(
            "audit_review_package.py",
            example,
            "--recommendation",
            "READY",
            "--require-perspectives",
            3,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL", result.stdout)


if __name__ == "__main__":
    unittest.main()
