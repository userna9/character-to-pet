#!/usr/bin/env python3
"""Register extracted standard rows with ONE uniform transform per entire row.

Does not draw, validate semantics or compose an atlas. Run official inspection
and quality gates after this optional deterministic extraction correction.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from PIL import Image

COUNTS = {"idle": 6, "running-right": 8, "running-left": 8, "waving": 4,
          "jumping": 5, "failed": 8, "waiting": 6, "running": 6, "review": 6}
CELL = (192, 208)


def bounds(image):
    return image.getchannel("A").point(lambda x: 255 if x > 16 else 0).getbbox()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frames-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--json-out", required=True)
    p.add_argument("--body-height", type=float)
    p.add_argument("--baseline", type=int, default=202)
    p.add_argument("--margin", type=int, default=5)
    args = p.parse_args()
    source, output = Path(args.frames_root).resolve(), Path(args.output_root).resolve()
    if source == output or output.is_relative_to(source) or source.is_relative_to(output):
        p.error("Input/output roots must be separate; input frames are never overwritten")
    if output.exists() and any(output.iterdir()):
        p.error("Output root must be empty")
    if args.margin < 1 or not args.margin < args.baseline <= CELL[1] - args.margin:
        p.error("Baseline must leave safe top and bottom margins")
    rows = {}
    for state, count in COUNTS.items():
        files = sorted((source / state).glob("*.png"))
        if len(files) != count:
            p.error(f"{state}: expected {count} PNG frames, found {len(files)}")
        images = [Image.open(f).convert("RGBA") for f in files]
        if any(im.size != CELL or bounds(im) is None for im in images):
            p.error(f"{state}: frames must be non-empty 192x208 RGBA cells")
        boxes = [bounds(im) for im in images]
        ground = max(b[3] for b in boxes)
        standing_height = (max(boxes[i][3] - boxes[i][1] for i in [0, len(boxes)-1])
                           if state == "jumping" else max(b[3] - b[1] for b in boxes))
        extent = ground - min(b[1] for b in boxes)
        horizontal_extent = max(max(96-b[0], b[2]-96) for b in boxes)
        safe_height = standing_height * min((args.baseline - args.margin) / extent,
                                            (96 - args.margin) / horizontal_extent)
        rows[state] = {"files": files, "images": images, "boxes": boxes, "ground": ground,
                       "standing_height": standing_height, "safe_height": safe_height}
    # Never enlarge beyond current neutral size or beyond any row's vertical fit.
    target = args.body_height if args.body_height is not None else min(rows["idle"]["standing_height"], *(r["safe_height"] for r in rows.values()))
    if target <= 0:
        p.error("body-height must be positive")
    pending, records = [], []
    for state, row in rows.items():
        scale = target / row["standing_height"]
        w, h = round(CELL[0] * scale), round(CELL[1] * scale)
        x, y = round(96 - 96 * scale), round(args.baseline - row["ground"] * scale)
        transformed = []
        for f, im, box in zip(row["files"], row["images"], row["boxes"]):
            # Compute transformed real bounds before rendering, so cropping cannot pass silently.
            left, top = x + box[0] * scale, y + box[1] * scale
            right, bottom = x + box[2] * scale, y + box[3] * scale
            if left < args.margin-1 or right > CELL[0]-args.margin+1 or top < args.margin-1 or bottom > CELL[1]-args.margin+1:
                p.error(f"{state}/{f.name}: requested common scale exceeds safe bounds; lower --body-height")
            dest = Image.new("RGBA", CELL)
            dest.alpha_composite(im.resize((w, h), Image.Resampling.LANCZOS), (x, y))
            transformed.append(bounds(dest))
            pending.append((output / state / f.name, dest))
        records.append({"state": state, "one_transform_for_entire_row": True,
                        "scale": scale, "translation": [x, y], "bounds_before": row["boxes"], "bounds_after": transformed})
    for filename, image in pending:
        filename.parent.mkdir(parents=True, exist_ok=True)
        image.save(filename)
    manifest = source / "frames-manifest.json"
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for row in data.get("rows", []):
            row["frames"] = [str(output / row["state"] / Path(f).name) for f in row.get("frames", [])]
        (output / "frames-manifest.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    report = {"body_height": target, "baseline": args.baseline, "semantic_validation": "not_performed",
              "official_reinspection_required": True, "rows": records}
    report_path = Path(args.json_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "body_height": target, "official_reinspection_required": True}))


if __name__ == "__main__":
    main()
