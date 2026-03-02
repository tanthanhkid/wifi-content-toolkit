#!/usr/bin/env python3
"""Produce TikTok video: Qwen3-Coder-Next open-source AI model."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vidmake.core import record_html_video, create_animated_slideshow, add_facecam_overlay
from pathlib import Path

OUT = Path.home() / "vidmake-output"
PROJECT = "qwen_coder"

def get_duration(path):
    r = subprocess.run(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",path],
                       capture_output=True, text=True, timeout=10)
    return float(r.stdout.strip())

# ── Get narration durations ──
print("=== Step 1: Reading narration durations ===")
nar_durs = []
for i in range(6):
    p = str(OUT / f"{PROJECT}_narration_{i+1:02d}.mp3")
    d = get_duration(p)
    nar_durs.append(d)
    print(f"  Slide {i+1}: {d:.1f}s")
print(f"  Total: {sum(nar_durs):.1f}s")

# ── Slide HTML definitions ──
slides = [
    # Slide 1: HOOK
    {"html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(135deg,#1e1b4b,#312e81,#4338ca);
display:flex;flex-direction:column;justify-content:center;align-items:center;overflow:hidden;color:#fff}
.big{font-size:140px;font-weight:900;color:#fbbf24;animation:popIn 0.6s 0.2s ease both}
.label{font-size:38px;color:#a5b4fc;margin-top:10px;animation:fadeIn 0.5s 0.4s ease both}
.vs{font-size:72px;font-weight:900;margin:40px 0;animation:scaleIn 0.5s 0.6s ease both}
.big2{font-size:100px;font-weight:900;color:#ef4444;animation:popIn 0.6s 0.8s ease both}
.label2{font-size:38px;color:#fca5a5;margin-top:10px;animation:fadeIn 0.5s 1.0s ease both}
.title{font-size:52px;font-weight:800;margin-top:60px;text-align:center;padding:0 60px;animation:slideUp 0.6s 1.2s ease both}
@keyframes popIn{from{transform:scale(0);opacity:0}to{transform:scale(1);opacity:1}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes scaleIn{from{transform:scale(0)}to{transform:scale(1)}}
@keyframes slideUp{from{transform:translateY(50px);opacity:0}to{transform:translateY(0);opacity:1}}
</style></head><body>
<div class='big'>3B</div>
<div class='label'>tham số</div>
<div class='vs'>⚡ đánh bại ⚡</div>
<div class='big2'>60B</div>
<div class='label2'>tham số</div>
<div class='title'>Model nhỏ mà mạnh!</div>
</body></html>"""},

    # Slide 2: Post card (readable on portrait)
    {"html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(160deg,#0a0a0a,#1a1a2e);
display:flex;flex-direction:column;justify-content:center;align-items:center;padding:0 50px;overflow:hidden;color:#fff}
.card{background:#16181c;border:1px solid #2f3336;border-radius:24px;padding:50px;width:100%;animation:fadeIn 0.6s ease both}
.header{display:flex;align-items:center;gap:20px;margin-bottom:30px}
.avatar{width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:900;color:#fff}
.name{font-size:32px;font-weight:700}
.handle{font-size:26px;color:#71767b;margin-top:4px}
.content{font-size:36px;line-height:1.5;color:#e7e9ea;margin-bottom:35px;animation:slideUp 0.5s 0.3s ease both}
.highlight{color:#1d9bf0;font-weight:700}
.bold{font-weight:800;color:#fbbf24}
.metrics{display:flex;gap:40px;color:#71767b;font-size:26px;animation:fadeIn 0.5s 0.6s ease both}
.metric{display:flex;align-items:center;gap:8px}
.metric-num{color:#e7e9ea;font-weight:700}
.tag{background:#1d9bf0;color:#fff;font-size:24px;font-weight:700;padding:8px 20px;border-radius:20px;display:inline-block;margin-top:25px;animation:popIn 0.4s 0.8s ease both}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes slideUp{from{transform:translateY(30px);opacity:0}to{transform:translateY(0);opacity:1}}
@keyframes popIn{from{transform:scale(0)}to{transform:scale(1)}}
</style></head><body>
<div class='card'>
<div class='header'>
<div class='avatar'>H</div>
<div><div class='name'>Harmanjot Kaur ✓</div><div class='handle'>@sukhdeep7896</div></div>
</div>
<div class='content'>
Qwen just dropped the <span class='highlight'>open-source</span> killer.<br><br>
It's called <span class='bold'>Qwen3-Coder-Next</span> and it's genuinely wild.<br><br>
Only <span class='bold'>3B active parameters</span> but beats models with <span class='bold'>10x-20x MORE</span> parameters on SWE-Bench-Pro.<br><br>
<span class='highlight'>1,000 free requests/day.</span>
</div>
<div class='metrics'>
<div class='metric'>❤️ <span class='metric-num'>37</span></div>
<div class='metric'>🔁 <span class='metric-num'>11</span></div>
<div class='metric'>🔖 <span class='metric-num'>15</span></div>
<div class='metric'>👁️ <span class='metric-num'>1.5K</span></div>
</div>
<div class='tag'>🔥 ĐANG VIRAL</div>
</div>
</body></html>"""},

    # Slide 3: Ý nghĩa
    {"html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(160deg,#0c4a6e,#075985,#0369a1);
display:flex;flex-direction:column;justify-content:center;padding:0 70px;overflow:hidden;color:#fff}
.title{font-size:50px;font-weight:800;color:#7dd3fc;margin-bottom:50px;animation:fadeIn 0.6s ease both}
.item{display:flex;align-items:center;gap:25px;margin-bottom:40px;animation:slideRight 0.5s ease both}
.item:nth-child(2){animation-delay:0.3s}
.item:nth-child(3){animation-delay:0.6s}
.item:nth-child(4){animation-delay:0.9s}
.icon{font-size:56px;min-width:70px;text-align:center}
.txt{font-size:42px;font-weight:600;line-height:1.3}
@keyframes fadeIn{from{opacity:0;transform:translateY(-30px)}to{opacity:1;transform:translateY(0)}}
@keyframes slideRight{from{transform:translateX(-80px);opacity:0}to{transform:translateX(0);opacity:1}}
</style></head><body>
<div class='title'>Nghĩa là gì cho bạn?</div>
<div class='item'><span class='icon'>🚫</span><span class='txt'>Không cần máy chủ đắt tiền</span></div>
<div class='item'><span class='icon'>💰</span><span class='txt'>Không tốn hàng triệu/tháng</span></div>
<div class='item'><span class='icon'>💻</span><span class='txt'>Laptop bình thường cũng chạy được!</span></div>
</body></html>"""},

    # Slide 4: CLI miễn phí
    {"html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(145deg,#0f172a,#1e293b);
display:flex;flex-direction:column;justify-content:center;align-items:center;padding:0 60px;overflow:hidden;color:#fff}
.badge{background:#22c55e;color:#000;font-size:36px;font-weight:800;padding:15px 40px;border-radius:50px;animation:popIn 0.5s 0.2s ease both;margin-bottom:50px}
.num{font-size:120px;font-weight:900;color:#fbbf24;animation:scaleIn 0.6s 0.5s ease both}
.unit{font-size:44px;color:#94a3b8;margin-top:10px;animation:fadeIn 0.5s 0.7s ease both}
.desc{font-size:46px;font-weight:700;text-align:center;margin-top:50px;line-height:1.4;animation:slideUp 0.6s 0.9s ease both;padding:0 40px}
.highlight{color:#38bdf8}
@keyframes popIn{from{transform:scale(0);opacity:0}to{transform:scale(1);opacity:1}}
@keyframes scaleIn{from{transform:scale(0)}to{transform:scale(1)}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes slideUp{from{transform:translateY(50px);opacity:0}to{transform:translateY(0);opacity:1}}
</style></head><body>
<div class='badge'>MIỄN PHÍ</div>
<div class='num'>1.000</div>
<div class='unit'>lượt dùng / ngày</div>
<div class='desc'>Công cụ dòng lệnh<br>thay thế dịch vụ<br><span class='highlight'>mất hàng chục đô/tháng</span></div>
</body></html>"""},

    # Slide 5: Áp dụng SME
    {"html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(135deg,#14532d,#166534,#15803d);
display:flex;flex-direction:column;justify-content:center;padding:0 70px;overflow:hidden;color:#fff}
.title{font-size:48px;font-weight:800;color:#86efac;margin-bottom:50px;animation:fadeDown 0.6s ease both}
.item{display:flex;align-items:center;gap:20px;margin-bottom:35px;animation:slideLeft 0.5s ease both}
.item:nth-child(2){animation-delay:0.3s}
.item:nth-child(3){animation-delay:0.6s}
.item:nth-child(4){animation-delay:0.9s}
.item:nth-child(5){animation-delay:1.2s}
.check{font-size:44px}.txt{font-size:40px;font-weight:600;line-height:1.3}
@keyframes fadeDown{from{opacity:0;transform:translateY(-40px)}to{opacity:1;transform:translateY(0)}}
@keyframes slideLeft{from{opacity:0;transform:translateX(80px)}to{opacity:1;transform:translateX(0)}}
</style></head><body>
<div class='title'>Doanh nghiệp Việt tận dụng ngay!</div>
<div class='item'><span class='check'>⚡</span><span class='txt'>Tự động hóa viết code</span></div>
<div class='item'><span class='check'>🤖</span><span class='txt'>Tạo chatbot nội bộ</span></div>
<div class='item'><span class='check'>📊</span><span class='txt'>Xử lý và phân tích dữ liệu</span></div>
<div class='item'><span class='check'>💸</span><span class='txt'>Không tốn một đồng!</span></div>
</body></html>"""},

    # Slide 6: CTA
    {"html": """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Be Vietnam Pro',sans-serif;width:1080px;height:1920px;
background:linear-gradient(135deg,#7c2d12,#c2410c,#ea580c);
display:flex;flex-direction:column;justify-content:center;align-items:center;padding:0 60px;overflow:hidden;color:#fff}
.headline{font-size:56px;font-weight:900;text-align:center;line-height:1.3;animation:fadeIn 0.6s ease both;margin-bottom:40px}
.sub{font-size:42px;font-weight:700;color:#fed7aa;text-align:center;animation:slideUp 0.6s 0.4s ease both;line-height:1.4}
.follow{margin-top:50px;font-size:36px;color:#fdba74;animation:fadeIn 0.5s 0.8s ease both}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes slideUp{from{transform:translateY(50px);opacity:0}to{transform:translateY(0);opacity:1}}
</style></head><body>
<div class='headline'>AI nhỏ mà mạnh...<br>đây là xu hướng<br>sẽ thay đổi mọi thứ!</div>
<div class='sub'>Bạn nghĩ sao?<br>Comment cho tôi biết!</div>
<div class='follow'>Follow để cập nhật AI mới nhất 🔥</div>
</body></html>"""},
]

# ── Step 2: Record slides ──
print("\n=== Step 2: Recording slides (duration = narration + 0.5s) ===")
clip_paths = []
for i, slide in enumerate(slides):
    idx = i + 1
    dur = nar_durs[i] + 0.5
    mp4 = str(OUT / f"{PROJECT}_{idx:02d}.mp4")

    if "image" in slide:
        print(f"  Slide {idx}: Ken Burns ({dur:.1f}s)...")
        r = create_animated_slideshow(images=[slide["image"]], output_path=mp4,
            duration_per_slide=dur, effects=[slide.get("effect","zoom_in")], size="1080x1920", fps=30)
    else:
        print(f"  Slide {idx}: CSS animated ({dur:.1f}s)...")
        r = record_html_video(html_content=slide["html"], output_path=mp4,
            duration=dur, width=1080, height=1920, fps=30, encoder="libx264")

    if r.get("success"):
        clip_paths.append(r.get("output_path", mp4))
        print(f"    ✓ {clip_paths[-1]}")
    else:
        print(f"    ✗ {r.get('error')}")
        sys.exit(1)

# ── Step 3: Merge clips ──
print("\n=== Step 3: Merge clips ===")
merged = str(OUT / f"{PROJECT}_merged.mp4")
concat_f = str(OUT / f"{PROJECT}_concat.txt")
with open(concat_f, "w") as f:
    for p in clip_paths:
        f.write(f"file '{p}'\n")
subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat_f,
    "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p","-r","30",
    "-crf","23","-movflags","+faststart","-an",merged],
    capture_output=True, text=True, timeout=300)
os.remove(concat_f)
print(f"  ✓ {merged}")

# ── Step 4: Merge narrations ──
print("\n=== Step 4: Merge narrations ===")
vo_path = str(OUT / f"{PROJECT}_voiceover.mp3")
nar_files = [str(OUT / f"{PROJECT}_narration_{i+1:02d}.mp3") for i in range(6)]
inputs = []
fparts = []
for i, nf in enumerate(nar_files):
    inputs += ["-i", nf]
    fparts.append(f"[{i}:a]aresample=44100[a{i}];")
    if i < 5:
        fparts.append(f"aevalsrc=0:d=0.3[s{i}];")
concat_in = []
for i in range(6):
    concat_in.append(f"[a{i}]")
    if i < 5:
        concat_in.append(f"[s{i}]")
fstr = "".join(fparts) + "".join(concat_in) + f"concat=n=11:v=0:a=1[out]"
subprocess.run(["ffmpeg","-y"]+inputs+["-filter_complex",fstr,"-map","[out]",
    "-c:a","libmp3lame","-b:a","192k",vo_path],
    capture_output=True, text=True, timeout=120)
print(f"  ✓ {vo_path}")

# ── Step 5: Mix audio ──
print("\n=== Step 5: Mix voiceover + music ===")
mixed = str(OUT / f"{PROJECT}_mixed.mp4")
music = "D:/Work/wifi-content-toolkit/music/loksii-no-copyright-music-211881.mp3"
subprocess.run(["ffmpeg","-y","-i",merged,"-i",vo_path,"-i",music,
    "-filter_complex","[1:a]volume=1.0[voice];[2:a]volume=0.15,afade=t=out:st=47:d=3[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
    "-map","0:v","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k",
    "-shortest","-movflags","+faststart",mixed],
    capture_output=True, text=True, timeout=300)
print(f"  ✓ {mixed}")

# ── Step 6: Facecam ──
print("\n=== Step 6: Facecam ===")
final = str(OUT / "model-3b-danh-bai-60b-ai-nho-ma-manh.mp4")
r = add_facecam_overlay(video_path=mixed, facecam_path="D:/Work/wifi-content-toolkit/human",
    output_path=final, position="bottom-left", size=22, border_radius=20, margin=350)
if r.get("success"):
    print(f"  ✓ {final}")
else:
    print(f"  ✗ {r.get('error')}")
    sys.exit(1)

print(f"\n{'='*60}")
print(f"DONE! {final}")
print(f"{'='*60}")
