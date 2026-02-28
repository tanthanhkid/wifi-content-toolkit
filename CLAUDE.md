# CLAUDE.md — Project Guide for AI Agents

## Project Overview

**WiFi Marketing Content Toolkit** — Python modules for creating marketing content (posters, videos) for small businesses. Runs on Mac Mini M4 with FFmpeg + Playwright.

## Architecture

```
ContentTool/
├── vidmake/          # Video assembly + Ken Burns animation + MCP server
│   ├── core.py       # Business logic: create_slideshow(), create_animated_slideshow()
│   ├── ui.py         # Gradio web UI (2 tabs: Pipeline + Slideshow)
│   ├── mcp_server.py # MCP server (14 tools) for AI-driven video creation
│   ├── cli.py        # CLI interface
│   └── VIDMAKE_MCP.md # Detailed MCP tool documentation
├── poster/           # HTML template → PNG rendering
│   ├── core.py       # Playwright screenshot: screenshot_sync(), render_poster()
│   ├── ui.py         # Gradio web UI
│   ├── cli.py        # CLI interface
│   └── templates/    # Jinja2 HTML templates (quote, carousel, promo, etc.)
├── shared/           # Shared utilities
│   ├── config.py     # Config loading (~/.wfm/config.json)
│   ├── platform.py   # FFmpeg encoder detection (videotoolbox/nvenc/libx264)
│   └── logger.py     # Logging
├── .mcp.json         # MCP server config for Claude Code
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

## MCP Server

The `vidmake` MCP server (`python -m vidmake.mcp_server`) exposes 14 tools for AI video creation. See `vidmake/VIDMAKE_MCP.md` for complete documentation.

Key tools: `batch_slides` (main workhorse), `merge_clips_crossfade`, `add_audio`, `add_text_overlay`.

7 built-in slide templates: hook, features, cta, comparison, quote, stats, blank.

Output directory: `~/vidmake-output/`

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
- Gradio 6.x (web UI)
- Click + Rich (CLI)
- Jinja2 (poster templates)

## Code Style

- Type hints on all public functions
- Docstrings in Google/NumPy style
- Error messages in Vietnamese for user-facing, English for internal
- Functions return `dict` with `success` bool + `error` string on failure
- Temp files cleaned up in `finally` blocks
