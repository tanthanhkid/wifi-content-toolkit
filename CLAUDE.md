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
│   ├── mcp_server.py     # MCP server (22 tools) for AI-driven video creation
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
│   ├── logger.py         # Logging
│   └── stickers.py       # Animated SVG stickers (CapCut/Canva-style, 25+ stickers)
├── music/                # Background music library (31 no-copyright MP3 tracks)
├── human/                # Facecam / talking-head videos (8 MP4 clips, portrait, auto-loop)
├── .claude/
│   └── skills/
│       └── tiktok-planner/   # /tiktok-planner slash command
│           └── SKILL.md      # Viral TikTok video planning skill
├── .mcp.json             # MCP server config (vidmake + firecrawl)
└── Pipeline_HTML_to_Video.md  # Pipeline design document
```

## Claude Code Skills

### `/tiktok-planner [topic]` — Viral TikTok Video Planner

Master marketer skill that plans TikTok videos optimized for millions of views.

**Usage:** `/tiktok-planner Trinity chatbot AI` or `/tiktok-planner review iPhone 16`

**What it does (7 steps):**
1. **Research trends** — Searches trending hashtags, viral formats, Vietnamese TikTok trends
2. **Hashtag strategy** — 3-tier system: mega (100M+), niche (1M-100M), micro (<1M) + Vietnamese hashtags
3. **3 video titles** — Rated by curiosity score, using viral formulas (curiosity gap, shock value, numbers)
4. **Script writing** — 3-Second Rule: Hook (0-3s) → Buildup (3-10s) → Value (10-25s) → CTA (25-30s)
5. **Slide mapping** — Each 3-5s segment: visual, narration, text overlay, sticker, voice preset
6. **Engagement hooks** — Comment bait, save triggers, share triggers
7. **Save plan** → `~/vidmake-output/{project}_tiktok_plan.md`

After plan approval, use vidmake MCP tools (batch_slides → narrations → merge → music → facecam) to produce the video.

**AUTO-INVOCATION RULE:** When the user asks to create any video (e.g., "tao video", "make a video about...", "video quang cao cho..."), ALWAYS invoke `/tiktok-planner` FIRST to plan the script before producing with vidmake MCP tools. Never skip the planning phase.

## Key Patterns

- **Module structure:** Each module has `core.py` (logic), `ui.py` (Gradio), `cli.py` (Click CLI)
- **Vietnamese UI:** All user-facing labels and error messages are in Vietnamese
- **Gradio theme:** `gr.themes.Soft()`, pass `theme` and `css` to `launch()` not constructor (Gradio 6.x)
- **FFmpeg encoder:** Auto-detected via `shared.platform.detect_ffmpeg_encoder()` — h264_videotoolbox on Mac, h264_nvenc on Windows+NVIDIA, libx264 fallback
- **Screenshots:** `poster.core.screenshot_sync(html, path, width, height)` — Playwright headless Chromium
- **Package names:** `wfm-vidmake`, `wfm-poster`, `wfm-shared` (pip installable)
- **Python:** >=3.10, venv at `.venv/`

## MCP Server — How to Create Videos

The `vidmake` MCP server exposes **22 tools** for video creation. Read these docs in order:

1. **`vidmake/BEST_PRACTICES.md`** — Start here. Design philosophy, workflows, sticker usage, script writing rules.
2. **`vidmake/VIDMAKE_MCP.md`** — Full tool reference with all parameters and examples.

### All 22 Tools at a Glance

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
| 17 | Stickers | `list_stickers` | Browse 25+ animated SVG stickers (CapCut/Canva-style) |
| 18 | Utility | `get_media_info` | Probe file info (duration, resolution, codec) |
| 19 | Utility | `list_effects` | 5 Ken Burns animation effects |
| 20 | Utility | `list_templates` | 7 built-in slide templates |
| 21 | Utility | `list_outputs` | Files in output dir |
| 22 | Utility | `cleanup_outputs` | Delete output files by pattern |

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
- **ElevenLabs voiceover**: LUÔN tạo voiceover tiếng Việt có dấu bằng `generate_slide_narrations`. Văn bản narration PHẢI viết tiếng Việt có dấu đầy đủ (ví dụ: "Một trăm mười tỉ đô la", KHÔNG ĐƯỢC viết "Mot tram muoi ti do la"). Không bao giờ giao video mà không có voiceover.
- **Background music**: ALWAYS use `mix_voiceover_music` with a track from `music/`. Never deliver a video without music.
- **Facecam**: LUÔN thêm facecam ở bước cuối. Dùng `position=bottom-left`, `margin=400` để tránh bị TikTok UI che (caption, nav bar, nút like/comment). KHÔNG dùng `middle-left`, `top-*`, hoặc bên phải. Nếu bỏ facecam, **HỎI user trước**.
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

### Animated Stickers (CapCut/Canva-style)

Replace static Unicode emoji (`⚡`, `✓`, `🔥`) with **animated SVG stickers** — bouncing, pulsing, glowing icons that bring slides to life.

- **25+ stickers** across 4 categories: reactions, business, arrows, decorative
- **Module:** `shared/stickers.py` — `get_sticker_html()`, `get_sticker_css()`, `build_sticker_slide_html()`
- **MCP tool:** `list_stickers` — browse all available stickers
- **Works with Playwright recording** — stickers animate in `"animated": true` slides

```python
from shared.stickers import get_sticker_html, get_sticker_css, build_sticker_slide_html

# Quick: build a slide with floating sticker decorations
html = build_sticker_slide_html(
    stickers=[
        {"name": "fire", "size": 100, "position": "top-right"},
        {"name": "checkmark", "size": 64, "position": "inline", "delay": "0.5s"},
    ],
    extra_html='<h1>Tính năng HOT</h1>',
    extra_css='h1{color:#fff;font-size:72px;text-align:center;padding-top:40%;}',
)
# Use: {"html": html, "animated": true}
```

See `BEST_PRACTICES.md` for full sticker guide and usage examples.

### Working with Images/Screenshots

For slides that embed local images (app screenshots, product photos):
- Use `file:///absolute/path` in HTML `<img>` tags
- Generate PNGs via Python script (Playwright with `page.goto` for local file support)
- Then animate with `batch_slides(slides=[{"image": "/path/to/png"}])`
- For landscape images in portrait video: use `object-fit: cover` to zoom in, blurred bg to fill frame

### Quy tắc Voiceover (BẮT BUỘC)

- **BẮT BUỘC:** Mọi video PHẢI có voiceover ElevenLabs TTS. KHÔNG BAO GIỜ giao video mà không có voiceover.
- **Tiếng Việt có dấu:** Tất cả văn bản narration PHẢI viết tiếng Việt có dấu đầy đủ (ví dụ: "Một trăm mười tỉ đô la", KHÔNG ĐƯỢC viết "Mot tram muoi ti do la"). Điều này đảm bảo phát âm chính xác.
- **Dùng `"preset"`** để điều chỉnh giọng đọc (ví dụ: `"energetic"`, `"warm"`, `"dramatic"`)
- **10-25 từ mỗi slide** — phải vừa trong 4-6 giây
- **Viết để nói, không phải để đọc** — ngắn gọn, mạnh mẽ, giọng hội thoại tự nhiên
- **Dùng `...` để tạo ngắt, `!` để nhấn mạnh**
- Model: `eleven_v3` (hỗ trợ tiếng Việt + 30 ngôn ngữ)

### Audio Mixing (Background Music is MANDATORY)

- **Every video MUST have background music.** Use `mix_voiceover_music` — never `add_audio` alone for final output.
- **Browse tracks:** Use `list_music` to see all 31 tracks with durations and file paths
- **Music folder:** `music/` contains no-copyright MP3 tracks (corporate, lofi, epic, soft, jazz...)
- **Key params:** `music_volume=0.15` (base level), `duck_level=0.1` (lower = more ducking), `fade_out=2.0`
- **`add_audio`** is only for intermediate steps or special cases — not for final video delivery

### Facecam Overlay (BẮT BUỘC)

- **Mọi video PHẢI có facecam.** Nếu muốn bỏ, **HỎI user trước** — không được tự ý bỏ.
- **Thư mục:** `human/` chứa 8 clip MP4 portrait (720x1280, ~10 giây mỗi clip)
- **Tool:** `add_facecam` overlay video talking-head với bo tròn góc, tự lặp nếu ngắn hơn
- **Luôn thêm facecam là BƯỚC CUỐI CÙNG** (sau khi mix audio xong)

#### Phân tích TikTok Safe Zone (1080x1920)

```
┌────────────────────────────┐ 0px
│  Username, Follow button   │ ~150px (vùng nguy hiểm trên)
│  ..........................│
│                            │
│      VÙNG AN TOÀN          │
│      (nội dung chính)      │ 150px → 1550px
│                            │
│                      [♥]   │ Sidebar phải: like,
│                      [💬]  │ comment, share, bookmark
│                      [↗]   │ (~120px từ mép phải)
│                      [🔖]  │
│  Caption text...           │ ~1550px
│  @username · Nhạc nền ♪    │ ~1650px
│  ──────────────────────    │ ~1700px
│  [Home][Shop][+][Inbox]    │ ~1780-1920px (thanh điều hướng)
└────────────────────────────┘ 1920px
```

**Vùng nguy hiểm bị TikTok UI che:**
- **Dưới cùng (1550-1920px):** Caption, thanh nhạc, thanh điều hướng = ~370px
- **Bên phải (960-1080px):** Nút like, comment, share, bookmark = ~120px
- **Trên cùng (0-150px):** Username, nút Follow

#### Quy tắc đặt Facecam

- **Vị trí:** `position=bottom-left`, `margin=400` — đẩy facecam lên trên vùng caption/nav
- **KHÔNG dùng:** `middle-left`, `top-*` (che tiêu đề slide), hoặc `bottom-*` với margin nhỏ (bị TikTok UI che)
- **KHÔNG đặt bên phải** — bị che bởi nút like/comment/share
- **Recommended:** `size=22`, `position=bottom-left`, `border_radius=20`, `margin=350`
- X margin cố định 20px sát mép trái (hardcode trong core.py), `margin` chỉ ảnh hưởng khoảng cách dọc (Y)
- Với `size=22`: facecam width ≈ 238px, height ≈ 423px (portrait). Y = 1920 - 423 - 350 = 1147px → nằm trong vùng an toàn, không che nội dung
- **KHÔNG dùng `size=28` + `margin=400`** — facecam quá lớn và bị đẩy lên giữa video, che nội dung

### Web-to-Video Workflow (Firecrawl)

When a user provides a URL and asks for a video:

1. **Scrape content** — Use Firecrawl MCP (`firecrawl_scrape`) or CLI (`firecrawl scrape --url <URL> --format markdown`) to extract page content
2. **Analyze & plan slides** — Identify key info (stats, features, quotes, images) → design unique slides
3. **Build video** — Follow standard workflow (batch_slides → narrations → merge → audio)

Firecrawl MCP provides: `firecrawl_scrape`, `firecrawl_crawl`, `firecrawl_map`, `firecrawl_search`, `firecrawl_extract`, `firecrawl_deep_research`.

### Vietnamese Font (BẮT BUỘC)

**LUÔN dùng Google Font "Be Vietnam Pro"** trong mọi HTML slide. Font hệ thống (Arial, Segoe UI) bị lỗi dấu tiếng Việt trong Playwright/Chromium.

```css
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
body { font-family: 'Be Vietnam Pro', sans-serif; }
```

KHÔNG BAO GIỜ dùng `font-family: Arial` hoặc `sans-serif` cho slide tiếng Việt.

### Key Rules

- Always set unique `project_name` per video (e.g., `"trinity"`, `"chatbot_v2"`)
- Call `cleanup_outputs(pattern="prefix_*")` before re-generating a video
- Vary animation effects across slides — don't repeat the same effect
- **Each slide gets unique visual design** — no repeated layouts
- **CSS Animated by default** — all text/content slides use `"animated": true`. Ken Burns only for image/screenshot slides.
- **Background music is mandatory** — always use `mix_voiceover_music`, never deliver without music
- **Facecam is mandatory** — always add facecam. If skipping, ask user first.
- **Screenshots when relevant** — if content is about a website/app/product, take screenshots and include as slides
- **Animated stickers preferred** — use `shared.stickers` instead of static Unicode emoji for icons. Use `list_stickers` to browse.
- **Vietnamese font** — LUÔN dùng `Be Vietnam Pro` (Google Fonts) trong HTML slides. KHÔNG dùng Arial/Segoe UI.

### Built-in Templates (Quick Prototyping)

Templates for when speed matters more than design quality:
`hook`, `features`, `cta`, `comparison`, `quote`, `stats`, `blank`

### Output

All files → `~/vidmake-output/`

Intermediate files: `{project_name}_{01..N}.png`, `{project_name}_{01..N}.mp4`, `{project_name}_voiceover.mp3`

**Final video naming (BẮT BUỘC):**
- File video cuối PHẢI đặt tên dễ đọc, mô tả nội dung: `ten-ngan-gon-noi-dung.mp4` (slug tiếng Việt không dấu, dùng dấu gạch ngang)
- KHÔNG dùng tên system như `project_final.mp4`
- Ví dụ: `93phan-tram-doanh-nghiep-chua-san-sang-cho-AI.mp4`, `3-sai-lam-khi-dung-chatbot.mp4`

**TikTok Caption (BẮT BUỘC):**
- LUÔN tạo file `{ten-video}_caption.txt` kèm theo, chứa caption sẵn để user copy-paste khi đăng TikTok:
  - Tiêu đề hấp dẫn (hook câu view)
  - Mô tả ngắn 2-3 dòng
  - CTA (follow, comment, save)
  - Hashtags 3 tầng: mega (#viral #fyp #xuhuong), niche (theo ngành), micro (theo chủ đề cụ thể)

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
