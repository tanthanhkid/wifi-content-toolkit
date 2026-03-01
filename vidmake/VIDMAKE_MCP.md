# Vidmake MCP Server — AI Agent Documentation

## What This Server Does

Creates TikTok-style short videos from HTML slides with Ken Burns animations **and AI voiceover**.
The full pipeline: **HTML → Screenshot (Playwright) → Animate (FFmpeg) → Voiceover (ElevenLabs) → Merge → Video MP4**.

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
      "cwd": "/path/to/ContentTool",
      "env": {
        "ELEVENLABS_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Code after adding.

**Requirements:** FFmpeg installed, Playwright browsers installed (`playwright install chromium`), ElevenLabs API key (for voiceover).

---

## Quick Start — 4 Tool Calls for Video + Voice + Music (Recommended)

**Call 1:** `batch_slides` — creates all slide PNGs + animated MP4 clips.

**Call 2:** `generate_slide_narrations` — generates context-aware voiceover for each slide.

```json
{
  "scripts": [
    {"text": "Hơn 200 tin nhắn mỗi ngày... bạn có trả lời kịp không?", "preset": "energetic"},
    {"text": "AI Chatbot giúp bạn phản hồi tự động, tiết kiệm 70% chi phí.", "preset": "informative"},
    {"text": "Liên hệ ngay để được tư vấn miễn phí!", "preset": "persuasive"}
  ],
  "project_name": "demo",
  "merge": true
}
```

Voice presets match content mood:
- `energetic` — excited, high energy (hooks, openers)
- `informative` — clear, steady (features, explanations)
- `persuasive` — urgent, confident (CTAs)
- `warm` — friendly, authentic (quotes, testimonials)
- `authoritative` — commanding (stats, data)
- `dramatic` — intense, building (comparisons, reveals)

**Call 3:** `merge_clips_crossfade` — join clips (no audio yet).

**Call 4:** `mix_voiceover_music` — voice + music with auto-ducking.

```json
{
  "video_path": "~/vidmake-output/demo_merged.mp4",
  "voiceover_path": "~/vidmake-output/demo_voiceover.mp3",
  "music_path": "/path/to/music.mp3",
  "output_filename": "demo_final.mp4",
  "music_volume": 0.15,
  "duck_level": 0.1
}
```

Music automatically ducks when voice speaks, rises during silent transitions.
Use `list_music` to browse available background tracks.

---

## Quick Start — 3 Tool Calls (Voice Only, No Music)

**Calls 1-2:** Same as above (batch_slides + generate_slide_narrations).

**Call 3:** `merge_clips_crossfade` → then `add_audio` to sync voiceover.

```json
{
  "video_path": "~/vidmake-output/demo_merged.mp4",
  "audio_path": "~/vidmake-output/demo_voiceover.mp3",
  "output_filename": "demo_final.mp4"
}
```

---

## Quick Start — 2 Tool Calls (No Voiceover)

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

### Tier 1: Fastest (2-4 calls)

Best for: quick video generation, template-based content.

```
batch_slides → merge_clips_crossfade                                    (video only, 2 calls)
batch_slides → narrations → merge → add_audio                          (+ voice, 4 calls)
batch_slides → narrations → merge → mix_voiceover_music                (+ voice + music, 4 calls)
```

### Tier 2: Medium (N+2 calls)

Best for: mix of templates and custom HTML, per-slide control.

```
create_slide × N → batch_slides (image mode) → merge_clips_crossfade
```

### Tier 3: Full Control (2N+1 calls)

Best for: fully custom HTML, different durations per slide, maximum flexibility.

```
screenshot_html × N → animate_image × N → merge_clips_crossfade → mix_voiceover_music or add_audio
```

---

## All 21 Tools — Reference

### BATCH (Primary Tool)

#### `batch_slides`

Process multiple slides in one call. Screenshots HTML/templates to PNG, then applies Ken Burns animation to each, producing ready-to-merge MP4 clips. Also supports CSS animation recording via `"animated": true` flag.

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
Template mode:      {"template": "hook", "fields": {"title": "...", ...}, "effect": "zoom_in"}
HTML mode:          {"html": "<full html>", "effect": "pan_down"}
Image mode:         {"image": "/absolute/path.png", "effect": "zoom_out"}
CSS animated mode:  {"html": "<html with @keyframes>", "animated": true}
CSS animated+dur:   {"html": "...", "animated": true, "duration": 6.0}
```

- `template` — use a built-in template (see Templates section). `fields` is required.
- `html` — raw HTML string. You write the full `<!DOCTYPE html>` document.
- `image` — skip screenshot, animate an existing PNG/JPG file.
- `effect` — optional Ken Burns effect. If omitted, auto-cycles through all 5 effects. Ignored when `animated` is true.
- `animated` — when `true`, records the browser playing CSS animations via Playwright video recording instead of screenshot + Ken Burns. Use for text animations: fadeIn, slideUp, bounce, typewriter, stagger.
- `duration` — optional per-slide duration override (seconds). Works for both animated and Ken Burns slides.

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

#### `record_html_video`

Record HTML with CSS `@keyframes` animations → MP4 via Playwright video recording. Instead of screenshotting a static image, this records the browser playing CSS animations in real-time. Use for CapCut/PowerPoint-style text animations.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `html_content` | `str` | required | Full HTML document with CSS @keyframes animations |
| `filename` | `str` | `"animated.mp4"` | Output filename |
| `width` | `int` | `1080` | Viewport width |
| `height` | `int` | `1920` | Viewport height |
| `duration` | `float` | `5.0` | Recording duration (must cover all animations) |
| `fps` | `int` | `30` | Frames per second |

**Note:** For batch processing, use `batch_slides` with `"animated": true` instead. This tool is for single-slide recording.

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

### AUDIO MIXING

#### `list_music`

List available background music tracks from the `music/` folder with durations.

No parameters. Returns track names, file paths, and durations.

#### `mix_voiceover_music`

Combine video + voiceover + background music in one step with automatic ducking.
Music automatically ducks when voice is speaking and returns to normal volume during transitions.
Replaces the 2-step process of `add_audio(voice)` → `add_audio(music)`.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `video_path` | `str` | required | Input video path (merged clips, no audio) |
| `voiceover_path` | `str` | required | Voiceover MP3 path |
| `music_path` | `str` | required | Background music MP3 path. Use `list_music` to browse |
| `output_filename` | `str` | `"mixed_audio.mp4"` | Output filename |
| `music_volume` | `float` | `0.15` | Base music volume before ducking (0.0-2.0) |
| `voice_volume` | `float` | `1.0` | Voiceover volume (0.0-2.0) |
| `duck_level` | `float` | `0.1` | Ducking aggressiveness (0.01-1.0, lower = more ducking) |
| `fade_out` | `float` | `2.0` | Fade out music at end (seconds, 0 = no fade) |

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

#### `add_facecam`

Overlay a facecam/talking-head video onto the main video with rounded corners. Loops automatically if shorter than the main video. Perfect for TikTok-style videos.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `video_path` | `str` | required | Main video path (MP4) |
| `facecam_path` | `str` | required | Facecam video path (MP4) |
| `output_filename` | `str` | `"with_facecam.mp4"` | Output filename |
| `position` | `str` | `"bottom-right"` | `"top-left"`, `"top-right"`, `"bottom-left"`, `"bottom-right"` |
| `size` | `int` | `30` | Width as % of main video (1-100) |
| `border_radius` | `int` | `20` | Corner radius in pixels |
| `margin` | `int` | `20` | Distance from edge in pixels |

---

### VOICEOVER (ElevenLabs TTS)

#### `generate_voiceover`

Generate a single voiceover audio file from text. Voice tone auto-matches video context.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | `str` | required | Narration script. Use punctuation for pacing: "..." for pauses, "!" for emphasis |
| `filename` | `str` | `"voiceover.mp3"` | Output filename |
| `voice` | `str` | `""` | Voice ID or name. Empty = auto (Vietnamese) |
| `preset` | `str` | `"neutral"` | Voice tone preset (see Voice Presets) |
| `model` | `str` | `"eleven_v3"` | ElevenLabs model. v3 supports Vietnamese + 30 languages |
| `speed` | `float\|null` | `null` | Speaking rate (0.7=slow, 1.0=normal, 1.3=fast). Null = use preset default |
| `stability` | `float\|null` | `null` | Override stability (0=expressive, 1=monotone) |
| `similarity_boost` | `float\|null` | `null` | Override voice similarity (0.0-1.0) |
| `style` | `float\|null` | `null` | Override style exaggeration (0=neutral, 1=dramatic) |

#### `generate_slide_narrations`

Batch generate voiceover for all slides. Auto-detects tone per slide from template type.
Merges into a single audio track with silence gaps (ready for `add_audio`).

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `scripts` | `list[dict]` | required | Per-slide narration (see Script Format below) |
| `project_name` | `str` | `"video"` | Filename prefix |
| `voice` | `str` | `""` | Voice ID. Empty = auto Vietnamese |
| `model` | `str` | `"eleven_v3"` | ElevenLabs model |
| `merge` | `bool` | `true` | Merge all narrations into single MP3 |
| `silence_between` | `float` | `0.5` | Seconds of silence between slides |

**Script Format** — each item in `scripts`:

```
Auto-detect:   {"text": "Narration script here"}
With template:  {"text": "...", "template": "hook"}     ← auto-selects "energetic" preset
With preset:    {"text": "...", "preset": "persuasive"}  ← explicit preset
With speed:     {"text": "...", "template": "cta", "speed": 1.2}
Silent slide:   {"text": ""}                             ← skipped in merge
```

**Returns:** Individual MP3 paths + merged audio path. Use merged audio with `add_audio` (voice only) or `mix_voiceover_music` (voice + music with ducking).

#### `list_voices`

List available ElevenLabs voices and voice presets.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `language` | `str` | `""` | Filter by language code (e.g. "vi", "en") |

#### Voice Presets

| Preset | Stability | Style | Speed | Auto for Template | Description |
|--------|-----------|-------|-------|-------------------|-------------|
| `energetic` | 0.30 | 0.80 | 1.10 | hook | Excited, high energy, fast |
| `informative` | 0.60 | 0.35 | 0.95 | features | Clear, professional, steady |
| `persuasive` | 0.40 | 0.70 | 1.05 | cta | Urgent, confident, compelling |
| `warm` | 0.65 | 0.55 | 0.90 | quote | Friendly, authentic, slower |
| `authoritative` | 0.55 | 0.45 | 0.95 | stats | Commanding, impressive |
| `dramatic` | 0.35 | 0.75 | 0.90 | comparison | Intense, building tension |
| `neutral` | 0.50 | 0.45 | 1.00 | blank | Balanced, natural |

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

### Example 5: Full Video with AI Voiceover (4 Calls)

**Goal:** 5-slide marketing video with Vietnamese narration.

**Call 1:** Create slides
```
batch_slides(
  slides=[
    {"template": "hook", "fields": {"title": "200+", "subtitle": "tin nhắn mỗi ngày", "highlight": "Trả lời kịp không?"}, "effect": "zoom_in"},
    {"template": "features", "fields": {"title": "AI Chatbot", "icon1": "⚡", "card1_title": "24/7", "card1_desc": "Không cần nhân viên", "icon2": "💰", "card2_title": "Chỉ 200$/tháng", "card2_desc": "Tiết kiệm 70%", "icon3": "🧠", "card3_title": "AI Thông minh", "card3_desc": "Hiểu ngữ cảnh"}, "effect": "pan_down"},
    {"template": "stats", "fields": {"title": "Kết quả thực tế", "stat1_value": "75%", "stat1_label": "Giảm chi phí", "stat2_value": "3x", "stat2_label": "Nhanh hơn", "stat3_value": "98%", "stat3_label": "Hài lòng"}, "effect": "zoom_out"},
    {"template": "quote", "fields": {"quote_text": "Doanh thu tăng gấp 3 chỉ sau 2 tháng", "author": "Anh Minh", "role": "Giám đốc ABC Corp"}, "effect": "pan_right"},
    {"template": "cta", "fields": {"title": "Sẵn sàng", "title_glow": "bứt phá?", "button_text": "Liên hệ MIỄN PHÍ", "subtitle": "Tư vấn trong 24h", "brand": "TRINITY"}, "effect": "zoom_in"}
  ],
  project_name="chatbot"
)
```

**Call 2:** Generate voiceover with per-slide tone
```
generate_slide_narrations(
  scripts=[
    {"text": "Hơn 200 tin nhắn mỗi ngày... bạn có trả lời kịp không?", "template": "hook"},
    {"text": "AI Chatbot phản hồi tự động 24/7, tiết kiệm đến 70% chi phí nhân sự.", "template": "features"},
    {"text": "Giảm 75% chi phí. Nhanh gấp 3 lần. 98% khách hàng hài lòng!", "template": "stats"},
    {"text": "Anh Minh, giám đốc ABC Corp chia sẻ: doanh thu tăng gấp 3 chỉ sau 2 tháng.", "template": "quote"},
    {"text": "Liên hệ ngay hôm nay để được tư vấn miễn phí!", "template": "cta"}
  ],
  project_name="chatbot",
  merge=true,
  silence_between=0.3
)
```

Voice tones auto-applied: hook→energetic, features→informative, stats→authoritative, quote→warm, cta→persuasive.

**Call 3:** Merge video clips
```
merge_clips_crossfade(
  clip_paths=["~/vidmake-output/chatbot_01.mp4", ..., "~/vidmake-output/chatbot_05.mp4"],
  output_filename="chatbot_merged.mp4"
)
```

**Call 4a (voice only):** Add voiceover to video
```
add_audio(
  video_path="~/vidmake-output/chatbot_merged.mp4",
  audio_path="~/vidmake-output/chatbot_voiceover.mp3",
  output_filename="chatbot_final.mp4"
)
```

**Call 4b (voice + music):** Or use smart mix with auto-ducking
```
mix_voiceover_music(
  video_path="~/vidmake-output/chatbot_merged.mp4",
  voiceover_path="~/vidmake-output/chatbot_voiceover.mp3",
  music_path="/path/to/music.mp3",
  output_filename="chatbot_final.mp4",
  music_volume=0.15,
  duck_level=0.1
)
```

**Result:** Professional 25s video with context-aware Vietnamese narration (+ auto-ducked background music if using 4b).

---

### Example 6: Reformat for Different Platforms

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

### Example 7: Video + Voiceover + Background Music with Auto-Ducking (4 Calls)

**Goal:** Video with voiceover AND background music. Music automatically ducks when voice speaks.

**Call 1-2:** Same as Example 5 (batch_slides + generate_slide_narrations)

**Call 3:** Merge video clips (no audio yet)
```
merge_clips_crossfade(
  clip_paths=["~/vidmake-output/chatbot_01.mp4", ..., "~/vidmake-output/chatbot_05.mp4"],
  output_filename="chatbot_merged.mp4"
)
```

**Call 4:** Smart mix — voice + music with auto-ducking
```
# First, check available music:
list_music()  # → lists 31 tracks with paths and durations

# Then mix everything in one step:
mix_voiceover_music(
  video_path="~/vidmake-output/chatbot_merged.mp4",
  voiceover_path="~/vidmake-output/chatbot_voiceover.mp3",
  music_path="/path/to/music/track.mp3",
  output_filename="chatbot_final.mp4",
  music_volume=0.15,    # base music level
  duck_level=0.1,       # lower = more ducking when voice active
  fade_out=2.0          # music fades out at end
)
```

**Result:** Music plays at 0.15 volume during transitions (no voice), ducks down when voice speaks.

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

9. **For voice + music, use `mix_voiceover_music`** — it auto-ducks music when voice speaks. For music-only videos, use `add_audio` with `audio_volume: 0.7` and `fade_out_duration: 2.0`.

10. **The `image` mode in batch_slides** is useful when the user provides their own screenshots or when you need to re-animate with different effects without re-screenshotting.

11. **For voiceover, always include `"template"` in scripts** so the voice tone auto-matches the slide. Hook slides get excited delivery, quotes get warm reading, CTAs get urgent tone.

12. **Keep narration scripts short** — 1-2 sentences per slide (10-25 words). Short sentences sound more natural and fit the 4-5s per slide timing.

13. **Use `silence_between: 0.3`** for fast-paced TikTok content, `0.5-1.0` for more professional corporate videos.

14. **Combine voiceover + background music:** Use `mix_voiceover_music` — it combines voice + music with auto-ducking in one step. Music ducks when voice speaks, rises during transitions. Use `list_music` to browse available tracks.
