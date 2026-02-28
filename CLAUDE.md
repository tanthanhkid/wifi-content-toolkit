# CLAUDE.md — Project Guide for AI Agents

## Project Overview

**WiFi Marketing Content Toolkit** — Python modules for creating marketing content (posters, videos) with AI voiceover for small businesses. Runs on Mac Mini M4 with FFmpeg + Playwright + ElevenLabs.

## Architecture

```
ContentTool/
├── vidmake/              # Video assembly + Ken Burns animation + MCP server
│   ├── core.py           # Business logic: create_slideshow(), create_animated_slideshow()
│   ├── ui.py             # Gradio web UI (2 tabs: Pipeline + Slideshow)
│   ├── mcp_server.py     # MCP server (17 tools) for AI-driven video creation + voiceover
│   ├── cli.py            # CLI interface
│   ├── VIDMAKE_MCP.md    # Full MCP tool reference (all 17 tools, all params)
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

The `vidmake` MCP server exposes **17 tools** for video creation. Read these docs in order:

1. **`vidmake/BEST_PRACTICES.md`** — Start here. Decision trees, workflows, script writing rules, common mistakes.
2. **`vidmake/VIDMAKE_MCP.md`** — Full tool reference with all parameters and examples.

### Standard Workflow (4 tool calls)

```
1. batch_slides        → Creates slide PNGs + animated MP4 clips (all at once)
2. generate_slide_narrations → Vietnamese voiceover with context-aware tone per slide
3. merge_clips_crossfade     → Join clips with smooth transitions
4. add_audio                 → Sync voiceover with video → Final MP4
```

### Slide Templates (7)

| Template | Voice Preset (auto) | Use For |
|----------|-------------------|---------|
| `hook` | energetic | Opening — bold stat, shocking question |
| `features` | informative | Product benefits — 3 cards with icons |
| `cta` | persuasive | Closing — button + urgent message |
| `comparison` | dramatic | Before/after — two columns |
| `quote` | warm | Testimonial — customer voice |
| `stats` | authoritative | Numbers — 3 big metrics |
| `blank` | neutral | Simple title + subtitle |

### Voiceover Rules

- **Always include `"template"` in narration scripts** → auto-selects correct voice tone
- **10-25 words per slide** — must fit within 4-6 second duration
- **Write for speaking, not reading** — short, punchy, conversational Vietnamese
- **Use `...` for pauses, `!` for emphasis**
- Model: `eleven_v3` (supports Vietnamese + 30 languages)
- Default voice: Đôn Hùng (Vietnamese male)

### Key Rules

- Always set unique `project_name` per video (e.g., `"trinity"`, `"chatbot_v2"`)
- Call `cleanup_outputs(pattern="prefix_*")` before re-generating a video
- Vary animation effects across slides — don't repeat the same effect
- First slide = `hook`, last slide = `cta` — proven TikTok formula
- Background music volume: `0.25` when layered with voiceover

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
