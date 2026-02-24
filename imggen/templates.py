"""
Marketing prompt templates for WiFi Marketing Image Generation.

Each template targets a specific social media content format and includes
structured fields and a prompt builder that instructs Gemini to produce
professional 1080x1920 Vietnamese social media visuals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TemplateField:
    """Describes a single input field for a template."""

    key: str
    label: str
    description: str
    required: bool = True
    multiple: bool = False  # accepts a list of values


@dataclass
class Template:
    """A reusable marketing image prompt template."""

    id: str
    name: str
    description: str
    fields: list[TemplateField]

    def build_prompt(self, fields: dict[str, Any], brand: dict[str, Any] | None = None) -> str:
        """
        Build a Gemini image generation prompt from field values and optional brand config.

        Args:
            fields: Mapping of field key -> value (str or list[str]).
            brand: Optional brand configuration dict with keys like
                   ``name``, ``primary_color``, ``secondary_color``, ``font``, ``logo_url``.

        Returns:
            A fully-formed prompt string ready for the Gemini API.
        """
        raise NotImplementedError  # implemented per template subclass


# ---------------------------------------------------------------------------
# Shared brand block helper
# ---------------------------------------------------------------------------

def _brand_block(brand: dict[str, Any] | None) -> str:
    if not brand:
        return (
            "Use a clean, modern design with a professional color palette "
            "(deep blue and white). Sans-serif typography."
        )
    parts: list[str] = []
    if brand.get("name"):
        parts.append(f"Brand name: {brand['name']}.")
    if brand.get("primary_color"):
        parts.append(f"Primary color: {brand['primary_color']}.")
    if brand.get("secondary_color"):
        parts.append(f"Accent color: {brand['secondary_color']}.")
    if brand.get("font"):
        parts.append(f"Typography: {brand['font']} font family.")
    if brand.get("logo_url"):
        parts.append("Include brand logo in the top-left corner.")
    return " ".join(parts) if parts else "Professional modern design."


# ---------------------------------------------------------------------------
# Base rendering instructions shared by every template
# ---------------------------------------------------------------------------

_BASE_INSTRUCTIONS = (
    "IMPORTANT RENDERING REQUIREMENTS:\n"
    "- Canvas size: 1080 x 1920 pixels (portrait, 9:16 ratio).\n"
    "- All Vietnamese text MUST be rendered with full diacritical marks "
    "(e.g., ắ, ề, ụ, ổ, ươ). Do NOT simplify or transliterate Vietnamese.\n"
    "- Use high-contrast, legible fonts sized appropriately for mobile screens.\n"
    "- Output a single, finished social-media-ready image — no mockups, "
    "no device frames, no placeholder boxes.\n"
    "- Professional quality: sharp edges, balanced layout, rich but not cluttered.\n"
)


# ---------------------------------------------------------------------------
# Template 1: Quote
# ---------------------------------------------------------------------------

class QuoteTemplate(Template):
    """Inspirational or testimonial quote card."""

    def build_prompt(self, fields: dict[str, Any], brand: dict[str, Any] | None = None) -> str:
        quote = fields.get("quote", "")
        author = fields.get("author", "")
        context = fields.get("context", "")

        brand_desc = _brand_block(brand)

        return (
            f"Create a stunning 1080x1920 social media quote card image.\n\n"
            f"QUOTE TEXT (render exactly in Vietnamese with diacritics):\n"
            f'"{quote}"\n\n'
            f"AUTHOR: {author}\n"
            + (f"CONTEXT / SUBTITLE: {context}\n\n" if context else "\n")
            + f"DESIGN STYLE:\n{brand_desc}\n\n"
            "Layout: Large decorative quotation marks in the background, "
            "quote text centred in bold, author name below in smaller italic text, "
            "subtle gradient overlay. Elegant and shareable.\n\n"
            + _BASE_INSTRUCTIONS
        )


# ---------------------------------------------------------------------------
# Template 2: Carousel (single slide representation)
# ---------------------------------------------------------------------------

class CarouselTemplate(Template):
    """Multi-slide carousel — generates a single representative slide."""

    def build_prompt(self, fields: dict[str, Any], brand: dict[str, Any] | None = None) -> str:
        headline = fields.get("headline", "")
        slides: list[str] = fields.get("slides", [])
        subtext = fields.get("subtext", "")

        brand_desc = _brand_block(brand)

        slides_block = ""
        if slides:
            numbered = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(slides))
            slides_block = f"SLIDE CONTENTS (list each point clearly on the image):\n{numbered}\n\n"

        return (
            f"Create a 1080x1920 social media carousel slide image.\n\n"
            f"MAIN HEADLINE (Vietnamese with diacritics): {headline}\n\n"
            + slides_block
            + (f"SUBTEXT / CAPTION: {subtext}\n\n" if subtext else "")
            + f"DESIGN STYLE:\n{brand_desc}\n\n"
            "Layout: Bold headline at the top, numbered list of points in the centre "
            "with icon bullets, a subtle swipe-right indicator arrow at the bottom right, "
            "progress dots or slide number indicator. Clean grid layout.\n\n"
            + _BASE_INSTRUCTIONS
        )


# ---------------------------------------------------------------------------
# Template 3: Before / After
# ---------------------------------------------------------------------------

class BeforeAfterTemplate(Template):
    """Before-and-after transformation comparison card."""

    def build_prompt(self, fields: dict[str, Any], brand: dict[str, Any] | None = None) -> str:
        before_title = fields.get("before_title", "Trước")
        before_points: list[str] = fields.get("before_points", [])
        after_title = fields.get("after_title", "Sau")
        after_points: list[str] = fields.get("after_points", [])
        headline = fields.get("headline", "")

        brand_desc = _brand_block(brand)

        def _points(pts: list[str], symbol: str) -> str:
            return "\n".join(f"  {symbol} {p}" for p in pts) if pts else f"  {symbol} (empty)"

        return (
            f"Create a 1080x1920 before-and-after comparison social media image.\n\n"
            + (f"OVERALL HEADLINE (Vietnamese with diacritics): {headline}\n\n" if headline else "")
            + f"LEFT PANEL — BEFORE ({before_title}):\n"
            + _points(before_points, "✗")
            + f"\n\nRIGHT PANEL — AFTER ({after_title}):\n"
            + _points(after_points, "✓")
            + f"\n\nDESIGN STYLE:\n{brand_desc}\n\n"
            "Layout: Split vertically — left half in muted grey/red tones labelled 'Trước', "
            "right half in vibrant green/blue tones labelled 'Sau'. "
            "A bold arrow or lightning bolt divides the panels. "
            "Text lists clearly readable. Dramatic, high-impact contrast.\n\n"
            + _BASE_INSTRUCTIONS
        )


# ---------------------------------------------------------------------------
# Template 4: Promo / Offer
# ---------------------------------------------------------------------------

class PromoTemplate(Template):
    """Promotional offer or discount announcement."""

    def build_prompt(self, fields: dict[str, Any], brand: dict[str, Any] | None = None) -> str:
        headline = fields.get("headline", "")
        offer = fields.get("offer", "")
        details: list[str] = fields.get("details", [])
        cta = fields.get("cta", "Liên hệ ngay")
        urgency = fields.get("urgency", "")

        brand_desc = _brand_block(brand)

        details_block = ""
        if details:
            bullet_list = "\n".join(f"  • {d}" for d in details)
            details_block = f"OFFER DETAILS:\n{bullet_list}\n\n"

        return (
            f"Create a 1080x1920 promotional social media image for a special offer.\n\n"
            f"HEADLINE (Vietnamese with diacritics): {headline}\n\n"
            f"MAIN OFFER TEXT (make it visually dominant): {offer}\n\n"
            + details_block
            + (f"URGENCY / DEADLINE: {urgency}\n\n" if urgency else "")
            + f"CALL TO ACTION BUTTON TEXT: {cta}\n\n"
            + f"DESIGN STYLE:\n{brand_desc}\n\n"
            "Layout: Eye-catching burst or badge for the main offer, bold headline, "
            "bullet details in a clean panel, bright CTA button at the bottom, "
            "urgency text in a contrasting colour (red/orange). "
            "Energetic, sales-focused design.\n\n"
            + _BASE_INSTRUCTIONS
        )


# ---------------------------------------------------------------------------
# Template 5: Case Study / Success Story
# ---------------------------------------------------------------------------

class CaseStudyTemplate(Template):
    """Client success story or case study highlight."""

    def build_prompt(self, fields: dict[str, Any], brand: dict[str, Any] | None = None) -> str:
        client = fields.get("client", "")
        headline = fields.get("headline", "")
        duration = fields.get("duration", "")
        metrics: list[str] = fields.get("metrics", [])
        testimonial = fields.get("testimonial", "")
        cta = fields.get("cta", "Xem thêm")

        brand_desc = _brand_block(brand)

        metrics_block = ""
        if metrics:
            m_list = "\n".join(f"  ★ {m}" for m in metrics)
            metrics_block = f"KEY RESULTS / METRICS (display as large stat cards):\n{m_list}\n\n"

        return (
            f"Create a 1080x1920 case study / success story social media image.\n\n"
            f"CLIENT NAME: {client}\n"
            + (f"CAMPAIGN DURATION: {duration}\n" if duration else "")
            + f"\nHEADLINE (Vietnamese with diacritics): {headline}\n\n"
            + metrics_block
            + (
                f"CLIENT TESTIMONIAL QUOTE (Vietnamese with diacritics):\n\"{testimonial}\"\n\n"
                if testimonial else ""
            )
            + f"CALL TO ACTION: {cta}\n\n"
            + f"DESIGN STYLE:\n{brand_desc}\n\n"
            "Layout: Client logo or name banner at the top, "
            "large metric stat cards (number + label) in the centre, "
            "testimonial quote in a styled box, CTA at the bottom. "
            "Professional, trust-building, data-driven aesthetic.\n\n"
            + _BASE_INSTRUCTIONS
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, Template] = {
    t.id: t
    for t in [
        QuoteTemplate(
            id="quote",
            name="Quote Card",
            description="Thẻ trích dẫn truyền cảm hứng hoặc lời chứng thực khách hàng.",
            fields=[
                TemplateField("quote", "Nội dung trích dẫn", "Câu trích dẫn chính (tiếng Việt).", required=True),
                TemplateField("author", "Tác giả", "Tên người được trích dẫn.", required=False),
                TemplateField("context", "Ngữ cảnh / Phụ đề", "Mô tả ngắn về tác giả hoặc ngữ cảnh.", required=False),
            ],
        ),
        CarouselTemplate(
            id="carousel",
            name="Carousel Slide",
            description="Slide carousel đa điểm — hiển thị danh sách nội dung có tiêu đề.",
            fields=[
                TemplateField("headline", "Tiêu đề chính", "Tiêu đề lớn của slide.", required=True),
                TemplateField("slides", "Các điểm nội dung", "Danh sách các điểm nội dung của slide.", required=True, multiple=True),
                TemplateField("subtext", "Phụ đề", "Văn bản bổ sung ở dưới cùng.", required=False),
            ],
        ),
        BeforeAfterTemplate(
            id="before_after",
            name="Before & After",
            description="Hình ảnh so sánh trước và sau khi sử dụng dịch vụ.",
            fields=[
                TemplateField("headline", "Tiêu đề tổng thể", "Tiêu đề bao quát cả hai phần.", required=False),
                TemplateField("before_title", "Nhãn phần Trước", "Nhãn cột bên trái.", required=False),
                TemplateField("before_points", "Điểm phần Trước", "Các điểm tiêu cực trước khi dùng dịch vụ.", required=True, multiple=True),
                TemplateField("after_title", "Nhãn phần Sau", "Nhãn cột bên phải.", required=False),
                TemplateField("after_points", "Điểm phần Sau", "Các điểm tích cực sau khi dùng dịch vụ.", required=True, multiple=True),
            ],
        ),
        PromoTemplate(
            id="promo",
            name="Promo / Offer",
            description="Thông báo ưu đãi khuyến mãi hoặc giảm giá hấp dẫn.",
            fields=[
                TemplateField("headline", "Tiêu đề", "Dòng tiêu đề chính của ưu đãi.", required=True),
                TemplateField("offer", "Nội dung ưu đãi", "Văn bản ưu đãi nổi bật (ví dụ: Giảm 50%).", required=True),
                TemplateField("details", "Chi tiết ưu đãi", "Danh sách các điểm chi tiết ưu đãi.", required=False, multiple=True),
                TemplateField("cta", "Kêu gọi hành động", "Văn bản nút CTA.", required=False),
                TemplateField("urgency", "Thông điệp khẩn cấp", "Hạn chót hoặc thông điệp tạo sự khẩn cấp.", required=False),
            ],
        ),
        CaseStudyTemplate(
            id="case_study",
            name="Case Study",
            description="Câu chuyện thành công của khách hàng hoặc tóm tắt nghiên cứu điển hình.",
            fields=[
                TemplateField("client", "Tên khách hàng", "Tên doanh nghiệp hoặc khách hàng.", required=True),
                TemplateField("headline", "Tiêu đề", "Dòng tiêu đề tóm tắt thành công.", required=True),
                TemplateField("duration", "Thời gian chiến dịch", "Khoảng thời gian thực hiện (ví dụ: 3 tháng).", required=False),
                TemplateField("metrics", "Chỉ số kết quả", "Các chỉ số thành công nổi bật (ví dụ: Tăng 200% doanh thu).", required=True, multiple=True),
                TemplateField("testimonial", "Lời chứng thực", "Câu trích dẫn của khách hàng (tiếng Việt).", required=False),
                TemplateField("cta", "Kêu gọi hành động", "Văn bản nút CTA.", required=False),
            ],
        ),
    ]
}


def get_template(template_id: str) -> Template:
    """Return a template by ID, raising KeyError if not found."""
    if template_id not in _TEMPLATES:
        raise KeyError(
            f"Template '{template_id}' không tồn tại. "
            f"Các template hợp lệ: {', '.join(_TEMPLATES.keys())}"
        )
    return _TEMPLATES[template_id]


def list_templates() -> list[Template]:
    """Return all available templates in definition order."""
    return list(_TEMPLATES.values())
