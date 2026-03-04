"""
10 Design System Themes for TikTok Video Production.

Usage:
    from design_system.themes import get_random_theme, get_theme, THEMES

    theme = get_random_theme()
    css = theme.base_css()
    # Use theme colors, typography in HTML slides
"""

import random
from dataclasses import dataclass, field


@dataclass
class Theme:
    name: str
    description: str
    # Colors
    primary: str
    secondary: str
    accent: str
    bg_dark: str
    bg_light: str
    text_on_dark: str
    text_on_light: str
    badge_border_dark: str
    badge_border_light: str
    # Typography
    font_family: str
    font_import: str
    heading_weight: int = 900
    heading_italic: bool = True
    heading_size: str = "96px"
    body_size: str = "26px"
    badge_size: str = "18px"
    letter_spacing: str = "-2px"
    # Style extras
    badge_radius: str = "999px"
    photo_filter: str = "none"
    gradient: str = ""  # optional gradient overlay

    def base_css(self) -> str:
        italic = "italic" if self.heading_italic else "normal"
        gradient_bg = ""
        if self.gradient:
            gradient_bg = f"background: {self.gradient};"
        return f"""@import url('{self.font_import}');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1080px; height: 1920px;
  font-family: '{self.font_family}', sans-serif;
  overflow: hidden;
}}
.slide-dark {{
  background: {self.bg_dark}; color: {self.text_on_dark};
  {gradient_bg}
}}
.slide-light {{
  background: {self.bg_light}; color: {self.text_on_light};
}}
.mega-heading {{
  font-size: {self.heading_size}; font-weight: {self.heading_weight};
  font-style: {italic}; line-height: 1.0;
  letter-spacing: {self.letter_spacing};
}}
.slide-dark .mega-heading {{ color: {self.text_on_dark}; }}
.slide-light .mega-heading {{ color: {self.primary}; }}
.sub-heading {{
  font-size: 42px; font-weight: 700; line-height: 1.2;
}}
.body-text {{
  font-size: {self.body_size}; font-weight: 400; line-height: 1.6;
}}
.pill-badge {{
  display: inline-block; padding: 12px 32px;
  border: 1.5px solid {self.badge_border_dark};
  border-radius: {self.badge_radius};
  font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.5px; font-size: {self.badge_size};
}}
.slide-dark .pill-badge {{ border-color: {self.badge_border_dark}; color: {self.text_on_dark}; }}
.slide-light .pill-badge {{ border-color: {self.badge_border_light}; color: {self.primary}; }}
.accent {{ color: {self.accent}; }}
.photo {{ filter: {self.photo_filter}; }}
.page-number {{
  position: absolute; top: 40px; right: 40px;
  width: 56px; height: 56px;
  border: 1.5px solid currentColor; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 600;
}}
"""

    def slide_dark_style(self) -> str:
        if self.gradient:
            return f"background: {self.gradient}; color: {self.text_on_dark};"
        return f"background: {self.bg_dark}; color: {self.text_on_dark};"

    def slide_light_style(self) -> str:
        return f"background: {self.bg_light}; color: {self.text_on_light};"


# ============================================================
# 10 THEMES
# ============================================================

THEMES: list[Theme] = [
    # 1. ORIGINAL — Trinity Blue/Beige (hiện tại)
    Theme(
        name="trinity",
        description="Original Trinity brand — professional blue & warm beige",
        primary="#1351aa",
        secondary="#e3e2de",
        accent="#f59e0b",
        bg_dark="#1351aa",
        bg_light="#e3e2de",
        text_on_dark="#ffffff",
        text_on_light="#1a1a1a",
        badge_border_dark="rgba(255,255,255,0.5)",
        badge_border_light="rgba(19,81,170,0.3)",
        font_family="Be Vietnam Pro",
        font_import="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap",
        photo_filter="grayscale(100%)",
    ),

    # 2. MIDNIGHT PURPLE — Dark luxury, tech/AI vibes
    Theme(
        name="midnight",
        description="Deep purple & electric violet — luxury tech, AI vibes",
        primary="#7c3aed",
        secondary="#1e1b4b",
        accent="#a78bfa",
        bg_dark="#0f0a2a",
        bg_light="#ede9fe",
        text_on_dark="#f5f3ff",
        text_on_light="#1e1b4b",
        badge_border_dark="rgba(167,139,250,0.5)",
        badge_border_light="rgba(124,58,237,0.3)",
        font_family="Be Vietnam Pro",
        font_import="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap",
        gradient="linear-gradient(135deg, #0f0a2a 0%, #1e1b4b 50%, #312e81 100%)",
    ),

    # 3. CORAL SUNSET — Warm, energetic, lifestyle
    Theme(
        name="coral",
        description="Coral & warm cream — energetic, lifestyle, food/beauty",
        primary="#ef4444",
        secondary="#fef2f2",
        accent="#fb923c",
        bg_dark="#991b1b",
        bg_light="#fff7ed",
        text_on_dark="#ffffff",
        text_on_light="#1c1917",
        badge_border_dark="rgba(255,255,255,0.4)",
        badge_border_light="rgba(239,68,68,0.3)",
        font_family="Be Vietnam Pro",
        font_import="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap",
        heading_italic=False,
        heading_weight=800,
        gradient="linear-gradient(180deg, #991b1b 0%, #b91c1c 100%)",
    ),

    # 4. FOREST GREEN — Nature, sustainability, health
    Theme(
        name="forest",
        description="Deep forest green & cream — nature, health, sustainability",
        primary="#166534",
        secondary="#f0fdf4",
        accent="#4ade80",
        bg_dark="#14532d",
        bg_light="#ecfdf5",
        text_on_dark="#f0fdf4",
        text_on_light="#14532d",
        badge_border_dark="rgba(74,222,128,0.5)",
        badge_border_light="rgba(22,101,52,0.3)",
        font_family="Be Vietnam Pro",
        font_import="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap",
    ),

    # 5. NEON CYBER — Bold neon on dark, gaming/tech
    Theme(
        name="neon",
        description="Neon cyan on near-black — gaming, tech, startups",
        primary="#06b6d4",
        secondary="#0a0a0a",
        accent="#22d3ee",
        bg_dark="#0a0a0a",
        bg_light="#ecfeff",
        text_on_dark="#ecfeff",
        text_on_light="#0a0a0a",
        badge_border_dark="rgba(6,182,212,0.6)",
        badge_border_light="rgba(6,182,212,0.3)",
        font_family="Be Vietnam Pro",
        font_import="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap",
        heading_italic=False,
        heading_weight=900,
        letter_spacing="-3px",
        heading_size="104px",
    ),

    # 6. GOLDEN ELEGANT — Gold & charcoal, premium/finance
    Theme(
        name="golden",
        description="Gold & charcoal — premium, finance, luxury brand",
        primary="#b45309",
        secondary="#292524",
        accent="#f59e0b",
        bg_dark="#1c1917",
        bg_light="#fffbeb",
        text_on_dark="#fef3c7",
        text_on_light="#292524",
        badge_border_dark="rgba(245,158,11,0.5)",
        badge_border_light="rgba(180,83,9,0.3)",
        font_family="Be Vietnam Pro",
        font_import="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap",
        photo_filter="sepia(30%)",
    ),

    # 7. OCEAN TEAL — Calm teal & sand, education/SaaS
    Theme(
        name="ocean",
        description="Teal & warm sand — calm, education, SaaS, productivity",
        primary="#0d9488",
        secondary="#f0fdfa",
        accent="#2dd4bf",
        bg_dark="#134e4a",
        bg_light="#f5f5f4",
        text_on_dark="#f0fdfa",
        text_on_light="#134e4a",
        badge_border_dark="rgba(45,212,191,0.5)",
        badge_border_light="rgba(13,148,136,0.3)",
        font_family="Be Vietnam Pro",
        font_import="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap",
        heading_size="88px",
    ),

    # 8. ROSE MINIMAL — Soft pink & white, clean minimal
    Theme(
        name="rose",
        description="Soft rose & white — minimal, feminine, beauty, wellness",
        primary="#e11d48",
        secondary="#fff1f2",
        accent="#fb7185",
        bg_dark="#9f1239",
        bg_light="#fff1f2",
        text_on_dark="#ffe4e6",
        text_on_light="#1a1a1a",
        badge_border_dark="rgba(251,113,133,0.5)",
        badge_border_light="rgba(225,29,72,0.25)",
        font_family="Be Vietnam Pro",
        font_import="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap",
        heading_italic=False,
        heading_weight=800,
        badge_radius="12px",
    ),

    # 9. SLATE MONO — Monochrome gray, editorial/news
    Theme(
        name="slate",
        description="Monochrome slate — editorial, news, serious content",
        primary="#334155",
        secondary="#f1f5f9",
        accent="#f97316",
        bg_dark="#0f172a",
        bg_light="#f8fafc",
        text_on_dark="#e2e8f0",
        text_on_light="#0f172a",
        badge_border_dark="rgba(226,232,240,0.4)",
        badge_border_light="rgba(51,65,85,0.3)",
        font_family="Be Vietnam Pro",
        font_import="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap",
        photo_filter="grayscale(100%) contrast(110%)",
        heading_size="92px",
    ),

    # 10. ELECTRIC ORANGE — Bold orange & navy, startup/launch
    Theme(
        name="electric",
        description="Electric orange & deep navy — startup launches, announcements",
        primary="#ea580c",
        secondary="#1e3a5f",
        accent="#fdba74",
        bg_dark="#172554",
        bg_light="#fff7ed",
        text_on_dark="#ffedd5",
        text_on_light="#172554",
        badge_border_dark="rgba(253,186,116,0.5)",
        badge_border_light="rgba(234,88,12,0.3)",
        font_family="Be Vietnam Pro",
        font_import="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700;1,800;1,900&display=swap",
        heading_weight=900,
        heading_italic=True,
        letter_spacing="-3px",
        heading_size="100px",
        gradient="linear-gradient(160deg, #172554 0%, #1e3a5f 60%, #1e40af 100%)",
    ),
]

THEME_MAP: dict[str, Theme] = {t.name: t for t in THEMES}


def get_theme(name: str) -> Theme:
    """Get a theme by name. Raises KeyError if not found."""
    return THEME_MAP[name]


def get_random_theme() -> Theme:
    """Get a random theme from the 10 available themes."""
    return random.choice(THEMES)


def list_themes() -> list[dict]:
    """Return summary of all themes."""
    return [{"name": t.name, "description": t.description, "primary": t.primary, "bg_dark": t.bg_dark, "bg_light": t.bg_light} for t in THEMES]
