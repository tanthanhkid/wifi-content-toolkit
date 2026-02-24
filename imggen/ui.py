"""
ui.py — Gradio web interface for WiFi Marketing Image Generation.

Tabs
----
1. Prompt tự do  — Free-form prompt with direct output path control.
2. Template      — Structured form for all 5 marketing templates.
3. Batch         — JSON batch processing with download support.

Port default: 7860. show_api=True.
All labels and messages are in Vietnamese.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import gradio as gr

from imggen.templates import list_templates, get_template


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _api_key_or_env(provided: str) -> str:
    """Return provided key, falling back to GEMINI_API_KEY env var."""
    key = (provided or "").strip()
    if not key:
        key = os.environ.get("GEMINI_API_KEY", "")
    return key


def _temp_output(suffix: str = ".png") -> str:
    """Create a temporary file path for image output."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


# ---------------------------------------------------------------------------
# Tab 1: Free-form prompt
# ---------------------------------------------------------------------------

def _tab_free_prompt(api_key_state: gr.State) -> None:
    gr.Markdown("## Tạo ảnh từ prompt tự do")
    gr.Markdown(
        "Nhập prompt mô tả hình ảnh bạn muốn tạo. "
        "Gemini sẽ render văn bản tiếng Việt với đầy đủ dấu thanh và dấu phụ."
    )

    with gr.Row():
        with gr.Column(scale=2):
            prompt_input = gr.Textbox(
                label="Prompt",
                placeholder="Nhập mô tả hình ảnh marketing (tiếng Việt hoặc tiếng Anh)...",
                lines=6,
            )
            model_input = gr.Textbox(
                label="Model",
                value="gemini-2.0-flash-exp-image-generation",
            )
            api_key_input = gr.Textbox(
                label="API Key (để trống để dùng biến môi trường GEMINI_API_KEY)",
                placeholder="AIza...",
                type="password",
            )
            generate_btn = gr.Button("Tạo ảnh", variant="primary")

        with gr.Column(scale=2):
            output_image = gr.Image(label="Ảnh đầu ra", type="filepath")
            status_text = gr.Textbox(label="Trạng thái", interactive=False, lines=3)

    def _generate(prompt: str, model: str, api_key_field: str) -> tuple[str | None, str]:
        from imggen.core import generate_image

        key = _api_key_or_env(api_key_field)
        if not key:
            return None, "Lỗi: Chưa cung cấp API key."
        if not prompt.strip():
            return None, "Lỗi: Prompt không được để trống."

        out_path = _temp_output(".png")
        result = generate_image(
            prompt=prompt.strip(),
            output_path=out_path,
            api_key=key,
            model=model.strip() or "gemini-2.0-flash-exp-image-generation",
        )
        if result["success"]:
            return result["output_path"], f"Thành công! Đã lưu tại: {result['output_path']}"
        return None, f"Lỗi: {result.get('error', 'Không xác định')}"

    generate_btn.click(
        fn=_generate,
        inputs=[prompt_input, model_input, api_key_input],
        outputs=[output_image, status_text],
    )


# ---------------------------------------------------------------------------
# Tab 2: Template
# ---------------------------------------------------------------------------

def _tab_template() -> None:
    gr.Markdown("## Tạo ảnh từ template marketing")
    gr.Markdown("Chọn template phù hợp và điền các trường thông tin. Ảnh sẽ được tạo theo bố cục chuẩn.")

    templates = list_templates()
    template_choices = [(f"{t.name} — {t.description}", t.id) for t in templates]

    with gr.Row():
        with gr.Column(scale=1):
            template_dropdown = gr.Dropdown(
                label="Chọn template",
                choices=template_choices,
                value=templates[0].id if templates else None,
            )
            model_input = gr.Textbox(
                label="Model",
                value="gemini-2.0-flash-exp-image-generation",
            )
            api_key_input = gr.Textbox(
                label="API Key",
                placeholder="AIza...",
                type="password",
            )

            # --- Brand section ---
            with gr.Accordion("Cấu hình thương hiệu (tuỳ chọn)", open=False):
                brand_name = gr.Textbox(label="Tên thương hiệu")
                brand_primary = gr.Textbox(label="Màu chủ đạo (ví dụ: #0055A4)")
                brand_secondary = gr.Textbox(label="Màu phụ")
                brand_font = gr.Textbox(label="Font chữ")

        with gr.Column(scale=2):
            # --- Quote fields ---
            with gr.Group(visible=True) as quote_group:
                gr.Markdown("### Quote Card")
                q_quote = gr.Textbox(label="Nội dung trích dẫn *", lines=3,
                                     placeholder="Câu trích dẫn chính...")
                q_author = gr.Textbox(label="Tác giả")
                q_context = gr.Textbox(label="Ngữ cảnh / Phụ đề")

            # --- Carousel fields ---
            with gr.Group(visible=False) as carousel_group:
                gr.Markdown("### Carousel Slide")
                c_headline = gr.Textbox(label="Tiêu đề chính *")
                c_slides = gr.Textbox(
                    label="Các điểm nội dung * (mỗi dòng một điểm)",
                    lines=5,
                    placeholder="Điểm 1\nĐiểm 2\nĐiểm 3",
                )
                c_subtext = gr.Textbox(label="Phụ đề")

            # --- Before/After fields ---
            with gr.Group(visible=False) as before_after_group:
                gr.Markdown("### Before & After")
                ba_headline = gr.Textbox(label="Tiêu đề tổng thể")
                ba_before_title = gr.Textbox(label="Nhãn cột Trước", value="Trước")
                ba_before_points = gr.Textbox(
                    label="Điểm phần Trước * (mỗi dòng một điểm)",
                    lines=4,
                    placeholder="Vấn đề 1\nVấn đề 2",
                )
                ba_after_title = gr.Textbox(label="Nhãn cột Sau", value="Sau")
                ba_after_points = gr.Textbox(
                    label="Điểm phần Sau * (mỗi dòng một điểm)",
                    lines=4,
                    placeholder="Kết quả 1\nKết quả 2",
                )

            # --- Promo fields ---
            with gr.Group(visible=False) as promo_group:
                gr.Markdown("### Promo / Offer")
                p_headline = gr.Textbox(label="Tiêu đề *")
                p_offer = gr.Textbox(label="Nội dung ưu đãi nổi bật *",
                                     placeholder="Giảm 50%")
                p_details = gr.Textbox(
                    label="Chi tiết ưu đãi (mỗi dòng một điểm)",
                    lines=4,
                )
                p_cta = gr.Textbox(label="Kêu gọi hành động", value="Liên hệ ngay")
                p_urgency = gr.Textbox(label="Thông điệp khẩn cấp",
                                       placeholder="Chỉ còn 3 ngày!")

            # --- Case Study fields ---
            with gr.Group(visible=False) as case_study_group:
                gr.Markdown("### Case Study")
                cs_client = gr.Textbox(label="Tên khách hàng *")
                cs_headline = gr.Textbox(label="Tiêu đề *")
                cs_duration = gr.Textbox(label="Thời gian chiến dịch",
                                         placeholder="3 tháng")
                cs_metrics = gr.Textbox(
                    label="Chỉ số kết quả * (mỗi dòng một chỉ số)",
                    lines=4,
                    placeholder="Tăng 200% doanh thu\nGiảm 30% chi phí",
                )
                cs_testimonial = gr.Textbox(
                    label="Lời chứng thực",
                    lines=3,
                )
                cs_cta = gr.Textbox(label="Kêu gọi hành động", value="Xem thêm")

    generate_btn = gr.Button("Tạo ảnh từ template", variant="primary")
    output_image = gr.Image(label="Ảnh đầu ra", type="filepath")
    status_text = gr.Textbox(label="Trạng thái / Prompt", interactive=False, lines=5)

    # Show/hide template field groups
    all_groups = [quote_group, carousel_group, before_after_group, promo_group, case_study_group]
    id_to_index = {"quote": 0, "carousel": 1, "before_after": 2, "promo": 3, "case_study": 4}

    def _switch_template(selected_id: str) -> list[dict]:
        selected_idx = id_to_index.get(selected_id, 0)
        return [gr.update(visible=(i == selected_idx)) for i in range(len(all_groups))]

    template_dropdown.change(
        fn=_switch_template,
        inputs=[template_dropdown],
        outputs=all_groups,
    )

    def _generate_template(
        template_id: str,
        model: str,
        api_key_field: str,
        brand_name_val: str,
        brand_primary_val: str,
        brand_secondary_val: str,
        brand_font_val: str,
        # quote
        q_quote_val: str, q_author_val: str, q_context_val: str,
        # carousel
        c_headline_val: str, c_slides_val: str, c_subtext_val: str,
        # before_after
        ba_headline_val: str,
        ba_before_title_val: str, ba_before_points_val: str,
        ba_after_title_val: str, ba_after_points_val: str,
        # promo
        p_headline_val: str, p_offer_val: str, p_details_val: str,
        p_cta_val: str, p_urgency_val: str,
        # case_study
        cs_client_val: str, cs_headline_val: str, cs_duration_val: str,
        cs_metrics_val: str, cs_testimonial_val: str, cs_cta_val: str,
    ) -> tuple[str | None, str]:
        from imggen.core import generate_from_template

        key = _api_key_or_env(api_key_field)
        if not key:
            return None, "Lỗi: Chưa cung cấp API key."

        # Build fields based on selected template
        fields: dict[str, Any] = {}
        if template_id == "quote":
            fields = {
                "quote": q_quote_val,
                "author": q_author_val,
                "context": q_context_val,
            }
        elif template_id == "carousel":
            fields = {
                "headline": c_headline_val,
                "slides": [s.strip() for s in c_slides_val.splitlines() if s.strip()],
                "subtext": c_subtext_val,
            }
        elif template_id == "before_after":
            fields = {
                "headline": ba_headline_val,
                "before_title": ba_before_title_val or "Trước",
                "before_points": [s.strip() for s in ba_before_points_val.splitlines() if s.strip()],
                "after_title": ba_after_title_val or "Sau",
                "after_points": [s.strip() for s in ba_after_points_val.splitlines() if s.strip()],
            }
        elif template_id == "promo":
            fields = {
                "headline": p_headline_val,
                "offer": p_offer_val,
                "details": [s.strip() for s in p_details_val.splitlines() if s.strip()],
                "cta": p_cta_val,
                "urgency": p_urgency_val,
            }
        elif template_id == "case_study":
            fields = {
                "client": cs_client_val,
                "headline": cs_headline_val,
                "duration": cs_duration_val,
                "metrics": [s.strip() for s in cs_metrics_val.splitlines() if s.strip()],
                "testimonial": cs_testimonial_val,
                "cta": cs_cta_val,
            }

        brand: dict[str, Any] | None = None
        if any([brand_name_val, brand_primary_val, brand_secondary_val, brand_font_val]):
            brand = {}
            if brand_name_val:
                brand["name"] = brand_name_val
            if brand_primary_val:
                brand["primary_color"] = brand_primary_val
            if brand_secondary_val:
                brand["secondary_color"] = brand_secondary_val
            if brand_font_val:
                brand["font"] = brand_font_val

        out_path = _temp_output(".png")
        result = generate_from_template(
            template_id=template_id,
            fields=fields,
            output_path=out_path,
            api_key=key,
            brand=brand,
            model=model.strip() or "gemini-2.0-flash-exp-image-generation",
        )

        if result["success"]:
            prompt_preview = (result.get("prompt") or "")[:500]
            status = f"Thành công!\nPrompt (rút gọn):\n{prompt_preview}..."
            return result["output_path"], status
        return None, f"Lỗi: {result.get('error', 'Không xác định')}"

    generate_btn.click(
        fn=_generate_template,
        inputs=[
            template_dropdown, model_input, api_key_input,
            brand_name, brand_primary, brand_secondary, brand_font,
            q_quote, q_author, q_context,
            c_headline, c_slides, c_subtext,
            ba_headline, ba_before_title, ba_before_points, ba_after_title, ba_after_points,
            p_headline, p_offer, p_details, p_cta, p_urgency,
            cs_client, cs_headline, cs_duration, cs_metrics, cs_testimonial, cs_cta,
        ],
        outputs=[output_image, status_text],
    )


# ---------------------------------------------------------------------------
# Tab 3: Batch
# ---------------------------------------------------------------------------

def _tab_batch() -> None:
    gr.Markdown("## Tạo ảnh hàng loạt (Batch)")
    gr.Markdown(
        "Tải lên file JSON chứa danh sách các yêu cầu tạo ảnh. "
        "Mỗi phần tử cần có `filename` và `prompt` hoặc `template_id` + `fields`."
    )

    with gr.Row():
        with gr.Column():
            batch_file = gr.File(
                label="File JSON batch",
                file_types=[".json"],
            )
            output_dir_input = gr.Textbox(
                label="Thư mục đầu ra",
                placeholder="/tmp/imggen_batch",
                value="/tmp/imggen_batch",
            )
            delay_input = gr.Number(
                label="Độ trễ giữa các yêu cầu (giây)",
                value=6.0,
                minimum=0.0,
            )
            model_input = gr.Textbox(
                label="Model mặc định",
                value="gemini-2.0-flash-exp-image-generation",
            )
            api_key_input = gr.Textbox(
                label="API Key",
                placeholder="AIza...",
                type="password",
            )
            run_btn = gr.Button("Chạy batch", variant="primary")

        with gr.Column():
            batch_status = gr.Textbox(
                label="Kết quả batch",
                lines=20,
                interactive=False,
            )
            batch_json_output = gr.JSON(label="Chi tiết JSON kết quả")

    gr.Markdown(
        "### Ví dụ format file JSON batch\n"
        "```json\n"
        "[\n"
        '  {"filename": "promo1.png", "prompt": "Ảnh quảng cáo WiFi marketing chuyên nghiệp"},\n'
        '  {"filename": "quote1.png", "template_id": "quote", '
        '"fields": {"quote": "Thành công đến từ sự kiên trì", "author": "Khuyết danh"}}\n'
        "]\n"
        "```"
    )

    def _run_batch(
        file_obj: Any,
        output_dir: str,
        delay: float,
        model: str,
        api_key_field: str,
    ) -> tuple[str, list[dict]]:
        from imggen.core import batch_generate
        import time

        key = _api_key_or_env(api_key_field)
        if not key:
            return "Lỗi: Chưa cung cấp API key.", []

        if file_obj is None:
            return "Lỗi: Chưa tải lên file batch.", []

        try:
            file_path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
            raw = json.loads(Path(file_path).read_text(encoding="utf-8"))
        except Exception as exc:
            return f"Lỗi đọc file JSON: {exc}", []

        if not isinstance(raw, list):
            return "Lỗi: File JSON phải là một array.", []

        for item in raw:
            item.setdefault("model", model.strip() or "gemini-2.0-flash-exp-image-generation")

        out_dir = Path(output_dir.strip() or "/tmp/imggen_batch")
        results = batch_generate(raw, out_dir, key, delay=float(delay))

        lines: list[str] = []
        success = sum(1 for r in results if r.get("success"))
        fail = len(results) - success
        lines.append(f"Tổng kết: {success} thành công, {fail} thất bại / {len(results)} tổng cộng\n")
        for r in results:
            idx = r.get("index", "?")
            if r.get("success"):
                lines.append(f"  [{int(idx)+1}] ✓ {r['output_path']}")
            else:
                lines.append(f"  [{int(idx)+1}] ✗ {r.get('error', 'Lỗi không xác định')}")

        return "\n".join(lines), results

    run_btn.click(
        fn=_run_batch,
        inputs=[batch_file, output_dir_input, delay_input, model_input, api_key_input],
        outputs=[batch_status, batch_json_output],
    )


# ---------------------------------------------------------------------------
# UI builder
# ---------------------------------------------------------------------------

def build_ui(api_key: str = "") -> gr.Blocks:
    """
    Construct and return the Gradio Blocks application.

    Parameters
    ----------
    api_key:
        Optional default API key pre-filled in the UI. If empty, the UI will
        read from the GEMINI_API_KEY environment variable at runtime.

    Returns
    -------
    gr.Blocks
        A configured (but not launched) Gradio application.
    """
    api_key_state = gr.State(value=api_key)

    with gr.Blocks(
        title="WiFi Marketing Image Generator",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown(
            "# WiFi Marketing Image Generator\n"
            "Tạo hình ảnh marketing chuyên nghiệp cho mạng xã hội bằng Google Gemini AI.\n"
            "Hỗ trợ đầy đủ tiếng Việt với dấu thanh và dấu phụ. Kích thước chuẩn 1080x1920px."
        )

        with gr.Tabs():
            with gr.Tab("Prompt tự do"):
                _tab_free_prompt(api_key_state)

            with gr.Tab("Template"):
                _tab_template()

            with gr.Tab("Batch"):
                _tab_batch()

        gr.Markdown(
            "---\n"
            "*wfm-imggen — WiFi Marketing Content Toolkit | "
            "Powered by Google Gemini*"
        )

    return app


# ---------------------------------------------------------------------------
# Direct launch (python -m imggen.ui)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    _api_key = os.environ.get("GEMINI_API_KEY", "")
    _app = build_ui(api_key=_api_key)
    _app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=True,
    )
