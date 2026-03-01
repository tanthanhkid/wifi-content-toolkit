# CLAUDE.md — Project Guide for AI Agents

## Project Overview

**WiFi Marketing Content Toolkit** — Python modules for creating marketing content (posters, videos) with AI voiceover for small businesses. Runs on Mac Mini M4 with FFmpeg + Playwright + ElevenLabs.

## Architecture

```
ContentTool/
├── vidmake/              # Video assembly + Ken Burns animation + MCP server
│   ├── core.py           # Business logic: create_slideshow(), create_animated_slideshow(),
│   │                     #   add_facecam_overlay(), mix_audio_with_ducking()
│   ├── ui.py             # Gradio web UI (2 tabs: Pipeline + Slideshow)
│   ├── mcp_server.py     # MCP server (20 tools) for AI-driven video creation
│   ├── cli.py            # CLI interface
│   ├── VIDMAKE_MCP.md    # Full MCP tool reference (all 20 tools, all params)
│   └── BEST_PRACTICES.md # Best practices for using MCP effectively
├── poster/               # HTML template → PNG rendering
│   ├── core.py           # Playwright screenshot: screenshot_sync(), render_poster()
│   ├── ui.py             # Gradio web UI
│   ├── cli.py            # CLI interface
│   └── templates/        # Jinja2 HTML templates (quote, carousel, promo, etc.)
├── shared/               # Shared utilities
│   ├── config.py         # Config loading (~/.wfm/config.json)
│   ├── platform.py       # FFmpeg encoder detection (videotoolbox/nvenc/libx264)
│   └── logger.py         # Logging
├── music/                # Background music library (31 no-copyright MP3 tracks)
├── human/                # Facecam / talking-head videos (8 MP4 clips, portrait, auto-loop)
├── .mcp.json             # MCP server config for Claude Code
└── Pipeline_HTML_to_Video.md  # Pipeline design document
```

## Key Patterns

- **Module structure:** Each module has `core.py` (logic), `ui.py` (Gradio), `cli.py` (Click CLI)
- **Vietnamese UI:** All user-facing labels and error messages are in Vietnamese
- **Gradio theme:** `gr.themes.Soft()`, pass `theme` and `css` to `launch()` not constructor (Gradio 6.x)
- **FFmpeg encoder:** Auto-detected via `shared.platform.detect_ffmpeg_encoder()` — h264_videotoolbox on Mac, h264_nvenc on Windows+NVIDIA, libx264 fallback
- **Screenshots:** `poster.core.screenshot_sync(html, path, width, height)` — Playwright headless Chromium
- **Package names:** `wfm-vidmake`, `wfm-poster`, `wfm-shared` (pip installable)
- **Python:** >=3.10, venv at `.venv/`

## MCP Server — How to Create Videos

The `vidmake` MCP server exposes **20 tools** for video creation. Read these docs in order:

1. **`vidmake/BEST_PRACTICES.md`** — Start here. Design philosophy, workflows, script writing rules.
2. **`vidmake/VIDMAKE_MCP.md`** — Full tool reference with all parameters and examples.

### All 20 Tools at a Glance

| # | Category | Tool | Description |
|---|----------|------|-------------|
| 1 | Batch | `batch_slides` | HTML/template/image → PNG + animated MP4 clips |
| 2 | Template | `create_slide` | Template → PNG (no HTML needed) |
| 3 | Atomic | `screenshot_html` | HTML → PNG |
| 4 | Atomic | `animate_image` | PNG → MP4 clip (Ken Burns) |
| 5 | Assembly | `merge_clips` | Concat clips → MP4 |
| 6 | Assembly | `merge_clips_crossfade` | Concat with crossfade transitions |
| 7 | Assembly | `add_audio` | Video + single audio → MP4 |
| 8 | Audio Mix | `mix_voiceover_music` | Video + voice + music with auto-ducking |
| 9 | Audio Mix | `list_music` | Browse 31 background music tracks |
| 10 | Post | `add_text_overlay` | Text/watermark onto video |
| 11 | Post | `resize_video` | Resize/crop/pad |
| 12 | Post | `add_facecam` | Overlay facecam with rounded corners, auto-loop |
| 13 | Voiceover | `generate_voiceover` | Text → MP3 (context-aware voice) |
| 14 | Voiceover | `generate_slide_narrations` | Batch TTS for all slides → merged MP3 |
| 15 | Voiceover | `list_voices` | Available ElevenLabs voices |
| 16 | Utility | `get_media_info` | Probe file info (duration, resolution, codec) |
| 17 | Utility | `list_effects` | 5 Ken Burns animation effects |
| 18 | Utility | `list_templates` | 7 built-in slide templates |
| 19 | Utility | `list_outputs` | Files in output dir |
| 20 | Utility | `cleanup_outputs` | Delete output files by pattern |

### Design Philosophy: Flexible, Not Fixed

**Every video gets unique slide designs.** Do NOT use the same template/layout for every slide. Analyze the content (images, screenshots, text, story) and design each slide with its own HTML/CSS tailored to what it needs to communicate.

Built-in templates (`hook`, `features`, `cta`, etc.) are for **quick prototyping only**. For production videos, write custom HTML per slide.

### Standard Workflow (4 tool calls)

```
1. batch_slides              → Animate slides with Ken Burns effects
2. generate_slide_narrations → Vietnamese voiceover with per-slide voice preset
3. merge_clips_crossfade     → Merged video (no audio)
4. mix_voiceover_music       → Voice + music with auto-ducking (one step)
   OR add_audio              → Voice only (no background music)

Optional:
5. add_facecam               → Overlay talking-head video from human/ folder
```

For custom HTML slides with local images, add a Step 0: generate PNGs via Python script (Playwright), then use `batch_slides` in image mode.

### Working with Images/Screenshots

For slides that embed local images (app screenshots, product photos):
- Use `file:///absolute/path` in HTML `<img>` tags
- Generate PNGs via Python script (Playwright with `page.goto` for local file support)
- Then animate with `batch_slides(slides=[{"image": "/path/to/png"}])`
- For landscape images in portrait video: use `object-fit: cover` to zoom in, blurred bg to fill frame

### Voiceover Rules

- **Use `"preset"` in narration scripts** to set voice tone (e.g., `"energetic"`, `"warm"`)
- **10-25 words per slide** — must fit within 4-6 second duration
- **Write for speaking, not reading** — short, punchy, conversational Vietnamese
- **Use `...` for pauses, `!` for emphasis**
- Model: `eleven_v3` (supports Vietnamese + 30 languages)

### Audio Mixing

- **Voice + music:** Use `mix_voiceover_music` — auto-ducks music when voice speaks, music rises during silent transitions
- **Browse tracks:** Use `list_music` to see all 31 tracks with durations and file paths
- **Music folder:** `music/` contains no-copyright MP3 tracks (corporate, lofi, epic, soft, jazz...)
- **Key params:** `music_volume=0.15` (base level), `duck_level=0.1` (lower = more ducking), `fade_out=2.0`
- **Voice only:** Use `add_audio` for simple mux without ducking

### Facecam Overlay

- **Folder:** `human/` contains 8 portrait MP4 clips of people (720x1280, ~10s each)
- **Tool:** `add_facecam` overlays a talking-head video with rounded corners, auto-loops if shorter
- **Always add facecam as the LAST step** (after all audio mixing)
- **Recommended:** `size=28`, `position=bottom-right`, `border_radius=20`, `margin=25`

### Key Rules

- Always set unique `project_name` per video (e.g., `"trinity"`, `"chatbot_v2"`)
- Call `cleanup_outputs(pattern="prefix_*")` before re-generating a video
- Vary animation effects across slides — don't repeat the same effect
- **Each slide gets unique visual design** — no repeated layouts

### Built-in Templates (Quick Prototyping)

Templates for when speed matters more than design quality:
`hook`, `features`, `cta`, `comparison`, `quote`, `stats`, `blank`

### Output

All files → `~/vidmake-output/`

File naming: `{project_name}_{01..N}.png`, `{project_name}_{01..N}.mp4`, `{project_name}_voiceover.mp3`, `{project_name}_final.mp4`

## Commands

```bash
# Run Gradio UI
python -m vidmake.ui          # Port 7864

# Run MCP server (stdio)
python -m vidmake.mcp_server

# Install Playwright browsers (one-time)
playwright install chromium
```

## Dependencies

- FFmpeg 8.x (brew install ffmpeg)
- Playwright + Chromium (for HTML→PNG screenshots)
- ElevenLabs SDK (for AI voiceover / TTS) — requires `ELEVENLABS_API_KEY` in `.mcp.json`
- Gradio 6.x (web UI)
- Click + Rich (CLI)
- Jinja2 (poster templates)

## Code Style

- Type hints on all public functions
- Docstrings in Google/NumPy style
- Error messages in Vietnamese for user-facing, English for internal
- Functions return `dict` with `success` bool + `error` string on failure
- Temp files cleaned up in `finally` blocks
