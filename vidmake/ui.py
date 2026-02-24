"""
ui.py — Gradio web interface for wfm-vidmake.

Single tab with:
- Multiple image uploads (File component)
- Optional audio upload
- Transition style dropdown
- Duration-per-slide number input
- Optional PIP video upload + position dropdown + size slider
- Output size dropdown
- Assemble button
- Video output

Port default: 7864. show_api=True.
All labels and messages are in Vietnamese.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import gradio as gr


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _temp_mp4() -> str:
    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    return path


# ---------------------------------------------------------------------------
# Generate function
# ---------------------------------------------------------------------------


def _assemble(
    image_files: list[Any] | None,
    audio_file: str | None,
    duration_per_slide: float | None,
    transition: str,
    transition_duration: float,
    size: str,
    pip_file: str | None,
    pip_position: str,
    pip_size: int,
) -> tuple[str | None, str]:
    from vidmake.core import create_slideshow

    if not image_files:
        return None, "Lỗi: Chưa tải lên ảnh nào."

    # Gradio File component returns list of file paths (strings) in multi-file mode
    img_paths: list[str] = []
    for f in image_files:
        if isinstance(f, str):
            img_paths.append(f)
        elif hasattr(f, "name"):
            img_paths.append(f.name)
        else:
            img_paths.append(str(f))

    if not img_paths:
        return None, "Lỗi: Không đọc được đường dẫn ảnh."

    aud_path: str | None = None
    if audio_file:
        aud_path = audio_file if isinstance(audio_file, str) else str(audio_file)

    pip_path: str | None = None
    if pip_file:
        pip_path = pip_file if isinstance(pip_file, str) else str(pip_file)

    dur: float | None = float(duration_per_slide) if duration_per_slide else None
    out_path = _temp_mp4()

    result = create_slideshow(
        images=img_paths,
        output_path=out_path,
        audio_path=aud_path,
        duration_per_slide=dur,
        transition=transition,
        transition_duration=float(transition_duration),
        size=size,
        pip_video=pip_path,
        pip_position=pip_position,
        pip_size=int(pip_size),
    )

    if result["success"]:
        slide_count = result.get("slide_count", len(img_paths))
        video_dur = result.get("duration_seconds", 0.0)
        encoder = result.get("encoder", "?")
        status = (
            f"Thành công! {slide_count} ảnh, thời lượng: {video_dur:.1f}s, "
            f"encoder: {encoder}."
        )
        return result["output_path"], status
    return None, f"Lỗi: {result.get('error', 'Không xác định')}"


# ---------------------------------------------------------------------------
# UI builder
# ---------------------------------------------------------------------------


def build_ui() -> gr.Blocks:
    """
    Construct and return the Gradio Blocks application for wfm-vidmake.

    Returns
    -------
    gr.Blocks
        A configured (but not launched) Gradio application.
    """
    with gr.Blocks(
        title="WiFi Marketing Video Maker",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown(
            "# WiFi Marketing Video Maker\n"
            "Ghép nhiều ảnh thành video slideshow với hiệu ứng chuyển cảnh, "
            "nhạc nền và video nhỏ góc màn hình (PIP)."
        )

        with gr.Row():
            # --- Left column: inputs ---
            with gr.Column(scale=2):
                gr.Markdown("### Ảnh đầu vào")
                image_upload = gr.File(
                    label="Tải lên ảnh (chọn nhiều file)",
                    file_types=["image"],
                    file_count="multiple",
                )

                gr.Markdown("### Cấu hình video")
                with gr.Row():
                    size_dropdown = gr.Dropdown(
                        label="Kích thước video",
                        choices=["1080x1920", "1920x1080", "1080x1080", "720x1280", "1280x720"],
                        value="1080x1920",
                    )
                    transition_dropdown = gr.Dropdown(
                        label="Hiệu ứng chuyển cảnh",
                        choices=["fade", "none"],
                        value="fade",
                    )

                with gr.Row():
                    duration_input = gr.Number(
                        label="Thời gian mỗi ảnh (giây, 0 = tự động)",
                        value=0,
                        minimum=0,
                        precision=1,
                    )
                    transition_dur_input = gr.Slider(
                        label="Thời gian chuyển cảnh (giây)",
                        minimum=0.1,
                        maximum=2.0,
                        step=0.1,
                        value=0.5,
                    )

                gr.Markdown("### Âm thanh (tuỳ chọn)")
                audio_upload = gr.Audio(
                    label="File âm thanh (WAV / MP3)",
                    type="filepath",
                    sources=["upload"],
                )

                gr.Markdown("### Video PIP — picture-in-picture (tuỳ chọn)")
                pip_upload = gr.File(
                    label="Video PIP (MP4)",
                    file_types=["video"],
                    file_count="single",
                )
                with gr.Row():
                    pip_position_dropdown = gr.Dropdown(
                        label="Vị trí PIP",
                        choices=["bottom-right", "bottom-left", "top-right", "top-left", "center"],
                        value="bottom-right",
                    )
                    pip_size_slider = gr.Slider(
                        label="Kích thước PIP (% chiều rộng)",
                        minimum=5,
                        maximum=80,
                        step=5,
                        value=30,
                    )

                assemble_btn = gr.Button("Tạo video slideshow", variant="primary", size="lg")

            # --- Right column: output ---
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

        assemble_btn.click(
            fn=_assemble,
            inputs=[
                image_upload,
                audio_upload,
                duration_input,
                transition_dropdown,
                transition_dur_input,
                size_dropdown,
                pip_upload,
                pip_position_dropdown,
                pip_size_slider,
            ],
            outputs=[video_output, status_text],
        )

        gr.Markdown(
            "---\n"
            "*wfm-vidmake — WiFi Marketing Content Toolkit | Powered by FFmpeg*"
        )

    return app


# ---------------------------------------------------------------------------
# Direct launch (python -m vidmake.ui)
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    _app = build_ui()
    _app.launch(
        server_name="0.0.0.0",
        server_port=7864,
        show_api=True,
    )
