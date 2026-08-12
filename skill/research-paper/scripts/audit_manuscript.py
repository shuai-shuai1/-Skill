#!/usr/bin/env python3
"""Heuristically audit a Markdown/text manuscript against evidence records."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from audit_utils import (
    issue,
    read_records,
    split_ids,
    summarize_issues,
    write_json,
    write_markdown,
)


EVIDENCE_TAG_RE = re.compile(r"\[E:([^\]]+)\]", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(
    r"\b(?:TODO|TBD|FIXME|XXX)\b|待补(?:充|数据|引用)?|待核(?:验|对)?|"
    r"citation\s+needed|引用待补|\?\?\?",
    re.IGNORECASE,
)
HIGH_RISK_TERMS = {
    "首次": "First/priority claims require an explicit search basis and evidence.",
    "首创": "First/priority claims require an explicit search basis and evidence.",
    "显著优于": "Significance claims require a stated statistical test and evidence.",
    "显著提升": "Significance claims require a stated statistical test and evidence.",
    "充分证明": "Proof language is usually stronger than empirical evidence permits.",
    "完全解决": "Absolute claims require exhaustive evidence and a defined scope.",
    "大幅优于": "Magnitude claims require a fair comparator and reported values.",
    "state-of-the-art": "SOTA claims require a complete, fair, current comparison.",
    "significantly outperforms": "Significance claims require a stated statistical test.",
    "proves that": "Proof language is usually stronger than empirical evidence permits.",
}
NUMERIC_CLAIM_RE = re.compile(
    r"(?<![A-Za-z0-9_])[-+]?\d+(?:\.\d+)?\s*(?:%|‰|ms|s|h|Hz|kHz|MHz|GHz|"
    r"B|KB|MB|GB|TB|B/s|KB/s|MB/s|GB/s|dB|dBm|W|mW|V|mV|A|mA|F1|epoch|epochs|次|倍)",
    re.IGNORECASE,
)
SYNTHETIC_WORDS = {"synthetic", "demo", "illustrative", "toy", "合成", "演示", "示意"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a Markdown/text manuscript for traceability and risky wording."
    )
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--claims", type=Path)
    parser.add_argument("--terminology", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def load_evidence(path: Path | None) -> dict[str, dict[str, str]]:
    if not path:
        return {}
    return {
        record.get("evidence_id", ""): record
        for record in read_records(path, collection_key="evidence")
        if record.get("evidence_id", "")
    }


def extract_evidence_ids(line: str) -> list[str]:
    ids: list[str] = []
    for match in EVIDENCE_TAG_RE.finditer(line):
        ids.extend(split_ids(match.group(1)))
    return ids


def check_claim_matrix(
    path: Path | None, evidence: dict[str, dict[str, str]]
) -> list[dict[str, object]]:
    if not path:
        return []
    issues: list[dict[str, object]] = []
    allowed_status = {"SUPPORTED", "PARTIAL", "UNSUPPORTED", "CONTRADICTED"}
    required = {"claim_id", "claim_text", "evidence_ids", "section", "boundary", "status"}
    seen: set[str] = set()
    for row_number, record in enumerate(read_records(path, collection_key="claims"), start=2):
        claim_id = record.get("claim_id", "") or f"row-{row_number}"
        for field in required:
            if not record.get(field, ""):
                issues.append(
                    issue(
                        "ERROR",
                        "CLAIM_FIELD_MISSING",
                        f"Claim matrix field '{field}' is empty.",
                        row=row_number,
                        field=field,
                        record_id=claim_id,
                    )
                )
        if claim_id in seen:
            issues.append(
                issue(
                    "ERROR",
                    "DUPLICATE_CLAIM_ID",
                    f"Claim ID '{claim_id}' occurs more than once.",
                    row=row_number,
                    record_id=claim_id,
                )
            )
        seen.add(claim_id)
        status = record.get("status", "").upper()
        if status and status not in allowed_status:
            issues.append(
                issue(
                    "ERROR",
                    "INVALID_CLAIM_STATUS",
                    f"Unknown claim status '{status}'.",
                    row=row_number,
                    field="status",
                    record_id=claim_id,
                )
            )
        linked = split_ids(record.get("evidence_ids", ""))
        if status == "SUPPORTED" and not linked:
            issues.append(
                issue(
                    "ERROR",
                    "SUPPORTED_WITHOUT_EVIDENCE",
                    "A SUPPORTED claim must link to evidence IDs.",
                    row=row_number,
                    record_id=claim_id,
                )
            )
        if evidence:
            for evidence_id in linked:
                if evidence_id not in evidence:
                    issues.append(
                        issue(
                            "ERROR",
                            "UNKNOWN_CLAIM_EVIDENCE",
                            f"Claim references unknown evidence ID '{evidence_id}'.",
                            row=row_number,
                            field="evidence_ids",
                            record_id=claim_id,
                        )
                    )
    return issues


def check_terminology(path: Path | None, lines: list[str]) -> list[dict[str, object]]:
    if not path:
        return []
    issues: list[dict[str, object]] = []
    records = read_records(path)
    for row_number, line in enumerate(lines, start=1):
        lower = line.lower()
        for record in records:
            canonical = record.get("canonical_term", "").strip()
            aliases = [
                alias.strip()
                for alias in record.get("aliases", "").replace("；", "|").split("|")
                if alias.strip()
            ]
            for alias in aliases:
                if alias and alias.lower() != canonical.lower() and alias.lower() in lower:
                    issues.append(
                        issue(
                            "WARNING",
                            "NONCANONICAL_TERM",
                            f"Use canonical term '{canonical}' instead of alias '{alias}'.",
                            row=row_number,
                            field="terminology",
                        )
                    )
    return issues


def audit(
    manuscript: Path,
    evidence: dict[str, dict[str, str]],
    claims_path: Path | None,
    terminology_path: Path | None,
) -> dict[str, object]:
    if manuscript.suffix.lower() not in {".md", ".txt"}:
        raise ValueError("audit_manuscript.py supports Markdown or plain text; extract DOCX/PDF first.")
    text = manuscript.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    issues: list[dict[str, object]] = []
    used_evidence: set[str] = set()

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        evidence_ids = extract_evidence_ids(line)
        used_evidence.update(evidence_ids)
        without_tags = EVIDENCE_TAG_RE.sub("", line)

        if PLACEHOLDER_RE.search(without_tags):
            issues.append(
                issue(
                    "ERROR",
                    "UNRESOLVED_PLACEHOLDER",
                    "Unresolved drafting placeholder detected.",
                    row=line_number,
                )
            )

        lower_line = without_tags.lower()
        for phrase, guidance in HIGH_RISK_TERMS.items():
            if phrase.lower() in lower_line:
                severity = "WARNING" if evidence_ids else "ERROR"
                issues.append(
                    issue(
                        severity,
                        "HIGH_RISK_CLAIM",
                        f"High-risk phrase '{phrase}' detected. {guidance}",
                        row=line_number,
                    )
                )

        is_heading_or_table = stripped.startswith("#") or stripped.startswith("|")
        if NUMERIC_CLAIM_RE.search(without_tags) and not evidence_ids and not is_heading_or_table:
            issues.append(
                issue(
                    "WARNING",
                    "NUMERIC_CLAIM_WITHOUT_EVIDENCE_TAG",
                    "A numeric claim has no internal [E:...] evidence tag.",
                    row=line_number,
                )
            )

        for evidence_id in evidence_ids:
            if evidence and evidence_id not in evidence:
                issues.append(
                    issue(
                        "ERROR",
                        "UNKNOWN_EVIDENCE_TAG",
                        f"Manuscript references unknown evidence ID '{evidence_id}'.",
                        row=line_number,
                        record_id=evidence_id,
                    )
                )
                continue
            record = evidence.get(evidence_id)
            if not record:
                continue
            evidence_type = record.get("evidence_type", "").upper()
            status = record.get("status", "").upper()
            if status != "VERIFIED":
                issues.append(
                    issue(
                        "WARNING",
                        "NONVERIFIED_EVIDENCE_USED",
                        f"Evidence '{evidence_id}' has status {status or 'UNKNOWN'}.",
                        row=line_number,
                        record_id=evidence_id,
                    )
                )
            if evidence_type == "SYNTHETIC" and not any(
                word in lower_line for word in SYNTHETIC_WORDS
            ):
                issues.append(
                    issue(
                        "ERROR",
                        "SYNTHETIC_USE_NOT_DISCLOSED",
                        f"Sentence uses synthetic evidence '{evidence_id}' without disclosure.",
                        row=line_number,
                        record_id=evidence_id,
                    )
                )
            if evidence_type == "UNVERIFIED":
                issues.append(
                    issue(
                        "ERROR",
                        "UNVERIFIED_EVIDENCE_USED",
                        f"Sentence relies on UNVERIFIED evidence '{evidence_id}'.",
                        row=line_number,
                        record_id=evidence_id,
                    )
                )

    issues.extend(check_claim_matrix(claims_path, evidence))
    issues.extend(check_terminology(terminology_path, lines))

    unused = sorted(set(evidence) - used_evidence)
    for evidence_id in unused:
        issues.append(
            issue(
                "INFO",
                "UNUSED_LEDGER_EVIDENCE",
                f"Evidence '{evidence_id}' is not referenced by an internal manuscript tag.",
                record_id=evidence_id,
            )
        )

    summary = summarize_issues(issues)
    status = "FAIL" if summary["ERROR"] else "PASS_WITH_WARNINGS" if summary["WARNING"] else "PASS"
    return {
        "title": "Manuscript Traceability Audit",
        "source": str(manuscript.resolve()),
        "status": status,
        "line_count": len(lines),
        "evidence_tag_count": sum(len(extract_evidence_ids(line)) for line in lines),
        "used_evidence_ids": sorted(used_evidence),
        "summary": summary,
        "issues": issues,
        "scope_note": "Checks are heuristic and do not replace scientific, statistical, citation, or peer review.",
    }


def main() -> int:
    args = parse_args()
    evidence = load_evidence(args.ledger)
    report = audit(args.manuscript, evidence, args.claims, args.terminology)
    if args.json_path:
        write_json(args.json_path, report, force=args.force)
    if args.markdown:
        write_markdown(args.markdown, report, force=args.force)
    print(
        f"{report['status']}: {report['line_count']} lines, "
        f"{report['summary']['ERROR']} errors, {report['summary']['WARNING']} warnings"
    )
    failed = report["summary"]["ERROR"] > 0 or (
        args.strict and report["summary"]["WARNING"] > 0
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
