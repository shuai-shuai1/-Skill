#!/usr/bin/env python3
"""Run deterministic raster-image checks for publication figure candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def require_pillow() -> tuple[Any, Any, Any]:
    try:
        from PIL import Image, ImageOps, ImageStat
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required. Install scripts/requirements.txt before running figure_qa.py."
        ) from exc
    return Image, ImageOps, ImageStat


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect raster figure dimensions and basic readability signals.")
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--min-width", type=int, default=1000)
    parser.add_argument("--min-height", type=int, default=700)
    parser.add_argument("--min-dpi", type=float, default=300.0)
    parser.add_argument("--max-white-ratio", type=float, default=0.985)
    parser.add_argument("--min-contrast-span", type=float, default=35.0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def percentile_from_histogram(histogram: list[int], fraction: float) -> int:
    target = sum(histogram) * fraction
    running = 0
    for value, count in enumerate(histogram):
        running += count
        if running >= target:
            return value
    return 255


def inspect_image(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    Image, ImageOps, ImageStat = require_pillow()
    if not path.exists():
        return {
            "path": str(path),
            "status": "FAIL",
            "errors": ["File does not exist."],
            "warnings": [],
        }
    errors: list[str] = []
    warnings: list[str] = []
    with Image.open(path) as image:
        image.load()
        width, height = image.size
        mode = image.mode
        dpi_value = image.info.get("dpi")
        if isinstance(dpi_value, (tuple, list)) and dpi_value:
            dpi = min(float(item) for item in dpi_value[:2] if item)
        elif isinstance(dpi_value, (int, float)):
            dpi = float(dpi_value)
        else:
            dpi = None

        if width < args.min_width:
            errors.append(f"Width {width}px is below minimum {args.min_width}px.")
        if height < args.min_height:
            errors.append(f"Height {height}px is below minimum {args.min_height}px.")
        if dpi is None:
            warnings.append("DPI metadata is missing; verify physical-size resolution manually.")
        elif dpi + 0.5 < args.min_dpi:
            warnings.append(f"DPI {dpi:.1f} is below target {args.min_dpi:.1f}.")

        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        alpha_mean = ImageStat.Stat(alpha).mean[0]
        if alpha_mean < 1:
            errors.append("Image is effectively fully transparent.")

        flattened = Image.new("RGBA", rgba.size, "white")
        flattened.alpha_composite(rgba)
        gray = ImageOps.grayscale(flattened.convert("RGB"))
        histogram = gray.histogram()
        total = max(1, width * height)
        white_ratio = sum(histogram[248:]) / total
        p05 = percentile_from_histogram(histogram, 0.05)
        p95 = percentile_from_histogram(histogram, 0.95)
        contrast_span = float(p95 - p05)
        if white_ratio > args.max_white_ratio:
            warnings.append(
                f"Near-white pixel ratio {white_ratio:.3f} exceeds {args.max_white_ratio:.3f}; figure may be empty or overly sparse."
            )
        if contrast_span < args.min_contrast_span:
            warnings.append(
                f"5th-95th percentile contrast span {contrast_span:.1f} is below {args.min_contrast_span:.1f}."
            )

        status = "FAIL" if errors else "PASS_WITH_WARNINGS" if warnings else "PASS"
        return {
            "path": str(path.resolve()),
            "status": status,
            "width_px": width,
            "height_px": height,
            "mode": mode,
            "dpi": dpi,
            "near_white_ratio": round(white_ratio, 6),
            "contrast_span_p05_p95": round(contrast_span, 3),
            "alpha_mean": round(alpha_mean, 3),
            "errors": errors,
            "warnings": warnings,
        }


def main() -> int:
    args = parse_args()
    results = [inspect_image(path, args) for path in args.images]
    error_count = sum(len(item["errors"]) for item in results)
    warning_count = sum(len(item["warnings"]) for item in results)
    status = "FAIL" if error_count else "PASS_WITH_WARNINGS" if warning_count else "PASS"
    report = {
        "title": "Figure Raster QA",
        "status": status,
        "summary": {"images": len(results), "errors": error_count, "warnings": warning_count},
        "results": results,
        "scope_note": "Checks raster properties only; inspect scientific content, text, axes, and final-size readability manually.",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists() and not args.force:
            raise SystemExit(f"Output already exists: {args.output}; pass --force to replace it")
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{status}: {len(results)} images, {error_count} errors, {warning_count} warnings")
    return 1 if error_count or (args.strict and warning_count) else 0


if __name__ == "__main__":
    raise SystemExit(main())
