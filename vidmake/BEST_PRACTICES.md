# Best Practices — Vidmake MCP for Claude Code

Guide for AI agents to create high-quality marketing videos efficiently.

---

## Core Philosophy: Flexible Design, Not Fixed Templates

**Every video is unique.** The slide structure, layout, and visual design must be driven by the story and content — not forced into a fixed template.

Built-in templates (`hook`, `features`, `cta`, etc.) exist for **quick prototyping only**. For production-quality videos, always write **custom HTML per slide** that adapts to the specific content, images, and narrative.

### Why Custom HTML?

| Fixed Templates | Custom HTML |
|----------------|-------------|
| Every slide looks the same | Each slide has unique design |
| Limited to text fields | Embed images, screenshots, icons, complex layouts |
| One-size-fits-all layout | Adapted to content type (data table, pipeline, flow diagram...) |
| Generic "template feel" | Professional, editorial quality |

---

## Decision Tree: Which Approach?

```
User request received
  │
  ├─ Has images/screenshots to showcase?
  │   └─ Custom HTML slides with embedded images (Workflow A)
  │
  ├─ Text-only marketing content (product/service)?
  │   ├─ Quick draft → Built-in templates (Workflow B)
  │   └─ Production quality → Custom HTML (Workflow A)
  │
  ├─ "Tạo poster / ảnh quảng cáo"
  │   └─ Custom HTML → screenshot_html (1 call)
  │
  └─ "Sửa video / chỉnh video"
      └─ Atomic tools: add_text_overlay, resize_video, add_audio
```

---

## Workflow A: Custom HTML Video (Recommended)

**Best for all production content. Each slide is hand-designed.**

### Step 1: Analyze Content & Plan Unique Slides

Before writing any HTML, understand the content:
- What images/screenshots are available?
- What story does each slide tell?
- What visual style fits each piece of content?

**There is NO fixed formula.** Design each slide based on what it needs to communicate:

```
Example: App showcase video
  Slide 1: Brand intro — gradient bg, logo, tagline
  Slide 2: Full-bleed screenshot — app interface zoomed in, floating label
  Slide 3: Screenshot + feature cards — split layout
  Slide 4: Big number overlay + screenshot bg — dramatic stat
  Slide 5: Screenshot in glowing frame — tech aesthetic
  Slide 6: Screenshot + grid of features — organized
  Slide 7: CTA — bold button, checklist

Example: Product promo video
  Slide 1: Product hero shot — full bleed image, price tag
  Slide 2: Before/after split — diagonal divide
  Slide 3: 3 benefit icons — clean grid layout
  Slide 4: Customer quote — testimonial style
  Slide 5: Limited offer — urgency with countdown feel
```

### Step 2: Write Custom HTML for Each Slide

Each slide gets its own HTML/CSS tailored to its content type.

**Guidelines for embedding images:**
- Use `file:///absolute/path/to/image.png` in `<img>` tags
- For landscape images in portrait video: use `object-fit: cover` with a tall container to zoom in
- Add blurred version of the same image as background fill: `filter: blur(50px) brightness(0.2)`
- Use gradient overlays for text readability over images

**Layout patterns for images in portrait (1080×1920):**

| Pattern | When to Use |
|---------|------------|
| **Full-bleed** — image fills 80%+ of frame, small label overlay | "Let the image speak" — clean app UI, product photos |
| **Screenshot + cards** — image top 55%, feature cards below | "Show & explain" — interface + capabilities |
| **Big number + image bg** — hero stat top, image below | "Impress with data" — revenue, users, performance |
| **Framed screenshot** — image in styled border/shadow, dark bg | "Tech showcase" — workflow diagrams, technical UI |
| **Split layout** — image one side, text/list other side | "Organize info" — settings, configurations |

### Step 3: Generate PNGs

Since MCP server's `screenshot_html` uses Playwright inside an async event loop, screenshots with local file references should be generated via a Python script:

```python
# Run outside MCP to create PNGs with local image support
import asyncio, tempfile, os
from playwright.async_api import async_playwright

async def screenshot(html, output_path, w=1080, h=1920):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": w, "height": h})
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8")
        tmp.write(html); tmp.close()
        try:
            await page.goto(f"file://{tmp.name}", wait_until="networkidle")
            await page.screenshot(path=str(output_path), full_page=False)
        finally:
            os.unlink(tmp.name); await browser.close()
```

Then use `batch_slides` with `{"image": "/path/to/png"}` to animate.

### Step 4: Animate, Voiceover, Merge

```python
# Animate existing PNGs (no screenshot needed)
batch_slides(
    slides=[
        {"image": "/path/to/slide_01.png", "effect": "zoom_in"},
        {"image": "/path/to/slide_02.png", "effect": "pan_down"},
        ...
    ],
    project_name="unique_name",
    duration_per_slide=4.5,
)

# Voiceover — use "preset" directly, NOT "template"
generate_slide_narrations(
    scripts=[
        {"text": "...", "preset": "energetic"},
        {"text": "...", "preset": "informative"},
        ...
    ],
    project_name="unique_name",
    merge=True,
)

# Merge video (no audio yet)
merge_clips_crossfade(clip_paths=[...], output_filename="merged.mp4")

# Option A: Voice + background music with auto-ducking (RECOMMENDED)
mix_voiceover_music(
    video_path="merged.mp4",
    voiceover_path="voiceover.mp3",
    music_path="/path/to/music.mp3",  # use list_music() to browse
    music_volume=0.15,
    duck_level=0.1,
)

# Option B: Voice only (no music)
add_audio(video_path="merged.mp4", audio_path="voiceover.mp3")
```

---

## Workflow B: Quick Templates (Prototyping Only)

**Use built-in templates when speed matters more than design quality.**

```python
batch_slides(
    slides=[
        {"template": "hook", "fields": {"title": "200+", ...}},
        {"template": "features", "fields": {...}},
        {"template": "cta", "fields": {...}},
    ],
    project_name="quick_draft",
)
```

Templates: `hook`, `features`, `cta`, `comparison`, `quote`, `stats`, `blank`.

---

## Writing Narration Scripts

### Rules

1. **1-2 sentences per slide, 10-25 words.** Must fit within slide duration (4-6s).

2. **Write for speaking, not reading.** Conversational Vietnamese:
   - Bad: "Phần mềm này tích hợp trí tuệ nhân tạo để tự động hóa quy trình chăm sóc khách hàng."
   - Good: "AI tự động trả lời khách hàng... không cần nhân viên!"

3. **Punctuation for pacing:**
   - `...` → natural pause (0.3-0.5s)
   - `!` → vocal emphasis
   - `,` → brief pause
   - `.` → full stop and breath

4. **Match voice preset to content mood, not to a template name:**

   | Content Mood | Preset | Example |
   |-------------|--------|---------|
   | Opening / attention | `energetic` | "200 tin nhắn mỗi ngày... trả lời kịp không?" |
   | Explaining features | `informative` | "Phản hồi tự động 24/7. Tiết kiệm 70% chi phí." |
   | Showing contrast | `dramatic` | "3000 đô cho nhân viên... chỉ 200 đô cho AI!" |
   | Impressive numbers | `authoritative` | "Giảm 75%. Nhanh gấp 3. Hài lòng 98%!" |
   | Testimonial / story | `warm` | "Anh Minh chia sẻ... doanh thu tăng gấp 3." |
   | Call to action | `persuasive` | "Liên hệ ngay! Tư vấn miễn phí trong 24 giờ." |

5. **Don't narrate what's already on screen.** Add verbal context that complements the visual.

### Character Budget

ElevenLabs charges per character. A typical 5-slide video uses 300-500 characters.
Starter plan: 40,000 chars/month ≈ 80-130 videos.

---

## Voice Presets

### When to override auto-mapping

| Situation | Override to |
|-----------|-----------|
| Opening but calm topic (healthcare) | `authoritative` |
| CTA but soft sell | `warm` |
| Feature slide for exciting product | `energetic` |
| Stats that are shocking | `dramatic` |

### Speed tuning

| Content Type | Speed |
|-------------|-------|
| TikTok / Reels | 1.05 - 1.15 |
| Corporate / B2B | 0.90 - 1.00 |
| Emotional story | 0.85 - 0.95 |
| Product demo | 0.95 - 1.05 |

---

## Effect Pairing

| Slide Purpose | Best Effect | Why |
|--------------|------------|-----|
| Opening | `zoom_in` | Draws viewer in |
| Data/table content | `pan_down` or `pan_right` | Reveals content naturally |
| Contrast/comparison | `zoom_out` | Shows full picture |
| Technical diagram | `zoom_in` | Focus on detail |
| Closing CTA | `zoom_in` | Creates urgency |

**Rule:** Never use the same effect for consecutive slides.

---

## Common Mistakes

### 1. Using the same layout for every slide

```
# BAD — same template repeated = boring
slides = [hook, features, features, features, cta]

# GOOD — each slide unique design
slides = [
    custom_html_brand_intro,
    custom_html_fullbleed_screenshot,
    custom_html_split_layout_features,
    custom_html_big_number_overlay,
    custom_html_cta_with_checklist,
]
```

### 2. Small images in portrait video

Landscape screenshots (1440×900) in portrait video (1080×1920) must be zoomed in:

```css
/* BAD — tiny screenshot with huge margins */
.screen { width: 800px; border-radius: 16px; margin: auto; }

/* GOOD — full-width, zoomed with object-fit */
.container { width: 1080px; height: 1300px; overflow: hidden; }
.container img { width: 100%; height: 100%; object-fit: cover; }
```

### 3. Narration too long for slide duration

5 seconds ≈ 15-20 Vietnamese words max. Keep it punchy.

### 4. Forgetting to merge before adding audio

```python
# BAD
add_audio(video_path="slide_01.mp4", audio_path="voiceover.mp3")

# GOOD
merge_clips_crossfade(clip_paths=[...], output_filename="merged.mp4")
add_audio(video_path="merged.mp4", audio_path="voiceover.mp3")
```

### 5. Background music too loud over voiceover

```python
# OLD (manual 2-step, constant volume):
# add_audio(voice) → add_audio(music, vol=0.25)

# NEW (smart ducking — music auto-ducks when voice speaks):
mix_voiceover_music(
    video_path="merged.mp4",
    voiceover_path="voiceover.mp3",
    music_path="/path/to/music.mp3",   # use list_music to browse tracks
    music_volume=0.15,                  # base music level
    duck_level=0.1,                     # lower = more ducking
)
```

---

## Tool Call Sequences

| Task | Calls | Sequence |
|------|-------|----------|
| Custom video + voiceover | 4 | batch_slides (image mode) → generate_slide_narrations → merge_clips_crossfade → add_audio |
| Quick template video | 4 | batch_slides (template mode) → generate_slide_narrations → merge_clips_crossfade → add_audio |
| Video only (no voice) | 2 | batch_slides → merge_clips_crossfade |
| **Video + voice + music** | **4** | **batch_slides → generate_slide_narrations → merge_clips_crossfade → mix_voiceover_music** |
| Video + facecam | +1 | ...add_audio/mix_voiceover_music → **add_facecam** (overlay talking head, auto-loop) |
| Single poster | 1 | screenshot_html or create_slide |
| Resize for IG | 1 | resize_video (mode="crop", size="1080x1080") |

`batch_slides` and `generate_slide_narrations` can run **in parallel** — slides don't need to exist before generating narrations.

---

## Facecam Overlay (TikTok-style Talking Head)

Use `add_facecam` to overlay a talking-head video in a corner with rounded corners. The facecam loops automatically if shorter than the main video.

```python
# Always add facecam as the LAST step (after merge + audio)
add_facecam(
    video_path="final_with_audio.mp4",
    facecam_path="/path/to/facecam.mp4",
    output_filename="final_with_facecam.mp4",
    position="bottom-right",   # top-left, top-right, bottom-left, bottom-right
    size=30,                   # 30% of video width
    border_radius=20,          # rounded corners in pixels
    margin=20,                 # distance from edge in pixels
)
```

**Tips:**
- `size=25-35` works best for TikTok — visible but not covering content
- Use `bottom-right` (default) — least likely to cover important content
- Facecam video should be portrait format for best results
- If facecam is shorter than main video, it loops seamlessly

---

## Smart Audio Mixing

### When to use `mix_voiceover_music` vs `add_audio`

| Scenario | Tool | Why |
|----------|------|-----|
| Voice + background music | `mix_voiceover_music` | Auto-ducking, one step |
| Voice only (no music) | `add_audio` | Simple mux, no ducking needed |
| Music only (no voice) | `add_audio` | Simple mux |
| Replace/adjust audio later | `add_audio` | Incremental changes |

### Ducking parameters

| Parameter | Default | Effect |
|-----------|---------|--------|
| `music_volume` | `0.15` | Base music level. Increase for louder music during transitions |
| `duck_level` | `0.1` | Lower = more aggressive ducking. `0.05` for very quiet music under voice |
| `fade_out` | `2.0` | Music fades out at end. Set `0` for abrupt stop |

### Browsing music

Use `list_music` to see all available tracks with durations:
```python
list_music()  # → 31 tracks with names, paths, durations
```

Then pass the `file` path to `mix_voiceover_music(music_path=...)`.

---

## Checklist Before Delivering

- [ ] Each slide has unique visual design (no repeated layout)
- [ ] Images/screenshots zoomed in for portrait readability
- [ ] Effects vary across slides
- [ ] Narration 10-25 words per slide, conversational tone
- [ ] Voice preset matches content mood (not forced to template name)
- [ ] If voice + music: used `mix_voiceover_music` (auto-ducking), not 2x `add_audio`
- [ ] Music fades out at end (`fade_out=2.0`)
- [ ] Unique `project_name` used
- [ ] Output verified with `get_media_info`
- [ ] Resolution correct for target platform
