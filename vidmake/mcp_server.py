"""
mcp_server.py — Video Pipeline MCP Server (v2).

Designed to minimize AI round-trips while keeping full customization.

  BATCH (1 tool call = multiple slides):
    1. batch_slides        — HTML[] → PNG[] → MP4 clips[] (screenshot + animate in one call)

  TEMPLATE (zero HTML needed):
    2. create_slide         — Template-based slide: just pass title/body/style → PNG

  ATOMIC (per-file control):
    3. screenshot_html      — HTML → PNG
    4. animate_image        — PNG → MP4 clip (Ken Burns)

  ASSEMBLY:
    5. merge_clips          — Concat clips → MP4
    6. merge_clips_crossfade— Concat with crossfade
    7. add_audio            — Video + music → MP4

  POST-PROCESSING:
    8. add_text_overlay     — Text/watermark onto video
    9. resize_video         — Resize/crop/pad

  UTILITY:
   10. get_media_info       — Probe file info
   11. list_effects         — Available animation effects
   12. list_templates       — Available slide templates
   13. list_outputs         — Files in output dir
   14. cleanup_outputs      — Delete output files

Run: python -m vidmake.mcp_server
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "vidmake",
    instructions=(
        "Video Pipeline MCP Server — create TikTok-style videos with Ken Burns animations.\n\n"
        "FASTEST workflow (2 tool calls for a full video):\n"
        "  1. batch_slides — pass HTML for all slides at once → gets PNGs + animated clips\n"
        "  2. merge_clips_crossfade — join clips into final video\n"
        "  (optional) add_audio, add_text_overlay\n\n"
        "TEMPLATE workflow (no HTML needed, 2 tool calls):\n"
        "  1. create_slide × N — pass title/body/style, get PNGs automatically\n"
        "  2. batch_slides — pass PNG paths to animate\n"
        "  3. merge_clips_crossfade\n\n"
        "CUSTOM workflow (full control per slide):\n"
        "  1. screenshot_html per slide\n"
        "  2. animate_image per slide (choose effect, duration)\n"
        "  3. merge_clips or merge_clips_crossfade\n"
        "  4. add_audio, add_text_overlay, resize_video\n\n"
        "All output → ~/vidmake-output/\n"
        "Effects: zoom_in, zoom_out, pan_right, pan_down, zoom_topleft"
    ),
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_DIR = os.environ.get("VIDMAKE_OUTPUT_DIR", os.path.expanduser("~/vidmake-output"))
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

AVAILABLE_EFFECTS = ["zoom_in", "zoom_out", "pan_right", "pan_down", "zoom_topleft"]

# ---------------------------------------------------------------------------
# Slide templates
# ---------------------------------------------------------------------------

_TEMPLATES = {
    "hook": {
        "description": "Big number/stat hook — grabs attention with a shocking statistic",
        "html": """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;height:{h}px;background:{bg};display:flex;flex-direction:column;
align-items:center;justify-content:center;font-family:{font};color:#fff;padding:80px;text-align:center}}
.badge{{background:rgba(255,101,132,0.2);border:2px solid {accent};border-radius:50px;
padding:15px 40px;font-size:28px;color:{accent};margin-bottom:50px;letter-spacing:2px}}
.big{{font-size:140px;font-weight:900;margin:20px 0;
background:linear-gradient(90deg,{accent},{accent2});-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
h2{{font-size:48px;font-weight:300;line-height:1.4;opacity:0.9;margin-top:25px}}
.hl{{color:{primary};-webkit-text-fill-color:{primary};font-weight:700}}
</style></head><body>
<div class="badge">{badge}</div>
<div class="big">{title}</div>
<h2>{subtitle}<br><span class="hl">{highlight}</span></h2>
</body></html>""",
        "defaults": {"badge": "", "title": "200+", "subtitle": "", "highlight": ""},
    },
    "features": {
        "description": "Feature cards — 3 cards with icon + title + description",
        "html": """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;height:{h}px;background:{bg};display:flex;flex-direction:column;
align-items:center;justify-content:center;font-family:{font};color:#fff;padding:80px}}
h1{{font-size:64px;text-align:center;margin-bottom:50px;
background:linear-gradient(90deg,{primary},{accent});-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.card{{background:rgba(108,99,255,0.12);border:1px solid rgba(108,99,255,0.3);border-radius:24px;
padding:35px 45px;margin:12px 0;width:90%;display:flex;align-items:center;gap:25px}}
.icon{{font-size:48px}}.ct{{font-size:36px;font-weight:600}}
.cd{{font-size:28px;opacity:0.7;margin-top:6px}}
</style></head><body>
<h1>{title}</h1>
<div class="card"><span class="icon">{icon1}</span><div><div class="ct">{card1_title}</div><div class="cd">{card1_desc}</div></div></div>
<div class="card"><span class="icon">{icon2}</span><div><div class="ct">{card2_title}</div><div class="cd">{card2_desc}</div></div></div>
<div class="card"><span class="icon">{icon3}</span><div><div class="ct">{card3_title}</div><div class="cd">{card3_desc}</div></div></div>
</body></html>""",
        "defaults": {"icon1": "", "icon2": "", "icon3": "", "card1_title": "", "card1_desc": "", "card2_title": "", "card2_desc": "", "card3_title": "", "card3_desc": ""},
    },
    "cta": {
        "description": "Call-to-action — big headline + button + subtitle",
        "html": """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;height:{h}px;background:{bg};display:flex;flex-direction:column;
align-items:center;justify-content:center;font-family:{font};color:#fff;padding:80px;text-align:center}}
h1{{font-size:68px;font-weight:800;margin-bottom:30px;line-height:1.3}}
.glow{{background:linear-gradient(90deg,{primary},{accent});-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.btn{{background:linear-gradient(90deg,{primary},#8B5CF6);border-radius:50px;padding:30px 70px;
font-size:40px;color:#fff;font-weight:700;margin:40px 0;box-shadow:0 15px 40px rgba(108,99,255,0.4)}}
.sub{{font-size:30px;opacity:0.6;margin-top:15px}}
.logo{{font-size:32px;margin-top:50px;opacity:0.4;letter-spacing:4px}}
</style></head><body>
<h1>{title} <span class="glow">{title_glow}</span></h1>
<div class="btn">{button_text}</div>
<div class="sub">{subtitle}</div>
<div class="logo">{brand}</div>
</body></html>""",
        "defaults": {"title": "", "title_glow": "", "button_text": "", "subtitle": "", "brand": ""},
    },
    "comparison": {
        "description": "Before/After comparison — two columns with contrasting stats",
        "html": """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;height:{h}px;background:{bg};display:flex;flex-direction:column;
align-items:center;justify-content:center;font-family:{font};color:#fff;padding:80px;text-align:center}}
h1{{font-size:56px;margin-bottom:50px;opacity:0.9}}
.row{{display:flex;gap:30px;width:90%}}
.col{{flex:1;border-radius:24px;padding:40px 30px}}
.bad{{background:rgba(255,101,132,0.15);border:2px solid rgba(255,101,132,0.4)}}
.good{{background:rgba(108,99,255,0.15);border:2px solid rgba(108,99,255,0.4)}}
.num{{font-size:72px;font-weight:900;margin:15px 0}}
.bad .num{{color:{accent}}}.good .num{{color:{primary}}}
.label{{font-size:28px;opacity:0.8}}
h3{{font-size:32px;margin-bottom:20px}}
</style></head><body>
<h1>{title}</h1>
<div class="row">
<div class="col bad"><h3>{left_label}</h3><div class="num">{left_value}</div><div class="label">{left_desc}</div></div>
<div class="col good"><h3>{right_label}</h3><div class="num">{right_value}</div><div class="label">{right_desc}</div></div>
</div>
</body></html>""",
        "defaults": {"left_label": "", "left_value": "", "left_desc": "", "right_label": "", "right_value": "", "right_desc": ""},
    },
    "quote": {
        "description": "Testimonial/quote — large quote text with attribution",
        "html": """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;height:{h}px;background:{bg};display:flex;flex-direction:column;
align-items:center;justify-content:center;font-family:{font};color:#fff;padding:100px;text-align:center}}
.q{{font-size:120px;opacity:0.2;color:{primary};margin-bottom:-30px}}
blockquote{{font-size:46px;line-height:1.5;font-style:italic;opacity:0.9;margin:30px 0}}
.author{{font-size:30px;opacity:0.6;margin-top:30px}}
.role{{font-size:26px;opacity:0.4;margin-top:8px}}
</style></head><body>
<div class="q">"</div>
<blockquote>{quote_text}</blockquote>
<div class="author">— {author}</div>
<div class="role">{role}</div>
</body></html>""",
        "defaults": {"quote_text": "", "author": "", "role": ""},
    },
    "stats": {
        "description": "Statistics grid — 3 big metrics in a row",
        "html": """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;height:{h}px;background:{bg};display:flex;flex-direction:column;
align-items:center;justify-content:center;font-family:{font};color:#fff;padding:80px;text-align:center}}
h1{{font-size:56px;margin-bottom:60px;opacity:0.9}}
.grid{{display:flex;flex-direction:column;gap:30px;width:85%}}
.stat{{background:rgba(108,99,255,0.1);border:1px solid rgba(108,99,255,0.25);border-radius:20px;padding:35px}}
.val{{font-size:72px;font-weight:900;background:linear-gradient(90deg,{primary},{accent});
-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.lbl{{font-size:30px;opacity:0.7;margin-top:8px}}
</style></head><body>
<h1>{title}</h1>
<div class="grid">
<div class="stat"><div class="val">{stat1_value}</div><div class="lbl">{stat1_label}</div></div>
<div class="stat"><div class="val">{stat2_value}</div><div class="lbl">{stat2_label}</div></div>
<div class="stat"><div class="val">{stat3_value}</div><div class="lbl">{stat3_label}</div></div>
</div>
</body></html>""",
        "defaults": {"stat1_value": "", "stat1_label": "", "stat2_value": "", "stat2_label": "", "stat3_value": "", "stat3_label": ""},
    },
    "blank": {
        "description": "Blank dark slide — just title and subtitle on gradient background",
        "html": """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{w}px;height:{h}px;background:{bg};display:flex;flex-direction:column;
align-items:center;justify-content:center;font-family:{font};color:#fff;padding:100px;text-align:center}}
h1{{font-size:72px;font-weight:800;line-height:1.3;
background:linear-gradient(90deg,{primary},{accent});-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
p{{font-size:40px;margin-top:30px;opacity:0.8;line-height:1.5}}
</style></head><body>
<h1>{title}</h1>
<p>{subtitle}</p>
</body></html>""",
        "defaults": {"subtitle": ""},
    },
}

# Brand/style defaults
_STYLE_DEFAULTS = {
    "bg": "linear-gradient(135deg,#0a0a2e,#1a1a4e,#0d0d3a)",
    "primary": "#6C63FF",
    "accent": "#FF6584",
    "accent2": "#FF8E53",
    "font": "'Segoe UI',Helvetica,Arial,sans-serif",
    "w": 1080,
    "h": 1920,
}


def _render_template(template_id: str, fields: dict, style: dict | None = None) -> str:
    """Render a template to HTML string."""
    tmpl = _TEMPLATES[template_id]
    ctx = {**_STYLE_DEFAULTS}
    if style:
        ctx.update(style)
    merged_fields = {**tmpl["defaults"], **fields}
    ctx.update(merged_fields)
    return tmpl["html"].format(**ctx)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_encoder() -> str:
    try:
        from shared.platform import detect_ffmpeg_encoder
        return detect_ffmpeg_encoder()
    except Exception:
        return "libx264"


def _encoder_args(encoder: str) -> list[str]:
    if encoder == "libx264":
        return ["-preset", "fast", "-crf", "23"]
    elif encoder == "h264_videotoolbox":
        return ["-b:v", "4M"]
    elif encoder == "h264_nvenc":
        return ["-preset", "fast", "-b:v", "4M"]
    return []


def _out(filename: str) -> str:
    return str(Path(OUTPUT_DIR) / filename)


def _file_info(path: str) -> str:
    size = os.path.getsize(path)
    if size > 1024 * 1024:
        return f"{size / (1024*1024):.1f} MB"
    return f"{size / 1024:.0f} KB"


def _probe(file_path: str) -> dict:
    """Get media info via ffprobe."""
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", file_path],
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode != 0:
            return {}
        data = json.loads(proc.stdout)
        info: dict = {}
        fmt = data.get("format", {})
        if "duration" in fmt:
            info["duration"] = round(float(fmt["duration"]), 2)
        if "size" in fmt:
            info["size_bytes"] = int(fmt["size"])
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                info["width"] = s.get("width")
                info["height"] = s.get("height")
                info["video_codec"] = s.get("codec_name")
                info["fps"] = s.get("r_frame_rate")
            elif s.get("codec_type") == "audio":
                info["audio_codec"] = s.get("codec_name")
                info["sample_rate"] = s.get("sample_rate")
        return info
    except Exception:
        return {}


# ===========================================================================
# BATCH (the main workhorse — 1 call does everything)
# ===========================================================================

@mcp.tool()
def batch_slides(
    slides: list[dict],
    project_name: str = "video",
    duration_per_slide: float = 5.0,
    size: str = "1080x1920",
    fps: int = 30,
    style: dict | None = None,
) -> str:
    """Process multiple slides in one call: HTML/template → PNG screenshots → animated MP4 clips.

    This is the most efficient tool. One call produces all clips ready for merging.

    Each slide dict can be EITHER:
      - {"html": "<full html>"} — custom HTML content
      - {"html": "<full html>", "effect": "zoom_in"} — custom HTML + specific effect
      - {"template": "hook", "fields": {"title": "200+", ...}} — use built-in template
      - {"template": "hook", "fields": {...}, "effect": "pan_down"} — template + specific effect
      - {"image": "/path/to/existing.png"} — skip screenshot, just animate existing image
      - {"image": "/path/to/existing.png", "effect": "zoom_out"} — existing image + effect

    Args:
        slides: List of slide dicts. See above for format.
        project_name: Prefix for output files (e.g. "trinity" → trinity_01.png, trinity_01.mp4).
        duration_per_slide: Seconds per slide animation.
        size: Resolution as "WxH".
        fps: Frames per second.
        style: Optional brand/style overrides for templates:
               {"bg": "linear-gradient(...)", "primary": "#color", "accent": "#color",
                "font": "font-family", "w": 1080, "h": 1920}

    Returns:
        Summary with paths to all PNGs and MP4 clips, ready for merge_clips or merge_clips_crossfade.
    """
    from poster.core import screenshot_sync
    from vidmake.core import _animate_single_slide

    if not slides:
        return "Error: No slides provided."

    # Parse size
    try:
        w, h = size.lower().split("x")
        w_int, h_int = int(w), int(h)
    except Exception:
        w_int, h_int = 1080, 1920

    encoder = _detect_encoder()
    results: list[str] = []
    clip_paths: list[str] = []
    png_paths: list[str] = []

    for i, slide in enumerate(slides):
        idx = f"{i+1:02d}"
        png_path = _out(f"{project_name}_{idx}.png")
        mp4_path = _out(f"{project_name}_{idx}.mp4")

        # Determine effect
        effect = slide.get("effect", AVAILABLE_EFFECTS[i % len(AVAILABLE_EFFECTS)])
        if effect not in AVAILABLE_EFFECTS:
            effect = AVAILABLE_EFFECTS[i % len(AVAILABLE_EFFECTS)]

        # Step A: Get PNG (screenshot or existing image)
        if "image" in slide:
            # Use existing image
            img_path = slide["image"]
            if not Path(img_path).exists():
                results.append(f"  Slide {idx}: ERROR - image not found: {img_path}")
                continue
            png_path = img_path  # use as-is
            results.append(f"  Slide {idx}: existing image")
        else:
            # Generate HTML
            if "template" in slide:
                template_id = slide["template"]
                if template_id not in _TEMPLATES:
                    results.append(f"  Slide {idx}: ERROR - unknown template '{template_id}'")
                    continue
                fields = slide.get("fields", {})
                html = _render_template(template_id, fields, style)
            elif "html" in slide:
                html = slide["html"]
            else:
                results.append(f"  Slide {idx}: ERROR - need 'html', 'template', or 'image'")
                continue

            # Screenshot
            try:
                screenshot_sync(html, png_path, width=w_int, height=h_int)
                results.append(f"  Slide {idx}: screenshot OK ({_file_info(png_path)})")
            except Exception as exc:
                results.append(f"  Slide {idx}: screenshot ERROR - {exc}")
                continue

        png_paths.append(png_path)

        # Step B: Animate
        result = _animate_single_slide(
            image_path=png_path, output_path=mp4_path, effect=effect,
            duration=duration_per_slide, size=size, fps=fps, encoder=encoder,
        )
        if result["success"]:
            results.append(f"           → {effect} → {_file_info(mp4_path)}")
            clip_paths.append(mp4_path)
        else:
            results.append(f"           → animate ERROR: {result['error']}")

    # Summary
    clip_list_str = "\n".join(f"  {p}" for p in clip_paths)
    return (
        f"Batch complete: {len(clip_paths)}/{len(slides)} slides\n\n"
        f"Details:\n" + "\n".join(results) + "\n\n"
        f"Clip paths (use with merge_clips or merge_clips_crossfade):\n{clip_list_str}"
    )


# ===========================================================================
# TEMPLATE
# ===========================================================================

@mcp.tool()
def create_slide(
    template: str,
    fields: dict,
    filename: str = "slide.png",
    style: dict | None = None,
    size: str = "1080x1920",
) -> str:
    """Create a slide from a built-in template — no HTML writing needed.

    Templates: hook, features, cta, comparison, quote, stats, blank.
    Use list_templates to see all templates with their fields.

    Args:
        template: Template name (e.g. "hook", "features", "cta").
        fields: Template-specific fields as dict. See list_templates for each template's fields.
        filename: Output PNG filename. Saved to output directory.
        style: Optional brand overrides: {"bg": "...", "primary": "#...", "accent": "#...",
               "font": "...", "w": 1080, "h": 1920}.
        size: Resolution as "WxH" (only used for Playwright viewport, template uses style.w/h).

    Returns:
        Path to saved PNG.
    """
    if template not in _TEMPLATES:
        avail = ", ".join(_TEMPLATES.keys())
        return f"Error: Unknown template '{template}'. Available: {avail}"

    from poster.core import screenshot_sync

    try:
        w, h = size.lower().split("x")
        w_int, h_int = int(w), int(h)
    except Exception:
        w_int, h_int = 1080, 1920

    html = _render_template(template, fields, style)
    out_path = _out(filename)

    try:
        screenshot_sync(html, out_path, width=w_int, height=h_int)
    except Exception as exc:
        return f"Error: {exc}"

    return f"{out_path} ({_file_info(out_path)}, template: {template})"


# ===========================================================================
# ATOMIC — screenshot & animate (kept for full control)
# ===========================================================================

@mcp.tool()
def screenshot_html(
    html_content: str,
    filename: str = "slide.png",
    width: int = 1080,
    height: int = 1920,
) -> str:
    """Render HTML to PNG screenshot via headless Chromium (Playwright).

    Args:
        html_content: Full HTML document string.
        filename: Output filename. Saved to output directory.
        width: Viewport width. Default 1080.
        height: Viewport height. Default 1920.

    Returns:
        Path and file size.
    """
    from poster.core import screenshot_sync
    out_path = _out(filename)
    screenshot_sync(html_content, out_path, width=width, height=height)
    return f"{out_path} ({_file_info(out_path)}, {width}x{height})"


@mcp.tool()
def animate_image(
    image_path: str,
    effect: str = "zoom_in",
    duration: float = 5.0,
    output_filename: str = "clip.mp4",
    size: str = "1080x1920",
    fps: int = 30,
) -> str:
    """Apply Ken Burns animation to a single image → MP4 clip.

    Effects: zoom_in, zoom_out, pan_right, pan_down, zoom_topleft.

    Args:
        image_path: Absolute path to input PNG/JPG.
        effect: Animation effect.
        duration: Clip duration in seconds.
        output_filename: Output filename.
        size: Resolution as "WxH".
        fps: Frames per second.

    Returns:
        Path and info.
    """
    from vidmake.core import _animate_single_slide

    if effect not in AVAILABLE_EFFECTS:
        return f"Error: Invalid effect '{effect}'. Choose from: {', '.join(AVAILABLE_EFFECTS)}"
    if not Path(image_path).exists():
        return f"Error: File not found: {image_path}"

    out_path = _out(output_filename)
    result = _animate_single_slide(
        image_path=image_path, output_path=out_path, effect=effect,
        duration=duration, size=size, fps=fps, encoder=_detect_encoder(),
    )
    if result["success"]:
        return f"{out_path} ({_file_info(out_path)}, {duration}s, {effect})"
    return f"Error: {result['error']}"


# ===========================================================================
# ASSEMBLY
# ===========================================================================

@mcp.tool()
def merge_clips(
    clip_paths: list[str],
    output_filename: str = "merged.mp4",
) -> str:
    """Concatenate MP4 clips into a single video (no transitions).

    Args:
        clip_paths: Ordered list of absolute paths to MP4 clips.
        output_filename: Output filename.

    Returns:
        Path and duration.
    """
    for p in clip_paths:
        if not Path(p).exists():
            return f"Error: File not found: {p}"

    list_file = tempfile.mktemp(suffix=".txt")
    with open(list_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{p}'\n")

    out_path = _out(output_filename)
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    os.unlink(list_file)

    if proc.returncode != 0:
        return f"Error: {(proc.stderr or '')[-500:]}"

    info = _probe(out_path)
    return f"{out_path} ({_file_info(out_path)}, {info.get('duration', '?')}s, {len(clip_paths)} clips)"


@mcp.tool()
def merge_clips_crossfade(
    clip_paths: list[str],
    crossfade_duration: float = 0.5,
    output_filename: str = "merged.mp4",
) -> str:
    """Concatenate clips with crossfade transitions between them.

    Args:
        clip_paths: Ordered list of absolute paths to MP4 clips (min 2).
        crossfade_duration: Crossfade duration in seconds (0.1 - 2.0).
        output_filename: Output filename.

    Returns:
        Path and duration.
    """
    if len(clip_paths) < 2:
        return "Error: Need at least 2 clips for crossfade."

    for p in clip_paths:
        if not Path(p).exists():
            return f"Error: File not found: {p}"

    crossfade_duration = max(0.1, min(crossfade_duration, 2.0))
    n = len(clip_paths)

    # Probe durations
    durations = []
    for p in clip_paths:
        info = _probe(p)
        durations.append(float(info.get("duration", 5.0)))

    # Build xfade filter chain
    filter_parts = []
    prev = "[0:v]"
    accumulated_offset = 0.0
    for i in range(1, n):
        accumulated_offset += durations[i - 1] - crossfade_duration
        out_label = f"[v{i}]" if i < n - 1 else "[vout]"
        filter_parts.append(
            f"{prev}[{i}:v]xfade=transition=fade:duration={crossfade_duration}:offset={accumulated_offset:.4f}{out_label}"
        )
        prev = out_label

    encoder = _detect_encoder()
    out_path = _out(output_filename)

    cmd = ["ffmpeg", "-y"]
    for p in clip_paths:
        cmd += ["-i", p]
    cmd += [
        "-filter_complex", ";".join(filter_parts),
        "-map", "[vout]", "-c:v", encoder, *_encoder_args(encoder),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        return f"Error: {(proc.stderr or '')[-500:]}"

    info = _probe(out_path)
    return f"{out_path} ({_file_info(out_path)}, {info.get('duration', '?')}s, {n} clips, crossfade {crossfade_duration}s)"


@mcp.tool()
def add_audio(
    video_path: str,
    audio_path: str,
    output_filename: str = "with_audio.mp4",
    audio_volume: float = 1.0,
    fade_out_duration: float = 0.0,
) -> str:
    """Add background music/audio to a video. Video stream is copied (no re-encode).

    Args:
        video_path: Absolute path to input MP4.
        audio_path: Absolute path to audio file (MP3/WAV).
        output_filename: Output filename.
        audio_volume: Volume multiplier (0.5 = half, 1.0 = normal, 2.0 = double).
        fade_out_duration: Fade out audio at end (seconds). 0 = no fade.

    Returns:
        Path and info.
    """
    if not Path(video_path).exists():
        return f"Error: Video not found: {video_path}"
    if not Path(audio_path).exists():
        return f"Error: Audio not found: {audio_path}"

    out_path = _out(output_filename)
    afilters = []
    if audio_volume != 1.0:
        afilters.append(f"volume={audio_volume}")
    if fade_out_duration > 0:
        v_dur = float(_probe(video_path).get("duration", 30))
        afilters.append(f"afade=t=out:st={max(0, v_dur - fade_out_duration):.2f}:d={fade_out_duration:.2f}")

    cmd = ["ffmpeg", "-y", "-i", video_path, "-i", audio_path]
    if afilters:
        cmd += ["-af", ",".join(afilters)]
    cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-map", "0:v:0", "-map", "1:a:0", "-movflags", "+faststart", out_path]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        return f"Error: {(proc.stderr or '')[-500:]}"
    return f"{out_path} ({_file_info(out_path)})"


# ===========================================================================
# POST-PROCESSING
# ===========================================================================

@mcp.tool()
def add_text_overlay(
    video_path: str,
    text: str,
    output_filename: str = "with_text.mp4",
    position: str = "bottom-center",
    font_size: int = 36,
    font_color: str = "white",
    bg_color: str = "rgba(0,0,0,0.5)",
    start_time: float = 0.0,
    end_time: float = 0.0,
) -> str:
    """Burn text overlay/watermark onto a video. Uses Playwright for text rendering.

    Args:
        video_path: Absolute path to input MP4.
        text: Text to display. Supports <br> for line breaks.
        output_filename: Output filename.
        position: top-left, top-center, top-right, center, bottom-left, bottom-center, bottom-right.
        font_size: Font size in pixels.
        font_color: CSS color (e.g. "white", "#FF6584").
        bg_color: CSS background (e.g. "rgba(0,0,0,0.5)", "transparent").
        start_time: Show text from this time (seconds). 0 = start.
        end_time: Hide text after this time (seconds). 0 = end.

    Returns:
        Path and info.
    """
    if not Path(video_path).exists():
        return f"Error: Video not found: {video_path}"

    v_info = _probe(video_path)
    v_w = v_info.get("width", 1080)

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{v_w}px;height:120px;background:transparent;display:flex;align-items:center;
justify-content:center;font-family:'Segoe UI',Helvetica,Arial,sans-serif}}
.t{{font-size:{font_size}px;color:{font_color};padding:12px 30px;
background:{bg_color};border-radius:8px;letter-spacing:1px;white-space:nowrap}}
</style></head><body><div class="t">{text}</div></body></html>"""

    from poster.core import screenshot_sync
    png_tmp = tempfile.mktemp(suffix="_overlay.png")
    try:
        screenshot_sync(html, png_tmp, width=v_w, height=120)
    except Exception as exc:
        return f"Error rendering text: {exc}"

    positions = {
        "top-left": "10:10", "top-center": "(W-w)/2:10", "top-right": "W-w-10:10",
        "center": "(W-w)/2:(H-h)/2",
        "bottom-left": "10:H-h-40", "bottom-center": "(W-w)/2:H-h-40", "bottom-right": "W-w-10:H-h-40",
    }
    overlay_pos = positions.get(position, positions["bottom-center"])

    enable = ""
    if start_time > 0 or end_time > 0:
        enable = f":enable='between(t,{start_time},{end_time})'" if end_time > 0 else f":enable='gte(t,{start_time})'"

    encoder = _detect_encoder()
    out_path = _out(output_filename)
    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-i", png_tmp,
        "-filter_complex", f"[0:v][1:v]overlay={overlay_pos}{enable}",
        "-c:v", encoder, *_encoder_args(encoder), "-c:a", "copy",
        "-movflags", "+faststart", out_path,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    os.unlink(png_tmp)
    if proc.returncode != 0:
        return f"Error: {(proc.stderr or '')[-500:]}"
    return f"{out_path} ({_file_info(out_path)})"


@mcp.tool()
def resize_video(
    video_path: str,
    size: str = "1080x1920",
    mode: str = "pad",
    output_filename: str = "resized.mp4",
    bg_color: str = "black",
) -> str:
    """Resize/crop/pad video to new resolution.

    Args:
        video_path: Absolute path to input video.
        size: Target "WxH".
        mode: "pad" (letterbox), "crop" (fill+crop), "stretch" (distort).
        output_filename: Output filename.
        bg_color: Padding color for pad mode.

    Returns:
        Path and info.
    """
    if not Path(video_path).exists():
        return f"Error: Video not found: {video_path}"
    try:
        w, h = size.lower().split("x")
        w, h = int(w), int(h)
    except Exception:
        return f"Error: Invalid size '{size}'."

    filters = {
        "pad": f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={bg_color},setsar=1",
        "crop": f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1",
        "stretch": f"scale={w}:{h},setsar=1",
    }
    vf = filters.get(mode)
    if not vf:
        return f"Error: Invalid mode '{mode}'. Choose: pad, crop, stretch."

    encoder = _detect_encoder()
    out_path = _out(output_filename)
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf,
           "-c:v", encoder, *_encoder_args(encoder), "-c:a", "copy",
           "-movflags", "+faststart", out_path]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        return f"Error: {(proc.stderr or '')[-500:]}"
    return f"{out_path} ({_file_info(out_path)}, {w}x{h}, {mode})"


# ===========================================================================
# UTILITY
# ===========================================================================

@mcp.tool()
def get_media_info(file_path: str) -> str:
    """Probe a media file for duration, resolution, codec, fps, size.

    Args:
        file_path: Absolute path to file.
    """
    if not Path(file_path).exists():
        return f"Error: File not found: {file_path}"
    info = _probe(file_path)
    if not info:
        return f"Error: Could not probe: {file_path}"
    lines = [f"File: {file_path}"]
    for k, label in [("size_bytes", None), ("duration", "Duration"), ("width", None),
                      ("video_codec", "Video"), ("fps", "FPS"), ("audio_codec", "Audio")]:
        if k == "size_bytes" and k in info:
            lines.append(f"  Size: {_file_info(file_path)}")
        elif k == "width" and "width" in info:
            lines.append(f"  Resolution: {info['width']}x{info.get('height', '?')}")
        elif k in info and label:
            lines.append(f"  {label}: {info[k]}")
    return "\n".join(lines)


@mcp.tool()
def list_effects() -> str:
    """List all available Ken Burns animation effects."""
    descs = {
        "zoom_in": "Classic Ken Burns — slowly zoom into center",
        "zoom_out": "Start zoomed, slowly zoom out to reveal full image",
        "pan_right": "Slowly pan from left to right",
        "pan_down": "Slowly pan top to bottom (great for vertical)",
        "zoom_topleft": "Zoom into top-left area",
    }
    lines = [f"Available effects:"] + [f"  {e}: {d}" for e, d in descs.items()]
    lines.append(f"\nOutput directory: {OUTPUT_DIR}")
    return "\n".join(lines)


@mcp.tool()
def list_templates() -> str:
    """List all available slide templates with their fields.

    Use these with create_slide or batch_slides (template mode).
    """
    lines = ["Available slide templates:\n"]
    for tid, tmpl in _TEMPLATES.items():
        fields = list(tmpl["defaults"].keys())
        lines.append(f"  {tid}: {tmpl['description']}")
        lines.append(f"    fields: {', '.join(fields)}")
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def list_outputs() -> str:
    """List all files in the output directory."""
    out_dir = Path(OUTPUT_DIR)
    files = sorted(f for f in out_dir.iterdir() if f.is_file())
    if not files:
        return f"Output directory empty: {OUTPUT_DIR}"
    lines = [f"Output: {OUTPUT_DIR}\n"]
    total = 0
    for f in files:
        s = f.stat().st_size
        total += s
        lines.append(f"  {f.name} ({_file_info(str(f))})")
    lines.append(f"\nTotal: {len(files)} files, {total / (1024*1024):.1f} MB")
    return "\n".join(lines)


@mcp.tool()
def cleanup_outputs(pattern: str = "*") -> str:
    """Delete files from output directory.

    Args:
        pattern: Glob pattern. "*" = all, "*.mp4" = videos only, "clip_*" = clips.
    """
    deleted = 0
    for f in Path(OUTPUT_DIR).glob(pattern):
        if f.is_file():
            f.unlink()
            deleted += 1
    return f"Deleted {deleted} files matching '{pattern}'"


# ===========================================================================
# MCP PROMPTS — guide AI on common workflows
# ===========================================================================

@mcp.prompt()
def tiktok_video(topic: str, num_slides: int = 5) -> str:
    """Generate a TikTok marketing video for a given topic.

    Creates a structured prompt that guides the AI to use batch_slides
    and merge_clips_crossfade for efficient video creation.
    """
    return (
        f"Create a {num_slides}-slide TikTok video about: {topic}\n\n"
        f"Use the vidmake MCP tools:\n"
        f"1. Call batch_slides with {num_slides} slides using templates:\n"
        f"   - Slide 1: 'hook' template (attention-grabbing stat)\n"
        f"   - Slides 2-{num_slides-1}: 'features', 'comparison', 'stats', or 'quote'\n"
        f"   - Slide {num_slides}: 'cta' template (call to action)\n"
        f"2. Call merge_clips_crossfade with the clip paths from step 1\n"
        f"3. (Optional) Call add_text_overlay for branding\n\n"
        f"Style: dark gradient background, bold colors, large text for mobile.\n"
        f"Duration: 5s per slide, 0.5s crossfade.\n"
        f"Resolution: 1080x1920 (TikTok portrait 9:16)."
    )


@mcp.prompt()
def product_showcase(product_name: str, features: str) -> str:
    """Create a product showcase video."""
    return (
        f"Create a product showcase video for: {product_name}\n"
        f"Features: {features}\n\n"
        f"Use batch_slides with:\n"
        f"  Slide 1: 'hook' — teaser with a bold claim\n"
        f"  Slide 2: 'features' — top 3 features with icons\n"
        f"  Slide 3: 'stats' — key metrics/numbers\n"
        f"  Slide 4: 'quote' — testimonial\n"
        f"  Slide 5: 'cta' — call to action\n"
        f"Then merge_clips_crossfade + add_text_overlay for brand watermark."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
