# CLAUDE.md — Project Guide for AI Agents

## Project Overview

**WiFi Marketing Content Toolkit** — Python modules for creating marketing content (posters, videos) with AI voiceover for small businesses. Runs on Mac Mini M4 with FFmpeg + Playwright + ElevenLabs.

## Architecture

```
ContentTool/
├── vidmake/              # Video assembly + Ken Burns animation + MCP server
│   ├── core.py           # Business logic: create_slideshow(), create_animated_slideshow(),
│   │                     #   add_facecam_overlay(), mix_audio_with_ducking(), record_html_video()
│   ├── ui.py             # Gradio web UI (2 tabs: Pipeline + Slideshow)
│   ├── mcp_server.py     # MCP server (21 tools) for AI-driven video creation
│   ├── cli.py            # CLI interface
│   ├── VIDMAKE_MCP.md    # Full MCP tool reference (all 21 tools, all params)
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
├── .mcp.json             # MCP server config (vidmake + firecrawl)
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

The `vidmake` MCP server exposes **21 tools** for video creation. Read these docs in order:

1. **`vidmake/BEST_PRACTICES.md`** — Start here. Design philosophy, workflows, script writing rules.
2. **`vidmake/VIDMAKE_MCP.md`** — Full tool reference with all parameters and examples.

### All 21 Tools at a Glance

| # | Category | Tool | Description |
|---|----------|------|-------------|
| 1 | Batch | `batch_slides` | HTML/template/image → PNG + animated MP4 clips |
| 2 | Template | `create_slide` | Template → PNG (no HTML needed) |
| 3 | Atomic | `screenshot_html` | HTML → PNG |
| 4 | Atomic | `animate_image` | PNG → MP4 clip (Ken Burns) |
| 5 | Atomic | `record_html_video` | HTML + CSS animations → MP4 (Playwright recording) |
| 6 | Assembly | `merge_clips` | Concat clips → MP4 |
| 7 | Assembly | `merge_clips_crossfade` | Concat with crossfade transitions |
| 8 | Assembly | `add_audio` | Video + single audio → MP4 |
| 9 | Audio Mix | `mix_voiceover_music` | Video + voice + music with auto-ducking |
| 10 | Audio Mix | `list_music` | Browse 31 background music tracks |
| 11 | Post | `add_text_overlay` | Text/watermark onto video |
| 12 | Post | `resize_video` | Resize/crop/pad |
| 13 | Post | `add_facecam` | Overlay facecam with rounded corners, auto-loop |
| 14 | Voiceover | `generate_voiceover` | Text → MP3 (context-aware voice) |
| 15 | Voiceover | `generate_slide_narrations` | Batch TTS for all slides → merged MP3 |
| 16 | Voiceover | `list_voices` | Available ElevenLabs voices |
| 17 | Utility | `get_media_info` | Probe file info (duration, resolution, codec) |
| 18 | Utility | `list_effects` | 5 Ken Burns animation effects |
| 19 | Utility | `list_templates` | 7 built-in slide templates |
| 20 | Utility | `list_outputs` | Files in output dir |
| 21 | Utility | `cleanup_outputs` | Delete output files by pattern |

### Design Philosophy: Flexible, Not Fixed

**Every video gets unique slide designs.** Do NOT use the same template/layout for every slide. Analyze the content (images, screenshots, text, story) and design each slide with its own HTML/CSS tailored to what it needs to communicate.

Built-in templates (`hook`, `features`, `cta`, etc.) are for **quick prototyping only**. For production videos, write custom HTML per slide.

### Standard Workflow (5 steps — ALL mandatory)

Every video MUST include: CSS animated slides, voiceover, background music, and facecam.

```
1. batch_slides              → CSS animated slides (animated: true) + Ken Burns for screenshots
2. generate_slide_narrations → Vietnamese voiceover with per-slide voice preset
3. merge_clips_crossfade     → Merged video (no audio)
4. mix_voiceover_music       → Voice + background music with auto-ducking (ALWAYS use music)
5. add_facecam               → Facecam overlay from human/ folder (MANDATORY)
```

**Mandatory rules:**
- **CSS Animated slides**: Use `"animated": true` for all text/content slides. Only use Ken Burns for image/screenshot slides.
- **Background music**: ALWAYS use `mix_voiceover_music` with a track from `music/`. Never deliver a video without music.
- **Facecam**: ALWAYS add facecam as the final step. If for some reason facecam should be skipped, **ASK the user first** — do not skip silently.
- **Screenshots**: When the content involves a website, app, or product — take screenshots (Playwright/Firecrawl) and include them as Ken Burns slides.

For custom HTML slides with local images, add a Step 0: generate PNGs via Python script (Playwright), then use `batch_slides` in image mode.

### CSS Text Animations (CapCut/PowerPoint-style)

For text that flies in, bounces, fades, or types out — use CSS `@keyframes` with `"animated": true`:

```python
# In batch_slides — mix animated + static slides
batch_slides(slides=[
    {"html": "<html with @keyframes>", "animated": True},       # CSS animation recording
    {"html": "<html>static content</html>", "effect": "zoom_in"}, # Ken Burns
])

# Or standalone
record_html_video(html_content="<html with @keyframes>...", filename="animated.mp4")
```

Key rules: `animation-fill-mode: both` on all elements, timeline ≤ slide duration, stagger delay = `0.3 + index × 0.4s`. See `BEST_PRACTICES.md` for 8 CSS animation patterns.

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

### Audio Mixing (Background Music is MANDATORY)

- **Every video MUST have background music.** Use `mix_voiceover_music` — never `add_audio` alone for final output.
- **Browse tracks:** Use `list_music` to see all 31 tracks with durations and file paths
- **Music folder:** `music/` contains no-copyright MP3 tracks (corporate, lofi, epic, soft, jazz...)
- **Key params:** `music_volume=0.15` (base level), `duck_level=0.1` (lower = more ducking), `fade_out=2.0`
- **`add_audio`** is only for intermediate steps or special cases — not for final video delivery

### Facecam Overlay (MANDATORY)

- **Every video MUST have facecam.** If you want to skip facecam, **ASK the user first** — never skip silently.
- **Folder:** `human/` contains 8 portrait MP4 clips of people (720x1280, ~10s each)
- **Tool:** `add_facecam` overlays a talking-head video with rounded corners, auto-loops if shorter
- **Always add facecam as the LAST step** (after all audio mixing)
- **Recommended:** `size=28`, `position=middle-left`, `border_radius=20`, `margin=25`

### Web-to-Video Workflow (Firecrawl)

When a user provides a URL and asks for a video:

1. **Scrape content** — Use Firecrawl MCP (`firecrawl_scrape`) or CLI (`firecrawl scrape --url <URL> --format markdown`) to extract page content
2. **Analyze & plan slides** — Identify key info (stats, features, quotes, images) → design unique slides
3. **Build video** — Follow standard workflow (batch_slides → narrations → merge → audio)

Firecrawl MCP provides: `firecrawl_scrape`, `firecrawl_crawl`, `firecrawl_map`, `firecrawl_search`, `firecrawl_extract`, `firecrawl_deep_research`.

### Key Rules

- Always set unique `project_name` per video (e.g., `"trinity"`, `"chatbot_v2"`)
- Call `cleanup_outputs(pattern="prefix_*")` before re-generating a video
- Vary animation effects across slides — don't repeat the same effect
- **Each slide gets unique visual design** — no repeated layouts
- **CSS Animated by default** — all text/content slides use `"animated": true`. Ken Burns only for image/screenshot slides.
- **Background music is mandatory** — always use `mix_voiceover_music`, never deliver without music
- **Facecam is mandatory** — always add facecam. If skipping, ask user first.
- **Screenshots when relevant** — if content is about a website/app/product, take screenshots and include as slides

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
- Firecrawl MCP (for web scraping → video scripts) — requires `FIRECRAWL_API_KEY` in `.mcp.json`
- Gradio 6.x (web UI)
- Click + Rich (CLI)
- Jinja2 (poster templates)

## Code Style

- Type hints on all public functions
- Docstrings in Google/NumPy style
- Error messages in Vietnamese for user-facing, English for internal
- Functions return `dict` with `success` bool + `error` string on failure
- Temp files cleaned up in `finally` blocks
