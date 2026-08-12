#!/usr/bin/env python3
"""Shared helpers for deterministic research-paper audits."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


def read_records(path: Path, collection_key: str | None = None) -> list[dict[str, str]]:
    """Read CSV or JSON records as normalized string dictionaries."""
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [normalize_record(row) for row in csv.DictReader(handle)]
    if suffix == ".json":
        with path.open("r", encoding="utf-8-sig") as handle:
            payload: Any = json.load(handle)
        if collection_key and isinstance(payload, dict):
            payload = payload.get(collection_key, payload)
        if isinstance(payload, dict):
            for candidate in ("records", "items", "evidence", "claims"):
                if isinstance(payload.get(candidate), list):
                    payload = payload[candidate]
                    break
        if not isinstance(payload, list):
            raise ValueError(f"JSON must contain a list of records: {path}")
        return [normalize_record(item) for item in payload]
    raise ValueError(f"Unsupported table format '{suffix}'; use CSV or JSON")


def normalize_record(record: Any) -> dict[str, str]:
    if not isinstance(record, dict):
        raise ValueError("Each record must be an object/dictionary")
    return {
        str(key).strip(): "" if value is None else str(value).strip()
        for key, value in record.items()
        if key is not None
    }


def split_ids(value: str) -> list[str]:
    cleaned = value.replace("，", ",").replace("；", ";")
    for separator in (";", "|", " "):
        cleaned = cleaned.replace(separator, ",")
    return [item.strip() for item in cleaned.split(",") if item.strip()]


def issue(
    severity: str,
    code: str,
    message: str,
    *,
    row: int | None = None,
    field: str | None = None,
    record_id: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "severity": severity,
        "code": code,
        "message": message,
    }
    if row is not None:
        result["row"] = row
    if field:
        result["field"] = field
    if record_id:
        result["record_id"] = record_id
    return result


def summarize_issues(issues: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
    for item in issues:
        severity = str(item.get("severity", "INFO")).upper()
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def write_json(path: Path, payload: dict[str, Any], force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"Output already exists: {path}; pass --force to replace it")
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_markdown(path: Path, report: dict[str, Any], force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"Output already exists: {path}; pass --force to replace it")
    summary = report.get("summary", {})
    lines = [
        f"# {report.get('title', 'Audit Report')}",
        "",
        f"- Status: `{report.get('status', 'UNKNOWN')}`",
        f"- Errors: {summary.get('ERROR', 0)}",
        f"- Warnings: {summary.get('WARNING', 0)}",
        f"- Info: {summary.get('INFO', 0)}",
        "",
        "## Issues",
        "",
    ]
    issues = report.get("issues", [])
    if not issues:
        lines.append("No issues detected by the deterministic checks.")
    for item in issues:
        location = []
        if item.get("record_id"):
            location.append(str(item["record_id"]))
        if item.get("row") is not None:
            location.append(f"row {item['row']}")
        if item.get("field"):
            location.append(str(item["field"]))
        where = f" ({', '.join(location)})" if location else ""
        lines.append(
            f"- **{item.get('severity', 'INFO')} {item.get('code', '')}**{where}: "
            f"{item.get('message', '')}"
        )
    lines.extend(
        [
            "",
            "> This report contains deterministic or heuristic checks only. "
            "It does not establish scientific validity by itself.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
