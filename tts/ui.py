"""
ui.py — Gradio web interface for wfm-tts.

Tabs
----
1. Tạo giọng nói  — Textarea, voice dropdown, speed slider, generate button, audio output.
2. Clone giọng     — Textarea, upload reference audio, generate, audio output.

Port default: 7862. show_api=True.
All labels and messages are in Vietnamese.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import gradio as gr

_DEFAULT_SERVER = os.environ.get("VIETTTS_URL", "http://localhost:8298")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _temp_wav() -> str:
    """Create a temporary WAV file path."""
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    return path


def _resolve_server(override: str) -> str:
    return (override or "").strip() or _DEFAULT_SERVER


# ---------------------------------------------------------------------------
# Tab 1: Standard TTS
# ---------------------------------------------------------------------------


def _tab_tts(default_server: str) -> None:
    gr.Markdown("## Tạo giọng nói từ văn bản")
    gr.Markdown(
        "Nhập văn bản tiếng Việt, chọn giọng đọc và tốc độ, "
        "sau đó nhấn **Tạo âm thanh** để tổng hợp."
    )

    with gr.Row():
        with gr.Column(scale=3):
            text_input = gr.Textbox(
                label="Văn bản cần đọc",
                placeholder="Nhập nội dung tiếng Việt cần chuyển thành giọng nói...",
                lines=8,
            )

            with gr.Row():
                voice_dropdown = gr.Dropdown(
                    label="Giọng đọc",
                    choices=["cdteam"],
                    value="cdteam",
                    allow_custom_value=True,
                )
                refresh_btn = gr.Button("Tải lại danh sách giọng", size="sm")

            speed_slider = gr.Slider(
                label="Tốc độ đọc",
                minimum=0.5,
                maximum=2.0,
                step=0.1,
                value=1.0,
            )

            server_input = gr.Textbox(
                label="URL máy chủ VietTTS",
                value=default_server,
                placeholder="http://localhost:8298",
            )

            generate_btn = gr.Button("Tạo âm thanh", variant="primary", size="lg")

        with gr.Column(scale=2):
            audio_output = gr.Audio(
                label="Âm thanh đầu ra",
                type="filepath",
            )
            status_text = gr.Textbox(
                label="Trạng thái",
                interactive=False,
                lines=4,
            )

    def _refresh_voices(srv: str) -> gr.update:
        from tts.core import list_voices
        voices = list_voices(server_url=_resolve_server(srv))
        if voices:
            return gr.update(choices=voices, value=voices[0])
        return gr.update(choices=["cdteam"], value="cdteam")

    def _generate(text: str, voice: str, speed: float, srv: str) -> tuple[str | None, str]:
        from tts.core import text_to_speech

        if not text or not text.strip():
            return None, "Lỗi: Văn bản không được để trống."

        out_path = _temp_wav()
        result = text_to_speech(
            text=text.strip(),
            output_path=out_path,
            server_url=_resolve_server(srv),
            voice=voice or "cdteam",
            speed=float(speed),
        )
        if result["success"]:
            dur = result.get("duration_seconds", 0.0)
            return result["output_path"], f"Thành công! Thời lượng: {dur:.2f} giây."
        return None, f"Lỗi: {result.get('error', 'Không xác định')}"

    refresh_btn.click(
        fn=_refresh_voices,
        inputs=[server_input],
        outputs=[voice_dropdown],
    )

    generate_btn.click(
        fn=_generate,
        inputs=[text_input, voice_dropdown, speed_slider, server_input],
        outputs=[audio_output, status_text],
    )


# ---------------------------------------------------------------------------
# Tab 2: Voice Cloning
# ---------------------------------------------------------------------------


def _tab_clone(default_server: str) -> None:
    gr.Markdown("## Clone giọng nói")
    gr.Markdown(
        "Tải lên file âm thanh tham chiếu (WAV hoặc MP3) để nhân bản giọng nói, "
        "nhập văn bản cần đọc rồi nhấn **Clone & Tạo âm thanh**."
    )

    with gr.Row():
        with gr.Column(scale=3):
            text_input = gr.Textbox(
                label="Văn bản cần đọc",
                placeholder="Nhập nội dung tiếng Việt...",
                lines=8,
            )

            reference_audio = gr.Audio(
                label="File âm thanh tham chiếu (WAV / MP3)",
                type="filepath",
                sources=["upload"],
            )

            server_input = gr.Textbox(
                label="URL máy chủ VietTTS",
                value=default_server,
                placeholder="http://localhost:8298",
            )

            generate_btn = gr.Button("Clone & Tạo âm thanh", variant="primary", size="lg")

        with gr.Column(scale=2):
            audio_output = gr.Audio(
                label="Âm thanh đầu ra (giọng đã clone)",
                type="filepath",
            )
            status_text = gr.Textbox(
                label="Trạng thái",
                interactive=False,
                lines=4,
            )

    def _clone(text: str, ref_path: str | None, srv: str) -> tuple[str | None, str]:
        from tts.core import clone_and_speak

        if not text or not text.strip():
            return None, "Lỗi: Văn bản không được để trống."
        if not ref_path:
            return None, "Lỗi: Chưa tải lên file âm thanh tham chiếu."

        out_path = _temp_wav()
        result = clone_and_speak(
            text=text.strip(),
            output_path=out_path,
            reference_audio=ref_path,
            server_url=_resolve_server(srv),
        )
        if result["success"]:
            dur = result.get("duration_seconds", 0.0)
            return result["output_path"], f"Thành công! Thời lượng: {dur:.2f} giây."
        return None, f"Lỗi: {result.get('error', 'Không xác định')}"

    generate_btn.click(
        fn=_clone,
        inputs=[text_input, reference_audio, server_input],
        outputs=[audio_output, status_text],
    )


# ---------------------------------------------------------------------------
# UI builder
# ---------------------------------------------------------------------------


def build_ui(server_url: str = _DEFAULT_SERVER) -> gr.Blocks:
    """
    Construct and return the Gradio Blocks application for wfm-tts.

    Parameters
    ----------
    server_url:
        Default VietTTS server URL pre-filled in the UI.

    Returns
    -------
    gr.Blocks
        A configured (but not launched) Gradio application.
    """
    with gr.Blocks(
        title="WiFi Marketing TTS",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown(
            "# WiFi Marketing TTS\n"
            "Chuyển văn bản thành giọng nói bằng VietTTS. "
            "Hỗ trợ tổng hợp tiêu chuẩn và nhân bản giọng nói."
        )

        with gr.Tabs():
            with gr.Tab("Tạo giọng nói"):
                _tab_tts(default_server=server_url)

            with gr.Tab("Clone giọng"):
                _tab_clone(default_server=server_url)

        gr.Markdown(
            "---\n"
            "*wfm-tts — WiFi Marketing Content Toolkit | Powered by VietTTS*"
        )

    return app


# ---------------------------------------------------------------------------
# Direct launch (python -m tts.ui)
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    _app = build_ui(server_url=_DEFAULT_SERVER)
    _app.launch(
        server_name="0.0.0.0",
        server_port=7862,
        show_api=True,
    )
