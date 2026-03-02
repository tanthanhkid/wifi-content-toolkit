#!/usr/bin/env python3
"""Produce TikTok video: NotebookLM + Antigravity no-code workflow.
Narration-first approach: generate voiceover → match slide duration to narration."""
import sys, os, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vidmake.core import (
    record_html_video, create_animated_slideshow,
    mix_audio_with_ducking, add_facecam_overlay
)
from pathlib import Path
OUT = Path.home() / "vidmake-output"
OUT.mkdir(exist_ok=True)
PROJECT = "nocode_google"

def get_mp3_duration(path: str) -> float:
    """Get MP3 duration via ffprobe."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, timeout=10
    )
    return float(r.stdout.strip())

# ── Slide definitions: (html, narration_text, voice_preset) ──
slides_data = [
    # Slide 1: HOOK
    {
        "narration": "Tạo app mà không cần lập trình viên? Hoàn toàn miễn phí!",
        "preset": "energetic",
        "html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
display:flex;flex-direction:column;justify-content:center;align-items:center;overflow:hidden;color:#fff}
.hook{font-size:78px;font-weight:900;text-align:center;line-height:1.2;padding:0 60px;animation:slideUp 0.8s ease both}
.sub{font-size:42px;color:#a78bfa;margin-top:40px;font-weight:600;animation:fadeIn 0.6s 0.5s ease both;text-align:center}
@keyframes slideUp{from{transform:translateY(100px);opacity:0}to{transform:translateY(0);opacity:1}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.icon{font-size:120px;animation:bounce 1s 0.3s ease both;margin-bottom:40px}
@keyframes bounce{0%{transform:scale(0)}50%{transform:scale(1.3)}100%{transform:scale(1)}}
</style></head><body>
<div class='icon'>🚀</div>
<div class='hook'>Tạo app mà<br>KHÔNG CẦN<br>lập trình viên?</div>
<div class='sub'>Hoàn toàn miễn phí!</div>
</body></html>""",
    },
    # Slide 2: Screenshot X post (Ken Burns)
    {
        "narration": "Một bài đăng viral vừa tiết lộ... quy trình cực đơn giản chỉ với hai công cụ AI miễn phí của Google.",
        "preset": "dramatic",
        "image": "D:/Work/wifi-content-toolkit/screenshots/xpost_seo_ai_automation.png",
        "effect": "zoom_in",
    },
    # Slide 3: Quy trình 4 bước
    {
        "narration": "Bước một, upload tài liệu vào NotebookLM. Bước hai, AI phân tích và tạo bản thiết kế. Bước ba, xuất ra Google Docs. Bước bốn, dán vào Antigravity... và nó tự build sản phẩm thật!",
        "preset": "warm",
        "html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(160deg,#1a1a2e,#16213e,#0f3460);
display:flex;flex-direction:column;justify-content:center;padding:0 70px;overflow:hidden;color:#fff}
.title{font-size:52px;font-weight:800;color:#67e8f9;margin-bottom:50px;animation:fadeIn 0.6s ease both}
.step{display:flex;align-items:flex-start;margin-bottom:35px;gap:25px}
.num{font-size:56px;font-weight:900;color:#f59e0b;min-width:60px;animation:scaleIn 0.5s ease both}
.txt{font-size:38px;font-weight:600;line-height:1.4;animation:slideRight 0.6s ease both}
.step:nth-child(2) .txt{animation-delay:0.4s}.step:nth-child(2) .num{animation-delay:0.4s}
.step:nth-child(3) .txt{animation-delay:0.7s}.step:nth-child(3) .num{animation-delay:0.7s}
.step:nth-child(4) .txt{animation-delay:1.0s}.step:nth-child(4) .num{animation-delay:1.0s}
.step:nth-child(5) .txt{animation-delay:1.3s}.step:nth-child(5) .num{animation-delay:1.3s}
@keyframes fadeIn{from{opacity:0;transform:translateY(-30px)}to{opacity:1;transform:translateY(0)}}
@keyframes scaleIn{from{transform:scale(0);opacity:0}to{transform:scale(1);opacity:1}}
@keyframes slideRight{from{transform:translateX(-60px);opacity:0}to{transform:translateX(0);opacity:1}}
</style></head><body>
<div class='title'>Quy trình 4 bước:</div>
<div class='step'><div class='num'>1</div><div class='txt'>Upload tài liệu, PDF, ghi chú vào NotebookLM</div></div>
<div class='step'><div class='num'>2</div><div class='txt'>AI phân tích và tạo bản thiết kế chi tiết</div></div>
<div class='step'><div class='num'>3</div><div class='txt'>Xuất blueprint sang Google Docs</div></div>
<div class='step'><div class='num'>4</div><div class='txt'>Dán vào Antigravity — nó build sản phẩm thật!</div></div>
</body></html>""",
    },
    # Slide 4: VS comparison
    {
        "narration": "Thuê dev tốn hàng trăm triệu, đợi cả nửa năm. Còn combo AI này... miễn phí, chỉ vài giờ là xong!",
        "preset": "dramatic",
        "html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(145deg,#0d1b2a,#1b2838,#2d4059);
display:flex;flex-direction:column;justify-content:center;align-items:center;padding:0 60px;overflow:hidden;color:#fff}
.vs{display:flex;flex-direction:column;gap:50px;width:100%}
.box{border-radius:24px;padding:45px;animation:popIn 0.5s ease both}
.box:nth-child(1){background:linear-gradient(135deg,#ef4444,#dc2626);animation-delay:0.3s}
.box:nth-child(3){background:linear-gradient(135deg,#22c55e,#16a34a);animation-delay:0.7s}
.label{font-size:36px;font-weight:600;opacity:0.9;margin-bottom:15px}
.val{font-size:52px;font-weight:900;line-height:1.3}
.divider{font-size:64px;text-align:center;animation:fadeIn 0.4s 0.5s ease both}
@keyframes popIn{from{transform:scale(0.5);opacity:0}to{transform:scale(1);opacity:1}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
</style></head><body>
<div class='vs'>
<div class='box'><div class='label'>❌ Cách truyền thống</div><div class='val'>Thuê dev → Hàng trăm triệu<br>Đợi 3-6 tháng</div></div>
<div class='divider'>⚡ VS ⚡</div>
<div class='box'><div class='label'>✅ Combo AI miễn phí</div><div class='val'>NotebookLM + Antigravity<br>Vài giờ → Sản phẩm thật!</div></div>
</div>
</body></html>""",
    },
    # Slide 5: Áp dụng cho SME
    {
        "narration": "Doanh nghiệp Việt áp dụng được ngay! Landing page, dashboard nội bộ, hệ thống đơn hàng, hay app prototype trình bày đối tác.",
        "preset": "warm",
        "html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(135deg,#064e3b,#065f46,#047857);
display:flex;flex-direction:column;justify-content:center;padding:0 70px;overflow:hidden;color:#fff}
.title{font-size:48px;font-weight:800;color:#fbbf24;margin-bottom:50px;animation:fadeDown 0.6s ease both}
.item{display:flex;align-items:center;gap:20px;margin-bottom:35px;animation:slideLeft 0.5s ease both}
.item:nth-child(2){animation-delay:0.3s}
.item:nth-child(3){animation-delay:0.6s}
.item:nth-child(4){animation-delay:0.9s}
.item:nth-child(5){animation-delay:1.2s}
.check{font-size:48px}.txt{font-size:40px;font-weight:600;line-height:1.3}
@keyframes fadeDown{from{opacity:0;transform:translateY(-40px)}to{opacity:1;transform:translateY(0)}}
@keyframes slideLeft{from{opacity:0;transform:translateX(80px)}to{opacity:1;transform:translateX(0)}}
</style></head><body>
<div class='title'>Doanh nghiệp Việt áp dụng được gì?</div>
<div class='item'><span class='check'>✅</span><span class='txt'>Landing page bán hàng</span></div>
<div class='item'><span class='check'>✅</span><span class='txt'>Dashboard quản lý nội bộ</span></div>
<div class='item'><span class='check'>✅</span><span class='txt'>Hệ thống quản lý đơn hàng</span></div>
<div class='item'><span class='check'>✅</span><span class='txt'>App prototype trình bày đối tác</span></div>
</body></html>""",
    },
    # Slide 6: CTA
    {
        "narration": "Từ ý tưởng đến sản phẩm chỉ trong vài giờ! Bạn sẽ thử build cái gì đầu tiên? Comment cho tôi biết!",
        "preset": "energetic",
        "html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(135deg,#4c1d95,#6d28d9,#7c3aed);
display:flex;flex-direction:column;justify-content:center;align-items:center;padding:0 60px;overflow:hidden;color:#fff}
.cta{font-size:58px;font-weight:900;text-align:center;line-height:1.3;animation:fadeIn 0.6s ease both;margin-bottom:50px}
.question{font-size:44px;font-weight:700;color:#fde68a;text-align:center;animation:slideUp 0.6s 0.4s ease both;line-height:1.4}
.follow{margin-top:50px;font-size:36px;color:#c4b5fd;animation:fadeIn 0.5s 0.8s ease both}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes slideUp{from{transform:translateY(50px);opacity:0}to{transform:translateY(0);opacity:1}}
</style></head><body>
<div class='cta'>Từ ý tưởng đến sản phẩm...<br>chỉ trong vài giờ!</div>
<div class='question'>Bạn sẽ thử build cái gì đầu tiên?<br>Comment cho tôi biết!</div>
<div class='follow'>Follow để xem thêm mẹo AI miễn phí 🔥</div>
</body></html>""",
    },
]

# ══════════════════════════════════════════════════════════════
# STEP 1: Generate narrations FIRST (to get per-slide durations)
# ══════════════════════════════════════════════════════════════
print("=== Step 1: Generating narrations (ElevenLabs) ===")

# Use the existing narration files if they exist
narration_files = []
narration_durations = []
all_exist = all(
    (OUT / f"{PROJECT}_narration_{i+1:02d}.mp3").exists()
    for i in range(len(slides_data))
)

if all_exist:
    print("  Using existing narration files...")
    for i in range(len(slides_data)):
        path = str(OUT / f"{PROJECT}_narration_{i+1:02d}.mp3")
        dur = get_mp3_duration(path)
        narration_files.append(path)
        narration_durations.append(dur)
        print(f"  Slide {i+1}: {dur:.1f}s — {path}")
else:
    print("  ERROR: Narration files not found. Generate them first via MCP.")
    print("  Run: mcp__vidmake__generate_slide_narrations")
    sys.exit(1)

print(f"\n  Total narration: {sum(narration_durations):.1f}s")

# ══════════════════════════════════════════════════════════════
# STEP 2: Record slides with duration matching narration
# ══════════════════════════════════════════════════════════════
print("\n=== Step 2: Recording slides (duration = narration + 0.5s buffer) ===")
clip_paths = []

for i, slide in enumerate(slides_data):
    idx = i + 1
    # Slide duration = narration duration + small buffer for crossfade
    slide_dur = narration_durations[i] + 0.5
    mp4_path = str(OUT / f"{PROJECT}_{idx:02d}.mp4")

    if "image" in slide:
        # Ken Burns for screenshot
        print(f"  Slide {idx}: Ken Burns ({slide_dur:.1f}s)...")
        result = create_animated_slideshow(
            images=[slide["image"]],
            output_path=mp4_path,
            duration_per_slide=slide_dur,
            effects=[slide.get("effect", "zoom_in")],
            size="1080x1920",
            fps=30
        )
    else:
        # CSS animated
        print(f"  Slide {idx}: CSS animated ({slide_dur:.1f}s)...")
        result = record_html_video(
            html_content=slide["html"],
            output_path=mp4_path,
            duration=slide_dur,
            width=1080,
            height=1920,
            fps=30,
            encoder="libx264"  # Force libx264 for speed
        )

    if result.get("success"):
        clip_paths.append(result.get("output_path", mp4_path))
        print(f"    ✓ {clip_paths[-1]}")
    else:
        print(f"    ✗ {result.get('error')}")
        sys.exit(1)

# ══════════════════════════════════════════════════════════════
# STEP 3: Merge clips with ffmpeg concat
# ══════════════════════════════════════════════════════════════
print("\n=== Step 3: Merging clips ===")
merged_path = str(OUT / f"{PROJECT}_merged.mp4")
concat_file = str(OUT / f"{PROJECT}_concat.txt")
with open(concat_file, "w") as f:
    for p in clip_paths:
        f.write(f"file '{p}'\n")

cmd = [
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
    "-r", "30", "-crf", "23", "-movflags", "+faststart", "-an", merged_path
]
proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
os.remove(concat_file)
if proc.returncode == 0:
    print(f"  ✓ Merged: {merged_path}")
else:
    print(f"  ✗ {proc.stderr[-300:]}")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
# STEP 4: Merge narrations into single voiceover (ffmpeg concat)
# ══════════════════════════════════════════════════════════════
print("\n=== Step 4: Merging narrations ===")
voiceover_path = str(OUT / f"{PROJECT}_voiceover_synced.mp3")

# Build ffmpeg filter to concat narrations with 0.3s silence gaps
silence_gap = 0.3
filter_parts = []
inputs = []
for i, nf in enumerate(narration_files):
    inputs.extend(["-i", nf])
    filter_parts.append(f"[{i}:a]aresample=44100[a{i}];")
    if i < len(narration_files) - 1:
        filter_parts.append(f"aevalsrc=0:d={silence_gap}[s{i}];")

# Build concat
concat_inputs = []
for i in range(len(narration_files)):
    concat_inputs.append(f"[a{i}]")
    if i < len(narration_files) - 1:
        concat_inputs.append(f"[s{i}]")

n_segments = len(narration_files) * 2 - 1
filter_str = "".join(filter_parts) + "".join(concat_inputs) + f"concat=n={n_segments}:v=0:a=1[out]"

cmd = ["ffmpeg", "-y"] + inputs + [
    "-filter_complex", filter_str,
    "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", voiceover_path
]
proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
if proc.returncode == 0:
    print(f"  ✓ Voiceover: {voiceover_path}")
else:
    print(f"  ✗ {proc.stderr[-300:]}")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
# STEP 5: Mix voiceover + background music
# ══════════════════════════════════════════════════════════════
print("\n=== Step 5: Mix voiceover + music ===")
mixed_path = str(OUT / f"{PROJECT}_mixed.mp4")
music_path = "D:/Work/wifi-content-toolkit/music/sigmamusicart-background-music-corporate-484577.mp3"

cmd = [
    "ffmpeg", "-y",
    "-i", merged_path,
    "-i", voiceover_path,
    "-i", music_path,
    "-filter_complex",
    "[1:a]volume=1.0[voice];[2:a]volume=0.15,afade=t=out:st=50:d=3[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
    "-map", "0:v", "-map", "[aout]",
    "-c:v", "copy",  # No re-encode video!
    "-c:a", "aac", "-b:a", "192k", "-shortest",
    "-movflags", "+faststart", mixed_path
]
proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
if proc.returncode == 0:
    print(f"  ✓ Mixed: {mixed_path}")
else:
    print(f"  ✗ {proc.stderr[-300:]}")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
# STEP 6: Add facecam
# ══════════════════════════════════════════════════════════════
print("\n=== Step 6: Adding facecam ===")
final_path = str(OUT / "tao-app-khong-can-lap-trinh-vien.mp4")
result = add_facecam_overlay(
    video_path=mixed_path,
    facecam_path="D:/Work/wifi-content-toolkit/human",
    output_path=final_path,
    position="bottom-left",
    size=22,
    border_radius=20,
    margin=350
)
if result.get("success"):
    print(f"  ✓ Final: {final_path}")
else:
    print(f"  ✗ {result.get('error')}")
    sys.exit(1)

print(f"\n{'='*60}")
print(f"DONE! Video: {final_path}")
print(f"{'='*60}")
