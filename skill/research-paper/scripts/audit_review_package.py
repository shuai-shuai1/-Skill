#!/usr/bin/env python3
"""Validate a source-grounded peer-review issue ledger."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from audit_utils import issue, read_records, summarize_issues, write_json, write_markdown


REQUIRED_FIELDS = {
    "issue_id",
    "perspective",
    "severity",
    "blocking",
    "axis",
    "claim_pointer",
    "evidence_pointer",
    "concern",
    "impact",
    "resolution_test",
    "status",
}
ISSUE_ID_RE = re.compile(r"^R[1-9]\d*-(?:M|m)[1-9]\d*$")
ALLOWED_SEVERITY = {"MAJOR", "MINOR"}
ALLOWED_BLOCKING = {"YES", "NO"}
ALLOWED_AXIS = {
    "SCOPE",
    "ORIGINALITY",
    "METHOD",
    "EVIDENCE",
    "REPRODUCIBILITY",
    "FAIRNESS",
    "STATISTICS",
    "INTERPRETATION",
    "WRITING",
    "LITERATURE",
    "FIGURE",
    "ETHICS",
}
ALLOWED_STATUS = {
    "OPEN",
    "AUTHOR_INPUT_NEEDED",
    "PLANNED",
    "RESOLVED",
    "NOT_ASSESSABLE",
    "FULLY_ADDRESSED",
    "PARTIALLY_ADDRESSED",
    "NOT_ADDRESSED",
    "MADE_WORSE",
}
CLOSED_STATUS = {"RESOLVED", "NOT_ASSESSABLE", "FULLY_ADDRESSED"}
RECOMMENDATIONS = {"READY", "MINOR_REVISION", "MAJOR_REVISION", "REJECT_RESUBMIT"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a simulated peer-review issue ledger and recommendation posture."
    )
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--recommendation", choices=sorted(RECOMMENDATIONS))
    parser.add_argument(
        "--require-perspectives",
        type=int,
        default=0,
        help="Require at least this many distinct review perspectives.",
    )
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def audit(
    ledger: Path,
    recommendation: str | None = None,
    require_perspectives: int = 0,
) -> dict[str, object]:
    records = read_records(ledger, collection_key="issues")
    issues: list[dict[str, object]] = []
    seen: set[str] = set()
    perspectives: set[str] = set()
    unresolved_major = 0
    unresolved_blocking = 0

    if not records:
        issues.append(issue("ERROR", "EMPTY_REVIEW_LEDGER", "Review ledger has no issues."))

    for row_number, record in enumerate(records, start=2):
        issue_id = record.get("issue_id", "") or f"row-{row_number}"
        perspectives.add(record.get("perspective", ""))

        for field in REQUIRED_FIELDS:
            if not record.get(field, ""):
                issues.append(
                    issue(
                        "ERROR",
                        "REVIEW_FIELD_MISSING",
                        f"Review field '{field}' is empty.",
                        row=row_number,
                        field=field,
                        record_id=issue_id,
                    )
                )

        if issue_id in seen:
            issues.append(
                issue(
                    "ERROR",
                    "DUPLICATE_REVIEW_ID",
                    f"Review issue ID '{issue_id}' occurs more than once.",
                    row=row_number,
                    record_id=issue_id,
                )
            )
        seen.add(issue_id)
        if issue_id and not ISSUE_ID_RE.fullmatch(issue_id):
            issues.append(
                issue(
                    "ERROR",
                    "INVALID_REVIEW_ID",
                    "Use stable IDs such as R1-M1 for Major and R1-m1 for Minor issues.",
                    row=row_number,
                    record_id=issue_id,
                )
            )
        elif severity := record.get("severity", "").upper():
            if (severity == "MAJOR" and "-m" in issue_id) or (
                severity == "MINOR" and "-M" in issue_id
            ):
                issues.append(
                    issue(
                        "ERROR",
                        "REVIEW_ID_SEVERITY_MISMATCH",
                        "Use uppercase M for Major IDs and lowercase m for Minor IDs.",
                        row=row_number,
                        record_id=issue_id,
                    )
                )

        severity = record.get("severity", "").upper()
        blocking = record.get("blocking", "").upper()
        axis = record.get("axis", "").upper()
        status = record.get("status", "").upper()

        if severity and severity not in ALLOWED_SEVERITY:
            issues.append(
                issue(
                    "ERROR",
                    "INVALID_REVIEW_SEVERITY",
                    f"Unknown severity '{severity}'.",
                    row=row_number,
                    record_id=issue_id,
                )
            )
        if blocking and blocking not in ALLOWED_BLOCKING:
            issues.append(
                issue(
                    "ERROR",
                    "INVALID_BLOCKING_VALUE",
                    f"Unknown blocking value '{blocking}'.",
                    row=row_number,
                    record_id=issue_id,
                )
            )
        if severity == "MINOR" and blocking == "YES":
            issues.append(
                issue(
                    "ERROR",
                    "MINOR_CANNOT_BLOCK",
                    "A Minor issue cannot be blocking; promote it to Major or set blocking to NO.",
                    row=row_number,
                    record_id=issue_id,
                )
            )
        if axis and axis not in ALLOWED_AXIS:
            issues.append(
                issue(
                    "ERROR",
                    "INVALID_REVIEW_AXIS",
                    f"Unknown review axis '{axis}'.",
                    row=row_number,
                    record_id=issue_id,
                )
            )
        if status and status not in ALLOWED_STATUS:
            issues.append(
                issue(
                    "ERROR",
                    "INVALID_REVIEW_STATUS",
                    f"Unknown review status '{status}'.",
                    row=row_number,
                    record_id=issue_id,
                )
            )

        is_closed = status in CLOSED_STATUS
        if severity == "MAJOR" and not is_closed:
            unresolved_major += 1
        if blocking == "YES" and not is_closed:
            unresolved_blocking += 1

        if status in {
            "FULLY_ADDRESSED",
            "PARTIALLY_ADDRESSED",
            "NOT_ADDRESSED",
            "MADE_WORSE",
        } and not record.get("rereview_note", ""):
            issues.append(
                issue(
                    "WARNING",
                    "REREVIEW_NOTE_MISSING",
                    "Re-review status should cite verification evidence and remaining action.",
                    row=row_number,
                    record_id=issue_id,
                )
            )

    perspectives.discard("")
    if require_perspectives and len(perspectives) < require_perspectives:
        issues.append(
            issue(
                "ERROR",
                "INSUFFICIENT_REVIEW_PERSPECTIVES",
                f"Found {len(perspectives)} perspectives; required {require_perspectives}.",
            )
        )

    if recommendation == "READY" and unresolved_major:
        issues.append(
            issue(
                "ERROR",
                "READY_WITH_OPEN_MAJOR",
                f"READY conflicts with {unresolved_major} unresolved Major issue(s).",
            )
        )
    if recommendation == "MINOR_REVISION" and unresolved_major:
        issues.append(
            issue(
                "ERROR",
                "MINOR_WITH_OPEN_MAJOR",
                f"MINOR_REVISION conflicts with {unresolved_major} unresolved Major issue(s).",
            )
        )
    if recommendation in {"READY", "MINOR_REVISION"} and unresolved_blocking:
        issues.append(
            issue(
                "ERROR",
                "RECOMMENDATION_WITH_BLOCKER",
                f"{recommendation} conflicts with {unresolved_blocking} unresolved blocker(s).",
            )
        )

    summary = summarize_issues(issues)
    status = "FAIL" if summary["ERROR"] else "PASS_WITH_WARNINGS" if summary["WARNING"] else "PASS"
    return {
        "title": "Peer-Review Package Audit",
        "source": str(ledger.resolve()),
        "status": status,
        "record_count": len(records),
        "perspective_count": len(perspectives),
        "perspectives": sorted(perspectives),
        "recommendation": recommendation or "NOT_PROVIDED",
        "unresolved_major_count": unresolved_major,
        "unresolved_blocking_count": unresolved_blocking,
        "summary": summary,
        "issues": issues,
        "scope_note": "Checks ledger structure and internal decision consistency; it does not perform scientific peer review.",
    }


def main() -> int:
    args = parse_args()
    report = audit(args.ledger, args.recommendation, args.require_perspectives)
    if args.json_path:
        write_json(args.json_path, report, force=args.force)
    if args.markdown:
        write_markdown(args.markdown, report, force=args.force)
    print(
        f"{report['status']}: {report['record_count']} issues, "
        f"{report['unresolved_major_count']} open major, "
        f"{report['unresolved_blocking_count']} blockers"
    )
    failed = report["summary"]["ERROR"] > 0 or (
        args.strict and report["summary"]["WARNING"] > 0
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
