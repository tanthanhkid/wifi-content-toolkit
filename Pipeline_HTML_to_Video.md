# 🎬 PIPELINE: HTML → Chrome MCP Screenshot → FFmpeg → Video
## Tự động hóa tạo video TikTok trên Mac Mini M4

---

## TỔNG QUAN

```
Claude Code tạo HTML poster
        ↓
Chrome DevTools MCP chụp screenshot (1080x1920)
        ↓
FFmpeg animate (zoom, pan, fade, slide)
        ↓
FFmpeg ghép nhiều clip + nhạc
        ↓
Video MP4 sẵn đăng TikTok
```

**Toàn bộ chạy bằng command line. Không cần mở app nào.**

---

## SETUP (LÀM 1 LẦN)

### 1. Cài FFmpeg

```bash
# Dùng Homebrew
brew install ffmpeg
```

### 2. Cài Chrome DevTools MCP Server

Trong Claude Code, thêm MCP server cho Chrome DevTools:

```bash
# File: ~/.claude/settings.json (hoặc project settings)
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/chrome-devtools-mcp@latest"]
    }
  }
}
```

Hoặc nếu dùng Puppeteer MCP:

```bash
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/puppeteer-mcp@latest"]
    }
  }
}
```

### 3. Tạo cấu trúc folder

```bash
mkdir -p ~/Trinity-Video/{html,screenshots,clips,bgm,exports}
```

- `html/` — HTML poster files
- `screenshots/` — Ảnh screenshot từ Chrome
- `clips/` — Video clips đã animate
- `bgm/` — Nhạc nền (download nhạc free từ Pixabay, etc.)
- `exports/` — Video final sẵn đăng

---

## CÁCH SỬ DỤNG TRONG CLAUDE CODE

### Flow hoàn chỉnh — 1 prompt duy nhất

Mở Claude Code trong folder `~/Trinity-Video` và nói:

```
Tạo video TikTok 30 giây cho Trinity Software.
Chủ đề: AI Chatbot thay thế nhân viên trực inbox.

Gồm 5 slides:
1. Hook: "200+ tin nhắn/ngày — Trả lời không kịp?"
2. Problem: "Thuê thêm người = 10 triệu/tháng"
3. Solution: "AI Chatbot trả lời 24/7, chỉ 3 triệu/tháng"
4. Proof: "Chuỗi trà sữa giảm 75% nhân sự"
5. CTA: "Nhắn tin tư vấn miễn phí"

Mỗi slide:
- Tạo file HTML 1080x1920 dark theme (style Trinity brand)
- Dùng Chrome DevTools MCP screenshot thành PNG
- Dùng FFmpeg tạo animation (zoom in, pan, fade)
- Ghép 5 clips + nhạc nền thành 1 video MP4
```

Claude Code sẽ:
1. Tạo 5 file HTML
2. Dùng Chrome MCP mở từng file → screenshot
3. Chạy FFmpeg tạo animation cho từng ảnh
4. Ghép tất cả thành video hoàn chỉnh

---

## FFMPEG CHEAT SHEET — CÁC HIỆU ỨNG ANIMATION

### 1. Zoom In (Ken Burns — phổ biến nhất)

```bash
ffmpeg -loop 1 -i input.png \
  -vf "zoompan=z='min(zoom+0.003,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1080x1920:fps=30" \
  -t 5 -c:v libx264 -pix_fmt yuv420p zoom_in.mp4
```

### 2. Zoom Out

```bash
ffmpeg -loop 1 -i input.png \
  -vf "zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.003))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1080x1920:fps=30" \
  -t 5 -c:v libx264 -pix_fmt yuv420p zoom_out.mp4
```

### 3. Pan Left → Right

```bash
ffmpeg -loop 1 -i input.png \
  -vf "zoompan=z=1.3:x='if(lte(on,1),0,x+2)':y='ih/2-(ih/zoom/2)':d=150:s=1080x1920:fps=30" \
  -t 5 -c:v libx264 -pix_fmt yuv420p pan_right.mp4
```

### 4. Pan Top → Bottom (tốt cho ảnh dọc)

```bash
ffmpeg -loop 1 -i input.png \
  -vf "zoompan=z=1.2:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,y+1.5)':d=150:s=1080x1920:fps=30" \
  -t 5 -c:v libx264 -pix_fmt yuv420p pan_down.mp4
```

### 5. Zoom In + Fade In

```bash
ffmpeg -loop 1 -i input.png \
  -vf "zoompan=z='min(zoom+0.003,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1080x1920:fps=30,fade=t=in:st=0:d=0.8" \
  -t 5 -c:v libx264 -pix_fmt yuv420p zoom_fade.mp4
```

### 6. Zoom In vào góc trái trên (focus vào 1 element)

```bash
ffmpeg -loop 1 -i input.png \
  -vf "zoompan=z='min(zoom+0.004,2.0)':x='iw*0.2':y='ih*0.15':d=150:s=1080x1920:fps=30" \
  -t 5 -c:v libx264 -pix_fmt yuv420p zoom_topleft.mp4
```

### 7. Ghép nhiều clip thành 1 video

```bash
# Tạo file list
cat > clips.txt << EOF
file 'clips/slide1.mp4'
file 'clips/slide2.mp4'
file 'clips/slide3.mp4'
file 'clips/slide4.mp4'
file 'clips/slide5.mp4'
EOF

# Ghép + thêm transition fade
ffmpeg -f concat -safe 0 -i clips.txt \
  -c:v libx264 -pix_fmt yuv420p merged.mp4
```

### 8. Thêm nhạc nền

```bash
ffmpeg -i merged.mp4 -i bgm/music.mp3 \
  -c:v copy -c:a aac -b:a 128k \
  -shortest -map 0:v:0 -map 1:a:0 \
  exports/final.mp4
```

### 9. Thêm fade giữa các clip (crossfade)

```bash
# Mỗi clip 5 giây, crossfade 0.5 giây
ffmpeg -i clips/slide1.mp4 -i clips/slide2.mp4 -i clips/slide3.mp4 \
  -filter_complex \
  "[0:v]fade=t=out:st=4.5:d=0.5[v0]; \
   [1:v]fade=t=in:st=0:d=0.5,fade=t=out:st=4.5:d=0.5[v1]; \
   [2:v]fade=t=in:st=0:d=0.5[v2]; \
   [v0][v1][v2]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -c:v libx264 -pix_fmt yuv420p merged_fade.mp4
```

---

## SCRIPT TỰ ĐỘNG HÓA HOÀN CHỈNH

Lưu file này vào `~/Trinity-Video/make-video.sh`:

```bash
#!/bin/bash
# =============================================
# Trinity Video Maker
# HTML screenshots → Animated Video
# =============================================

set -e

PROJECT_DIR="$HOME/Trinity-Video"
SCREENSHOTS_DIR="$PROJECT_DIR/screenshots"
CLIPS_DIR="$PROJECT_DIR/clips"
EXPORTS_DIR="$PROJECT_DIR/exports"
BGM_DIR="$PROJECT_DIR/bgm"

# Thời lượng mỗi slide (giây)
SLIDE_DURATION=5
FPS=30
FRAMES=$((SLIDE_DURATION * FPS))
# Output resolution (TikTok 9:16)
WIDTH=1080
HEIGHT=1920

# Danh sách hiệu ứng xoay vòng
EFFECTS=(
  "zoom_in"
  "zoom_out"
  "pan_right"
  "pan_down"
  "zoom_topleft"
  "zoom_in"
)

# =============================================
# Hàm tạo animation cho từng ảnh
# =============================================
animate_slide() {
  local input="$1"
  local output="$2"
  local effect="$3"
  local duration="$SLIDE_DURATION"

  case "$effect" in
    zoom_in)
      ffmpeg -y -loop 1 -i "$input" \
        -vf "zoompan=z='min(zoom+0.003,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=${WIDTH}x${HEIGHT}:fps=$FPS,fade=t=in:st=0:d=0.5,fade=t=out:st=$((duration-1)):d=0.5" \
        -t "$duration" -c:v libx264 -pix_fmt yuv420p "$output" 2>/dev/null
      ;;
    zoom_out)
      ffmpeg -y -loop 1 -i "$input" \
        -vf "zoompan=z='if(lte(zoom,1.001),1.5,max(1.001,zoom-0.003))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=${WIDTH}x${HEIGHT}:fps=$FPS,fade=t=in:st=0:d=0.5,fade=t=out:st=$((duration-1)):d=0.5" \
        -t "$duration" -c:v libx264 -pix_fmt yuv420p "$output" 2>/dev/null
      ;;
    pan_right)
      ffmpeg -y -loop 1 -i "$input" \
        -vf "zoompan=z=1.3:x='if(lte(on,1),0,min(x+2,iw-iw/zoom))':y='ih/2-(ih/zoom/2)':d=$FRAMES:s=${WIDTH}x${HEIGHT}:fps=$FPS,fade=t=in:st=0:d=0.5,fade=t=out:st=$((duration-1)):d=0.5" \
        -t "$duration" -c:v libx264 -pix_fmt yuv420p "$output" 2>/dev/null
      ;;
    pan_down)
      ffmpeg -y -loop 1 -i "$input" \
        -vf "zoompan=z=1.2:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,min(y+1.5,ih-ih/zoom))':d=$FRAMES:s=${WIDTH}x${HEIGHT}:fps=$FPS,fade=t=in:st=0:d=0.5,fade=t=out:st=$((duration-1)):d=0.5" \
        -t "$duration" -c:v libx264 -pix_fmt yuv420p "$output" 2>/dev/null
      ;;
    zoom_topleft)
      ffmpeg -y -loop 1 -i "$input" \
        -vf "zoompan=z='min(zoom+0.004,2.0)':x='iw*0.2':y='ih*0.15':d=$FRAMES:s=${WIDTH}x${HEIGHT}:fps=$FPS,fade=t=in:st=0:d=0.5,fade=t=out:st=$((duration-1)):d=0.5" \
        -t "$duration" -c:v libx264 -pix_fmt yuv420p "$output" 2>/dev/null
      ;;
  esac
}

# =============================================
# Main
# =============================================
echo "🎬 Trinity Video Maker"
echo "======================"

# Tìm tất cả screenshots
SLIDES=($(ls -1 "$SCREENSHOTS_DIR"/*.png 2>/dev/null | sort))
TOTAL=${#SLIDES[@]}

if [ "$TOTAL" -eq 0 ]; then
  echo "❌ Không tìm thấy ảnh trong $SCREENSHOTS_DIR/"
  echo "   Hãy đặt các file .png vào folder screenshots/"
  exit 1
fi

echo "📸 Tìm thấy $TOTAL slides"

# Animate từng slide
echo ""
echo "🎞️  Tạo animation..."
CLIP_LIST="$CLIPS_DIR/clips.txt"
> "$CLIP_LIST"

for i in "${!SLIDES[@]}"; do
  SLIDE="${SLIDES[$i]}"
  FILENAME=$(basename "$SLIDE" .png)
  EFFECT_IDX=$((i % ${#EFFECTS[@]}))
  EFFECT="${EFFECTS[$EFFECT_IDX]}"
  OUTPUT="$CLIPS_DIR/${FILENAME}.mp4"

  echo "  [$((i+1))/$TOTAL] $FILENAME → $EFFECT"
  animate_slide "$SLIDE" "$OUTPUT" "$EFFECT"
  echo "file '$OUTPUT'" >> "$CLIP_LIST"
done

# Ghép clips
echo ""
echo "🔗 Ghép $TOTAL clips..."
MERGED="$CLIPS_DIR/merged.mp4"
ffmpeg -y -f concat -safe 0 -i "$CLIP_LIST" \
  -c:v libx264 -pix_fmt yuv420p "$MERGED" 2>/dev/null

# Thêm nhạc nền (nếu có)
BGM_FILE=$(ls -1 "$BGM_DIR"/*.mp3 2>/dev/null | head -1)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FINAL="$EXPORTS_DIR/trinity_${TIMESTAMP}.mp4"

if [ -n "$BGM_FILE" ]; then
  echo "🎵 Thêm nhạc: $(basename "$BGM_FILE")"
  ffmpeg -y -i "$MERGED" -i "$BGM_FILE" \
    -c:v copy -c:a aac -b:a 128k \
    -shortest -map 0:v:0 -map 1:a:0 \
    "$FINAL" 2>/dev/null
else
  echo "⚠️  Không có nhạc trong bgm/ — xuất video không nhạc"
  cp "$MERGED" "$FINAL"
fi

echo ""
echo "✅ Hoàn tất! Video: $FINAL"
echo "📱 Thời lượng: $((TOTAL * SLIDE_DURATION)) giây"
echo ""
echo "Bước tiếp: AirDrop file qua iPhone → đăng TikTok"
```

Cấp quyền chạy:

```bash
chmod +x ~/Trinity-Video/make-video.sh
```

---

## WORKFLOW HÀNG NGÀY VỚI CLAUDE CODE

### Bước 1: Tạo HTML + Screenshot (trong Claude Code)

```bash
cd ~/Trinity-Video
claude
```

Prompt:

```
Tạo 5 slides TikTok cho Trinity Software, chủ đề "So sánh chi phí nhân viên vs AI".

Mỗi slide:
- File HTML riêng, kích thước 1080x1920, dark theme Trinity brand
- Lưu vào html/slide1.html ... html/slide5.html

Slide 1 (Hook): Số lớn "120 triệu" gạch đỏ vs "36 triệu" xanh
Slide 2 (Problem): 5 vấn đề khi thuê nhân viên CSKH
Slide 3 (Solution): AI Chatbot Trinity — 24/7, 3 triệu/tháng
Slide 4 (Proof): Case study chuỗi trà sữa, 3 metrics lớn
Slide 5 (CTA): "Nhắn tin tư vấn miễn phí" + logo Trinity

Sau khi tạo xong, dùng Chrome DevTools MCP:
- Mở từng file HTML
- Set viewport 1080x1920
- Screenshot lưu vào screenshots/slide1.png ... screenshots/slide5.png
```

### Bước 2: Chạy script tạo video

```bash
./make-video.sh
```

Output:
```
🎬 Trinity Video Maker
======================
📸 Tìm thấy 5 slides
🎞️  Tạo animation...
  [1/5] slide1 → zoom_in
  [2/5] slide2 → zoom_out
  [3/5] slide3 → pan_right
  [4/5] slide4 → pan_down
  [5/5] slide5 → zoom_topleft
🔗 Ghép 5 clips...
🎵 Thêm nhạc: energetic.mp3
✅ Hoàn tất! Video: exports/trinity_20260228_143052.mp4
📱 Thời lượng: 25 giây
```

### Bước 3: Đăng

AirDrop video qua iPhone → TikTok → thêm caption + hashtag → đăng.

---

## PROMPT MẪU CHO CLAUDE CODE (Copy & Dùng Lại)

### Template 1: So sánh

```
Tạo 5 slides TikTok 1080x1920 dark theme cho Trinity Software.
Chủ đề: [CHỦ ĐỀ]
Slide 1: Hook với số liệu gây sốc
Slide 2: Pain point khách hàng
Slide 3: Giải pháp AI Trinity
Slide 4: Social proof / case study
Slide 5: CTA nhắn tin tư vấn

Tạo HTML → Chrome MCP screenshot → lưu screenshots/
```

### Template 2: Checklist

```
Tạo 4 slides TikTok 1080x1920.
Slide 1: "Bạn gặp mấy vấn đề?" + 5 checkbox items
Slide 2: "Nếu ≥ 2 → Bạn cần AI"
Slide 3: 4 giải pháp AI (icons + tên)
Slide 4: CTA "Nhắn tin ngay — Tư vấn free"

Tạo HTML → Chrome MCP screenshot → lưu screenshots/
```

### Template 3: Tips / Hướng dẫn

```
Tạo 6 slides TikTok 1080x1920.
Chủ đề: "3 cách tiết kiệm chi phí nhân sự bằng AI"
Slide 1: Title hook
Slide 2: Cách 1 — AI Chatbot
Slide 3: Cách 2 — AI Content Creator
Slide 4: Cách 3 — AI Kế Toán
Slide 5: Tổng tiết kiệm bao nhiêu
Slide 6: CTA

Tạo HTML → Chrome MCP screenshot → lưu screenshots/
```

---

## NÂNG CAP SAU NÀY

### Thêm voiceover bằng TTS

```bash
# Dùng macOS built-in TTS (tiếng Việt)
say -v "Linh" -o voiceover.aiff "Bạn đang trả lương cho nhân viên để gõ tin nhắn cả ngày?"
ffmpeg -i voiceover.aiff voiceover.mp3

# Ghép voiceover + bgm + video
ffmpeg -i merged.mp4 -i voiceover.mp3 -i bgm/music.mp3 \
  -filter_complex "[1:a]volume=1.0[vo];[2:a]volume=0.2[bg];[vo][bg]amix=inputs=2:duration=shortest[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -shortest final_with_voice.mp4
```

### Thêm text overlay bằng FFmpeg

```bash
# Thêm text "TRINITY SOFTWARE" ở cuối video
ffmpeg -i merged.mp4 \
  -vf "drawtext=text='TRINITY SOFTWARE':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h-80:enable='gte(t,0)'" \
  -c:v libx264 -c:a copy output_text.mp4
```

### Batch generate 7 video (cả tuần)

```bash
# Tạo array chủ đề
TOPICS=(
  "So sánh nhân viên vs AI Chatbot"
  "3 cách tiết kiệm chi phí bằng AI"
  "Case study chuỗi trà sữa"
  "AI kế toán đọc hóa đơn tự động"
  "Checklist vấn đề doanh nghiệp"
  "AI Content Creator viết bài 10 giây"
  "30 giải pháp AI từ 2 triệu/tháng"
)

for i in "${!TOPICS[@]}"; do
  echo "📹 Video $((i+1))/7: ${TOPICS[$i]}"
  # Claude Code tạo HTML + screenshot
  # make-video.sh render
  # Move to exports/day$((i+1)).mp4
done
```

---

## TÓM TẮT

| Bước | Tool | Thời gian |
|------|------|-----------|
| Tạo HTML slides | Claude Code | 2 phút (prompt) |
| Screenshot | Chrome DevTools MCP | 30 giây (tự động) |
| Animate + ghép | FFmpeg (make-video.sh) | 1-2 phút (tự động) |
| Thêm nhạc | FFmpeg | 10 giây (tự động) |
| **Tổng** | **Tất cả trong terminal** | **~5 phút** |

**Zero app cần mở. Zero click chuột. Chỉ terminal + Claude Code.**
