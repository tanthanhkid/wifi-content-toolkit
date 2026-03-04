# Design System — WiFi Content Toolkit

> Auto-generated from `/design_system/*.png`. Signature below — chỉ re-explore khi signature thay đổi.

## Signature (MD5 checksums)
```
b929357975bd29ed459f16a59d1fe57b  1.png
72b466c8f908f559c6bb73c295e11010  2.png
55f7d458999aef2fb9490b6d7664e51f  3.png
297e764c68631a37db1396d6bdc32893  4.png
b0092d2370539d90bff5d018e7bfc0c1  5.png
a1d0997e18fc8718536fc254c3ab2e65  6.png
0c1e75f56af64570b36b805e9587d28f  7.png
c94595383d4f8f4bd05aa620a3ae2b0f  8.png
442e14472975a3dcf65548529b0385fe  9.png
e0dd3e89a20d2a2da733698f741ba377  10.png
```

## Bảng Màu (Color Palette)

| Token | Hex | Sử dụng |
|-------|-----|---------|
| `--primary` | `#1351aa` | Nền blue slides, text headings trên nền sáng |
| `--secondary-bg` | `#e3e2de` | Nền beige/xám nhạt (slides chẵn: 1, 4, 7, 10) |
| `--white` | `#ffffff` | Text trên nền blue, nền phụ |
| `--text-dark` | `#1a1a1a` | Body text trên nền beige |
| `--badge-border` | `rgba(255,255,255,0.5)` | Viền pill badges trên nền blue |
| `--badge-border-dark` | `rgba(19,81,170,0.3)` | Viền pill badges trên nền beige |

## Typography

- **Font:** Bold italic sans-serif (giống Poppins/Montserrat Black Italic)
- **Headings:** Cực lớn, bold italic, chiếm 30-50% slide. Trên nền blue → white. Trên nền beige → `#1351aa`
- **Body text:** Regular weight, size nhỏ, justified/left-aligned
- **Badges/Labels:** UPPERCASE, font-weight 700, letter-spacing 1-2px

### Kích thước heading cho TikTok (1080x1920)
- Mega heading: `font-size: 84-120px`, `font-weight: 900`, `font-style: italic`
- Sub heading: `font-size: 36-48px`, `font-weight: 700`
- Body: `font-size: 24-28px`, `font-weight: 400`
- Badge text: `font-size: 18-22px`, `font-weight: 700`, `text-transform: uppercase`

## Pill Badges (Signature Element)

Đặc trưng nhất của design system — xuất hiện trong hầu hết slides.

```css
.pill-badge {
  display: inline-block;
  padding: 12px 32px;
  border: 1.5px solid rgba(255,255,255,0.5); /* trên nền blue */
  border-radius: 999px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-size: 18px;
  color: #fff; /* trên nền blue */
}
/* Trên nền beige */
.pill-badge--dark {
  border-color: rgba(19,81,170,0.3);
  color: #1351aa;
}
```

## Photo Treatment

### Arch/Shield Clip-path (Primary)
Ảnh được crop thành hình arch (vòm) hoặc shield — đặc trưng nhất.

```css
.photo-arch {
  clip-path: polygon(
    0% 15%, 0% 100%, 100% 100%, 100% 15%,
    95% 5%, 85% 1%, 50% 0%, 15% 1%, 5% 5%
  );
  /* Hoặc đơn giản hơn: */
  border-radius: 200px 200px 20px 20px;
}
```

### Circle Crop (Secondary)
Dùng cho portrait/avatar nhỏ.
```css
.photo-circle {
  border-radius: 50%;
  overflow: hidden;
}
```

### Ảnh B&W
Tất cả ảnh trong design system đều grayscale:
```css
.photo { filter: grayscale(100%); }
```

## Page Numbers

Góc phải trên, trong rounded circle:
```css
.page-number {
  position: absolute;
  top: 40px;
  right: 40px;
  width: 56px;
  height: 56px;
  border: 1.5px solid currentColor;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
}
```

## Layout Patterns (Slides → TikTok Adaptation)

### Pattern A: Hero Title + Photo (Slides 1, 10)
- Mega heading chiếm 60% diện tích
- 1 ảnh arch/circle bên cạnh hoặc dưới
- Nền beige
- **TikTok:** Heading trên, ảnh giữa, info dưới

### Pattern B: Title + Content Grid (Slides 3, 4, 6, 7)
- Heading lớn italic phía trên
- Nền blue
- Content bên dưới: text + ảnh song song
- **TikTok:** Heading trên, ảnh giữa, text body dưới

### Pattern C: List/Timeline (Slides 2, 9)
- Nền blue
- Heading trái, list items (pill badges) bên phải xếp chéo
- **TikTok:** Heading trên, items xếp dọc với stagger animation

### Pattern D: People Grid (Slides 5, 8)
- 3 ảnh arch/shield xếp ngang
- Pill badge tên + chức danh dưới mỗi ảnh
- Nền blue
- **TikTok:** 1-2 ảnh xếp dọc hoặc grid 2 cột

## Nền Alternating Rule

| Slide type | Background | Text color | Badge border |
|------------|-----------|------------|--------------|
| Odd (info-heavy) | `#1351aa` blue | `#fff` white | `rgba(255,255,255,0.5)` |
| Even (visual-heavy) | `#e3e2de` beige | `#1351aa` blue | `rgba(19,81,170,0.3)` |

Không bắt buộc tuân theo chẵn/lẻ, nhưng NÊN xen kẽ blue/beige để tạo rhythm.

## CSS Template Base (TikTok Portrait 1080x1920)

```css
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  width: 1080px;
  height: 1920px;
  font-family: 'Be Vietnam Pro', sans-serif;
  overflow: hidden;
}

/* Blue slide */
.slide-blue {
  background: #1351aa;
  color: #fff;
}

/* Beige slide */
.slide-beige {
  background: #e3e2de;
  color: #1a1a1a;
}

.mega-heading {
  font-size: 96px;
  font-weight: 900;
  font-style: italic;
  line-height: 1.0;
  letter-spacing: -2px;
}

.slide-blue .mega-heading { color: #fff; }
.slide-beige .mega-heading { color: #1351aa; }
```

## Slide Matching Reference

| File | Pattern | Nền | Nội dung chính |
|------|---------|-----|----------------|
| 1.png | A: Hero Title | Beige | Mega "Project Proposal" + ảnh B&W bên trái + year badge |
| 2.png | C: List | Blue | "Table of Contents" + 7 pill badges xếp chéo |
| 3.png | B: Title+Content | Blue | "Introduction" + ảnh arch phải + text trái + page 01 |
| 4.png | B: Title+Content | Beige | "About the Event" + 2 ảnh arch trái + text phải + page 02 |
| 5.png | D: People Grid | Blue | "Event Committee" + 3 shield photos + pill names |
| 6.png | B: Title+Content | Blue | "Event Activities" + timeline trái + ảnh circle phải + page 04 |
| 7.png | B: Title+Content | Beige | "Event Venue" + ảnh arch phải + pill badge địa chỉ + page 05 |
| 8.png | D: People Grid | Blue | "List of Artists" + 3 arch photos + pill names + page 06 |
| 9.png | C: Timeline | Blue | "Project Timeline" + zigzag path + 4 pill badges + page 07 |
| 10.png | A: Hero CTA | Beige | "Let's Make an Amazing Event" + 2 ảnh + year badge + contact |
