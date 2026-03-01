"""Animated sticker library — CapCut/Canva-style SVG stickers with CSS animations.

Each sticker is an animated SVG with CSS @keyframes that plays in Playwright
recordings. Use stickers to replace static Unicode emoji/icons in slides.

Usage in HTML slides:
    from shared.stickers import get_sticker_html, get_sticker_css

    # Inline sticker (flows with text)
    html_snippet = get_sticker_html("fire", size=64)

    # Absolute-positioned sticker (floating decoration)
    html_snippet = get_sticker_html("sparkle", size=80, position="top-right")

    # Get just the CSS (for <style> block)
    css = get_sticker_css("fire")
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Sticker catalog — animated SVG + CSS keyframes
# ---------------------------------------------------------------------------

# Each entry: {svg: str, animation: str, description: str, category: str}
# SVG uses currentColor so it inherits the color from CSS.
# Animation names are prefixed with "stk-" to avoid collisions.

_STICKERS: dict[str, dict] = {
    # ─── Reactions ────────────────────────────────────────────────
    "fire": {
        "category": "reactions",
        "description": "Lửa rực cháy (fire) — bouncing flame",
        "color": "#FF6B35",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M32 4C32 4 16 20 16 36C16 44.8 23.2 52 32 52C40.8 52 48 44.8 48 36C48 20 32 4 32 4Z" '
            'fill="url(#fire_g1)" />'
            '<path d="M32 24C32 24 24 32 24 40C24 44.4 27.6 48 32 48C36.4 48 40 44.4 40 40C40 32 32 24 32 24Z" '
            'fill="url(#fire_g2)" />'
            '<defs>'
            '<linearGradient id="fire_g1" x1="32" y1="4" x2="32" y2="52" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FF6B35"/><stop offset="1" stop-color="#FF3D00"/>'
            '</linearGradient>'
            '<linearGradient id="fire_g2" x1="32" y1="24" x2="32" y2="48" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FFD54F"/><stop offset="1" stop-color="#FF9800"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-fire",
        "keyframes": (
            "@keyframes stk-fire {"
            "0%,100%{transform:scale(1) translateY(0);}"
            "25%{transform:scale(1.05) translateY(-4px);}"
            "50%{transform:scale(0.98) translateY(-2px);}"
            "75%{transform:scale(1.03) translateY(-5px);}"
            "}"
        ),
        "css": "animation:stk-fire 0.8s ease-in-out infinite;",
    },
    "heart": {
        "category": "reactions",
        "description": "Trái tim đập (heart) — pulsing heartbeat",
        "color": "#FF4D6A",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M32 56L27.6 52C14.4 40 6 32.4 6 23.2C6 15.6 12 9.6 19.6 9.6C24 9.6 28.2 11.6 32 15.2'
            'C35.8 11.6 40 9.6 44.4 9.6C52 9.6 58 15.6 58 23.2C58 32.4 49.6 40 36.4 52L32 56Z" '
            'fill="url(#heart_g)"/>'
            '<defs>'
            '<linearGradient id="heart_g" x1="6" y1="9" x2="58" y2="56" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FF4D6A"/><stop offset="1" stop-color="#FF1744"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-heart",
        "keyframes": (
            "@keyframes stk-heart {"
            "0%,100%{transform:scale(1);}"
            "15%{transform:scale(1.25);}"
            "30%{transform:scale(1);}"
            "45%{transform:scale(1.15);}"
            "60%{transform:scale(1);}"
            "}"
        ),
        "css": "animation:stk-heart 1.2s ease-in-out infinite;",
    },
    "star": {
        "category": "reactions",
        "description": "Ngôi sao lấp lánh (star) — spinning sparkle",
        "color": "#FFD700",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M32 4L39.6 24.4L60 24.4L43.2 38L50.8 60L32 46L13.2 60L20.8 38L4 24.4L24.4 24.4L32 4Z" '
            'fill="url(#star_g)"/>'
            '<defs>'
            '<linearGradient id="star_g" x1="4" y1="4" x2="60" y2="60" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FFD700"/><stop offset="1" stop-color="#FFA000"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-star",
        "keyframes": (
            "@keyframes stk-star {"
            "0%{transform:rotate(0deg) scale(1);}"
            "25%{transform:rotate(15deg) scale(1.1);}"
            "50%{transform:rotate(0deg) scale(1);}"
            "75%{transform:rotate(-15deg) scale(1.1);}"
            "100%{transform:rotate(0deg) scale(1);}"
            "}"
        ),
        "css": "animation:stk-star 1.5s ease-in-out infinite;",
    },
    "rocket": {
        "category": "reactions",
        "description": "Tên lửa bay lên (rocket) — launching upward",
        "color": "#FF6B35",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M32 4C32 4 28 16 28 28C28 34 29.6 39.6 32 44C34.4 39.6 36 34 36 28C36 16 32 4 32 4Z" '
            'fill="url(#rocket_body)"/>'
            '<path d="M28 28L20 40L28 36V28Z" fill="#6C63FF"/>'
            '<path d="M36 28L44 40L36 36V28Z" fill="#6C63FF"/>'
            '<circle cx="32" cy="22" r="3" fill="#fff"/>'
            '<path d="M29 44L32 56L35 44C33.8 45.2 30.2 45.2 29 44Z" fill="#FF6B35"/>'
            '<path d="M30 48L32 56L34 48" stroke="#FFD54F" stroke-width="1.5" fill="none"/>'
            '<defs>'
            '<linearGradient id="rocket_body" x1="28" y1="4" x2="36" y2="44" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#E0E0E0"/><stop offset="1" stop-color="#9E9E9E"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-rocket",
        "keyframes": (
            "@keyframes stk-rocket {"
            "0%{transform:translateY(0) rotate(-45deg);}"
            "50%{transform:translateY(-12px) rotate(-45deg);}"
            "100%{transform:translateY(0) rotate(-45deg);}"
            "}"
        ),
        "css": "animation:stk-rocket 1s ease-in-out infinite;transform-origin:center;",
    },
    "sparkle": {
        "category": "reactions",
        "description": "Lấp lánh (sparkle) — twinkling stars",
        "color": "#FFD700",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path class="stk-sp1" d="M32 8L35 24L32 16L29 24L32 8Z" fill="#FFD700"/>'
            '<path class="stk-sp1" d="M32 56L35 40L32 48L29 40L32 56Z" fill="#FFD700"/>'
            '<path class="stk-sp1" d="M8 32L24 29L16 32L24 35L8 32Z" fill="#FFD700"/>'
            '<path class="stk-sp1" d="M56 32L40 29L48 32L40 35L56 32Z" fill="#FFD700"/>'
            '<path class="stk-sp2" d="M16 16L20 26L16 22L12 26L16 16Z" fill="#FFA000" opacity="0.7"/>'
            '<path class="stk-sp2" d="M48 16L52 26L48 22L44 26L48 16Z" fill="#FFA000" opacity="0.7"/>'
            '<path class="stk-sp2" d="M16 48L20 38L16 42L12 38L16 48Z" fill="#FFA000" opacity="0.7"/>'
            '<path class="stk-sp2" d="M48 48L52 38L48 42L44 38L48 48Z" fill="#FFA000" opacity="0.7"/>'
            '<circle cx="32" cy="32" r="4" fill="#FFD700"/>'
            '</svg>'
        ),
        "animation": "stk-sparkle",
        "keyframes": (
            "@keyframes stk-sparkle {"
            "0%,100%{transform:scale(1) rotate(0deg);opacity:1;}"
            "25%{transform:scale(1.2) rotate(15deg);opacity:0.8;}"
            "50%{transform:scale(0.9) rotate(0deg);opacity:1;}"
            "75%{transform:scale(1.15) rotate(-15deg);opacity:0.85;}"
            "}"
        ),
        "css": "animation:stk-sparkle 1.5s ease-in-out infinite;",
    },
    "thumbsup": {
        "category": "reactions",
        "description": "Like / thích (thumbs up) — bouncing thumb",
        "color": "#4FC3F7",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M20 28H10C8.9 28 8 28.9 8 30V54C8 55.1 8.9 56 10 56H20V28Z" fill="#4FC3F7"/>'
            '<path d="M44 28H28L30.6 17.6C31.2 15 29.6 12 27 12L20 28V56H41.2C43.6 56 45.6 54.2 46 51.8'
            'L49.2 33.8C49.6 30.6 47.2 28 44 28Z" fill="url(#thumb_g)"/>'
            '<defs>'
            '<linearGradient id="thumb_g" x1="20" y1="12" x2="49" y2="56" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#64B5F6"/><stop offset="1" stop-color="#1E88E5"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-thumbsup",
        "keyframes": (
            "@keyframes stk-thumbsup {"
            "0%,100%{transform:rotate(0deg) scale(1);}"
            "20%{transform:rotate(-15deg) scale(1.15);}"
            "40%{transform:rotate(5deg) scale(1.05);}"
            "60%{transform:rotate(-5deg) scale(1);}"
            "}"
        ),
        "css": "animation:stk-thumbsup 1.2s ease-in-out infinite;transform-origin:bottom center;",
    },
    "party": {
        "category": "reactions",
        "description": "Tiệc tùng (party popper) — confetti burst",
        "color": "#FF6B35",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M8 56L20 20L44 44L8 56Z" fill="url(#party_g)"/>'
            '<circle cx="36" cy="12" r="3" fill="#FF4081"/>'
            '<circle cx="52" cy="20" r="2.5" fill="#FFD740"/>'
            '<circle cx="48" cy="8" r="2" fill="#69F0AE"/>'
            '<rect x="42" y="14" width="4" height="4" rx="1" fill="#448AFF" transform="rotate(30 44 16)"/>'
            '<rect x="28" y="8" width="3" height="3" rx="0.5" fill="#FF6E40" transform="rotate(-20 29.5 9.5)"/>'
            '<circle cx="56" cy="32" r="2" fill="#E040FB"/>'
            '<rect x="50" y="28" width="3" height="3" rx="1" fill="#FFD740" transform="rotate(45 51.5 29.5)"/>'
            '<path d="M22 18L18 10" stroke="#FF4081" stroke-width="2" stroke-linecap="round"/>'
            '<path d="M16 22L8 20" stroke="#69F0AE" stroke-width="2" stroke-linecap="round"/>'
            '<defs>'
            '<linearGradient id="party_g" x1="8" y1="56" x2="44" y2="20" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FFD740"/><stop offset="0.5" stop-color="#FF6B35"/><stop offset="1" stop-color="#FF4081"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-party",
        "keyframes": (
            "@keyframes stk-party {"
            "0%{transform:rotate(0deg) scale(1);}"
            "15%{transform:rotate(-20deg) scale(1.1);}"
            "30%{transform:rotate(10deg) scale(1.05);}"
            "45%{transform:rotate(-5deg) scale(1);}"
            "100%{transform:rotate(0deg) scale(1);}"
            "}"
        ),
        "css": "animation:stk-party 1.5s ease-in-out infinite;transform-origin:bottom left;",
    },

    # ─── Business ─────────────────────────────────────────────────
    "checkmark": {
        "category": "business",
        "description": "Tích xanh (checkmark) — popping check",
        "color": "#4CAF50",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<circle cx="32" cy="32" r="28" fill="url(#check_g)"/>'
            '<path d="M18 32L28 42L46 22" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
            '<defs>'
            '<linearGradient id="check_g" x1="4" y1="4" x2="60" y2="60" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#66BB6A"/><stop offset="1" stop-color="#2E7D32"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-checkmark",
        "keyframes": (
            "@keyframes stk-checkmark {"
            "0%{transform:scale(0) rotate(-45deg);opacity:0;}"
            "50%{transform:scale(1.2) rotate(5deg);opacity:1;}"
            "70%{transform:scale(0.95) rotate(-2deg);}"
            "100%{transform:scale(1) rotate(0deg);opacity:1;}"
            "}"
        ),
        "css": "animation:stk-checkmark 0.6s cubic-bezier(0.34,1.56,0.64,1) both;",
    },
    "chart_up": {
        "category": "business",
        "description": "Biểu đồ tăng (chart up) — rising graph",
        "color": "#4CAF50",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="8" y="42" width="10" height="16" rx="2" fill="#66BB6A" opacity="0.6"/>'
            '<rect x="22" y="32" width="10" height="26" rx="2" fill="#4CAF50" opacity="0.8"/>'
            '<rect x="36" y="22" width="10" height="36" rx="2" fill="#43A047"/>'
            '<rect x="50" y="10" width="10" height="48" rx="2" fill="url(#chart_g)"/>'
            '<path d="M12 38L26 28L40 18L56 8" stroke="#FFD740" stroke-width="3" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            '<circle cx="56" cy="8" r="4" fill="#FFD740"/>'
            '<defs>'
            '<linearGradient id="chart_g" x1="50" y1="10" x2="60" y2="58" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#2E7D32"/><stop offset="1" stop-color="#1B5E20"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-chartup",
        "keyframes": (
            "@keyframes stk-chartup {"
            "0%{transform:scaleY(0.3);opacity:0.5;}"
            "60%{transform:scaleY(1.05);opacity:1;}"
            "100%{transform:scaleY(1);opacity:1;}"
            "}"
        ),
        "css": "animation:stk-chartup 1s cubic-bezier(0.34,1.56,0.64,1) both;transform-origin:bottom;",
    },
    "money": {
        "category": "business",
        "description": "Tiền bay (money) — floating dollar",
        "color": "#4CAF50",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="8" y="16" width="48" height="32" rx="6" fill="url(#money_g)"/>'
            '<rect x="12" y="20" width="40" height="24" rx="3" fill="none" '
            'stroke="#fff" stroke-width="1.5" opacity="0.3"/>'
            '<circle cx="32" cy="32" r="10" fill="none" stroke="#fff" stroke-width="2" opacity="0.4"/>'
            '<text x="32" y="38" text-anchor="middle" fill="#fff" font-size="18" font-weight="bold" '
            'font-family="Arial">$</text>'
            '<circle cx="16" cy="32" r="3" fill="#fff" opacity="0.2"/>'
            '<circle cx="48" cy="32" r="3" fill="#fff" opacity="0.2"/>'
            '</svg>'
        ),
        "animation": "stk-money",
        "keyframes": (
            "@keyframes stk-money {"
            "0%,100%{transform:translateY(0) rotate(0deg);}"
            "25%{transform:translateY(-8px) rotate(3deg);}"
            "75%{transform:translateY(-4px) rotate(-2deg);}"
            "}"
        ),
        "css": "animation:stk-money 2s ease-in-out infinite;",
    },
    "trophy": {
        "category": "business",
        "description": "Cúp vàng (trophy) — shining trophy",
        "color": "#FFD700",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M20 8H44V28C44 34.6 38.6 40 32 40C25.4 40 20 34.6 20 28V8Z" fill="url(#trophy_g)"/>'
            '<path d="M20 12H8C8 12 6 24 16 24C18 24 19.6 22 20 20" fill="#FFA000"/>'
            '<path d="M44 12H56C56 12 58 24 48 24C46 24 44.4 22 44 20" fill="#FFA000"/>'
            '<rect x="28" y="40" width="8" height="8" fill="#FFA000"/>'
            '<rect x="22" y="48" width="20" height="6" rx="2" fill="#FFD740"/>'
            '<path d="M30 20L32 16L34 20L32 18Z" fill="#fff" opacity="0.4"/>'
            '<defs>'
            '<linearGradient id="trophy_g" x1="20" y1="8" x2="44" y2="40" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FFD740"/><stop offset="1" stop-color="#F9A825"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-trophy",
        "keyframes": (
            "@keyframes stk-trophy {"
            "0%,100%{transform:scale(1);filter:brightness(1);}"
            "50%{transform:scale(1.08);filter:brightness(1.2);}"
            "}"
        ),
        "css": "animation:stk-trophy 2s ease-in-out infinite;",
    },
    "lightbulb": {
        "category": "business",
        "description": "Bóng đèn sáng (lightbulb) — glowing idea",
        "color": "#FFD740",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<circle cx="32" cy="26" r="18" fill="url(#bulb_g)" class="stk-bulb-glow"/>'
            '<path d="M24 40V44C24 46.2 25.8 48 28 48H36C38.2 48 40 46.2 40 44V40" '
            'fill="#E0E0E0"/>'
            '<line x1="26" y1="52" x2="38" y2="52" stroke="#BDBDBD" stroke-width="2" stroke-linecap="round"/>'
            '<line x1="27" y1="56" x2="37" y2="56" stroke="#BDBDBD" stroke-width="2" stroke-linecap="round"/>'
            '<path d="M32 8V4" stroke="#FFD740" stroke-width="2" stroke-linecap="round" opacity="0.6"/>'
            '<path d="M48 12L52 8" stroke="#FFD740" stroke-width="2" stroke-linecap="round" opacity="0.6"/>'
            '<path d="M16 12L12 8" stroke="#FFD740" stroke-width="2" stroke-linecap="round" opacity="0.6"/>'
            '<path d="M52 26H56" stroke="#FFD740" stroke-width="2" stroke-linecap="round" opacity="0.6"/>'
            '<path d="M12 26H8" stroke="#FFD740" stroke-width="2" stroke-linecap="round" opacity="0.6"/>'
            '<defs>'
            '<linearGradient id="bulb_g" x1="14" y1="8" x2="50" y2="44" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FFF176"/><stop offset="1" stop-color="#FFD740"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-lightbulb",
        "keyframes": (
            "@keyframes stk-lightbulb {"
            "0%,100%{filter:drop-shadow(0 0 8px rgba(255,215,64,0.4));}"
            "50%{filter:drop-shadow(0 0 20px rgba(255,215,64,0.8));}"
            "}"
        ),
        "css": "animation:stk-lightbulb 2s ease-in-out infinite;",
    },
    "target": {
        "category": "business",
        "description": "Mục tiêu (target) — pulsing bullseye",
        "color": "#FF4081",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<circle cx="32" cy="32" r="28" fill="none" stroke="#FF4081" stroke-width="3" opacity="0.3"/>'
            '<circle cx="32" cy="32" r="20" fill="none" stroke="#FF4081" stroke-width="3" opacity="0.5"/>'
            '<circle cx="32" cy="32" r="12" fill="none" stroke="#FF4081" stroke-width="3" opacity="0.7"/>'
            '<circle cx="32" cy="32" r="5" fill="#FF4081"/>'
            '<path d="M32 4V12" stroke="#FF4081" stroke-width="2" opacity="0.4"/>'
            '<path d="M32 52V60" stroke="#FF4081" stroke-width="2" opacity="0.4"/>'
            '<path d="M4 32H12" stroke="#FF4081" stroke-width="2" opacity="0.4"/>'
            '<path d="M52 32H60" stroke="#FF4081" stroke-width="2" opacity="0.4"/>'
            '</svg>'
        ),
        "animation": "stk-target",
        "keyframes": (
            "@keyframes stk-target {"
            "0%,100%{transform:scale(1);}"
            "50%{transform:scale(1.1);}"
            "}"
        ),
        "css": "animation:stk-target 1.5s ease-in-out infinite;",
    },
    "megaphone": {
        "category": "business",
        "description": "Loa phát (megaphone) — shaking announcement",
        "color": "#FF6B35",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M12 24H20V40H12C9.8 40 8 38.2 8 36V28C8 25.8 9.8 24 12 24Z" fill="#FFB74D"/>'
            '<path d="M20 24L44 12V52L20 40V24Z" fill="url(#mega_g)"/>'
            '<rect x="44" y="20" width="6" height="24" rx="3" fill="#FF8A65"/>'
            '<path d="M54 24L60 20" stroke="#FF6B35" stroke-width="2.5" stroke-linecap="round"/>'
            '<path d="M54 32H60" stroke="#FF6B35" stroke-width="2.5" stroke-linecap="round"/>'
            '<path d="M54 40L60 44" stroke="#FF6B35" stroke-width="2.5" stroke-linecap="round"/>'
            '<defs>'
            '<linearGradient id="mega_g" x1="20" y1="12" x2="44" y2="52" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FF8A65"/><stop offset="1" stop-color="#FF6B35"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-megaphone",
        "keyframes": (
            "@keyframes stk-megaphone {"
            "0%,100%{transform:rotate(0deg);}"
            "10%{transform:rotate(-8deg);}"
            "20%{transform:rotate(8deg);}"
            "30%{transform:rotate(-5deg);}"
            "40%{transform:rotate(5deg);}"
            "50%{transform:rotate(0deg);}"
            "}"
        ),
        "css": "animation:stk-megaphone 1.5s ease-in-out infinite;transform-origin:left center;",
    },

    # ─── Arrows / Pointers ───────────────────────────────────────
    "arrow_right": {
        "category": "arrows",
        "description": "Mũi tên phải (arrow right) — sliding arrow",
        "color": "#6C63FF",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M8 32H48" stroke="url(#arr_g)" stroke-width="6" stroke-linecap="round"/>'
            '<path d="M40 20L56 32L40 44" stroke="url(#arr_g)" stroke-width="6" '
            'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
            '<defs>'
            '<linearGradient id="arr_g" x1="8" y1="32" x2="56" y2="32" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#6C63FF"/><stop offset="1" stop-color="#FF6584"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-arrowright",
        "keyframes": (
            "@keyframes stk-arrowright {"
            "0%,100%{transform:translateX(0);}"
            "50%{transform:translateX(8px);}"
            "}"
        ),
        "css": "animation:stk-arrowright 1s ease-in-out infinite;",
    },
    "arrow_down": {
        "category": "arrows",
        "description": "Mũi tên xuống (arrow down) — bouncing down",
        "color": "#6C63FF",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M32 8V48" stroke="url(#arrd_g)" stroke-width="6" stroke-linecap="round"/>'
            '<path d="M20 40L32 56L44 40" stroke="url(#arrd_g)" stroke-width="6" '
            'stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
            '<defs>'
            '<linearGradient id="arrd_g" x1="32" y1="8" x2="32" y2="56" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#6C63FF"/><stop offset="1" stop-color="#FF6584"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-arrowdown",
        "keyframes": (
            "@keyframes stk-arrowdown {"
            "0%,100%{transform:translateY(0);}"
            "50%{transform:translateY(8px);}"
            "}"
        ),
        "css": "animation:stk-arrowdown 1s ease-in-out infinite;",
    },
    "swipe_up": {
        "category": "arrows",
        "description": "Vuốt lên (swipe up) — swipe gesture",
        "color": "#6C63FF",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="20" y="16" width="24" height="40" rx="12" fill="none" stroke="#6C63FF" stroke-width="3"/>'
            '<circle cx="32" cy="28" r="4" fill="#6C63FF" class="stk-swipe-dot"/>'
            '<path d="M32 8L26 16H38L32 8Z" fill="#FF6584"/>'
            '</svg>'
        ),
        "animation": "stk-swipeup",
        "keyframes": (
            "@keyframes stk-swipeup {"
            "0%{transform:translateY(12px);opacity:1;}"
            "50%{transform:translateY(-4px);opacity:0.6;}"
            "100%{transform:translateY(12px);opacity:1;}"
            "}"
        ),
        "css": "animation:stk-swipeup 1.5s ease-in-out infinite;",
    },
    "pointing_right": {
        "category": "arrows",
        "description": "Tay chỉ phải (pointing hand) — pointing gesture",
        "color": "#FFB74D",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M12 28H36C38.2 28 40 29.8 40 32C40 34.2 38.2 36 36 36H12V28Z" fill="#FFB74D"/>'
            '<path d="M40 32L56 32" stroke="#FFB74D" stroke-width="8" stroke-linecap="round"/>'
            '<path d="M52 24L60 32L52 40" fill="#FFB74D"/>'
            '<rect x="4" y="24" width="12" height="16" rx="4" fill="#FFCC80"/>'
            '</svg>'
        ),
        "animation": "stk-pointright",
        "keyframes": (
            "@keyframes stk-pointright {"
            "0%,100%{transform:translateX(0);}"
            "50%{transform:translateX(8px);}"
            "}"
        ),
        "css": "animation:stk-pointright 1s ease-in-out infinite;",
    },

    # ─── Decorative / Effects ────────────────────────────────────
    "confetti": {
        "category": "decorative",
        "description": "Pháo hoa giấy (confetti) — falling pieces",
        "color": "#FF4081",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="8" y="12" width="6" height="6" rx="1" fill="#FF4081" transform="rotate(30 11 15)"/>'
            '<rect x="24" y="4" width="5" height="5" rx="1" fill="#FFD740" transform="rotate(-20 26.5 6.5)"/>'
            '<rect x="44" y="8" width="6" height="6" rx="1" fill="#69F0AE" transform="rotate(45 47 11)"/>'
            '<rect x="52" y="24" width="5" height="5" rx="1" fill="#448AFF" transform="rotate(-15 54.5 26.5)"/>'
            '<circle cx="16" cy="32" r="3" fill="#E040FB"/>'
            '<circle cx="36" cy="20" r="2.5" fill="#FF6E40"/>'
            '<rect x="4" y="44" width="5" height="5" rx="1" fill="#FFD740" transform="rotate(60 6.5 46.5)"/>'
            '<rect x="28" y="40" width="4" height="4" rx="1" fill="#69F0AE" transform="rotate(-30 30 42)"/>'
            '<circle cx="48" cy="44" r="3" fill="#FF4081"/>'
            '<rect x="40" y="52" width="5" height="5" rx="1" fill="#448AFF" transform="rotate(25 42.5 54.5)"/>'
            '<circle cx="20" cy="52" r="2" fill="#E040FB"/>'
            '<rect x="54" y="40" width="4" height="4" rx="1" fill="#FF6E40" transform="rotate(50 56 42)"/>'
            '</svg>'
        ),
        "animation": "stk-confetti",
        "keyframes": (
            "@keyframes stk-confetti {"
            "0%{transform:translateY(-8px) rotate(0deg);opacity:0;}"
            "20%{opacity:1;}"
            "100%{transform:translateY(8px) rotate(15deg);opacity:0.7;}"
            "}"
        ),
        "css": "animation:stk-confetti 2s ease-in-out infinite;",
    },
    "badge_new": {
        "category": "decorative",
        "description": "Badge MỚI (new badge) — pulsing badge",
        "color": "#FF4081",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M32 4L38 20L56 14L46 28L60 38L42 38L44 56L32 44L20 56L22 38L4 38'
            'L18 28L8 14L26 20L32 4Z" fill="url(#badge_g)"/>'
            '<text x="32" y="36" text-anchor="middle" fill="#fff" font-size="13" font-weight="bold" '
            'font-family="Arial">NEW</text>'
            '<defs>'
            '<linearGradient id="badge_g" x1="4" y1="4" x2="60" y2="56" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FF4081"/><stop offset="1" stop-color="#F50057"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-badgenew",
        "keyframes": (
            "@keyframes stk-badgenew {"
            "0%,100%{transform:scale(1) rotate(0deg);}"
            "25%{transform:scale(1.1) rotate(5deg);}"
            "75%{transform:scale(1.05) rotate(-3deg);}"
            "}"
        ),
        "css": "animation:stk-badgenew 2s ease-in-out infinite;",
    },
    "wave": {
        "category": "decorative",
        "description": "Sóng vẫy (wave) — waving hand",
        "color": "#FFB74D",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M36 12C36 12 40 8 44 12L46 20C46 20 50 16 54 20L52 32'
            'C52 32 54 28 56 30C58 32 56 44 48 52C40 60 28 56 24 48L16 28'
            'C14 24 18 22 20 24L24 32V16C24 12 28 12 28 16V28L28 16C28 12 32 12 32 16V30'
            'L32 18C32 14 36 12 36 18V30" fill="url(#wave_g)"/>'
            '<defs>'
            '<linearGradient id="wave_g" x1="16" y1="8" x2="56" y2="60" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FFCC80"/><stop offset="1" stop-color="#FFB74D"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-wave",
        "keyframes": (
            "@keyframes stk-wave {"
            "0%,100%{transform:rotate(0deg);}"
            "15%{transform:rotate(14deg);}"
            "30%{transform:rotate(-8deg);}"
            "45%{transform:rotate(14deg);}"
            "60%{transform:rotate(-4deg);}"
            "75%{transform:rotate(10deg);}"
            "}"
        ),
        "css": "animation:stk-wave 1.8s ease-in-out infinite;transform-origin:bottom center;",
    },
    "clock": {
        "category": "business",
        "description": "Đồng hồ (clock) — spinning hands",
        "color": "#6C63FF",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<circle cx="32" cy="32" r="28" fill="url(#clock_bg)" />'
            '<circle cx="32" cy="32" r="25" fill="none" stroke="#fff" stroke-width="2" opacity="0.3"/>'
            '<line x1="32" y1="32" x2="32" y2="16" stroke="#fff" stroke-width="3" stroke-linecap="round"'
            ' class="stk-clock-min"/>'
            '<line x1="32" y1="32" x2="42" y2="32" stroke="#fff" stroke-width="2.5" stroke-linecap="round"'
            ' class="stk-clock-hr"/>'
            '<circle cx="32" cy="32" r="3" fill="#FF6584"/>'
            '<defs>'
            '<linearGradient id="clock_bg" x1="4" y1="4" x2="60" y2="60" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#7C74FF"/><stop offset="1" stop-color="#5046E5"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-clock",
        "keyframes": (
            "@keyframes stk-clock {"
            "from{transform:rotate(0deg);}"
            "to{transform:rotate(360deg);}"
            "}"
            ".stk-clock-min{animation:stk-clock 4s linear infinite;transform-origin:32px 32px;}"
            ".stk-clock-hr{animation:stk-clock 12s linear infinite;transform-origin:32px 32px;}"
        ),
        "css": "",
    },
    "shield": {
        "category": "business",
        "description": "Khiên bảo vệ (shield) — glowing shield",
        "color": "#4CAF50",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M32 4L8 16V32C8 46 18 56 32 60C46 56 56 46 56 32V16L32 4Z" fill="url(#shield_g)"/>'
            '<path d="M24 32L30 38L42 26" stroke="#fff" stroke-width="4" stroke-linecap="round" '
            'stroke-linejoin="round"/>'
            '<defs>'
            '<linearGradient id="shield_g" x1="8" y1="4" x2="56" y2="60" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#66BB6A"/><stop offset="1" stop-color="#2E7D32"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-shield",
        "keyframes": (
            "@keyframes stk-shield {"
            "0%,100%{transform:scale(1);filter:drop-shadow(0 0 4px rgba(76,175,80,0.3));}"
            "50%{transform:scale(1.05);filter:drop-shadow(0 0 12px rgba(76,175,80,0.6));}"
            "}"
        ),
        "css": "animation:stk-shield 2s ease-in-out infinite;",
    },
    "bell": {
        "category": "business",
        "description": "Chuông thông báo (bell) — ringing bell",
        "color": "#FFD740",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M32 8C32 8 22 8 18 20C14 32 12 36 8 40H56C52 36 50 32 46 20C42 8 32 8 32 8Z" '
            'fill="url(#bell_g)"/>'
            '<path d="M8 40C8 40 8 46 16 46H48C56 46 56 40 56 40" fill="#FFA000"/>'
            '<circle cx="32" cy="52" r="6" fill="#FFD740"/>'
            '<path d="M32 4V8" stroke="#FFD740" stroke-width="3" stroke-linecap="round"/>'
            '<circle cx="32" cy="4" r="2" fill="#FF6B35"/>'
            '<defs>'
            '<linearGradient id="bell_g" x1="8" y1="8" x2="56" y2="46" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FFE082"/><stop offset="1" stop-color="#FFD740"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-bell",
        "keyframes": (
            "@keyframes stk-bell {"
            "0%,100%{transform:rotate(0deg);}"
            "10%{transform:rotate(14deg);}"
            "20%{transform:rotate(-12deg);}"
            "30%{transform:rotate(10deg);}"
            "40%{transform:rotate(-6deg);}"
            "50%{transform:rotate(0deg);}"
            "}"
        ),
        "css": "animation:stk-bell 2s ease-in-out infinite;transform-origin:top center;",
    },
    "zap": {
        "category": "reactions",
        "description": "Sét đánh (lightning) — flashing bolt",
        "color": "#FFD740",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M36 4L12 36H28L24 60L52 24H36L36 4Z" fill="url(#zap_g)"/>'
            '<path d="M36 4L12 36H28L24 60L52 24H36L36 4Z" fill="none" stroke="#fff" '
            'stroke-width="1" opacity="0.3"/>'
            '<defs>'
            '<linearGradient id="zap_g" x1="12" y1="4" x2="52" y2="60" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FFE082"/><stop offset="1" stop-color="#FFD740"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-zap",
        "keyframes": (
            "@keyframes stk-zap {"
            "0%,100%{transform:scale(1);opacity:1;}"
            "10%{transform:scale(1.15);opacity:0.8;}"
            "20%{transform:scale(1);opacity:1;}"
            "30%{transform:scale(1.1);opacity:0.9;}"
            "40%{transform:scale(1);opacity:1;}"
            "}"
        ),
        "css": "animation:stk-zap 1.5s ease-in-out infinite;",
    },
    "gift": {
        "category": "decorative",
        "description": "Hộp quà (gift) — bouncing gift box",
        "color": "#FF4081",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="8" y="24" width="48" height="8" rx="2" fill="#FF4081"/>'
            '<rect x="12" y="32" width="40" height="24" rx="2" fill="url(#gift_g)"/>'
            '<rect x="28" y="24" width="8" height="32" fill="#FF80AB"/>'
            '<path d="M32 24C32 24 32 16 24 16C20 16 20 24 24 24" fill="none" '
            'stroke="#FF4081" stroke-width="3" stroke-linecap="round"/>'
            '<path d="M32 24C32 24 32 16 40 16C44 16 44 24 40 24" fill="none" '
            'stroke="#FF4081" stroke-width="3" stroke-linecap="round"/>'
            '<defs>'
            '<linearGradient id="gift_g" x1="12" y1="32" x2="52" y2="56" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FF4081"/><stop offset="1" stop-color="#C51162"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-gift",
        "keyframes": (
            "@keyframes stk-gift {"
            "0%,100%{transform:translateY(0) rotate(0deg);}"
            "20%{transform:translateY(-8px) rotate(-3deg);}"
            "40%{transform:translateY(0) rotate(2deg);}"
            "60%{transform:translateY(-4px) rotate(-1deg);}"
            "}"
        ),
        "css": "animation:stk-gift 1.5s ease-in-out infinite;",
    },
    "crown": {
        "category": "decorative",
        "description": "Vương miện (crown) — floating crown",
        "color": "#FFD740",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M8 44L16 20L28 32L32 12L36 32L48 20L56 44H8Z" fill="url(#crown_g)"/>'
            '<rect x="8" y="44" width="48" height="8" rx="2" fill="#FFA000"/>'
            '<circle cx="16" cy="20" r="3" fill="#FFE082"/>'
            '<circle cx="32" cy="12" r="3" fill="#FFE082"/>'
            '<circle cx="48" cy="20" r="3" fill="#FFE082"/>'
            '<circle cx="20" cy="48" r="2" fill="#FF6B35"/>'
            '<circle cx="32" cy="48" r="2" fill="#FF4081"/>'
            '<circle cx="44" cy="48" r="2" fill="#448AFF"/>'
            '<defs>'
            '<linearGradient id="crown_g" x1="8" y1="12" x2="56" y2="52" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#FFD740"/><stop offset="1" stop-color="#F9A825"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-crown",
        "keyframes": (
            "@keyframes stk-crown {"
            "0%,100%{transform:translateY(0) rotate(0deg);}"
            "25%{transform:translateY(-6px) rotate(3deg);}"
            "75%{transform:translateY(-4px) rotate(-2deg);}"
            "}"
        ),
        "css": "animation:stk-crown 2s ease-in-out infinite;",
    },
    "diamond": {
        "category": "decorative",
        "description": "Kim cương (diamond) — spinning gem",
        "color": "#4FC3F7",
        "svg": (
            '<svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M32 4L12 24L32 60L52 24L32 4Z" fill="url(#diamond_g)"/>'
            '<path d="M12 24H52L32 4" fill="url(#diamond_top)"/>'
            '<path d="M32 4L22 24H42L32 4Z" fill="#B3E5FC" opacity="0.6"/>'
            '<path d="M22 24L32 60L42 24" fill="#4FC3F7" opacity="0.3"/>'
            '<defs>'
            '<linearGradient id="diamond_g" x1="12" y1="4" x2="52" y2="60" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#81D4FA"/><stop offset="1" stop-color="#0288D1"/>'
            '</linearGradient>'
            '<linearGradient id="diamond_top" x1="12" y1="4" x2="52" y2="24" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="#B3E5FC"/><stop offset="1" stop-color="#4FC3F7"/>'
            '</linearGradient>'
            '</defs>'
            '</svg>'
        ),
        "animation": "stk-diamond",
        "keyframes": (
            "@keyframes stk-diamond {"
            "0%,100%{transform:scale(1);filter:brightness(1);}"
            "50%{transform:scale(1.08);filter:brightness(1.3);}"
            "}"
        ),
        "css": "animation:stk-diamond 2s ease-in-out infinite;",
    },
}

# ---------------------------------------------------------------------------
# Category labels (Vietnamese)
# ---------------------------------------------------------------------------

_CATEGORIES = {
    "reactions": "Cảm xúc / Phản ứng",
    "business": "Kinh doanh / Công việc",
    "arrows": "Mũi tên / Chỉ dẫn",
    "decorative": "Trang trí / Hiệu ứng",
}

# ---------------------------------------------------------------------------
# Position presets
# ---------------------------------------------------------------------------

_POSITIONS = {
    "top-left": "position:absolute;top:20px;left:20px;",
    "top-right": "position:absolute;top:20px;right:20px;",
    "top-center": "position:absolute;top:20px;left:50%;transform:translateX(-50%);",
    "bottom-left": "position:absolute;bottom:20px;left:20px;",
    "bottom-right": "position:absolute;bottom:20px;right:20px;",
    "bottom-center": "position:absolute;bottom:20px;left:50%;transform:translateX(-50%);",
    "center": "position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);",
    "inline": "display:inline-block;vertical-align:middle;",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_stickers(category: str = "") -> list[dict]:
    """List available stickers, optionally filtered by category.

    Returns list of {name, category, description, color}.
    """
    result = []
    for name, stk in _STICKERS.items():
        if category and stk["category"] != category:
            continue
        result.append({
            "name": name,
            "category": stk["category"],
            "description": stk["description"],
            "color": stk["color"],
        })
    return result


def list_categories() -> dict[str, str]:
    """Return {category_id: vietnamese_label}."""
    return dict(_CATEGORIES)


def get_sticker_css(name: str) -> str:
    """Get CSS @keyframes for a sticker (include in <style> block).

    Args:
        name: Sticker name (e.g. "fire", "heart").

    Returns:
        CSS string with @keyframes.
    """
    stk = _STICKERS.get(name)
    if not stk:
        return ""
    return stk["keyframes"]


def get_all_sticker_css(names: list[str]) -> str:
    """Get combined CSS @keyframes for multiple stickers.

    Args:
        names: List of sticker names.

    Returns:
        Combined CSS string.
    """
    parts = []
    seen = set()
    for n in names:
        if n in seen:
            continue
        seen.add(n)
        css = get_sticker_css(n)
        if css:
            parts.append(css)
    return "\n".join(parts)


def get_sticker_html(
    name: str,
    size: int = 64,
    position: str = "inline",
    margin: str = "",
    animation_delay: str = "",
    custom_style: str = "",
) -> str:
    """Generate HTML snippet for an animated sticker.

    The returned HTML is a <div> containing the animated SVG.
    Include get_sticker_css() output in your <style> block.

    Args:
        name: Sticker name (e.g. "fire", "heart", "checkmark").
        size: Size in pixels (width & height).
        position: Placement preset: "inline", "top-left", "top-right",
                  "bottom-left", "bottom-right", "center", or custom CSS.
        margin: Extra margin CSS (e.g. "10px 0").
        animation_delay: CSS animation-delay (e.g. "0.5s").
        custom_style: Additional inline CSS.

    Returns:
        HTML string with animated SVG sticker.
    """
    stk = _STICKERS.get(name)
    if not stk:
        return f'<!-- sticker "{name}" not found -->'

    pos_css = _POSITIONS.get(position, position)
    styles = [
        f"width:{size}px;height:{size}px;",
        pos_css,
        stk["css"],
    ]
    if margin:
        styles.append(f"margin:{margin};")
    if animation_delay:
        styles.append(f"animation-delay:{animation_delay};")
    if custom_style:
        styles.append(custom_style)

    style_str = "".join(styles)
    return f'<div class="stk stk-{name}" style="{style_str}">{stk["svg"]}</div>'


def build_sticker_slide_html(
    stickers: list[dict],
    background: str = "transparent",
    width: int = 1080,
    height: int = 1920,
    extra_html: str = "",
    extra_css: str = "",
) -> str:
    """Build a complete HTML page with animated stickers as decorations.

    Use this to create sticker-decorated slides for record_html_video.

    Args:
        stickers: List of sticker configs:
            [{"name": "fire", "size": 80, "position": "top-right", "delay": "0.3s"}, ...]
        background: CSS background for the page (default transparent for overlay).
        width: Page width in px.
        height: Page height in px.
        extra_html: Additional HTML content to include in <body>.
        extra_css: Additional CSS rules.

    Returns:
        Complete HTML string ready for record_html_video or batch_slides.
    """
    # Collect unique keyframes
    names = [s["name"] for s in stickers if s.get("name") in _STICKERS]
    keyframes = get_all_sticker_css(names)

    # Build sticker elements
    sticker_divs = []
    for s in stickers:
        html = get_sticker_html(
            name=s.get("name", ""),
            size=s.get("size", 64),
            position=s.get("position", "inline"),
            margin=s.get("margin", ""),
            animation_delay=s.get("delay", ""),
            custom_style=s.get("style", ""),
        )
        sticker_divs.append(html)

    return (
        f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>\n'
        f'*{{margin:0;padding:0;box-sizing:border-box;}}\n'
        f'body{{width:{width}px;height:{height}px;background:{background};'
        f'position:relative;overflow:hidden;}}\n'
        f'.stk{{display:inline-block;}}\n'
        f'.stk svg{{width:100%;height:100%;}}\n'
        f'{keyframes}\n'
        f'{extra_css}\n'
        f'</style></head><body>\n'
        f'{extra_html}\n'
        f'{"".join(sticker_divs)}\n'
        f'</body></html>'
    )
