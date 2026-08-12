#!/usr/bin/env python3
"""Initialize a non-destructive evidence-driven paper workspace."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import date
from pathlib import Path


DIRECTORIES = (
    "paper",
    "evidence",
    "figures/specs",
    "figures/data",
    "figures/src",
    "figures/output",
    "reviews",
    "qa",
)

TEMPLATE_MAP = {
    "paper_brief.md": "paper/paper_brief.md",
    "evidence_ledger.csv": "evidence/evidence_ledger.csv",
    "claim_evidence_matrix.csv": "evidence/claim_evidence_matrix.csv",
    "terminology_metrics.csv": "evidence/terminology_metrics.csv",
    "figure_spec.md": "figures/specs/figure_spec_template.md",
    "revision_tracker.csv": "reviews/revision_tracker.csv",
    "review_issue_ledger.csv": "reviews/review_issue_ledger.csv",
    "reviewer_report.md": "reviews/reviewer_report_template.md",
    "ppt_reproduction_spec.md": "figures/specs/ppt_reproduction_spec_template.md",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a non-destructive research-paper workspace from bundled templates."
    )
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--title", default="")
    parser.add_argument(
        "--update-missing",
        action="store_true",
        help="Add missing directories/files to an existing workspace without overwriting files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = args.workspace.resolve()
    template_dir = Path(__file__).resolve().parents[1] / "assets" / "templates"

    if target.exists() and not args.update_missing:
        if any(target.iterdir()):
            raise SystemExit(
                f"Workspace is not empty: {target}. Use --update-missing to add only missing files."
            )
    target.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    skipped: list[str] = []
    for relative in DIRECTORIES:
        directory = target / relative
        if not directory.exists():
            directory.mkdir(parents=True)
            created.append(relative + "/")

    for source_name, destination_name in TEMPLATE_MAP.items():
        source = template_dir / source_name
        destination = target / destination_name
        if destination.exists():
            skipped.append(destination_name)
            continue
        shutil.copy2(source, destination)
        if source_name == "paper_brief.md" and args.title:
            content = destination.read_text(encoding="utf-8")
            content = content.replace(
                "- Working title:", f"- Working title: {args.title}", 1
            )
            content = content.replace(
                "- Owner / date / version:",
                f"- Owner / date / version: {date.today().isoformat()} / draft",
                1,
            )
            destination.write_text(content, encoding="utf-8")
        created.append(destination_name)

    manifest = {
        "workspace": str(target),
        "created": created,
        "skipped_existing": skipped,
        "non_destructive": True,
    }
    manifest_path = target / "workspace_manifest.json"
    if not manifest_path.exists():
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        created.append("workspace_manifest.json")
    else:
        skipped.append("workspace_manifest.json")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
