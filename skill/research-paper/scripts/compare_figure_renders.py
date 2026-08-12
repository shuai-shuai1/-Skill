#!/usr/bin/env python3
"""Compare a reference figure with a rendered PPT candidate using pixel metrics."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def require_pillow() -> dict[str, Any]:
    try:
        from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps, ImageStat
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required. Install scripts/requirements.txt before running compare_figure_renders.py."
        ) from exc
    return {
        "Image": Image,
        "ImageChops": ImageChops,
        "ImageEnhance": ImageEnhance,
        "ImageFilter": ImageFilter,
        "ImageOps": ImageOps,
        "ImageStat": ImageStat,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pixel-difference QA for a reference and candidate render.")
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--resize", choices=("none", "stretch", "contain", "crop"), default="none")
    parser.add_argument("--background", default="#FFFFFF")
    parser.add_argument("--pixel-threshold", type=int, default=16)
    parser.add_argument("--max-mae", type=float, default=None)
    parser.add_argument("--max-differing-ratio", type=float, default=None)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--diff", type=Path)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def flatten(image: Any, background: str, Image: Any) -> Any:
    rgba = image.convert("RGBA")
    canvas = Image.new("RGBA", rgba.size, background)
    canvas.alpha_composite(rgba)
    return canvas.convert("RGB")


def resize_candidate(candidate: Any, size: tuple[int, int], strategy: str, background: str, lib: dict[str, Any]) -> Any:
    Image = lib["Image"]
    ImageOps = lib["ImageOps"]
    if strategy == "none":
        if candidate.size != size:
            raise ValueError(
                f"Image sizes differ: reference={size}, candidate={candidate.size}. "
                "Use --resize only when the alignment policy is intentional."
            )
        return candidate
    if strategy == "stretch":
        return candidate.resize(size, Image.Resampling.LANCZOS)
    if strategy == "crop":
        return ImageOps.fit(candidate, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    contained = ImageOps.contain(candidate, size, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, background)
    x = (size[0] - contained.size[0]) // 2
    y = (size[1] - contained.size[1]) // 2
    canvas.paste(contained, (x, y))
    return canvas


def compute_metrics(reference: Any, candidate: Any, threshold: int, lib: dict[str, Any]) -> tuple[dict[str, float], Any]:
    ImageChops = lib["ImageChops"]
    ImageFilter = lib["ImageFilter"]
    diff = ImageChops.difference(reference, candidate)
    histogram = diff.histogram()
    pixels = reference.size[0] * reference.size[1]
    channels = 3
    absolute_sum = 0.0
    square_sum = 0.0
    exact_channels = 0
    for channel in range(channels):
        channel_hist = histogram[channel * 256 : (channel + 1) * 256]
        absolute_sum += sum(value * count for value, count in enumerate(channel_hist))
        square_sum += sum((value**2) * count for value, count in enumerate(channel_hist))
        exact_channels += channel_hist[0]
    mae = absolute_sum / (pixels * channels * 255.0)
    rmse = math.sqrt(square_sum / (pixels * channels)) / 255.0
    exact_channel_ratio = exact_channels / (pixels * channels)

    gray_diff = diff.convert("L")
    differing = sum(count for value, count in enumerate(gray_diff.histogram()) if value > threshold)
    differing_ratio = differing / pixels

    reference_edge = reference.convert("L").filter(ImageFilter.FIND_EDGES)
    candidate_edge = candidate.convert("L").filter(ImageFilter.FIND_EDGES)
    edge_diff = ImageChops.difference(reference_edge, candidate_edge)
    edge_hist = edge_diff.histogram()
    edge_mae = sum(value * count for value, count in enumerate(edge_hist)) / (pixels * 255.0)

    return (
        {
            "normalized_mae": round(mae, 8),
            "normalized_rmse": round(rmse, 8),
            "exact_channel_ratio": round(exact_channel_ratio, 8),
            "differing_pixel_ratio": round(differing_ratio, 8),
            "edge_normalized_mae": round(edge_mae, 8),
        },
        diff,
    )


def prepare_output(path: Path | None, force: bool) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"Output already exists: {path}; pass --force to replace it")


def main() -> int:
    args = parse_args()
    if not 0 <= args.pixel_threshold <= 255:
        raise SystemExit("--pixel-threshold must be between 0 and 255")
    lib = require_pillow()
    Image = lib["Image"]
    ImageEnhance = lib["ImageEnhance"]
    ImageOps = lib["ImageOps"]

    with Image.open(args.reference) as ref_image, Image.open(args.candidate) as cand_image:
        candidate_original_size = cand_image.size
        reference = flatten(ref_image, args.background, Image)
        candidate = flatten(cand_image, args.background, Image)
    candidate = resize_candidate(candidate, reference.size, args.resize, args.background, lib)
    metrics, diff = compute_metrics(reference, candidate, args.pixel_threshold, lib)

    failures: list[str] = []
    if args.max_mae is not None and metrics["normalized_mae"] > args.max_mae:
        failures.append(
            f"normalized_mae {metrics['normalized_mae']:.6f} exceeds {args.max_mae:.6f}"
        )
    if (
        args.max_differing_ratio is not None
        and metrics["differing_pixel_ratio"] > args.max_differing_ratio
    ):
        failures.append(
            "differing_pixel_ratio "
            f"{metrics['differing_pixel_ratio']:.6f} exceeds {args.max_differing_ratio:.6f}"
        )
    status = "FAIL" if failures else "PASS"
    report = {
        "title": "Figure Render Pixel Comparison",
        "status": status,
        "reference": str(args.reference.resolve()),
        "candidate": str(args.candidate.resolve()),
        "reference_size": list(reference.size),
        "candidate_original_size": list(candidate_original_size),
        "resize_strategy": args.resize,
        "pixel_threshold": args.pixel_threshold,
        "metrics": metrics,
        "threshold_failures": failures,
        "scope_note": "Pixel metrics are QA signals, not proof of scientific correctness or reuse permission.",
    }

    for output_path in (args.output, args.diff, args.overlay):
        prepare_output(output_path, args.force)
    if args.diff:
        amplified = ImageEnhance.Contrast(ImageOps.autocontrast(diff.convert("RGB"))).enhance(2.0)
        amplified.save(args.diff)
    if args.overlay:
        Image.blend(reference, candidate, 0.5).save(args.overlay)
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"{status}: MAE={metrics['normalized_mae']:.6f}, "
        f"differing_ratio={metrics['differing_pixel_ratio']:.6f}, "
        f"edge_MAE={metrics['edge_normalized_mae']:.6f}"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
