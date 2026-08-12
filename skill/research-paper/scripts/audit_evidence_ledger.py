#!/usr/bin/env python3
"""Audit an evidence ledger without making scientific-validity claims."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from audit_utils import (
    issue,
    read_records,
    split_ids,
    summarize_issues,
    write_json,
    write_markdown,
)


REQUIRED_FIELDS = (
    "evidence_id",
    "evidence_type",
    "title",
    "source_path",
    "claim_ids",
    "status",
)
ALLOWED_TYPES = {
    "MEASURED",
    "LOGGED",
    "DERIVED",
    "THEORETICAL",
    "LITERATURE",
    "SYNTHETIC",
    "UNVERIFIED",
}
ALLOWED_STATUS = {"VERIFIED", "PARTIAL", "PENDING", "REJECTED"}
PUBLIC_VALUES = {"YES", "NO", "RESTRICTED", "UNKNOWN", ""}
DISCLOSURE_WORDS = {
    "synthetic",
    "demo",
    "illustrative",
    "toy",
    "合成",
    "演示",
    "示意",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a CSV/JSON Evidence Ledger.")
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failure.")
    parser.add_argument("--force", action="store_true", help="Replace report outputs.")
    return parser.parse_args()


def audit(records: list[dict[str, str]], source: Path) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    ids: list[str] = []
    type_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()

    if not records:
        issues.append(issue("ERROR", "EMPTY_LEDGER", "The ledger contains no evidence records."))

    for row_number, record in enumerate(records, start=2):
        record_id = record.get("evidence_id", "") or f"row-{row_number}"
        for field in REQUIRED_FIELDS:
            if not record.get(field, "").strip():
                issues.append(
                    issue(
                        "ERROR",
                        "MISSING_REQUIRED_FIELD",
                        f"Required field '{field}' is empty.",
                        row=row_number,
                        field=field,
                        record_id=record_id,
                    )
                )

        evidence_id = record.get("evidence_id", "").strip()
        if evidence_id:
            ids.append(evidence_id)
            if not evidence_id.upper().startswith("E"):
                issues.append(
                    issue(
                        "WARNING",
                        "NONSTANDARD_EVIDENCE_ID",
                        "Evidence IDs should use a stable E-prefixed convention such as E001.",
                        row=row_number,
                        field="evidence_id",
                        record_id=evidence_id,
                    )
                )

        evidence_type = record.get("evidence_type", "").upper()
        status = record.get("status", "").upper()
        type_counter[evidence_type] += 1
        status_counter[status] += 1
        if evidence_type and evidence_type not in ALLOWED_TYPES:
            issues.append(
                issue(
                    "ERROR",
                    "INVALID_EVIDENCE_TYPE",
                    f"Unknown evidence_type '{evidence_type}'.",
                    row=row_number,
                    field="evidence_type",
                    record_id=record_id,
                )
            )
        if status and status not in ALLOWED_STATUS:
            issues.append(
                issue(
                    "ERROR",
                    "INVALID_STATUS",
                    f"Unknown status '{status}'.",
                    row=row_number,
                    field="status",
                    record_id=record_id,
                )
            )

        if evidence_type == "UNVERIFIED" and status == "VERIFIED":
            issues.append(
                issue(
                    "ERROR",
                    "UNVERIFIED_MARKED_VERIFIED",
                    "UNVERIFIED evidence cannot have VERIFIED status.",
                    row=row_number,
                    record_id=record_id,
                )
            )

        if evidence_type in {"MEASURED", "LOGGED", "DERIVED"} and status == "VERIFIED":
            if not record.get("version_or_run", ""):
                issues.append(
                    issue(
                        "ERROR",
                        "MISSING_RUN_IDENTITY",
                        "Verified empirical evidence requires version_or_run.",
                        row=row_number,
                        field="version_or_run",
                        record_id=record_id,
                    )
                )
            if not record.get("source_locator", ""):
                issues.append(
                    issue(
                        "WARNING",
                        "MISSING_SOURCE_LOCATOR",
                        "Add a result key, table, line, page, or field locator.",
                        row=row_number,
                        field="source_locator",
                        record_id=record_id,
                    )
                )

        if evidence_type == "SYNTHETIC":
            disclosure_text = " ".join(
                [record.get("title", ""), record.get("limitations", ""), record.get("notes", "")]
            ).lower()
            if not any(word in disclosure_text for word in DISCLOSURE_WORDS):
                issues.append(
                    issue(
                        "ERROR",
                        "SYNTHETIC_NOT_DISCLOSED",
                        "Synthetic evidence must be explicitly labeled in title, limitations, or notes.",
                        row=row_number,
                        record_id=record_id,
                    )
                )

        public_release = record.get("public_release", "").upper()
        if public_release not in PUBLIC_VALUES:
            issues.append(
                issue(
                    "WARNING",
                    "INVALID_PUBLIC_RELEASE",
                    "Use YES, NO, RESTRICTED, UNKNOWN, or blank for public_release.",
                    row=row_number,
                    field="public_release",
                    record_id=record_id,
                )
            )

        if not split_ids(record.get("claim_ids", "")):
            issues.append(
                issue(
                    "ERROR",
                    "NO_LINKED_CLAIMS",
                    "Every evidence record must link to at least one claim_id.",
                    row=row_number,
                    field="claim_ids",
                    record_id=record_id,
                )
            )
        if not record.get("limitations", ""):
            issues.append(
                issue(
                    "WARNING",
                    "MISSING_LIMITATIONS",
                    "Record what this evidence cannot support.",
                    row=row_number,
                    field="limitations",
                    record_id=record_id,
                )
            )

    duplicates = sorted(key for key, count in Counter(ids).items() if count > 1)
    for duplicate in duplicates:
        issues.append(
            issue(
                "ERROR",
                "DUPLICATE_EVIDENCE_ID",
                f"Evidence ID '{duplicate}' occurs more than once.",
                record_id=duplicate,
            )
        )

    summary = summarize_issues(issues)
    status = "FAIL" if summary["ERROR"] else "PASS_WITH_WARNINGS" if summary["WARNING"] else "PASS"
    return {
        "title": "Evidence Ledger Audit",
        "source": str(source.resolve()),
        "status": status,
        "record_count": len(records),
        "evidence_type_counts": dict(sorted(type_counter.items())),
        "evidence_status_counts": dict(sorted(status_counter.items())),
        "summary": summary,
        "issues": issues,
        "scope_note": "This audit checks ledger structure and traceability fields, not scientific validity.",
    }


def main() -> int:
    args = parse_args()
    records = read_records(args.ledger, collection_key="evidence")
    report = audit(records, args.ledger)
    if args.json_path:
        write_json(args.json_path, report, force=args.force)
    if args.markdown:
        write_markdown(args.markdown, report, force=args.force)
    print(
        f"{report['status']}: {report['record_count']} records, "
        f"{report['summary']['ERROR']} errors, {report['summary']['WARNING']} warnings"
    )
    failed = report["summary"]["ERROR"] > 0 or (
        args.strict and report["summary"]["WARNING"] > 0
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
