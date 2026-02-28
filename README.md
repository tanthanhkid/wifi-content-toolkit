# WiFi Marketing Content Toolkit

Python toolkit for creating marketing videos and posters. Built for small businesses and agencies that need to produce TikTok/Reels content quickly.

**HTML slides → Screenshot → Ken Burns animation → Video MP4**

Everything runs from the terminal. No GUI apps needed.

## Features

- **Video Pipeline** — Create TikTok-style videos from HTML slides with Ken Burns animations (zoom, pan, fade)
- **7 Slide Templates** — hook, features, CTA, comparison, quote, stats, blank — just fill in text
- **Gradio Web UI** — HTML editor with live preview, screenshot, animation config, video export
- **AI Voiceover** — ElevenLabs TTS with context-aware voice (energetic hooks, warm quotes, urgent CTAs)
- **MCP Server** — 17 tools for AI agents (Claude Code) to create videos with voiceover programmatically
- **Poster Renderer** — HTML/Jinja2 templates → pixel-perfect PNG via Playwright
- **Hardware Accelerated** — Auto-detects VideoToolbox (Mac), NVENC (Windows), libx264 fallback

## Quick Start

```bash
# Clone
git clone https://github.com/tanthanhkid/wifi-content-toolkit.git
cd wifi-content-toolkit

# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e shared/ -e poster/ -e vidmake/

# Install browser for screenshots
playwright install chromium

# Launch web UI
python -m vidmake.ui
# Opens at http://localhost:7864
```

## Requirements

- Python >= 3.10
- FFmpeg (`brew install ffmpeg` on Mac)
- Playwright + Chromium (installed automatically)

## Modules

### vidmake — Video Assembly

Creates slideshow videos with Ken Burns animations from images.

```bash
# Gradio web UI
python -m vidmake.ui

# CLI
vidmake --help
```

**Animation effects:** zoom_in, zoom_out, pan_right, pan_down, zoom_topleft

### poster — Poster/Image Renderer

Renders HTML templates to PNG using headless Chromium.

```bash
# Gradio web UI
python -m poster.ui

# CLI
poster --help
```

**Templates:** quote, carousel, before_after, promo, case_study

### shared — Shared Utilities

Config management, FFmpeg encoder detection, logging.

## MCP Server (for AI Agents)

The MCP server lets AI agents like Claude Code create videos through tool calls.

### Setup

Add to `.mcp.json` in project root:

```json
{
  "mcpServers": {
    "vidmake": {
      "command": ".venv/bin/python",
      "args": ["-m", "vidmake.mcp_server"],
      "cwd": "/path/to/wifi-content-toolkit",
      "env": {
        "ELEVENLABS_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Usage

Tell Claude Code:

> "Tạo video quảng cáo 30 giây cho sản phẩm AI Chatbot"

Claude will call `batch_slides` → `generate_slide_narrations` → `merge_clips_crossfade` → `add_audio` to produce a ready-to-post MP4 with Vietnamese voiceover.

### Available Tools (17)

| Category | Tools |
|----------|-------|
| **Batch** | `batch_slides` — process all slides in 1 call (screenshot + animate) |
| **Template** | `create_slide` — template-based, no HTML needed |
| **Atomic** | `screenshot_html`, `animate_image` — per-file control |
| **Assembly** | `merge_clips`, `merge_clips_crossfade`, `add_audio` |
| **Voiceover** | `generate_voiceover`, `generate_slide_narrations`, `list_voices` — ElevenLabs TTS |
| **Post-processing** | `add_text_overlay`, `resize_video` |
| **Utility** | `get_media_info`, `list_effects`, `list_templates`, `list_outputs`, `cleanup_outputs` |

### Slide Templates (7)

| Template | Description |
|----------|-------------|
| `hook` | Big number/stat — attention grabber |
| `features` | 3 cards with icons |
| `cta` | Call-to-action with button |
| `comparison` | Before/after two columns |
| `quote` | Testimonial with attribution |
| `stats` | 3 big metrics |
| `blank` | Title + subtitle on gradient |

Full MCP documentation: [`vidmake/VIDMAKE_MCP.md`](vidmake/VIDMAKE_MCP.md)

Best practices for AI agents: [`vidmake/BEST_PRACTICES.md`](vidmake/BEST_PRACTICES.md)

## Video Pipeline (Manual)

For creating videos without AI, use the shell script workflow:

1. Create HTML slides (1080x1920, dark theme)
2. Screenshot via Playwright or Chrome DevTools
3. Apply FFmpeg Ken Burns animations
4. Merge clips + add background music

See [`Pipeline_HTML_to_Video.md`](Pipeline_HTML_to_Video.md) for the full manual workflow.

## Project Structure

```
├── vidmake/              # Video assembly + animations + MCP server
│   ├── core.py           # create_slideshow(), create_animated_slideshow()
│   ├── ui.py             # Gradio UI (Pipeline + Slideshow tabs)
│   ├── mcp_server.py     # MCP server (17 tools, 7 templates, 2 prompts)
│   ├── cli.py            # CLI
│   ├── VIDMAKE_MCP.md    # AI agent tool reference
│   └── BEST_PRACTICES.md # Best practices for AI video creation
├── poster/               # HTML → PNG rendering
│   ├── core.py           # Playwright screenshot engine
│   ├── templates/        # Jinja2 HTML templates
│   ├── ui.py             # Gradio UI
│   └── cli.py            # CLI
├── shared/               # Shared utilities
│   ├── platform.py       # FFmpeg encoder auto-detection
│   ├── config.py         # Config management
│   └── logger.py         # Logging
├── .mcp.json             # MCP server config
├── CLAUDE.md             # AI agent project guide
└── Pipeline_HTML_to_Video.md
```

## License

MIT
