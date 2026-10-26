#!/usr/bin/env python3
"""Render exact-atlas previews and package verified character-pet artifacts.

No image generation, account mutation, atlas composition or replacement quality
validator. Report inputs must come from the actual Pets tools and scripts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import runpy
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def render(args):
    from PIL import Image, ImageDraw, ImageFont
    atlas_path, output = Path(args.atlas).resolve(), Path(args.output_dir).resolve()
    scripts = Path(args.pet_scripts).resolve()
    renderer = scripts / "render_animation_previews.py"
    if not renderer.is_file():
        raise ValueError("Current Pets bundled preview renderer is required")
    ffmpeg = args.ffmpeg or shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValueError("ffmpeg is required for the MP4 deliverable; locate the bundled runtime or install it explicitly")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Preview output must be empty; choose a new revision directory")
    api = runpy.run_path(str(renderer))
    timings, save_gif = api["ROW_DURATIONS"], api["save_preview"]
    if len(timings) != 9 or sum(map(len, timings.values())) != 57:
        raise ValueError("This helper supports the v2 nine-state contract only; use updated official tools")
    with Image.open(atlas_path) as opened:
        atlas = opened.convert("RGBA")
    if atlas.size != (1536, 2288):
        raise ValueError("This preview helper requires the validated v2 1536x2288 atlas")
    output.mkdir(parents=True, exist_ok=True)
    fonts = [Path("C:/Windows/Fonts/msyh.ttc"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    font_path = next((f for f in fonts if f.is_file()), None)
    font = ImageFont.truetype(str(font_path), 19) if font_path else ImageFont.load_default(size=19)

    def panel(frame, label):
        board = Image.new("RGB", (384, 466), "#f0eef5")
        scaled = frame.resize((384, 416), Image.Resampling.LANCZOS)
        board.paste(scaled, (0, 42), scaled)
        ImageDraw.Draw(board).text((12, 10), label, fill="#3c314e", font=font)
        return board

    frames_root = output / "frames-from-final-atlas"
    states, all_frames, durations = {}, [], []
    for row, (state, times) in enumerate(timings.items()):
        state_dir = frames_root / state
        state_dir.mkdir(parents=True, exist_ok=True)
        states[state] = []
        for column, duration in enumerate(times):
            frame = atlas.crop((column * 192, row * 208, (column + 1) * 192, (row + 1) * 208))
            frame.save(state_dir / f"{column:02d}.png")
            states[state].append(frame)
            all_frames.append(panel(frame, state))
            durations.append(duration)
    subprocess.run([sys.executable, str(renderer), "--frames-root", str(frames_root),
                    "--output-dir", str(output / "states")], check=True, capture_output=True, text=True)
    save_gif(all_frames, durations, output / "all-states.gif")
    save_gif(states["idle"] + states["jumping"] + states["idle"],
             timings["idle"] + timings["jumping"] + timings["idle"], output / "idle-jump-idle.gif")
    angles = ["000", "022.5", "045", "067.5", "090", "112.5", "135", "157.5",
              "180", "202.5", "225", "247.5", "270", "292.5", "315", "337.5"]
    look_frames = []
    for i, angle in enumerate(angles):
        row, col = 9 + i // 8, i % 8
        frame = atlas.crop((col * 192, row * 208, (col + 1) * 192, (row + 1) * 208))
        look_frames.append(panel(frame, f"Look {angle} deg"))
    save_gif(look_frames, [220] * 16, output / "look-loop.gif")
    stills = Image.new("RGB", (1536, 466), "#f0eef5")
    for i, (state, index) in enumerate([("idle", 0), ("waving", 2), ("jumping", 2), ("failed", 5)]):
        stills.paste(panel(states[state][index], f"{state} #{index + 1}"), (384 * i, 0))
    stills.save(output / "four-state-stills.png")
    subprocess.run([str(ffmpeg), "-y", "-hide_banner", "-loglevel", "error", "-i", str(output / "all-states.gif"),
                    "-movflags", "+faststart", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output / "all-states.mp4")], check=True)
    write_json(output / "preview-manifest.json", {"source": str(atlas_path), "sha256": sha(atlas_path),
               "exact_final_atlas_pixels": True, "standard_frames": 57, "look_frames": 16,
               "duration_ms": sum(durations), "cell_size": [192, 208]})
    print(json.dumps({"output": str(output), "source_sha256": sha(atlas_path)}))


def package(args):
    atlas, root, deliverables, output = map(lambda v: Path(v).resolve(), [args.atlas, args.run_dir, args.deliverables, args.output])
    if output.exists():
        raise ValueError("Archive exists; choose a new revision filename")
    digest, size = sha(atlas), atlas.stat().st_size
    atlas_report, quality = read_json(args.atlas_report), read_json(args.quality_report)
    for label, report in [("atlas", atlas_report), ("quality", quality)]:
        if report.get("ok") is not True or report.get("errors"):
            raise ValueError(f"{label} report did not pass")
        if report.get("sha256") != digest:
            raise ValueError(f"{label} report hash does not match the exact atlas")
        if report.get("encoded_bytes") != size:
            raise ValueError(f"{label} report byte length does not match the exact atlas")
    gates = {"atlas": atlas_report, "quality": quality}
    if not args.local_only:
        if not args.mcp_report:
            raise ValueError("MCP report required; use --local-only only for an explicitly local artifact package")
        preflight = read_json(args.mcp_report)
        response = preflight.get("structuredContent", preflight)
        if response.get("valid") is not True or response.get("errors"):
            raise ValueError("Pets MCP preflight did not pass")
        if response.get("file_size_bytes") != size or (response.get("width"), response.get("height")) != (1536, 2288):
            raise ValueError("MCP report size/dimensions do not match the final v2 file")
        bound_hash = preflight.get("validated_sha256", response.get("validated_sha256"))
        if bound_hash and bound_hash != digest:
            raise ValueError("MCP preflight binding hash does not match")
        gates["mcp"] = response
    blind = root / "qa/blind-validation.json"
    if blind.is_file():
        blind_data = read_json(blind)
        if blind_data.get("ok") is not True:
            raise ValueError("Available independent blind validation did not pass")
        gates["blind"] = blind_data
    candidates = {}

    def add(path, archive_name):
        path = Path(path)
        if path.is_symlink():
            raise ValueError("Symlinks are not accepted in asset packages")
        path = path.resolve()
        if path.is_file():
            candidates[archive_name] = path

    add(atlas, "deliverables/spritesheet.png")
    for name in ["main-look.png", "contact-sheet.png", "directions.png", "README.md", "request-brief.md"]:
        add(deliverables / name, f"deliverables/{name}")
    previews = deliverables / "previews"
    for file in previews.rglob("*") if previews.is_dir() else []:
        if file.suffix.lower() in {".png", ".gif", ".mp4", ".json"}:
            add(file, "deliverables/previews/" + file.relative_to(previews).as_posix())
    jobs_file = root / "imagegen-jobs.json"
    if jobs_file.exists():
        jobs = read_json(jobs_file).get("jobs", [])
        for job in jobs:
            if job.get("status") != "complete":
                raise ValueError(f"Manifest job is not complete: {job.get('id')}")
            source = (root / job["output_path"]).resolve()
            if not source.is_relative_to(root):
                raise ValueError("Manifest output leaves run directory")
            if not source.is_file():
                raise ValueError(f"Selected source is missing: {job['output_path']}")
            add(source, "production/" + source.relative_to(root).as_posix())
        add(jobs_file, "production/imagegen-jobs.json")
    for folder, extensions in [("references", {".png", ".webp", ".jpg", ".jpeg"}), ("prompts", {".md", ".txt"})]:
        for file in (root / folder).rglob("*"):
            if file.suffix.lower() in extensions:
                add(file, "production/" + file.relative_to(root).as_posix())
    for name in ["request-brief.md", "request-brief.json", "sources.md", "sources.json", "qa/look-mechanics.md", "qa/standard-visual-review.md", "qa/final-visual-review.md",
                 "qa/direction-semantics.json", "qa/look-continuity.json", "qa/review.json", "qa/chroma-despill-extended.json",
                 "qa/blind-validation.json", "qa/blind-majority.json", "qa/look-row-9-registration.json", "qa/standard-registration.json",
                 "decoded/look-anchors-approved.png", "decoded/look-cardinals-normalized.png", "decoded/look-row-9-registered.png"]:
        add(root / name, "production/" + name)
    stable = {}
    info = deliverables / "pet-info.json"
    if info.exists():
        actual = read_json(info)
        fields = {"id", "name", "description", "is_custom", "is_active", "active_pet_id", "sprite_version", "sha256", "generation_mode"}
        stable = {k: v for k, v in actual.items() if k in fields}
        if stable.get("sha256") not in {None, digest}:
            raise ValueError("Pet metadata references different atlas bytes")
    manifest = {"mode": "local-only" if args.local_only else "mcp-validated", "sha256": digest,
                "bytes": size, "pet_metadata": stable, "checks": gates,
                "files": [{"path": name, "bytes": file.stat().st_size, "sha256": sha(file)} for name, file in sorted(candidates.items())]}
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, file in sorted(candidates.items()):
                archive.write(file, name)
            archive.writestr("package-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            archive.writestr("deliverables/pet-info.json", json.dumps(stable, ensure_ascii=False, indent=2))
        with zipfile.ZipFile(output) as archive:
            if archive.testzip() is not None:
                raise ValueError("Archive CRC verification failed")
    except Exception:
        output.unlink(missing_ok=True)
        raise
    print(json.dumps({"archive": str(output), "bytes": output.stat().st_size, "mode": manifest["mode"], "sha256": digest}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("render")
    p.add_argument("--atlas", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--pet-scripts", required=True)
    p.add_argument("--ffmpeg")
    p.set_defaults(run=render)
    p = sub.add_parser("package")
    for arg in ["atlas", "run-dir", "deliverables", "atlas-report", "quality-report", "output"]:
        p.add_argument("--" + arg, required=True)
    p.add_argument("--mcp-report")
    p.add_argument("--local-only", action="store_true")
    p.set_defaults(run=package)
    args = parser.parse_args()
    try:
        args.run(args)
    except (ValueError, OSError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
