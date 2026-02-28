# Best Practices — Vidmake MCP for Claude Code

Guide for AI agents to create high-quality marketing videos efficiently.

---

## Decision Tree: Which Workflow?

```
User request received
  │
  ├─ "Tạo video quảng cáo / marketing video"
  │   └─ Workflow A: Full Video with Voiceover (4 calls)
  │
  ├─ "Tạo video nhanh / quick video"
  │   └─ Workflow B: Video Only (2 calls)
  │
  ├─ "Tạo poster / ảnh quảng cáo"
  │   └─ Use create_slide or screenshot_html (1 call)
  │
  ├─ "Sửa video / chỉnh video"
  │   └─ Use atomic tools: add_text_overlay, resize_video, add_audio
  │
  └─ "Tạo nhiều video cho nhiều sản phẩm"
      └─ Workflow C: Batch Production (loop Workflow A per product)
```

---

## Workflow A: Full Video with Voiceover (Recommended)

**4 tool calls. Best for marketing content.**

### Step 1: Plan slide structure BEFORE calling tools

Always plan the slide sequence first. A proven TikTok formula:

| Slide | Template | Purpose | Duration |
|-------|----------|---------|----------|
| 1 | `hook` | Shock stat / bold question | 4-5s |
| 2 | `features` or `comparison` | Explain the solution | 5-6s |
| 3 | `stats` | Prove with numbers | 5s |
| 4 | `quote` | Social proof | 5-6s |
| 5 | `cta` | Call to action | 4-5s |

For longer videos (30s+), add 1-2 more middle slides. For short videos (15s), use 3 slides: hook → features → cta.

### Step 2: Call batch_slides

```python
batch_slides(
    slides=[...],          # All slides at once
    project_name="unique", # IMPORTANT: unique per video to avoid file conflicts
    duration_per_slide=5.0,
)
```

**Key rules:**
- Always set a unique `project_name` — prevents overwriting other videos
- Call `cleanup_outputs(pattern="projectname_*")` first if re-generating
- Vary effects across slides: don't use `zoom_in` for all 5

### Step 3: Call generate_slide_narrations

```python
generate_slide_narrations(
    scripts=[
        {"text": "...", "template": "hook"},    # auto → energetic
        {"text": "...", "template": "features"}, # auto → informative
        ...
    ],
    project_name="same_as_step2",
    merge=True,
    silence_between=0.3,  # TikTok pace
)
```

### Step 4: Merge + add audio

```python
merge_clips_crossfade(clip_paths=[...], output_filename="project_merged.mp4")
add_audio(video_path="...merged.mp4", audio_path="...voiceover.mp3", output_filename="project_final.mp4")
```

---

## Writing Narration Scripts

**This is critical.** Bad scripts waste ElevenLabs characters and produce unnatural voiceover.

### Rules

1. **1-2 sentences per slide, 10-25 words.** The narration must fit within the slide's duration (4-6s).

2. **Write for speaking, not reading.** Use conversational Vietnamese:
   - Bad: "Phần mềm này tích hợp trí tuệ nhân tạo để tự động hóa quy trình chăm sóc khách hàng."
   - Good: "AI tự động trả lời khách hàng... không cần nhân viên!"

3. **Use punctuation for pacing:**
   - `...` → creates a natural pause (0.3-0.5s)
   - `!` → adds vocal emphasis
   - `,` → brief pause
   - `.` → full stop and breath

4. **Match tone to template type:**

   | Template | Script Style | Example |
   |----------|-------------|---------|
   | `hook` | Short, punchy, question | "200 tin nhắn mỗi ngày... trả lời kịp không?" |
   | `features` | Clear, benefit-focused | "Phản hồi tự động 24/7. Tiết kiệm 70% chi phí." |
   | `comparison` | Contrast, surprise | "3000 đô cho nhân viên... chỉ 200 đô cho AI!" |
   | `stats` | Impressive, rhythmic | "Giảm 75%. Nhanh gấp 3. Hài lòng 98%!" |
   | `quote` | Warm, storytelling | "Anh Minh chia sẻ... doanh thu tăng gấp 3 sau 2 tháng." |
   | `cta` | Urgent, direct | "Liên hệ ngay! Tư vấn miễn phí trong 24 giờ." |

5. **Don't narrate what's already on screen.** Add verbal context that complements the visual:
   - Screen shows "200+" → Narrate "Hơn 200 tin nhắn đổ về mỗi ngày"
   - Screen shows price comparison → Narrate the emotional impact "Tiết kiệm hơn 90%!"

### Character Budget

ElevenLabs charges per character. A typical 5-slide video uses 300-500 characters.

| Video Length | Slides | ~Characters | ~Cost (Starter) |
|-------------|--------|------------|-----------------|
| 15s | 3 | 150-250 | negligible |
| 25s | 5 | 300-500 | negligible |
| 45s | 8 | 500-800 | ~1% of quota |
| 60s | 10 | 700-1000 | ~2.5% of quota |

Starter plan: 40,000 chars/month = ~80-130 full videos.

---

## Voice Presets Deep Dive

### When to override defaults

The auto-mapping (template → preset) works well for 90% of cases. Override only when:

| Situation | Override to |
|-----------|-----------|
| Hook slide but calm topic (healthcare) | `preset: "authoritative"` |
| CTA slide but soft sell | `preset: "warm"` |
| Features slide for exciting product | `preset: "energetic"` |
| Quote from a CEO (formal) | `preset: "authoritative"` |
| Stats that are shocking | `preset: "dramatic"` |

### Speed tuning

| Content Type | Recommended Speed |
|-------------|------------------|
| TikTok / Reels | 1.05 - 1.15 (slightly fast) |
| Corporate / B2B | 0.90 - 1.00 (measured) |
| Emotional story | 0.85 - 0.95 (slow, dramatic) |
| Product demo | 0.95 - 1.05 (clear, normal) |

---

## Slide Design Patterns

### Vietnamese Marketing Content

**Color schemes that work:**
- Default dark gradient (built-in) — best for tech/SaaS
- Red + Gold (`primary: "#FF4444", accent: "#FFD700"`) — Tết, promotions, sales
- Green + White (`primary: "#00C853", accent: "#FFFFFF"`) — health, eco, organic
- Blue + Orange (`primary: "#2196F3", accent: "#FF9800"`) — corporate, finance

**Font tips:**
- Default `Segoe UI` works well for Vietnamese
- For formal: `"'Georgia', serif"`
- For modern: `"'Inter', sans-serif"`

### Effect Pairing

| Slide Position | Best Effect | Why |
|---------------|------------|-----|
| First (hook) | `zoom_in` | Draws viewer in |
| Middle (info) | `pan_down` or `pan_right` | Reveals content naturally |
| Comparison | `zoom_out` | Shows both sides at once |
| Last (CTA) | `zoom_in` or `zoom_out` | Creates urgency or openness |

**Never:** Same effect for consecutive slides. Auto-cycle handles this if you omit `effect`.

---

## Common Mistakes

### 1. Not using `project_name`

```
# BAD — files named video_01.mp4, mix with other projects
batch_slides(slides=[...])

# GOOD — files named trinity_01.mp4, isolated
batch_slides(slides=[...], project_name="trinity")
```

### 2. Narration too long for slide duration

Each slide is 5 seconds. At normal speed, Vietnamese speakers read ~3-4 words/second.
5 seconds = ~15-20 words max. If narration is longer, the voiceover will extend past the slide.

**Fix:** Keep scripts under 20 words per slide, or increase `duration_per_slide`.

### 3. Forgetting to merge before adding audio

```
# BAD — adds audio to a single clip, not the full video
add_audio(video_path="trinity_01.mp4", audio_path="voiceover.mp3")

# GOOD — merge first, then add audio
merge_clips_crossfade(clip_paths=[...], output_filename="merged.mp4")
add_audio(video_path="merged.mp4", audio_path="voiceover.mp3")
```

### 4. Not varying slide templates

```
# BAD — all features templates = boring
slides = [
    {"template": "features", ...},
    {"template": "features", ...},
    {"template": "features", ...},
]

# GOOD — varied templates = engaging
slides = [
    {"template": "hook", ...},
    {"template": "features", ...},
    {"template": "comparison", ...},
    {"template": "stats", ...},
    {"template": "cta", ...},
]
```

### 5. Adding background music too loud over voiceover

```
# BAD — music drowns out voice
add_audio(video_path="with_voice.mp4", audio_path="music.mp3", audio_volume=1.0)

# GOOD — subtle background
add_audio(video_path="with_voice.mp4", audio_path="music.mp3", audio_volume=0.25, fade_out_duration=2.0)
```

---

## Optimal Tool Call Sequences

### Minimum calls for common tasks

| Task | Calls | Sequence |
|------|-------|----------|
| Video + voiceover | 4 | batch_slides → generate_slide_narrations → merge_clips_crossfade → add_audio |
| Video only | 2 | batch_slides → merge_clips_crossfade |
| Video + voiceover + music + watermark | 6 | batch_slides → generate_slide_narrations → merge_clips_crossfade → add_audio (voice) → add_audio (music, vol=0.25) → add_text_overlay |
| Single poster | 1 | create_slide |
| Re-do voiceover only | 2 | generate_slide_narrations → add_audio |
| Resize for Instagram | 1 | resize_video (mode="crop", size="1080x1080") |

### Parallelism

`batch_slides` and `generate_slide_narrations` are independent — they CAN run in parallel if the AI agent supports it. Slides don't need to exist before generating narrations.

---

## Checklist Before Delivering Video

- [ ] Used unique `project_name` (not "video")
- [ ] Slide 1 is a `hook` (attention-grabbing)
- [ ] Last slide is a `cta` (call to action)
- [ ] Effects vary across slides (no 5x zoom_in)
- [ ] Narration scripts are 10-25 words per slide
- [ ] Template type included in narration scripts for auto-tone
- [ ] Merged voiceover synced with video duration
- [ ] Output verified with `get_media_info`
- [ ] Resolution is correct for target platform (1080x1920 for TikTok)
