#!/usr/bin/env python3
"""Combine existing identity references, preserving content and aspect ratio."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image", action="append", required=True)
    p.add_argument("--label", action="append", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--columns", type=int, default=2)
    p.add_argument("--tile-size", type=int, default=1024)
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    if len(args.image) != len(args.label):
        p.error("Each image needs exactly one role label")
    if args.columns < 1 or args.tile_size < 128:
        p.error("columns must be positive and tile-size at least 128")
    output = Path(args.output).resolve()
    if output.exists() and not args.overwrite:
        p.error("Output exists; use a new filename or --overwrite")
    columns = min(args.columns, len(args.image))
    size, header = args.tile_size, 42
    panel = Image.new("RGB", (columns * size, math.ceil(len(args.image) / columns) * (size + header)), "#eeedf2")
    draw = ImageDraw.Draw(panel)
    fonts = [Path("C:/Windows/Fonts/msyh.ttc"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    font_path = next((f for f in fonts if f.is_file()), None)
    font = ImageFont.truetype(str(font_path), 20) if font_path else ImageFont.load_default(size=20)
    records = []
    for i, (filename, label) in enumerate(zip(args.image, args.label)):
        source = Path(filename).resolve()
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGBA")
        fitted = ImageOps.contain(image, (size - 24, size - 24), Image.Resampling.LANCZOS)
        x, y = (i % columns) * size, (i // columns) * (size + header)
        panel.paste(fitted, (x + (size - fitted.width) // 2, y + header + (size - fitted.height) // 2), fitted)
        draw.text((x + 12, y + 10), label, fill="#292333", font=font)
        records.append({"role": label, "source": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        "source_size": list(image.size), "fitted_size": list(fitted.size), "cropped": False})
    output.parent.mkdir(parents=True, exist_ok=True)
    panel.save(output, format="PNG")
    output.with_suffix(".json").write_text(json.dumps({"reference_only": True, "images": records}, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "references": len(records), "reference_only": True}))


if __name__ == "__main__":
    main()
