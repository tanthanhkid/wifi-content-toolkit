"""
mcp_server.py — Video Pipeline MCP Server (v3).

Designed to minimize AI round-trips while keeping full customization.

  BATCH (1 tool call = multiple slides):
    1. batch_slides        — HTML[] → PNG[] → MP4 clips[] (screenshot + animate in one call)
                             Supports "animated": true for CSS animation recording

  TEMPLATE (zero HTML needed):
    2. create_slide         — Template-based slide: just pass title/body/style → PNG

  ATOMIC (per-file control):
    3. screenshot_html      — HTML → PNG
    4. animate_image        — PNG → MP4 clip (Ken Burns)
    5. record_html_video    — HTML + CSS animations → MP4 (Playwright video recording)

  ASSEMBLY:
    6. merge_clips          — Concat clips → MP4
    7. merge_clips_crossfade— Concat with crossfade
    8. add_audio            — Video + music → MP4

  AUDIO MIXING:
    9. mix_voiceover_music  — Video + voice + music with auto-ducking (sidechaincompress)
   10. list_music           — List available background music tracks

  POST-PROCESSING:
   11. add_text_overlay     — Text/watermark onto video
   12. resize_video         — Resize/crop/pad
   13. add_facecam          — Overlay facecam with rounded corners (auto-loop)

  VOICEOVER (ElevenLabs TTS):
   14. generate_voiceover   — Text → MP3 with context-aware voice
   15. generate_slide_narrations — Batch: all slide scripts → MP3s + merged audio
   16. list_voices          — Available ElevenLabs voices

  STICKERS:
   17. list_stickers        — Browse animated SVG stickers (CapCut/Canva-style)

  UTILITY:
   18. get_media_info       — Probe file info
   19. list_effects         — Available animation effects
   20. list_templates       — Available slide templates
   21. list_outputs         — Files in output dir
   22. cleanup_outputs      — Delete output files

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
        "Video Pipeline MCP Server — create TikTok-style videos with Ken Burns animations + AI voiceover.\n\n"
        "FASTEST workflow (4 tool calls for video + voice + music with auto-ducking):\n"
        "  1. batch_slides — PNGs + animated clips (Ken Burns or CSS animation recording)\n"
        "  2. generate_slide_narrations — context-aware voiceover MP3\n"
        "  3. merge_clips_crossfade — join clips (no audio)\n"
        "  4. mix_voiceover_music — voice + music with auto-ducking in one step\n\n"
        "FASTEST workflow (3 tool calls, voice only, no music):\n"
        "  1. batch_slides → PNGs + animated clips\n"
        "  2. generate_slide_narrations → voiceover MP3\n"
        "  3. merge_clips_crossfade → join clips, then add_audio with voiceover\n\n"
        "CSS ANIMATIONS: Use {\"html\": \"<html with @keyframes>\", \"animated\": true}\n"
        "  in batch_slides for CapCut-style text animations (fadeIn, slideUp, bounce, etc.).\n"
        "  Or use record_html_video for single animated slides.\n\n"
        "SMART AUDIO: mix_voiceover_music combines voice + background music with\n"
        "  automatic ducking — music ducks when voice speaks, rises during transitions.\n"
        "  Use list_music to browse available background tracks.\n\n"
        "STICKERS: Use list_stickers to browse 25+ animated SVG stickers (CapCut/Canva-style).\n"
        "  Replace static emoji icons with vivid animated stickers in slides.\n"
        "  Use shared.stickers module to embed stickers in custom HTML.\n\n"
        "All output → ~/vidmake-output/\n"
        "Effects: zoom_in, zoom_out, pan_right, pan_down, zoom_topleft"
    ),
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OUTPUT_DIR = os.environ.get("VIDMAKE_OUTPUT_DIR", os.path.expanduser("~/vidmake-output"))
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Music library directory (relative to project root)
MUSIC_DIR = os.environ.get(
    "VIDMAKE_MUSIC_DIR",
    str(Path(__file__).resolve().parent.parent / "music"),
)

AVAILABLE_EFFECTS = ["zoom_in", "zoom_out", "pan_right", "pan_down", "zoom_topleft"]

# ---------------------------------------------------------------------------
# ElevenLabs TTS config
# ---------------------------------------------------------------------------

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")

# Voice presets mapped to video context/mood.
# Each preset tunes stability, similarity_boost, style, and speed to match
# the emotional tone of the content.
#
# stability: 0=expressive/variable, 1=stable/monotone
# similarity_boost: voice similarity fidelity
# style: 0=neutral, 1=highly expressive (only for v2+ models)
# speed: speaking rate multiplier (0.7=slow, 1.0=normal, 1.3=fast)
_VOICE_PRESETS: dict[str, dict] = {
    "energetic": {
        "description": "High energy, excited — great for hooks, teasers, social media openers",
        "stability": 0.30,
        "similarity_boost": 0.75,
        "style": 0.80,
        "speed": 1.10,
    },
    "informative": {
        "description": "Clear, professional — for features, explanations, tutorials",
        "stability": 0.60,
        "similarity_boost": 0.80,
        "style": 0.35,
        "speed": 0.95,
    },
    "persuasive": {
        "description": "Urgent, confident — for CTAs, sales pitches, promotions",
        "stability": 0.40,
        "similarity_boost": 0.75,
        "style": 0.70,
        "speed": 1.05,
    },
    "warm": {
        "description": "Friendly, authentic — for quotes, testimonials, stories",
        "stability": 0.65,
        "similarity_boost": 0.80,
        "style": 0.55,
        "speed": 0.90,
    },
    "authoritative": {
        "description": "Commanding, impressive — for stats, data, achievements",
        "stability": 0.55,
        "similarity_boost": 0.80,
        "style": 0.45,
        "speed": 0.95,
    },
    "dramatic": {
        "description": "Intense, building tension — for comparisons, before/after reveals",
        "stability": 0.35,
        "similarity_boost": 0.75,
        "style": 0.75,
        "speed": 0.90,
    },
    "neutral": {
        "description": "Balanced, natural — default for any content",
        "stability": 0.50,
        "similarity_boost": 0.75,
        "style": 0.45,
        "speed": 1.00,
    },
}

# Map slide template types to the best voice preset
_TEMPLATE_TO_PRESET: dict[str, str] = {
    "hook": "energetic",
    "features": "informative",
    "cta": "persuasive",
    "comparison": "dramatic",
    "quote": "warm",
    "stats": "authoritative",
    "blank": "neutral",
}

# Default voice recommendations per language
_DEFAULT_VOICES: dict[str, dict] = {
    "vi": {"name": "Tuyết - Nữ miền Nam (Crisp, Professional)", "id": "xPEfmymXC4WdBxGMznS7"},
    "en": {"name": "Liam - Energetic, Social Media Creator", "id": "TX3LPaxmHKxFdv7VOQHJ"},
}


def _get_elevenlabs_client():
    """Get ElevenLabs client, raising clear error if no API key."""
    api_key = ELEVENLABS_API_KEY
    if not api_key:
        raise ValueError(
            "ELEVENLABS_API_KEY not set. "
            "Set it as environment variable or pass via MCP config."
        )
    from elevenlabs.client import ElevenLabs
    return ElevenLabs(api_key=api_key)


def _get_voice_settings(preset_name: str, overrides: dict | None = None) -> dict:
    """Build voice settings from preset + optional overrides."""
    preset = _VOICE_PRESETS.get(preset_name, _VOICE_PRESETS["neutral"])
    settings = {
        "stability": preset["stability"],
        "similarity_boost": preset["similarity_boost"],
        "style": preset["style"],
    }
    if overrides:
        settings.update({k: v for k, v in overrides.items() if k in settings})
    return settings


def _tts_generate(
    text: str,
    voice_id: str,
    output_path: str,
    preset: str = "neutral",
    model_id: str = "eleven_v3",
    speed: float | None = None,
    voice_overrides: dict | None = None,
) -> dict:
    """Core TTS generation. Returns {"success": bool, "path": str, "error": str}."""
    try:
        client = _get_elevenlabs_client()
        from elevenlabs import VoiceSettings

        settings = _get_voice_settings(preset, voice_overrides)
        preset_data = _VOICE_PRESETS.get(preset, _VOICE_PRESETS["neutral"])
        actual_speed = speed if speed is not None else preset_data.get("speed", 1.0)

        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            voice_settings=VoiceSettings(
                stability=settings["stability"],
                similarity_boost=settings["similarity_boost"],
                style=settings["style"],
                use_speaker_boost=True,
                speed=actual_speed,
            ),
            output_format="mp3_44100_128",
        )

        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        return {"success": True, "path": output_path}
    except Exception as exc:
        return {"success": False, "path": output_path, "error": str(exc)}


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
    """Detect best H.264 encoder for simple operations."""
    try:
        from shared.platform import detect_ffmpeg_encoder
        return detect_ffmpeg_encoder()
    except Exception:
        return "libx264"


def _detect_encoder_for_filter() -> str:
    """Detect encoder safe for filter_complex operations.

    h264_mf hangs on complex filter_complex pipelines, so we fall back
    to libx264 for xfade, overlay, geq, etc.
    """
    try:
        from shared.platform import detect_ffmpeg_encoder_for_filter
        return detect_ffmpeg_encoder_for_filter()
    except Exception:
        return "libx264"


def _encoder_args(encoder: str) -> list[str]:
    if encoder == "libx264":
        return ["-preset", "fast", "-crf", "23"]
    elif encoder == "h264_videotoolbox":
        return ["-b:v", "4M"]
    elif encoder == "h264_nvenc":
        return ["-preset", "fast", "-b:v", "4M"]
    elif encoder == "h264_mf":
        return ["-b:v", "4M"]
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
      - {"html": "<full html>"} — custom HTML content (Ken Burns animation)
      - {"html": "<full html>", "effect": "zoom_in"} — custom HTML + specific effect
      - {"html": "<full html>", "animated": true} — CSS animation recording (text flies in, fades, bounces)
      - {"html": "<full html>", "animated": true, "duration": 6.0} — animated + custom duration
      - {"template": "hook", "fields": {"title": "200+", ...}} — use built-in template
      - {"template": "hook", "fields": {...}, "effect": "pan_down"} — template + specific effect
      - {"image": "/path/to/existing.png"} — skip screenshot, just animate existing image
      - {"image": "/path/to/existing.png", "effect": "zoom_out"} — existing image + effect

    When "animated" is true, the HTML is rendered in a browser with Playwright video
    recording, capturing CSS @keyframes animations directly. No Ken Burns effect is applied.
    Use this for CapCut/PowerPoint-style text animations: fadeIn, slideUp, bounce, typewriter, etc.

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
    from vidmake.core import _animate_single_slide, record_html_video, batch_record_html_videos

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

    # --- Phase 1: Batch all animated slides (single browser launch) ---
    animated_jobs = []  # (original_index, slide_dict, mp4_path)
    for i, slide in enumerate(slides):
        if slide.get("animated"):
            idx = f"{i+1:02d}"
            mp4_path = _out(f"{project_name}_{idx}.mp4")
            if "html" in slide:
                html = slide["html"]
            elif "template" in slide:
                template_id = slide["template"]
                if template_id not in _TEMPLATES:
                    continue
                fields = slide.get("fields", {})
                html = _render_template(template_id, fields, style)
            else:
                continue
            slide_duration = slide.get("duration", duration_per_slide)
            animated_jobs.append((i, html, mp4_path, slide_duration))

    # Record all animated slides with ONE browser
    animated_results = {}
    if animated_jobs:
        batch_input = [
            {"html": html, "output_path": mp4, "width": w_int, "height": h_int, "duration": dur}
            for _, html, mp4, dur in animated_jobs
        ]
        batch_out = batch_record_html_videos(batch_input, encoder=encoder, fps=fps)
        for job, res in zip(animated_jobs, batch_out):
            animated_results[job[0]] = (res, job[2], job[3])

    # --- Phase 2: Process all slides in order ---
    for i, slide in enumerate(slides):
        idx = f"{i+1:02d}"
        png_path = _out(f"{project_name}_{idx}.png")
        mp4_path = _out(f"{project_name}_{idx}.mp4")

        # --- CSS Animation: use pre-computed results ---
        if slide.get("animated"):
            if i in animated_results:
                res, mp4_path, slide_duration = animated_results[i]
                if res["success"]:
                    results.append(f"  Slide {idx}: CSS animated → {slide_duration}s → {_file_info(mp4_path)}")
                    clip_paths.append(mp4_path)
                else:
                    results.append(f"  Slide {idx}: animated ERROR - {res['error']}")
            else:
                results.append(f"  Slide {idx}: animated ERROR - invalid slide config")
            continue

        # --- Static path: screenshot → Ken Burns ---

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

        # Step B: Animate (Ken Burns)
        slide_duration = slide.get("duration", duration_per_slide)
        result = _animate_single_slide(
            image_path=png_path, output_path=mp4_path, effect=effect,
            duration=slide_duration, size=size, fps=fps, encoder=encoder,
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


@mcp.tool()
def record_html_video(
    html_content: str,
    filename: str = "animated.mp4",
    width: int = 1080,
    height: int = 1920,
    duration: float = 5.0,
    fps: int = 30,
) -> str:
    """Record HTML with CSS animations → MP4 via Playwright video recording.

    Instead of screenshotting a static image, this records the browser playing
    CSS @keyframes animations in real-time. Use for CapCut/PowerPoint-style
    text animations: fadeIn, slideUp, bounce, typewriter, stagger, etc.

    For static slides (no CSS animation), use screenshot_html + animate_image instead.

    Args:
        html_content: Full HTML document with CSS @keyframes animations.
            Must include animation-fill-mode: both on all animated elements.
        filename: Output MP4 filename. Saved to output directory.
        width: Viewport width. Default 1080.
        height: Viewport height. Default 1920.
        duration: Recording duration in seconds. Must cover all animations. Default 5.0.
        fps: Frames per second. Default 30.

    Returns:
        Path and info.
    """
    from vidmake.core import record_html_video as _record

    out_path = _out(filename)
    result = _record(
        html_content=html_content,
        output_path=out_path,
        width=width,
        height=height,
        duration=duration,
        fps=fps,
        encoder=_detect_encoder(),
    )
    if result["success"]:
        return f"{out_path} ({_file_info(out_path)}, {duration}s, CSS animated)"
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

    encoder = _detect_encoder_for_filter()
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
# AUDIO MIXING — smart ducking
# ===========================================================================


@mcp.tool()
def list_music() -> str:
    """List available background music tracks from the music/ folder with durations.

    Returns:
        List of music files with names and durations.
    """
    music_dir = Path(MUSIC_DIR)
    if not music_dir.exists():
        return f"Error: Music directory not found: {MUSIC_DIR}"

    tracks: list[dict] = []
    for f in sorted(music_dir.iterdir()):
        if f.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg", ".flac"}:
            info = _probe(str(f))
            duration = info.get("duration", 0)
            tracks.append({
                "name": f.stem,
                "file": str(f),
                "duration": duration,
                "duration_display": f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "?",
            })

    if not tracks:
        return f"No music files found in {MUSIC_DIR}"

    lines = [f"Found {len(tracks)} tracks in {MUSIC_DIR}:\n"]
    for t in tracks:
        lines.append(f"  {t['duration_display']}  {t['name']}")
    lines.append(f"\nUse the 'file' path with mix_voiceover_music(music_path=...)")

    return "\n".join(lines) + "\n\n" + json.dumps(tracks, ensure_ascii=False)


@mcp.tool()
def mix_voiceover_music(
    video_path: str,
    voiceover_path: str,
    music_path: str,
    output_filename: str = "mixed_audio.mp4",
    music_volume: float = 0.15,
    voice_volume: float = 1.0,
    duck_level: float = 0.1,
    fade_out: float = 2.0,
) -> str:
    """Combine video + voiceover + background music in one step with automatic ducking.

    Uses FFmpeg sidechaincompress so music automatically ducks when voice is
    speaking and returns to normal volume during silent transitions.

    Replaces the 2-step process of add_audio(voice) → add_audio(music).

    Args:
        video_path: Absolute path to input MP4 (merged clips, no audio).
        voiceover_path: Absolute path to voiceover MP3.
        music_path: Absolute path to background music MP3. Use list_music to browse available tracks.
        output_filename: Output filename.
        music_volume: Base music volume before ducking (0.0-2.0, default 0.15).
        voice_volume: Voiceover volume (0.0-2.0, default 1.0).
        duck_level: How aggressively to duck music (0.01-1.0, lower = more ducking, default 0.1).
        fade_out: Fade out music at end (seconds, default 2.0). 0 = no fade.

    Returns:
        Path and info.
    """
    from vidmake.core import mix_audio_with_ducking

    out_path = _out(output_filename)
    result = mix_audio_with_ducking(
        video_path=video_path,
        voiceover_path=voiceover_path,
        music_path=music_path,
        output_path=out_path,
        music_volume=music_volume,
        voice_volume=voice_volume,
        duck_level=duck_level,
        fade_out=fade_out,
    )

    if not result["success"]:
        return f"Error: {result['error']}"

    info = _file_info(out_path)
    duration = result.get("duration_seconds", 0)
    return (
        f"{out_path} ({info})\n"
        f"Duration: {duration}s | Music ducking: level={duck_level}, base_vol={music_volume}\n"
        f"Voice active → music ducks. Voice silent → music at full {music_volume} volume."
    )


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

    encoder = _detect_encoder_for_filter()
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

    encoder = _detect_encoder_for_filter()
    out_path = _out(output_filename)
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf,
           "-c:v", encoder, *_encoder_args(encoder), "-c:a", "copy",
           "-movflags", "+faststart", out_path]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        return f"Error: {(proc.stderr or '')[-500:]}"
    return f"{out_path} ({_file_info(out_path)}, {w}x{h}, {mode})"


@mcp.tool()
def add_facecam(
    video_path: str,
    facecam_path: str,
    output_filename: str = "with_facecam.mp4",
    position: str = "middle-left",
    size: int = 30,
    border_radius: int = 20,
    margin: int = 20,
) -> str:
    """Overlay a facecam video onto the main video with rounded corners. Loops automatically if shorter.

    Perfect for TikTok-style videos where the creator appears in a small corner
    while content plays in the background.

    Args:
        video_path: Absolute path to the main video (MP4).
        facecam_path: Path to facecam MP4 file OR directory of MP4 clips (randomly picks one).
        output_filename: Output filename.
        position: Placement: middle-left, top-left, top-right, bottom-left, bottom-right.
        size: Width of facecam as percentage of main video width (1-100). Default 30.
        border_radius: Corner radius in pixels for rounded rectangle. Default 20.
        margin: Distance in pixels from the video edge. Default 20.

    Returns:
        Path and info.
    """
    from vidmake.core import add_facecam_overlay

    out_path = _out(output_filename)
    result = add_facecam_overlay(
        video_path=video_path,
        facecam_path=facecam_path,
        output_path=out_path,
        position=position,
        size=size,
        border_radius=border_radius,
        margin=margin,
    )

    if not result["success"]:
        return f"Error: {result['error']}"
    return f"{result['output_path']} ({_file_info(result['output_path'])})"


# ===========================================================================
# VOICEOVER — ElevenLabs TTS with context-aware voice
# ===========================================================================

@mcp.tool()
def generate_voiceover(
    text: str,
    filename: str = "voiceover.mp3",
    voice: str = "",
    preset: str = "neutral",
    model: str = "eleven_v3",
    speed: float | None = None,
    stability: float | None = None,
    similarity_boost: float | None = None,
    style: float | None = None,
) -> str:
    """Generate voiceover audio from text using ElevenLabs TTS.

    The voice tone and delivery automatically match the video context via presets.
    Supports Vietnamese and 30+ languages with eleven_v3 model.

    Args:
        text: The narration script. Use natural punctuation for pacing:
              - Periods and commas create natural pauses
              - "..." creates longer pauses
              - "!" adds emphasis
              - Keep sentences short for better delivery
        filename: Output MP3 filename.
        voice: Voice ID or name. Leave empty for auto-select.
               Use list_voices to see available voices.
        preset: Voice tone preset. Determines delivery style:
                - "energetic" — hooks, teasers, openers (fast, excited)
                - "informative" — features, tutorials (clear, steady)
                - "persuasive" — CTAs, sales (urgent, confident)
                - "warm" — quotes, testimonials (friendly, slow)
                - "authoritative" — stats, data (commanding)
                - "dramatic" — comparisons, reveals (intense, building)
                - "neutral" — default balanced delivery
        model: ElevenLabs model. "eleven_v3" supports Vietnamese + 30 languages.
               "eleven_flash_v2_5" for faster generation.
        speed: Speaking rate override (0.7=slow, 1.0=normal, 1.3=fast).
               If None, uses preset's default speed.
        stability: Override voice stability (0.0-1.0). Lower = more expressive.
        similarity_boost: Override similarity boost (0.0-1.0).
        style: Override style exaggeration (0.0-1.0). Higher = more dramatic.

    Returns:
        Path to generated MP3, duration, and preset used.
    """
    if not text.strip():
        return "Error: Text cannot be empty."

    # Resolve voice
    voice_id = voice
    if not voice_id:
        voice_id = _DEFAULT_VOICES["vi"]["id"]
    elif len(voice_id) < 15:
        # Might be a name — search
        try:
            client = _get_elevenlabs_client()
            voices = client.voices.get_all()
            for v in voices.voices:
                if voice_id.lower() in v.name.lower():
                    voice_id = v.voice_id
                    break
        except Exception:
            pass

    # Build overrides
    overrides = {}
    if stability is not None:
        overrides["stability"] = stability
    if similarity_boost is not None:
        overrides["similarity_boost"] = similarity_boost
    if style is not None:
        overrides["style"] = style

    out_path = _out(filename)
    result = _tts_generate(
        text=text,
        voice_id=voice_id,
        output_path=out_path,
        preset=preset,
        model_id=model,
        speed=speed,
        voice_overrides=overrides if overrides else None,
    )

    if not result["success"]:
        return f"Error: {result['error']}"

    # Get duration
    info = _probe(out_path)
    duration = info.get("duration", "?")
    preset_desc = _VOICE_PRESETS.get(preset, {}).get("description", preset)
    return (
        f"{out_path} ({_file_info(out_path)}, {duration}s)\n"
        f"Preset: {preset} — {preset_desc}\n"
        f"Characters: {len(text)}"
    )


@mcp.tool()
def generate_slide_narrations(
    scripts: list[dict],
    project_name: str = "video",
    voice: str = "",
    model: str = "eleven_v3",
    merge: bool = True,
    silence_between: float = 0.5,
) -> str:
    """Generate voiceover for multiple slides in one call. Auto-detects voice tone per slide.

    Each script can specify its own preset or let it auto-detect from template type.
    Optionally merges all narrations into a single audio track with configurable
    silence gaps between slides (perfect for syncing with video).

    Args:
        scripts: List of narration dicts, one per slide:
                 - {"text": "narration script"} — auto-detect preset
                 - {"text": "...", "preset": "energetic"} — explicit preset
                 - {"text": "...", "template": "hook"} — detect from template type
                 - {"text": "...", "speed": 1.2} — override speed for this slide
                 Slides with empty text are skipped (silent slides).
        project_name: Prefix for output files.
        voice: Voice ID. Leave empty for auto-select Vietnamese voice.
        model: ElevenLabs model ID.
        merge: If True, concatenate all narrations into a single MP3 with silence gaps.
        silence_between: Seconds of silence between slide narrations (for merged output).

    Returns:
        Paths to individual MP3s + merged audio (if merge=True).
        Use the merged audio with add_audio to sync with video.
    """
    if not scripts:
        return "Error: No scripts provided."

    # Resolve voice once
    voice_id = voice
    if not voice_id:
        voice_id = _DEFAULT_VOICES["vi"]["id"]
    elif len(voice_id) < 15:
        try:
            client = _get_elevenlabs_client()
            voices = client.voices.get_all()
            for v in voices.voices:
                if voice_id.lower() in v.name.lower():
                    voice_id = v.voice_id
                    break
        except Exception:
            pass

    results: list[str] = []
    mp3_paths: list[str] = []
    total_chars = 0

    for i, script in enumerate(scripts):
        idx = f"{i+1:02d}"
        text = script.get("text", "").strip()

        if not text:
            results.append(f"  Slide {idx}: (silent — no narration)")
            mp3_paths.append("")  # placeholder for merge
            continue

        # Determine preset
        preset = script.get("preset", "")
        if not preset:
            template_type = script.get("template", "")
            preset = _TEMPLATE_TO_PRESET.get(template_type, "neutral")

        speed = script.get("speed")
        mp3_path = _out(f"{project_name}_narration_{idx}.mp3")

        result = _tts_generate(
            text=text,
            voice_id=voice_id,
            output_path=mp3_path,
            preset=preset,
            model_id=model,
            speed=speed,
        )

        if result["success"]:
            info = _probe(mp3_path)
            duration = info.get("duration", "?")
            results.append(f"  Slide {idx}: {preset} — {duration}s ({len(text)} chars)")
            mp3_paths.append(mp3_path)
            total_chars += len(text)
        else:
            results.append(f"  Slide {idx}: ERROR — {result['error']}")
            mp3_paths.append("")

    # Merge all narrations into single audio track
    merged_path = ""
    if merge and any(mp3_paths):
        merged_path = _out(f"{project_name}_voiceover.mp3")
        valid_paths = [p for p in mp3_paths if p]

        if len(valid_paths) == 1:
            import shutil
            shutil.copy2(valid_paths[0], merged_path)
        elif len(valid_paths) > 1:
            # Use FFmpeg to concat with silence gaps
            filter_parts = []
            inputs_cmd = []
            for j, p in enumerate(valid_paths):
                inputs_cmd += ["-i", p]
                filter_parts.append(f"[{j}:a]aresample=44100[a{j}]")

            # Build concat with silence between
            concat_parts = []
            for j in range(len(valid_paths)):
                concat_parts.append(f"[a{j}]")
                if j < len(valid_paths) - 1:
                    # Generate silence
                    silence_label = f"[s{j}]"
                    filter_parts.append(
                        f"aevalsrc=0:d={silence_between}:s=44100:c=mono{silence_label}"
                    )
                    concat_parts.append(silence_label)

            n_streams = len(valid_paths) + (len(valid_paths) - 1)  # audio + silences
            filter_parts.append(
                f"{''.join(concat_parts)}concat=n={n_streams}:v=0:a=1[aout]"
            )

            cmd = ["ffmpeg", "-y"] + inputs_cmd + [
                "-filter_complex", ";".join(filter_parts),
                "-map", "[aout]", "-c:a", "libmp3lame", "-b:a", "128k",
                merged_path,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode != 0:
                results.append(f"\n  Merge ERROR: {(proc.stderr or '')[-300:]}")
                merged_path = ""

    # Summary
    output = f"Narrations: {len([p for p in mp3_paths if p])}/{len(scripts)} slides\n"
    output += f"Total characters: {total_chars}\n\n"
    output += "Details:\n" + "\n".join(results)

    if merged_path and Path(merged_path).exists():
        info = _probe(merged_path)
        output += (
            f"\n\nMerged voiceover: {merged_path}\n"
            f"  Duration: {info.get('duration', '?')}s, {_file_info(merged_path)}\n"
            f"  → Use with add_audio to sync with video"
        )

    individual = [p for p in mp3_paths if p]
    if individual:
        output += "\n\nIndividual files:\n" + "\n".join(f"  {p}" for p in individual)

    return output


@mcp.tool()
def list_voices(language: str = "") -> str:
    """List available ElevenLabs voices and voice presets.

    Args:
        language: Filter by language (e.g. "vi", "en"). Empty = show all.

    Returns:
        Available voices + voice presets for context-aware delivery.
    """
    lines = ["=== Voice Presets (context-aware delivery) ===\n"]
    for name, preset in _VOICE_PRESETS.items():
        template_matches = [t for t, p in _TEMPLATE_TO_PRESET.items() if p == name]
        match_str = f" (auto for: {', '.join(template_matches)})" if template_matches else ""
        lines.append(f"  {name}: {preset['description']}{match_str}")
        lines.append(f"    stability={preset['stability']}, style={preset['style']}, speed={preset['speed']}")

    lines.append("\n=== Available Voices ===\n")
    try:
        client = _get_elevenlabs_client()
        voices = client.voices.get_all()
        for v in voices.voices:
            labels = v.labels or {}
            lang = labels.get("language", "")
            if language and lang and language.lower() not in lang.lower():
                continue
            accent = labels.get("accent", "")
            use_case = labels.get("use_case", "")
            lines.append(f"  {v.voice_id} | {v.name}")
            if lang or accent or use_case:
                details = ", ".join(filter(None, [lang, accent, use_case]))
                lines.append(f"    {details}")
    except Exception as exc:
        lines.append(f"  Error fetching voices: {exc}")
        lines.append("  Set ELEVENLABS_API_KEY environment variable.")

    lines.append(f"\nDefault Vietnamese voice: {_DEFAULT_VOICES['vi']['name']}")
    lines.append(f"Default English voice: {_DEFAULT_VOICES['en']['name']}")
    return "\n".join(lines)


# ===========================================================================
# STICKERS — animated SVG stickers (CapCut/Canva-style)
# ===========================================================================

@mcp.tool()
def list_stickers(category: str = "") -> str:
    """Browse animated SVG stickers — CapCut/Canva-style icons with CSS animations.

    These stickers replace static Unicode emoji with vivid, animated SVG graphics.
    Use them in custom HTML slides with "animated": true for maximum impact.

    Categories: reactions, business, arrows, decorative.

    Args:
        category: Filter by category. Empty = show all stickers.

    Returns:
        Available stickers with names, descriptions, and usage example.
    """
    from shared.stickers import list_stickers as _list, list_categories

    cats = list_categories()
    stickers = _list(category=category)

    if not stickers:
        return f"Không tìm thấy sticker cho category '{category}'.\nCategories: {', '.join(cats.keys())}"

    lines = ["=== Animated Stickers (CapCut/Canva-style) ===\n"]

    # Group by category
    by_cat: dict[str, list] = {}
    for s in stickers:
        by_cat.setdefault(s["category"], []).append(s)

    for cat_id, cat_stickers in by_cat.items():
        label = cats.get(cat_id, cat_id)
        lines.append(f"── {label} ──")
        for s in cat_stickers:
            lines.append(f"  {s['name']:16s} {s['description']}")
        lines.append("")

    lines.append(f"Total: {len(stickers)} stickers\n")
    lines.append("=== Cách sử dụng trong HTML slide ===\n")
    lines.append(
        "from shared.stickers import get_sticker_html, get_sticker_css\n\n"
        "# 1. Thêm CSS keyframes vào <style>:\n"
        "css = get_sticker_css('fire')  # hoặc get_all_sticker_css(['fire','heart'])\n\n"
        "# 2. Thêm sticker vào HTML:\n"
        "html = get_sticker_html('fire', size=80, position='top-right')\n\n"
        "# 3. Hoặc dùng build_sticker_slide_html() để tạo slide hoàn chỉnh:\n"
        "from shared.stickers import build_sticker_slide_html\n"
        "full_html = build_sticker_slide_html(\n"
        "    stickers=[{'name':'fire','size':80,'position':'top-right','delay':'0.3s'}],\n"
        "    extra_html='<h1>Nội dung slide</h1>',\n"
        "    extra_css='h1{color:#fff;font-size:72px;text-align:center;padding-top:40%;}',\n"
        ")\n\n"
        "# 4. Dùng với batch_slides:\n"
        '{"html": full_html, "animated": true}\n\n'
        "Positions: inline, top-left, top-right, bottom-left, bottom-right, center"
    )

    return "\n".join(lines)


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
    """Generate a TikTok marketing video with voiceover for a given topic.

    Creates a structured prompt that guides the AI to use batch_slides,
    generate_slide_narrations, and merge_clips_crossfade for efficient
    video creation with context-aware voiceover.
    """
    return (
        f"Create a {num_slides}-slide TikTok video with voiceover about: {topic}\n\n"
        f"Use the vidmake MCP tools:\n"
        f"1. Call batch_slides with {num_slides} slides using templates:\n"
        f"   - Slide 1: 'hook' template (attention-grabbing stat)\n"
        f"   - Slides 2-{num_slides-1}: 'features', 'comparison', 'stats', or 'quote'\n"
        f"   - Slide {num_slides}: 'cta' template (call to action)\n\n"
        f"2. Call generate_slide_narrations with a narration script for each slide:\n"
        f"   - Each script should be 1-2 short sentences (10-20 words)\n"
        f"   - Match the slide content but add verbal context\n"
        f"   - Include 'template' field so voice tone auto-matches:\n"
        f'     {{"text": "Con số không tưởng!", "template": "hook"}}\n'
        f'     {{"text": "Hãy liên hệ ngay hôm nay!", "template": "cta"}}\n'
        f"   - Voice presets auto-apply: hook→energetic, features→informative,\n"
        f"     cta→persuasive, quote→warm, stats→authoritative\n\n"
        f"3. Call merge_clips_crossfade with the clip paths from step 1\n\n"
        f"4. Call add_audio to sync the merged voiceover with the final video\n\n"
        f"Style: dark gradient background, bold colors, large text for mobile.\n"
        f"Duration: 5s per slide, 0.5s crossfade.\n"
        f"Resolution: 1080x1920 (TikTok portrait 9:16).\n"
        f"Language: Vietnamese narration for Vietnamese audience."
    )


@mcp.prompt()
def product_showcase(product_name: str, features: str) -> str:
    """Create a product showcase video with voiceover."""
    return (
        f"Create a product showcase video with voiceover for: {product_name}\n"
        f"Features: {features}\n\n"
        f"Use batch_slides with:\n"
        f"  Slide 1: 'hook' — teaser with a bold claim\n"
        f"  Slide 2: 'features' — top 3 features with icons\n"
        f"  Slide 3: 'stats' — key metrics/numbers\n"
        f"  Slide 4: 'quote' — testimonial\n"
        f"  Slide 5: 'cta' — call to action\n\n"
        f"Then generate_slide_narrations with Vietnamese scripts for each slide:\n"
        f"  - Hook: Excited, attention-grabbing opening line\n"
        f"  - Features: Clear explanation of each benefit\n"
        f"  - Stats: Impressive numbers with emphasis\n"
        f"  - Quote: Warm, authentic testimonial reading\n"
        f"  - CTA: Urgent, persuasive call to action\n\n"
        f"Finally: merge_clips_crossfade → add_audio with voiceover → add_text_overlay for brand."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
