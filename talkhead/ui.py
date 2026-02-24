"""
ui.py — Gradio web interface for wfm-talkhead.

Single tab with:
- Portrait image upload
- Audio file upload
- Still mode checkbox
- Face enhancer dropdown
- Preprocess mode dropdown
- Generate button
- Video output with download link

Port default: 7863. show_api=True.
All labels and messages are in Vietnamese.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import gradio as gr

_DEFAULT_SERVER = os.environ.get("SADTALKER_URL", "http://localhost:8299")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _temp_mp4() -> str:
    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    return path


def _resolve_server(override: str) -> str:
    return (override or "").strip() or _DEFAULT_SERVER


# ---------------------------------------------------------------------------
# Main generate function
# ---------------------------------------------------------------------------


def _generate(
    image_path: str | None,
    audio_path: str | None,
    still: bool,
    enhancer: str,
    preprocess: str,
    srv: str,
    sadtalker_dir_input: str,
) -> tuple[str | None, str]:
    from talkhead.core import generate_talking_head

    if not image_path:
        return None, "Lỗi: Chưa tải lên ảnh chân dung."
    if not audio_path:
        return None, "Lỗi: Chưa tải lên file âm thanh."

    enh_val = "" if enhancer == "Không dùng" else enhancer
    sad_dir = sadtalker_dir_input.strip() or None
    out_path = _temp_mp4()

    result = generate_talking_head(
        image_path=image_path,
        audio_path=audio_path,
        output_path=out_path,
        still=still,
        preprocess=preprocess,
        enhancer=enh_val,
        sadtalker_dir=sad_dir,
        server_url=_resolve_server(srv),
    )

    if result["success"]:
        method = result.get("method", "?")
        return result["output_path"], f"Thành công! Phương thức: {method}."
    return None, f"Lỗi: {result.get('error', 'Không xác định')}"


# ---------------------------------------------------------------------------
# UI builder
# ---------------------------------------------------------------------------


def build_ui(server_url: str = _DEFAULT_SERVER) -> gr.Blocks:
    """
    Construct and return the Gradio Blocks application for wfm-talkhead.

    Parameters
    ----------
    server_url:
        Default SadTalker API server URL.

    Returns
    -------
    gr.Blocks
        A configured (but not launched) Gradio application.
    """
    with gr.Blocks(
        title="WiFi Marketing Talking Head",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown(
            "# WiFi Marketing Talking Head\n"
            "Tạo video đầu người nói từ ảnh chân dung và file âm thanh bằng SadTalker. "
            "Hỗ trợ chế độ API và chạy trực tiếp."
        )

        with gr.Row():
            # --- Left column: inputs ---
            with gr.Column(scale=2):
                gr.Markdown("### Đầu vào")

                image_input = gr.Image(
                    label="Ảnh chân dung (JPG / PNG)",
                    type="filepath",
                    sources=["upload"],
                )

                audio_input = gr.Audio(
                    label="File âm thanh (WAV / MP3)",
                    type="filepath",
                    sources=["upload"],
                )

                with gr.Row():
                    still_checkbox = gr.Checkbox(
                        label="Đứng yên (giảm chuyển động đầu)",
                        value=True,
                    )

                with gr.Row():
                    enhancer_dropdown = gr.Dropdown(
                        label="Bộ tăng cường khuôn mặt",
                        choices=["gfpgan", "RestoreFormer", "Không dùng"],
                        value="gfpgan",
                    )
                    preprocess_dropdown = gr.Dropdown(
                        label="Chế độ tiền xử lý",
                        choices=["full", "crop", "resize"],
                        value="full",
                    )

                with gr.Accordion("Cấu hình nâng cao", open=False):
                    server_input = gr.Textbox(
                        label="URL máy chủ SadTalker API",
                        value=server_url,
                        placeholder="http://localhost:8299",
                    )
                    sadtalker_dir_input = gr.Textbox(
                        label="Thư mục SadTalker (nếu không dùng API)",
                        placeholder="/path/to/SadTalker",
                        value="",
                    )

                generate_btn = gr.Button("Tạo video talking-head", variant="primary", size="lg")

            # --- Right column: outputs ---
            with gr.Column(scale=3):
                gr.Markdown("### Kết quả")

                video_output = gr.Video(
                    label="Video đầu ra",
                    format="mp4",
                )
                status_text = gr.Textbox(
                    label="Trạng thái",
                    interactive=False,
                    lines=4,
                )

        generate_btn.click(
            fn=_generate,
            inputs=[
                image_input,
                audio_input,
                still_checkbox,
                enhancer_dropdown,
                preprocess_dropdown,
                server_input,
                sadtalker_dir_input,
            ],
            outputs=[video_output, status_text],
        )

        gr.Markdown(
            "---\n"
            "*wfm-talkhead — WiFi Marketing Content Toolkit | Powered by SadTalker*"
        )

    return app


# ---------------------------------------------------------------------------
# Direct launch (python -m talkhead.ui)
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    _app = build_ui(server_url=_DEFAULT_SERVER)
    _app.launch(
        server_name="0.0.0.0",
        server_port=7863,
        show_api=True,
    )
