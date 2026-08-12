#!/usr/bin/env python3
"""Reusable Matplotlib styles and provenance helpers for scientific figures."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


COLORBLIND_PALETTE = (
    "#0077BB",
    "#EE7733",
    "#009988",
    "#CC3311",
    "#33BBEE",
    "#EE3377",
    "#BBBBBB",
    "#000000",
)
LINE_STYLES = ("-", "--", "-.", ":")
MARKERS = ("o", "s", "^", "D", "v", "P", "X", "*")

STYLE_PRESETS: dict[str, dict[str, Any]] = {
    "engineering": {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Noto Sans CJK SC", "Microsoft YaHei", "DejaVu Sans"],
        "font.size": 8.5,
        "axes.labelsize": 9,
        "axes.titlesize": 9.5,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.35,
        "lines.markersize": 4.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    },
    "grayscale": {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Noto Serif CJK SC", "SimSun", "DejaVu Serif"],
        "font.size": 8.5,
        "axes.labelsize": 9,
        "axes.titlesize": 9.5,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    },
}


@dataclass
class FigureProvenance:
    """Minimal machine-readable provenance for a generated figure."""

    figure_id: str
    evidence_type: str
    source_files: list[str]
    claim_ids: list[str] = field(default_factory=list)
    transformations: list[str] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)
    synthetic_disclosure: str = ""
    assumptions: list[str] = field(default_factory=list)
    generator: str = ""
    generated_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def validate(self) -> None:
        allowed = {
            "MEASURED",
            "LOGGED",
            "DERIVED",
            "THEORETICAL",
            "LITERATURE",
            "SYNTHETIC",
            "UNVERIFIED",
        }
        self.evidence_type = self.evidence_type.upper()
        if self.evidence_type not in allowed:
            raise ValueError(f"Unsupported evidence_type: {self.evidence_type}")
        if not self.figure_id:
            raise ValueError("figure_id is required")
        if not self.source_files:
            raise ValueError("At least one source file or source identifier is required")
        if self.evidence_type == "SYNTHETIC" and not self.synthetic_disclosure:
            raise ValueError("Synthetic figures require synthetic_disclosure")


def apply_matplotlib_style(preset: str = "engineering") -> dict[str, Any]:
    """Apply a bundled style and return the applied rcParams dictionary."""
    if preset not in STYLE_PRESETS:
        raise ValueError(f"Unknown preset '{preset}'. Choose from {sorted(STYLE_PRESETS)}")
    import matplotlib as mpl

    style = dict(STYLE_PRESETS[preset])
    mpl.rcParams.update(style)
    return style


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_provenance(path: Path, provenance: FigureProvenance, force: bool = False) -> Path:
    provenance.validate()
    if path.exists() and not force:
        raise FileExistsError(f"Output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(provenance)
    payload["source_hashes"] = {
        source: file_sha256(Path(source))
        for source in provenance.source_files
        if Path(source).is_file()
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def save_figure(
    figure: Any,
    output_stem: Path,
    formats: Iterable[str] = ("pdf", "svg", "png"),
    dpi: int = 300,
    force: bool = False,
) -> list[Path]:
    """Save one figure to deterministic publication formats without overwriting by default."""
    outputs: list[Path] = []
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    for raw_format in formats:
        fmt = raw_format.lower().lstrip(".")
        if fmt not in {"pdf", "svg", "png", "tif", "tiff", "eps"}:
            raise ValueError(f"Unsupported figure format: {fmt}")
        path = output_stem.with_suffix(f".{fmt}")
        if path.exists() and not force:
            raise FileExistsError(f"Output already exists: {path}")
        save_args = {"format": fmt, "bbox_inches": "tight", "facecolor": "white"}
        if fmt in {"png", "tif", "tiff"}:
            save_args["dpi"] = dpi
        figure.savefig(path, **save_args)
        outputs.append(path)
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a bundled Matplotlib style preset.")
    parser.add_argument("--preset", choices=sorted(STYLE_PRESETS), default="engineering")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(STYLE_PRESETS[args.preset], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
