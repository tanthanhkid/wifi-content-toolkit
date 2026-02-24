"""
ui.py — Gradio web UI for the poster module.

Port: 7861
Tabs: Quote, Carousel, Before/After, Promo, Case Study, Batch
Language: Vietnamese labels
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import gradio as gr

from .core import batch_render, render_poster

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TMP_DIR = Path(tempfile.gettempdir()) / "wfm_poster"
_TMP_DIR.mkdir(parents=True, exist_ok=True)

_DEFAULT_PRIMARY = "#6C63FF"
_DEFAULT_ACCENT = "#FF6584"


def _tmp_path(name: str) -> str:
    return str(_TMP_DIR / name)


def _brand_kwargs(brand_name: str, primary: str, accent: str) -> dict[str, Any]:
    return {
        "brand_name": brand_name,
        "brand_primary_color": primary or _DEFAULT_PRIMARY,
        "brand_accent_color": accent or _DEFAULT_ACCENT,
    }


# ---------------------------------------------------------------------------
# Tab renderers — each returns (image_path, status_text)
# ---------------------------------------------------------------------------


def render_quote(
    headline: str,
    subtext: str,
    brand_name: str,
    primary: str,
    accent: str,
) -> tuple[str | None, str]:
    out = _tmp_path("quote.png")
    result = render_poster(
        template_id="quote",
        fields={"headline": headline, "subtext": subtext},
        output_path=out,
        brand=_brand_kwargs(brand_name, primary, accent),
    )
    if result["status"] == "ok":
        return out, "Tạo poster thành công!"
    return None, f"Lỗi: {result['error']}"


def render_carousel(
    slides_text: str,
    headline: str,
    brand_name: str,
    primary: str,
    accent: str,
) -> tuple[str | None, str]:
    slides = [s.strip() for s in slides_text.splitlines() if s.strip()]
    out = _tmp_path("carousel.png")
    result = render_poster(
        template_id="carousel",
        fields={"headline": headline, "slides": slides},
        output_path=out,
        brand=_brand_kwargs(brand_name, primary, accent),
    )
    if result["status"] == "ok":
        return out, "Tạo carousel thành công!"
    return None, f"Lỗi: {result['error']}"


def render_before_after(
    headline: str,
    before_title: str,
    before_text: str,
    after_title: str,
    after_text: str,
    brand_name: str,
    primary: str,
    accent: str,
) -> tuple[str | None, str]:
    before_points = [s.strip() for s in before_text.splitlines() if s.strip()]
    after_points = [s.strip() for s in after_text.splitlines() if s.strip()]
    out = _tmp_path("before_after.png")
    result = render_poster(
        template_id="before_after",
        fields={
            "headline": headline,
            "before_title": before_title or "Trước",
            "before_points": before_points,
            "after_title": after_title or "Sau",
            "after_points": after_points,
        },
        output_path=out,
        brand=_brand_kwargs(brand_name, primary, accent),
    )
    if result["status"] == "ok":
        return out, "Tạo ảnh so sánh thành công!"
    return None, f"Lỗi: {result['error']}"


def render_promo(
    headline: str,
    offer: str,
    details_text: str,
    cta: str,
    urgency: str,
    brand_name: str,
    primary: str,
    accent: str,
) -> tuple[str | None, str]:
    details = [s.strip() for s in details_text.splitlines() if s.strip()]
    out = _tmp_path("promo.png")
    result = render_poster(
        template_id="promo",
        fields={
            "headline": headline,
            "offer": offer,
            "details": details,
            "cta": cta,
            "urgency": urgency,
        },
        output_path=out,
        brand=_brand_kwargs(brand_name, primary, accent),
    )
    if result["status"] == "ok":
        return out, "Tạo banner khuyến mãi thành công!"
    return None, f"Lỗi: {result['error']}"


def render_case_study(
    client: str,
    headline: str,
    duration: str,
    metrics_text: str,
    testimonial: str,
    subtext: str,
    brand_name: str,
    primary: str,
    accent: str,
) -> tuple[str | None, str]:
    metrics: list[dict[str, str]] = []
    for line in metrics_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            label, _, value = line.partition(":")
            metrics.append({"label": label.strip(), "value": value.strip()})
        else:
            metrics.append({"label": line, "value": ""})

    out = _tmp_path("case_study.png")
    result = render_poster(
        template_id="case_study",
        fields={
            "client": client,
            "headline": headline,
            "duration": duration,
            "metrics": metrics,
            "testimonial": testimonial,
            "subtext": subtext,
        },
        output_path=out,
        brand=_brand_kwargs(brand_name, primary, accent),
    )
    if result["status"] == "ok":
        return out, "Tạo case study thành công!"
    return None, f"Lỗi: {result['error']}"


def render_batch_ui(manifest_json: str, output_dir: str) -> tuple[str, str]:
    """Parse manifest JSON and batch render, returning a summary."""
    try:
        items: list[dict[str, Any]] = json.loads(manifest_json)
    except Exception as exc:
        return "", f"JSON không hợp lệ: {exc}"

    out_dir = output_dir.strip() or str(_TMP_DIR / "batch")
    results = batch_render(items, output_dir=out_dir)

    ok = sum(1 for r in results if r["status"] == "ok")
    errors = len(results) - ok
    summary_lines = [f"Tổng: {len(results)} | Thành công: {ok} | Lỗi: {errors}", ""]
    for r in results:
        icon = "✓" if r["status"] == "ok" else "✗"
        summary_lines.append(f"{icon} {r.get('output_path', '?')}  {r.get('error', '')}")

    return out_dir, "\n".join(summary_lines)


# ---------------------------------------------------------------------------
# UI builder
# ---------------------------------------------------------------------------


def build_ui() -> gr.Blocks:
    """Construct and return the Gradio Blocks application."""

    with gr.Blocks(
        title="WFM Poster Generator",
        theme=gr.themes.Soft(
            primary_hue="violet",
            secondary_hue="pink",
            font=["Be Vietnam Pro", "sans-serif"],
        ),
        css="""
        .tab-nav button { font-weight: 600; }
        .output-status { font-size: 0.9rem; color: #6C63FF; }
        """,
    ) as app:
        gr.Markdown(
            "# 🎨 WFM Poster Generator\n"
            "Tạo ảnh poster chuyên nghiệp cho mạng xã hội — 1080×1920px"
        )

        # --- shared brand block -------------------------------------------
        def brand_block() -> tuple[gr.Textbox, gr.ColorPicker, gr.ColorPicker]:
            with gr.Accordion("Thương hiệu", open=False):
                bn = gr.Textbox(label="Tên thương hiệu", placeholder="Công ty ABC")
                with gr.Row():
                    pc = gr.ColorPicker(label="Màu chính", value=_DEFAULT_PRIMARY)
                    ac = gr.ColorPicker(label="Màu nhấn", value=_DEFAULT_ACCENT)
            return bn, pc, ac

        with gr.Tabs():

            # ================================================================
            # Tab 1 — Quote
            # ================================================================
            with gr.Tab("Quote"):
                gr.Markdown("### Poster trích dẫn / câu nói truyền cảm hứng")
                with gr.Row():
                    with gr.Column(scale=2):
                        q_headline = gr.Textbox(
                            label="Câu trích dẫn (Headline)",
                            lines=4,
                            placeholder="Thành công không phải là đích đến, đó là hành trình.",
                        )
                        q_subtext = gr.Textbox(
                            label="Phụ đề / Tác giả",
                            placeholder="— Steve Jobs",
                        )
                        q_bn, q_pc, q_ac = brand_block()
                        q_btn = gr.Button("Tạo Poster", variant="primary")
                    with gr.Column(scale=3):
                        q_img = gr.Image(label="Kết quả", type="filepath", height=540)
                        q_status = gr.Textbox(label="Trạng thái", interactive=False)

                q_btn.click(
                    fn=render_quote,
                    inputs=[q_headline, q_subtext, q_bn, q_pc, q_ac],
                    outputs=[q_img, q_status],
                )

            # ================================================================
            # Tab 2 — Carousel
            # ================================================================
            with gr.Tab("Carousel"):
                gr.Markdown("### Ảnh carousel (nhiều slide)")
                with gr.Row():
                    with gr.Column(scale=2):
                        ca_headline = gr.Textbox(
                            label="Tiêu đề tổng",
                            placeholder="5 bí quyết thành công",
                        )
                        ca_slides = gr.Textbox(
                            label="Nội dung từng slide (mỗi dòng = 1 slide)",
                            lines=8,
                            placeholder="Slide 1: Đặt mục tiêu rõ ràng\nSlide 2: Hành động mỗi ngày\nSlide 3: Học hỏi không ngừng",
                        )
                        ca_bn, ca_pc, ca_ac = brand_block()
                        ca_btn = gr.Button("Tạo Carousel", variant="primary")
                    with gr.Column(scale=3):
                        ca_img = gr.Image(label="Kết quả", type="filepath", height=540)
                        ca_status = gr.Textbox(label="Trạng thái", interactive=False)

                ca_btn.click(
                    fn=render_carousel,
                    inputs=[ca_slides, ca_headline, ca_bn, ca_pc, ca_ac],
                    outputs=[ca_img, ca_status],
                )

            # ================================================================
            # Tab 3 — Before / After
            # ================================================================
            with gr.Tab("Trước / Sau"):
                gr.Markdown("### Ảnh so sánh Trước & Sau")
                with gr.Row():
                    with gr.Column(scale=2):
                        ba_headline = gr.Textbox(
                            label="Tiêu đề",
                            placeholder="Kết quả sau 30 ngày làm việc cùng chúng tôi",
                        )
                        with gr.Row():
                            ba_bt = gr.Textbox(label="Nhãn Trước", value="Trước")
                            ba_at = gr.Textbox(label="Nhãn Sau", value="Sau")
                        ba_bp = gr.Textbox(
                            label="Điểm yếu (Trước) — mỗi dòng 1 ý",
                            lines=5,
                            placeholder="Doanh thu thấp\nKhách hàng ít\nQuy trình lộn xộn",
                        )
                        ba_ap = gr.Textbox(
                            label="Điểm mạnh (Sau) — mỗi dòng 1 ý",
                            lines=5,
                            placeholder="Doanh thu tăng 3x\nKhách hàng trung thành\nQuy trình chuẩn hóa",
                        )
                        ba_bn, ba_pc, ba_ac = brand_block()
                        ba_btn = gr.Button("Tạo Ảnh So Sánh", variant="primary")
                    with gr.Column(scale=3):
                        ba_img = gr.Image(label="Kết quả", type="filepath", height=540)
                        ba_status = gr.Textbox(label="Trạng thái", interactive=False)

                ba_btn.click(
                    fn=render_before_after,
                    inputs=[ba_headline, ba_bt, ba_bp, ba_at, ba_ap, ba_bn, ba_pc, ba_ac],
                    outputs=[ba_img, ba_status],
                )

            # ================================================================
            # Tab 4 — Promo
            # ================================================================
            with gr.Tab("Khuyến Mãi"):
                gr.Markdown("### Banner khuyến mãi / ưu đãi")
                with gr.Row():
                    with gr.Column(scale=2):
                        pr_headline = gr.Textbox(
                            label="Tiêu đề",
                            placeholder="Ưu đãi đặc biệt tháng này!",
                        )
                        pr_offer = gr.Textbox(
                            label="Nội dung ưu đãi",
                            placeholder="Giảm 50% tất cả gói dịch vụ",
                        )
                        pr_details = gr.Textbox(
                            label="Chi tiết (mỗi dòng 1 điểm)",
                            lines=4,
                            placeholder="Áp dụng đến 31/12\nKhông giới hạn số lượng\nHỗ trợ 24/7",
                        )
                        pr_cta = gr.Textbox(
                            label="Nút kêu gọi hành động (CTA)",
                            placeholder="Đăng ký ngay",
                        )
                        pr_urgency = gr.Textbox(
                            label="Badge khẩn cấp",
                            placeholder="Chỉ còn 3 ngày!",
                        )
                        pr_bn, pr_pc, pr_ac = brand_block()
                        pr_btn = gr.Button("Tạo Banner Khuyến Mãi", variant="primary")
                    with gr.Column(scale=3):
                        pr_img = gr.Image(label="Kết quả", type="filepath", height=540)
                        pr_status = gr.Textbox(label="Trạng thái", interactive=False)

                pr_btn.click(
                    fn=render_promo,
                    inputs=[pr_headline, pr_offer, pr_details, pr_cta, pr_urgency, pr_bn, pr_pc, pr_ac],
                    outputs=[pr_img, pr_status],
                )

            # ================================================================
            # Tab 5 — Case Study
            # ================================================================
            with gr.Tab("Case Study"):
                gr.Markdown("### Poster case study / kết quả dự án")
                with gr.Row():
                    with gr.Column(scale=2):
                        cs_client = gr.Textbox(
                            label="Tên khách hàng / dự án",
                            placeholder="Công ty XYZ",
                        )
                        cs_headline = gr.Textbox(
                            label="Tiêu đề kết quả",
                            placeholder="Tăng trưởng 300% doanh thu trong 6 tháng",
                        )
                        cs_duration = gr.Textbox(
                            label="Thời gian",
                            placeholder="6 tháng",
                        )
                        cs_metrics = gr.Textbox(
                            label="Chỉ số (Nhãn:Giá trị — mỗi dòng 1 chỉ số)",
                            lines=4,
                            placeholder="Doanh thu:+300%\nKhách hàng mới:+150\nTỷ lệ chuyển đổi:8.5%",
                        )
                        cs_testimonial = gr.Textbox(
                            label="Trích dẫn của khách hàng",
                            lines=3,
                            placeholder="Nhờ đội ngũ WFM, chúng tôi đã vượt mọi mục tiêu đề ra.",
                        )
                        cs_subtext = gr.Textbox(
                            label="Mô tả ngắn",
                            placeholder="Giải pháp marketing toàn diện cho doanh nghiệp SME",
                        )
                        cs_bn, cs_pc, cs_ac = brand_block()
                        cs_btn = gr.Button("Tạo Case Study", variant="primary")
                    with gr.Column(scale=3):
                        cs_img = gr.Image(label="Kết quả", type="filepath", height=540)
                        cs_status = gr.Textbox(label="Trạng thái", interactive=False)

                cs_btn.click(
                    fn=render_case_study,
                    inputs=[
                        cs_client, cs_headline, cs_duration, cs_metrics,
                        cs_testimonial, cs_subtext, cs_bn, cs_pc, cs_ac,
                    ],
                    outputs=[cs_img, cs_status],
                )

            # ================================================================
            # Tab 6 — Batch
            # ================================================================
            with gr.Tab("Batch"):
                gr.Markdown(
                    "### Tạo hàng loạt từ JSON\n\n"
                    "Nhập một mảng JSON, mỗi phần tử có: "
                    "`template_id`, `fields`, `filename` (tuỳ chọn: `brand`, `size`)."
                )
                with gr.Row():
                    with gr.Column(scale=2):
                        bt_json = gr.Code(
                            label="Manifest JSON",
                            language="json",
                            value=json.dumps(
                                [
                                    {
                                        "template_id": "quote",
                                        "filename": "quote_01.png",
                                        "fields": {
                                            "headline": "Hành động ngay hôm nay.",
                                            "subtext": "— WFM Team",
                                        },
                                        "brand": {"brand_name": "WFM"},
                                    }
                                ],
                                ensure_ascii=False,
                                indent=2,
                            ),
                        )
                        bt_dir = gr.Textbox(
                            label="Thư mục xuất (để trống = tự động)",
                            placeholder="/tmp/my_posters",
                        )
                        bt_btn = gr.Button("Bắt đầu Batch Render", variant="primary")
                    with gr.Column(scale=3):
                        bt_out_dir = gr.Textbox(label="Thư mục đã lưu", interactive=False)
                        bt_summary = gr.Textbox(
                            label="Kết quả", lines=12, interactive=False
                        )

                bt_btn.click(
                    fn=render_batch_ui,
                    inputs=[bt_json, bt_dir],
                    outputs=[bt_out_dir, bt_summary],
                )

        gr.Markdown(
            "<div style='text-align:center;color:#888;font-size:0.8rem;margin-top:1rem'>"
            "WFM Poster Generator · port 7861 · show_api=True"
            "</div>"
        )

    return app


# ---------------------------------------------------------------------------
# Direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7861, show_api=True)
