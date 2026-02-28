# Vidmake MCP Server — AI Agent Documentation

## What This Server Does

Creates TikTok-style short videos from HTML slides with Ken Burns animations.
The full pipeline: **HTML → Screenshot (Playwright) → Animate (FFmpeg) → Merge → Video MP4**.

All output files are saved to `~/vidmake-output/`.

---

## Setup

Add to `.mcp.json` in project root (or `~/.claude/settings.json` for global):

```json
{
  "mcpServers": {
    "vidmake": {
      "command": "/path/to/ContentTool/.venv/bin/python",
      "args": ["-m", "vidmake.mcp_server"],
      "cwd": "/path/to/ContentTool"
    }
  }
}
```

Restart Claude Code after adding.

**Requirements:** FFmpeg installed, Playwright browsers installed (`playwright install chromium`).

---

## Quick Start — 2 Tool Calls for a Complete Video

**Call 1:** `batch_slides` — creates all slide PNGs + animated MP4 clips in one call.

```json
{
  "slides": [
    {"template": "hook", "fields": {"title": "200+", "subtitle": "messages per day", "highlight": "Can't keep up?"}, "effect": "zoom_in"},
    {"template": "features", "fields": {"title": "AI Chatbot", "icon1": "⚡", "card1_title": "24/7 Auto Reply", "card1_desc": "No staff needed", "icon2": "💰", "card2_title": "Only $200/mo", "card2_desc": "Save 70%", "icon3": "🧠", "card3_title": "Smart AI", "card3_desc": "Context-aware"}, "effect": "pan_down"},
    {"template": "cta", "fields": {"title": "Ready to", "title_glow": "grow revenue?", "button_text": "Message us FREE", "subtitle": "Free consultation", "brand": "ACME INC"}, "effect": "zoom_out"}
  ],
  "project_name": "demo",
  "duration_per_slide": 5.0
}
```

**Call 2:** `merge_clips_crossfade` — join the clips.

```json
{
  "clip_paths": [
    "~/vidmake-output/demo_01.mp4",
    "~/vidmake-output/demo_02.mp4",
    "~/vidmake-output/demo_03.mp4"
  ],
  "crossfade_duration": 0.5,
  "output_filename": "demo_final.mp4"
}
```

Done. Video is at `~/vidmake-output/demo_final.mp4`.

---

## Workflow Tiers

### Tier 1: Fastest (2-3 calls)

Best for: quick video generation, template-based content.

```
batch_slides (templates) → merge_clips_crossfade → (optional) add_audio / add_text_overlay
```

### Tier 2: Medium (N+2 calls)

Best for: mix of templates and custom HTML, per-slide control.

```
create_slide × N → batch_slides (image mode) → merge_clips_crossfade
```

### Tier 3: Full Control (2N+1 calls)

Best for: fully custom HTML, different durations per slide, maximum flexibility.

```
screenshot_html × N → animate_image × N → merge_clips or merge_clips_crossfade → add_audio → add_text_overlay
```

---

## All 14 Tools — Reference

### BATCH (Primary Tool)

#### `batch_slides`

Process multiple slides in one call. Screenshots HTML/templates to PNG, then applies Ken Burns animation to each, producing ready-to-merge MP4 clips.

**Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `slides` | `list[dict]` | required | List of slide definitions (see Slide Format below) |
| `project_name` | `str` | `"video"` | Filename prefix (e.g. `"trinity"` → `trinity_01.png`, `trinity_01.mp4`) |
| `duration_per_slide` | `float` | `5.0` | Duration per animated clip in seconds |
| `size` | `str` | `"1080x1920"` | Resolution as `"WxH"` |
| `fps` | `int` | `30` | Frames per second |
| `style` | `dict\|null` | `null` | Brand/style overrides for templates |

**Slide Format** — each item in `slides` is a dict with ONE of these structures:

```
Template mode:  {"template": "hook", "fields": {"title": "...", ...}, "effect": "zoom_in"}
HTML mode:      {"html": "<full html>", "effect": "pan_down"}
Image mode:     {"image": "/absolute/path.png", "effect": "zoom_out"}
```

- `template` — use a built-in template (see Templates section). `fields` is required.
- `html` — raw HTML string. You write the full `<!DOCTYPE html>` document.
- `image` — skip screenshot, animate an existing PNG/JPG file.
- `effect` — optional. If omitted, auto-cycles through all 5 effects.

**Style overrides** (applies to templates only):

```json
{
  "bg": "linear-gradient(135deg, #0a0a2e, #1a1a4e)",
  "primary": "#6C63FF",
  "accent": "#FF6584",
  "accent2": "#FF8E53",
  "font": "'Segoe UI', Helvetica, Arial, sans-serif",
  "w": 1080,
  "h": 1920
}
```

**Returns:** Summary with all PNG + MP4 paths. Use the clip paths with `merge_clips` or `merge_clips_crossfade`.

---

### TEMPLATE

#### `create_slide`

Create a single slide PNG from a template without writing HTML.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `template` | `str` | required | Template name |
| `fields` | `dict` | required | Template fields |
| `filename` | `str` | `"slide.png"` | Output filename |
| `style` | `dict\|null` | `null` | Brand overrides |
| `size` | `str` | `"1080x1920"` | Resolution |

---

### ATOMIC

#### `screenshot_html`

Render any HTML string to PNG via headless Chromium.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `html_content` | `str` | required | Full HTML document string |
| `filename` | `str` | `"slide.png"` | Output filename |
| `width` | `int` | `1080` | Viewport width |
| `height` | `int` | `1920` | Viewport height |

#### `animate_image`

Apply a single Ken Burns animation to one image, producing an MP4 clip.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `image_path` | `str` | required | Absolute path to PNG/JPG |
| `effect` | `str` | `"zoom_in"` | Animation effect |
| `duration` | `float` | `5.0` | Clip duration (seconds) |
| `output_filename` | `str` | `"clip.mp4"` | Output filename |
| `size` | `str` | `"1080x1920"` | Resolution |
| `fps` | `int` | `30` | Frames per second |

---

### ASSEMBLY

#### `merge_clips`

Concatenate MP4 clips with no transition (lossless, instant).

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `clip_paths` | `list[str]` | required | Ordered clip paths |
| `output_filename` | `str` | `"merged.mp4"` | Output filename |

#### `merge_clips_crossfade`

Concatenate clips with smooth crossfade transitions.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `clip_paths` | `list[str]` | required | Ordered clip paths (min 2) |
| `crossfade_duration` | `float` | `0.5` | Crossfade seconds (0.1 - 2.0) |
| `output_filename` | `str` | `"merged.mp4"` | Output filename |

#### `add_audio`

Mux background music onto a video. Video is not re-encoded.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `video_path` | `str` | required | Input video path |
| `audio_path` | `str` | required | Audio file path (MP3/WAV) |
| `output_filename` | `str` | `"with_audio.mp4"` | Output filename |
| `audio_volume` | `float` | `1.0` | Volume (0.5 = half, 2.0 = double) |
| `fade_out_duration` | `float` | `0.0` | Fade out at end (seconds, 0 = off) |

---

### POST-PROCESSING

#### `add_text_overlay`

Burn text/watermark onto video. Text is rendered as PNG via Playwright then composited.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `video_path` | `str` | required | Input video path |
| `text` | `str` | required | Text to display (`<br>` for line breaks) |
| `output_filename` | `str` | `"with_text.mp4"` | Output filename |
| `position` | `str` | `"bottom-center"` | Position (see below) |
| `font_size` | `int` | `36` | Font size in pixels |
| `font_color` | `str` | `"white"` | CSS color |
| `bg_color` | `str` | `"rgba(0,0,0,0.5)"` | CSS background color |
| `start_time` | `float` | `0.0` | Show from (seconds, 0 = start) |
| `end_time` | `float` | `0.0` | Show until (seconds, 0 = end) |

**Positions:** `top-left`, `top-center`, `top-right`, `center`, `bottom-left`, `bottom-center`, `bottom-right`

#### `resize_video`

Resize, crop, or pad a video to a new resolution.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `video_path` | `str` | required | Input video path |
| `size` | `str` | `"1080x1920"` | Target `"WxH"` |
| `mode` | `str` | `"pad"` | `"pad"` (letterbox), `"crop"` (fill+crop), `"stretch"` |
| `output_filename` | `str` | `"resized.mp4"` | Output filename |
| `bg_color` | `str` | `"black"` | Padding color for pad mode |

---

### UTILITY

#### `get_media_info`

Probe a file for duration, resolution, codec, FPS, file size.

| Param | Type | Description |
|-------|------|-------------|
| `file_path` | `str` | Absolute path to any media file |

#### `list_effects`

Returns all 5 Ken Burns animation effects with descriptions.

#### `list_templates`

Returns all 7 slide templates with their field names.

#### `list_outputs`

Returns all files in `~/vidmake-output/` with sizes.

#### `cleanup_outputs`

Delete files from the output directory.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `pattern` | `str` | `"*"` | Glob pattern: `"*"` = all, `"*.mp4"` = videos, `"demo_*"` = project files |

---

## Templates Reference

### `hook`

Big attention-grabbing stat/number.

| Field | Example | Description |
|-------|---------|-------------|
| `badge` | `"STATS 2026"` | Small badge text above the number |
| `title` | `"200+"` | Big number/stat (main focal point) |
| `subtitle` | `"messages per day"` | Description line |
| `highlight` | `"Can't keep up?"` | Highlighted call-out text |

### `features`

Three feature cards with icons.

| Field | Example | Description |
|-------|---------|-------------|
| `title` | `"AI Chatbot"` | Main heading |
| `icon1` | `"⚡"` | Emoji/icon for card 1 |
| `card1_title` | `"24/7 Auto Reply"` | Card 1 title |
| `card1_desc` | `"No staff needed"` | Card 1 description |
| `icon2` | `"💰"` | Card 2 icon |
| `card2_title` | `"Only $200/mo"` | Card 2 title |
| `card2_desc` | `"Save 70%"` | Card 2 description |
| `icon3` | `"🧠"` | Card 3 icon |
| `card3_title` | `"Smart AI"` | Card 3 title |
| `card3_desc` | `"Context-aware"` | Card 3 description |

### `cta`

Call-to-action with button.

| Field | Example | Description |
|-------|---------|-------------|
| `title` | `"Ready to"` | First line (normal text) |
| `title_glow` | `"grow revenue?"` | Second line (gradient glow) |
| `button_text` | `"Contact us FREE"` | CTA button text |
| `subtitle` | `"Free consultation"` | Small text below button |
| `brand` | `"ACME INC"` | Brand name at bottom |

### `comparison`

Two-column before/after comparison.

| Field | Example | Description |
|-------|---------|-------------|
| `title` | `"Monthly Cost"` | Heading |
| `left_label` | `"Employee"` | Left column header (red/bad) |
| `left_value` | `"$3,000"` | Left big number |
| `left_desc` | `"Salary + benefits"` | Left description |
| `right_label` | `"AI Bot"` | Right column header (blue/good) |
| `right_value` | `"$200"` | Right big number |
| `right_desc` | `"24/7 • No vacation"` | Right description |

### `quote`

Testimonial/quote with attribution.

| Field | Example | Description |
|-------|---------|-------------|
| `quote_text` | `"Revenue increased 3x in 2 months"` | The quote text |
| `author` | `"John Doe"` | Author name |
| `role` | `"CEO, Acme Corp"` | Author role/company |

### `stats`

Three big metrics.

| Field | Example | Description |
|-------|---------|-------------|
| `title` | `"Real Results"` | Heading |
| `stat1_value` | `"75%"` | Metric 1 number |
| `stat1_label` | `"Cost reduction"` | Metric 1 label |
| `stat2_value` | `"3x"` | Metric 2 number |
| `stat2_label` | `"Response speed"` | Metric 2 label |
| `stat3_value` | `"98%"` | Metric 3 number |
| `stat3_label` | `"Customer satisfaction"` | Metric 3 label |

### `blank`

Simple title + subtitle on dark gradient.

| Field | Example | Description |
|-------|---------|-------------|
| `title` | `"Any Title"` | Main heading (gradient text) |
| `subtitle` | `"Supporting text"` | Subtitle (optional) |

---

## Animation Effects

| Effect | Description | Best For |
|--------|-------------|----------|
| `zoom_in` | Slowly zoom into center | Hook slides, emphasis |
| `zoom_out` | Start zoomed, slowly reveal | Reveals, CTA slides |
| `pan_right` | Pan from left to right | Feature lists, horizontal content |
| `pan_down` | Pan from top to bottom | Vertical content, cards |
| `zoom_topleft` | Zoom into top-left area | Focus on specific element |

If no effect is specified, they auto-cycle in this order per slide.

---

## Full Examples

### Example 1: Marketing Video (Templates Only, 2 Calls)

**Goal:** 5-slide TikTok video for "AI Chatbot" product.

**Call 1:**
```
batch_slides(
  slides=[
    {"template": "hook", "fields": {"badge": "2026 STATS", "title": "200+", "subtitle": "messages daily", "highlight": "Can't reply fast enough?"}, "effect": "zoom_in"},
    {"template": "comparison", "fields": {"title": "Monthly Cost", "left_label": "Staff", "left_value": "$3K", "left_desc": "Salary + insurance", "right_label": "AI Bot", "right_value": "$200", "right_desc": "24/7 no breaks"}, "effect": "pan_down"},
    {"template": "features", "fields": {"title": "AI Chatbot Pro", "icon1": "⚡", "card1_title": "24/7 Auto", "card1_desc": "Never sleeps", "icon2": "💰", "card2_title": "$200/mo", "card2_desc": "Save 70%", "icon3": "🧠", "card3_title": "Smart AI", "card3_desc": "Understands context"}, "effect": "zoom_out"},
    {"template": "stats", "fields": {"title": "Proven Results", "stat1_value": "75%", "stat1_label": "Less staff needed", "stat2_value": "3x", "stat2_label": "Faster replies", "stat3_value": "98%", "stat3_label": "Satisfaction"}, "effect": "pan_right"},
    {"template": "cta", "fields": {"title": "Ready to", "title_glow": "grow?", "button_text": "Get Started FREE", "subtitle": "Setup in 24h", "brand": "ACME"}, "effect": "zoom_in"}
  ],
  project_name="chatbot",
  duration_per_slide=5.0
)
```

**Call 2:**
```
merge_clips_crossfade(
  clip_paths=["~/vidmake-output/chatbot_01.mp4", "~/vidmake-output/chatbot_02.mp4", "~/vidmake-output/chatbot_03.mp4", "~/vidmake-output/chatbot_04.mp4", "~/vidmake-output/chatbot_05.mp4"],
  output_filename="chatbot_final.mp4"
)
```

**Result:** 23-second video at `~/vidmake-output/chatbot_final.mp4`.

---

### Example 2: Custom HTML + Template Mix (2 Calls)

```
batch_slides(
  slides=[
    {"html": "<!DOCTYPE html><html>..custom slide 1..</html>", "effect": "zoom_in"},
    {"template": "features", "fields": {...}},
    {"template": "cta", "fields": {...}, "effect": "zoom_out"},
    {"image": "/path/to/existing-screenshot.png", "effect": "pan_down"}
  ],
  project_name="mix"
)
```

---

### Example 3: Custom Brand Colors (2 Calls)

```
batch_slides(
  slides=[...],
  project_name="brand",
  style={
    "bg": "linear-gradient(135deg, #1a0000, #4a0000)",
    "primary": "#FF4444",
    "accent": "#FFD700",
    "font": "'Georgia', serif"
  }
)
```

---

### Example 4: Full Control Pipeline (6 Calls)

```
# 1. Screenshot custom HTML
screenshot_html(html_content="<html>..slide 1..</html>", filename="s1.png")

# 2. Screenshot with template
create_slide(template="cta", fields={...}, filename="s2.png")

# 3. Animate with different durations
animate_image(image_path="~/vidmake-output/s1.png", effect="zoom_in", duration=7.0, output_filename="c1.mp4")
animate_image(image_path="~/vidmake-output/s2.png", effect="zoom_out", duration=4.0, output_filename="c2.mp4")

# 4. Merge
merge_clips_crossfade(clip_paths=["~/vidmake-output/c1.mp4", "~/vidmake-output/c2.mp4"], output_filename="video.mp4")

# 5. Add music with fade-out
add_audio(video_path="~/vidmake-output/video.mp4", audio_path="/path/to/music.mp3", output_filename="with_music.mp4", audio_volume=0.7, fade_out_duration=2.0)

# 6. Add watermark (visible only last 5 seconds)
add_text_overlay(video_path="~/vidmake-output/with_music.mp4", text="ACME INC", output_filename="final.mp4", position="bottom-right", font_size=24, start_time=6.0)
```

---

### Example 5: Reformat for Different Platforms

```
# TikTok (9:16) — already default
batch_slides(slides=[...], size="1080x1920")

# Instagram Reels (9:16) — same
batch_slides(slides=[...], size="1080x1920")

# YouTube Shorts (9:16) — same
batch_slides(slides=[...], size="1080x1920")

# Instagram Post (1:1)
batch_slides(slides=[...], size="1080x1080")

# YouTube (16:9)
batch_slides(slides=[...], size="1920x1080")

# Or resize an existing video
resize_video(video_path="~/vidmake-output/tiktok.mp4", size="1080x1080", mode="crop", output_filename="instagram.mp4")
```

---

## MCP Prompts

The server includes built-in prompts that structure your workflow:

### `tiktok_video`

```
Use prompt: tiktok_video(topic="AI chatbot for customer service", num_slides=5)
```

### `product_showcase`

```
Use prompt: product_showcase(product_name="AI Chatbot Pro", features="24/7 replies, smart context, $200/month")
```

---

## Tips for AI Agents

1. **Always use `batch_slides` as your first choice.** It's 5-10x more efficient than calling screenshot + animate per slide.

2. **Use templates when possible.** They produce consistent, professional results without writing HTML. Only use raw HTML for layouts that no template covers.

3. **Name projects consistently.** Use `project_name` in batch_slides to keep files organized (e.g., `"chatbot"`, `"sale_q1"`).

4. **Call `cleanup_outputs` before starting** a new video project to avoid mixing files from previous runs.

5. **Crossfade duration 0.3-0.5s** works best for TikTok-style content. Longer feels slow.

6. **Duration 4-5s per slide** is ideal for marketing content. Shorter for hooks (3s), longer for detailed slides (6-7s).

7. **Effect variety matters.** Don't use the same effect for all slides. Mix zoom_in, pan_down, zoom_out for visual interest. The auto-cycle does this for you if you omit `effect`.

8. **Check results with `get_media_info`** if you need to verify duration, resolution, or file size before the next step.

9. **Audio volume 0.5-0.7** is good for background music under voiceover. Use 1.0 for music-only videos. Always add `fade_out_duration: 2.0` for a professional ending.

10. **The `image` mode in batch_slides** is useful when the user provides their own screenshots or when you need to re-animate with different effects without re-screenshotting.
