# Best Practices — Vidmake MCP for Claude Code

Guide for AI agents to create high-quality marketing videos efficiently.

---

## MANDATORY: Every Video Must Have These

**All videos produced MUST include ALL of the following:**

| Component | Required | Details |
|-----------|----------|---------|
| **CSS Animated slides** | YES | All text/content slides use `"animated": true`. Ken Burns ONLY for image/screenshot slides. |
| **Voiceover** | YES | Vietnamese narration with per-slide voice presets |
| **Background music** | YES | Always use `mix_voiceover_music` with a track from `music/`. NEVER deliver without music. |
| **Facecam** | YES | Always add facecam from `human/` folder as the LAST step. |
| **Screenshots** | When relevant | If content involves a website, app, or product — take screenshots (Playwright/Firecrawl) and include as slides. |

**If you want to skip facecam for any reason, you MUST ask the user first.** Never skip silently.

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
  │   ├─ Production quality, static → Custom HTML (Workflow A)
  │   └─ Animated text (fly-in, bounce, typewriter) → CSS animations (Workflow C)
  │
  ├─ "CapCut/PowerPoint-style text animations"
  │   └─ CSS animations with "animated": true (Workflow C)
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

### Step 4: Animate, Voiceover, Merge, Music, Facecam

```python
# Animate — CSS animated for text, Ken Burns for screenshots
batch_slides(
    slides=[
        {"html": "<html with @keyframes>", "animated": True},         # Text → CSS animated
        {"html": "<html with @keyframes>", "animated": True},         # Text → CSS animated
        {"image": "/path/to/screenshot.png", "effect": "zoom_in"},    # Screenshot → Ken Burns
        {"html": "<html with @keyframes>", "animated": True},         # Text → CSS animated
    ],
    project_name="unique_name",
    duration_per_slide=5,
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

# Voice + background music with auto-ducking (MANDATORY — always include music)
mix_voiceover_music(
    video_path="merged.mp4",
    voiceover_path="voiceover.mp3",
    music_path="/path/to/music.mp3",  # use list_music() to browse
    music_volume=0.15,
    duck_level=0.1,
)

# Facecam overlay (MANDATORY — always add, ask user if skipping)
add_facecam(
    video_path="with_audio.mp4",
    facecam_path="/path/to/human/clip.mp4",  # pick from human/ folder
    output_filename="final.mp4",
    position="middle-left", size=28, border_radius=20, margin=25,
)
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

## Workflow C: CSS Animation Recording (CapCut-style Text Animations)

**Best for text animations: fadeIn, slideUp, bounce, typewriter, stagger.**

Instead of Ken Burns (zoom/pan on a static image), this records the browser playing CSS `@keyframes` animations in real-time via Playwright video recording.

```
WORKFLOW A (Ken Burns):  HTML → screenshot (PNG) → FFmpeg zoompan → MP4
WORKFLOW C (CSS anim):   HTML + @keyframes → Playwright record video → MP4
```

### When to Use Which

| Content | Workflow | Why |
|---------|----------|-----|
| **All text/content slides** | **C (CSS anim) — DEFAULT** | **CSS animated is the standard for all text slides** |
| Image/screenshot showcase | A (Ken Burns) | Zoom/pan makes static images feel alive |
| Text flying in, bouncing | C (CSS anim) | Ken Burns can't animate individual elements |
| Typewriter effect | C (CSS anim) | Requires per-character animation |
| Numbers counting up | C (CSS anim) | Requires JS + CSS animation |
| Static text on gradient bg | C (CSS anim) | Use fadeIn/slideUp instead of Ken Burns for text |
| Mixed (some animated, some static) | A + C | `"animated": true` for text, Ken Burns for images |

### How to Use

**Option 1: `batch_slides` with `"animated": true` (recommended)**

```python
batch_slides(
    slides=[
        # Static slide → Ken Burns zoom
        {"html": "<html>...</html>", "effect": "zoom_in"},
        # Animated slide → CSS animation recording
        {"html": "<html with @keyframes>...</html>", "animated": True},
        # Animated with custom duration
        {"html": "...", "animated": True, "duration": 6.0},
    ],
    project_name="mixed_video",
)
```

**Option 2: `record_html_video` (single slide)**

```python
record_html_video(
    html_content="<html with CSS animations>...",
    filename="animated_slide.mp4",
    duration=5.0,
)
```

### CSS Animation Timing Rules

- Total animation timeline ≤ slide duration (4-6s)
- Reserve **0.5s at start** before first element appears (enter delay)
- Reserve **0.3s at end** so last element is visible before cut
- Use `animation-fill-mode: both` on ALL animated elements
- Stagger formula: `animation-delay: calc(0.3s + INDEX × 0.4s)`
- Smooth easing: `cubic-bezier(0.25, 0.46, 0.45, 0.94)`

### Timing Blueprint (5s slide)

```
0.0s ─────── 0.5s ─────── 1.0s ─────── 2.0s ─────── 3.5s ─────── 4.7s ─── 5.0s
│  dark bg    │  title     │  element 1  │  element 2  │  element 3  │  hold │
│  (wait)     │  fadeIn    │  slideUp    │  slideUp    │  slideUp    │       │
```

### CSS Animation Pattern Library

**1. fadeIn** — opacity 0→1

```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.fade { animation: fadeIn 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) both; }
```

**2. slideUp** — translate from below

```css
@keyframes slideUp {
  from { opacity: 0; transform: translateY(60px); }
  to { opacity: 1; transform: translateY(0); }
}
.slide-up { animation: slideUp 0.7s cubic-bezier(0.25, 0.46, 0.45, 0.94) both; }
```

**3. slideInLeft** — translate from left

```css
@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-80px); }
  to { opacity: 1; transform: translateX(0); }
}
.slide-left { animation: slideInLeft 0.7s ease-out both; }
```

**4. scaleBounce** — scale 0→1.1→1 (great for numbers/stats)

```css
@keyframes scaleBounce {
  0% { opacity: 0; transform: scale(0); }
  60% { opacity: 1; transform: scale(1.15); }
  100% { transform: scale(1); }
}
.bounce { animation: scaleBounce 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
```

**5. typewriter** — characters appear one by one

```css
@keyframes typewriter {
  from { width: 0; }
  to { width: 100%; }
}
.typewriter {
  overflow: hidden;
  white-space: nowrap;
  border-right: 3px solid #6C63FF;
  animation: typewriter 2s steps(20) both, blink 0.5s step-end infinite alternate;
}
@keyframes blink { 50% { border-color: transparent; } }
```

**6. stagger** — list items appear one by one

```css
.stagger-item {
  animation: slideUp 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
}
.stagger-item:nth-child(1) { animation-delay: 0.3s; }
.stagger-item:nth-child(2) { animation-delay: 0.7s; }
.stagger-item:nth-child(3) { animation-delay: 1.1s; }
.stagger-item:nth-child(4) { animation-delay: 1.5s; }
```

**7. glowPulse** — text glow effect

```css
@keyframes glowPulse {
  0%, 100% { text-shadow: 0 0 20px rgba(108, 99, 255, 0.5); }
  50% { text-shadow: 0 0 40px rgba(108, 99, 255, 0.9), 0 0 80px rgba(108, 99, 255, 0.4); }
}
.glow {
  animation: fadeIn 0.5s ease both, glowPulse 2s ease-in-out 0.5s infinite;
}
```

**8. counter** — JS number count-up (requires `<script>`)

```html
<div class="counter" data-target="200">0</div>
<script>
document.querySelectorAll('.counter').forEach(el => {
  const target = +el.dataset.target;
  const duration = 2000;
  const start = performance.now();
  (function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    el.textContent = Math.floor(progress * target);
    if (progress < 1) requestAnimationFrame(tick);
  })(start);
});
</script>
```

### Full Animated Slide Example — Hook with Stagger

```html
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 1080px; height: 1920px;
  background: linear-gradient(135deg, #0a0a2e, #1a1a4e, #0d0d3a);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  font-family: 'Segoe UI', sans-serif; color: #fff;
  padding: 80px; text-align: center;
}
@keyframes fadeIn {
  from { opacity: 0; } to { opacity: 1; }
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(60px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes scaleBounce {
  0% { opacity: 0; transform: scale(0); }
  60% { opacity: 1; transform: scale(1.15); }
  100% { transform: scale(1); }
}
.badge {
  background: rgba(255,101,132,0.2); border: 2px solid #FF6584;
  border-radius: 50px; padding: 15px 40px; font-size: 28px;
  color: #FF6584; letter-spacing: 2px;
  animation: fadeIn 0.5s ease both;
  animation-delay: 0.3s;
}
.big {
  font-size: 140px; font-weight: 900; margin: 30px 0;
  background: linear-gradient(90deg, #FF6584, #FF8E53);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  animation: scaleBounce 0.8s cubic-bezier(0.34,1.56,0.64,1) both;
  animation-delay: 0.8s;
}
h2 {
  font-size: 48px; font-weight: 300; line-height: 1.4;
  animation: slideUp 0.7s cubic-bezier(0.25,0.46,0.45,0.94) both;
  animation-delay: 1.4s;
}
.hl {
  color: #6C63FF; -webkit-text-fill-color: #6C63FF; font-weight: 700;
  animation: slideUp 0.7s cubic-bezier(0.25,0.46,0.45,0.94) both;
  animation-delay: 1.8s;
}
</style></head>
<body>
  <div class="badge">THỐNG KÊ 2026</div>
  <div class="big">200+</div>
  <h2>tin nhắn mỗi ngày</h2>
  <div class="hl">Bạn trả lời kịp không?</div>
</body></html>
```

Use with: `{"html": "...", "animated": true, "duration": 5.0}`

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
| Text flying in/bouncing | `animated: true` | CSS animations (no Ken Burns) |
| Numbers counting up | `animated: true` | JS + CSS counter animation |
| Typewriter effect | `animated: true` | Per-character CSS animation |

**Rule:** Never use the same effect for consecutive slides. Mix Ken Burns and CSS animated slides for variety.

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

### Standard Full Video (5 steps — ALL mandatory)

```
1. batch_slides              → CSS animated (text) + Ken Burns (screenshots)
2. generate_slide_narrations → Vietnamese voiceover
3. merge_clips_crossfade     → Merged video
4. mix_voiceover_music       → Voice + background music (ALWAYS)
5. add_facecam               → Facecam overlay (ALWAYS, last step)
```

**Steps 1 & 2 can run in parallel** — narrations don't need slides to exist first.

### All Sequences

| Task | Calls | Sequence |
|------|-------|----------|
| **Full video (standard)** | **5** | **batch_slides → narrations → merge → mix_voiceover_music → add_facecam** |
| CSS animated + screenshots | 5 | batch_slides (mixed animated) → narrations → merge → mix_voiceover_music → add_facecam |
| Web-to-video (URL provided) | 6 | Firecrawl scrape + Playwright screenshots → batch_slides → narrations → merge → mix_voiceover_music → add_facecam |
| Single poster | 1 | screenshot_html or create_slide |
| Resize for IG | 1 | resize_video (mode="crop", size="1080x1080") |

### When to Ask the User

| Situation | Action |
|-----------|--------|
| User didn't mention facecam | Still add facecam (mandatory). Pick a clip from `human/`. |
| User explicitly says "no facecam" | OK to skip — user has been consulted. |
| You want to skip facecam for any reason | **ASK the user first.** Never skip silently. |
| User didn't mention music | Still add music (mandatory). Pick a fitting track from `music/`. |
| User explicitly says "no music" | OK to skip — user has been consulted. |

---

## Facecam Overlay (TikTok-style Talking Head)

Use `add_facecam` to overlay a talking-head video in a corner with rounded corners. The facecam loops automatically if shorter than the main video.

```python
# Always add facecam as the LAST step (after merge + audio)
add_facecam(
    video_path="final_with_audio.mp4",
    facecam_path="/path/to/facecam.mp4",
    output_filename="final_with_facecam.mp4",
    position="middle-left",    # middle-left, top-left, top-right, bottom-left, bottom-right
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

### Mandatory Components
- [ ] **CSS Animated slides** — all text/content slides use `"animated": true`
- [ ] **Ken Burns** — only for image/screenshot slides (not for text)
- [ ] **Background music** — used `mix_voiceover_music` (NEVER deliver without music)
- [ ] **Facecam** — added as last step (if skipped, user was asked and agreed)
- [ ] **Screenshots** — if content is about a website/app, screenshots are included

### Quality Checks
- [ ] Each slide has unique visual design (no repeated layout)
- [ ] Images/screenshots zoomed in for portrait readability
- [ ] Effects vary across slides (mix Ken Burns + CSS animations for variety)
- [ ] Animated slides use `animation-fill-mode: both` on all elements
- [ ] Animated slide timing fits within duration (reserve 0.5s start + 0.3s end)
- [ ] Narration 10-25 words per slide, conversational tone
- [ ] Voice preset matches content mood (not forced to template name)
- [ ] Music fades out at end (`fade_out=2.0`)
- [ ] Unique `project_name` used
- [ ] Output verified with `get_media_info`
- [ ] Resolution correct for target platform
