"""
ui.py — Gradio web interface for wfm-vidmake.

Two tabs:
1. Pipeline: Full HTML → Screenshot → Ken Burns Animation → Video workflow
2. Slideshow: Original simple slideshow assembler

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
# Constants
# ---------------------------------------------------------------------------

MAX_SLIDES = 10

_DEFAULT_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 1080px; height: 1920px;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    font-family: 'Segoe UI', sans-serif;
    color: #fff; padding: 80px;
  }
  h1 { font-size: 72px; text-align: center; margin-bottom: 40px;
       background: linear-gradient(90deg, #6C63FF, #FF6584);
       -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  p { font-size: 42px; text-align: center; line-height: 1.5; opacity: 0.85; }
</style>
</head>
<body>
  <h1>Slide Title Here</h1>
  <p>Your content goes here.<br>Edit this HTML to create your slide.</p>
</body>
</html>"""

_EFFECT_LABELS = {
    "zoom_in": "Zoom In (Ken Burns)",
    "zoom_out": "Zoom Out",
    "pan_right": "Pan Left \u2192 Right",
    "pan_down": "Pan Top \u2192 Bottom",
    "zoom_topleft": "Zoom v\u00e0o g\u00f3c tr\u00e1i tr\u00ean",
}

_EFFECT_CHOICES = list(_EFFECT_LABELS.keys())

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _temp_mp4() -> str:
    fd, path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    return path


def _temp_png() -> str:
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    return path


# ---------------------------------------------------------------------------
# Pipeline tab: state management
# ---------------------------------------------------------------------------
# State is a dict: {"slides": [{"html": str, "png_path": str|None}, ...], "current": int}


def _init_state() -> dict:
    return {
        "slides": [{"html": _DEFAULT_HTML, "png_path": None}],
        "current": 0,
    }


def _add_slide(state: dict) -> tuple[dict, str, str, gr.update, str]:
    """Add a new slide and switch to it."""
    if len(state["slides"]) >= MAX_SLIDES:
        choices = [f"Slide {i+1}" for i in range(len(state["slides"]))]
        return (
            state,
            state["slides"][state["current"]]["html"],
            _render_preview(state["slides"][state["current"]]["html"]),
            gr.update(choices=choices, value=f"Slide {state['current']+1}"),
            f"Tối đa {MAX_SLIDES} slides.",
        )
    state["slides"].append({"html": _DEFAULT_HTML, "png_path": None})
    state["current"] = len(state["slides"]) - 1
    choices = [f"Slide {i+1}" for i in range(len(state["slides"]))]
    return (
        state,
        _DEFAULT_HTML,
        _render_preview(_DEFAULT_HTML),
        gr.update(choices=choices, value=f"Slide {state['current']+1}"),
        f"Slide {state['current']+1} mới.",
    )


def _remove_slide(state: dict) -> tuple[dict, str, str, gr.update, str]:
    """Remove current slide."""
    if len(state["slides"]) <= 1:
        choices = [f"Slide {i+1}" for i in range(len(state["slides"]))]
        return (
            state,
            state["slides"][0]["html"],
            _render_preview(state["slides"][0]["html"]),
            gr.update(choices=choices, value="Slide 1"),
            "Cần ít nhất 1 slide.",
        )
    removed_idx = state["current"]
    state["slides"].pop(removed_idx)
    state["current"] = min(removed_idx, len(state["slides"]) - 1)
    cur = state["current"]
    choices = [f"Slide {i+1}" for i in range(len(state["slides"]))]
    return (
        state,
        state["slides"][cur]["html"],
        _render_preview(state["slides"][cur]["html"]),
        gr.update(choices=choices, value=f"Slide {cur+1}"),
        f"Xoá slide {removed_idx+1}.",
    )


def _switch_slide(state: dict, slide_label: str) -> tuple[dict, str, str]:
    """Switch to a different slide by label."""
    try:
        idx = int(slide_label.replace("Slide ", "")) - 1
    except (ValueError, AttributeError):
        idx = 0
    idx = max(0, min(idx, len(state["slides"]) - 1))
    state["current"] = idx
    html = state["slides"][idx]["html"]
    return state, html, _render_preview(html)


def _save_html(state: dict, html_code: str) -> tuple[dict, str]:
    """Save the current editor content to state."""
    cur = state["current"]
    state["slides"][cur]["html"] = html_code
    state["slides"][cur]["png_path"] = None  # invalidate screenshot
    return state, _render_preview(html_code)


def _render_preview(html: str) -> str:
    """Wrap HTML in a scaled iframe for preview."""
    # Encode HTML for srcdoc
    escaped = html.replace("&", "&amp;").replace('"', "&quot;")
    return (
        '<div style="width:100%;aspect-ratio:9/16;max-height:700px;overflow:hidden;'
        'border:1px solid #444;border-radius:8px;background:#000;">'
        f'<iframe srcdoc="{escaped}" '
        'style="width:1080px;height:1920px;border:none;'
        'transform:scale(0.28);transform-origin:top left;" '
        'sandbox="allow-same-origin"></iframe>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# Pipeline tab: screenshot all slides
# ---------------------------------------------------------------------------


def _screenshot_all(state: dict, size: str) -> tuple[dict, list[str], str]:
    """Use Playwright to screenshot all slides."""
    from poster.core import screenshot_sync

    w, h = 1080, 1920
    try:
        parts = size.lower().split("x")
        w, h = int(parts[0]), int(parts[1])
    except Exception:
        pass

    gallery_images: list[str] = []
    errors: list[str] = []

    for i, slide in enumerate(state["slides"]):
        png_path = _temp_png()
        try:
            screenshot_sync(slide["html"], png_path, width=w, height=h)
            state["slides"][i]["png_path"] = png_path
            gallery_images.append(png_path)
        except Exception as exc:
            errors.append(f"Slide {i+1}: {exc}")

    if errors:
        status = f"Screenshot xong {len(gallery_images)}/{len(state['slides'])} slides.\n" + "\n".join(errors)
    else:
        status = f"Screenshot xong {len(gallery_images)} slides."

    return state, gallery_images, status


# ---------------------------------------------------------------------------
# Pipeline tab: generate animated video
# ---------------------------------------------------------------------------


def _generate_video(
    state: dict,
    *effect_and_config,
) -> tuple[str | None, str]:
    """Generate the final animated video from screenshots."""
    from vidmake.core import create_animated_slideshow, ANIMATION_EFFECTS

    # Unpack: first MAX_SLIDES are effects, then duration, audio, size, fps
    effect_values = list(effect_and_config[:MAX_SLIDES])
    duration = effect_and_config[MAX_SLIDES]
    audio_file = effect_and_config[MAX_SLIDES + 1]
    size = effect_and_config[MAX_SLIDES + 2]
    fps = int(effect_and_config[MAX_SLIDES + 3])

    # Collect screenshot paths
    img_paths: list[str] = []
    for i, slide in enumerate(state["slides"]):
        if slide.get("png_path") and Path(slide["png_path"]).exists():
            img_paths.append(slide["png_path"])
        else:
            return None, f"Slide {i+1} chưa được screenshot. Bấm 'Screenshot tất cả' trước."

    # Collect effects per slide
    effects: list[str] = []
    for i in range(len(img_paths)):
        if i < len(effect_values) and effect_values[i] in ANIMATION_EFFECTS:
            effects.append(effect_values[i])
        else:
            effects.append(ANIMATION_EFFECTS[i % len(ANIMATION_EFFECTS)])

    # Audio path
    aud_path: str | None = None
    if audio_file:
        aud_path = audio_file if isinstance(audio_file, str) else str(audio_file)

    out_path = _temp_mp4()
    result = create_animated_slideshow(
        images=img_paths,
        output_path=out_path,
        effects=effects,
        duration_per_slide=float(duration),
        audio_path=aud_path,
        size=size,
        fps=fps,
    )

    if result["success"]:
        efx = result.get("effects", effects)
        status = (
            f"Video {result['slide_count']} slides, "
            f"{result['duration_seconds']:.1f}s, "
            f"encoder: {result.get('encoder', '?')}.\n"
            f"Effects: {', '.join(efx)}"
        )
        return result["output_path"], status
    return None, f"Lỗi: {result.get('error', 'Không xác định')}"


# ---------------------------------------------------------------------------
# Slideshow tab (original)
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
    with gr.Blocks(
        title="Video Pipeline — HTML to TikTok",
    ) as app:
        gr.Markdown(
            "# Video Pipeline\n"
            "HTML \u2192 Screenshot \u2192 Ken Burns Animation \u2192 Video TikTok"
        )

        with gr.Tabs():
            # ==============================================================
            # TAB 1: PIPELINE
            # ==============================================================
            with gr.Tab("Pipeline"):
                pipeline_state = gr.State(_init_state())

                # --- Step 1: HTML Editor ---
                gr.Markdown("## B\u01b0\u1edbc 1: T\u1ea1o Slides HTML")

                with gr.Row():
                    slide_selector = gr.Dropdown(
                        label="Ch\u1ecdn slide",
                        choices=["Slide 1"],
                        value="Slide 1",
                        scale=2,
                    )
                    add_btn = gr.Button("+ Th\u00eam slide", size="sm", scale=1)
                    remove_btn = gr.Button("- X\u00f3a slide", size="sm", variant="stop", scale=1)

                with gr.Row():
                    with gr.Column(scale=3):
                        html_editor = gr.Code(
                            label="HTML Code",
                            language="html",
                            value=_DEFAULT_HTML,
                            lines=25,
                        )
                    with gr.Column(scale=2):
                        gr.Markdown("### Preview")
                        html_preview = gr.HTML(
                            value=_render_preview(_DEFAULT_HTML),
                            elem_classes=["slide-preview"],
                        )

                pipeline_status = gr.Textbox(
                    label="Tr\u1ea1ng th\u00e1i",
                    interactive=False,
                    lines=2,
                )

                # --- Step 2: Screenshot ---
                gr.Markdown("---")
                gr.Markdown("## B\u01b0\u1edbc 2: Screenshot")

                with gr.Row():
                    screenshot_size = gr.Dropdown(
                        label="K\u00edch th\u01b0\u1edbc",
                        choices=["1080x1920", "1920x1080", "1080x1080"],
                        value="1080x1920",
                        scale=1,
                    )
                    screenshot_btn = gr.Button(
                        "Screenshot t\u1ea5t c\u1ea3 slides",
                        variant="primary",
                        scale=2,
                    )

                screenshot_gallery = gr.Gallery(
                    label="Screenshots",
                    columns=5,
                    height=300,
                )

                # --- Step 3: Animation config ---
                gr.Markdown("---")
                gr.Markdown("## B\u01b0\u1edbc 3: C\u1ea5u h\u00ecnh Animation & T\u1ea1o Video")

                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("### Hi\u1ec7u \u1ee9ng cho t\u1eebng slide")
                        effect_dropdowns: list[gr.Dropdown] = []
                        for i in range(MAX_SLIDES):
                            dd = gr.Dropdown(
                                label=f"Slide {i+1}",
                                choices=_EFFECT_CHOICES,
                                value=_EFFECT_CHOICES[i % len(_EFFECT_CHOICES)],
                                visible=(i == 0),
                            )
                            effect_dropdowns.append(dd)

                    with gr.Column(scale=1):
                        gr.Markdown("### C\u1ea5u h\u00ecnh chung")
                        anim_duration = gr.Number(
                            label="Th\u1eddi gian m\u1ed7i slide (gi\u00e2y)",
                            value=5.0,
                            minimum=2.0,
                            maximum=15.0,
                            precision=1,
                        )
                        anim_fps = gr.Number(
                            label="FPS",
                            value=30,
                            minimum=24,
                            maximum=60,
                            precision=0,
                        )
                        anim_size = gr.Dropdown(
                            label="K\u00edch th\u01b0\u1edbc video",
                            choices=["1080x1920", "1920x1080", "1080x1080"],
                            value="1080x1920",
                        )
                        anim_audio = gr.Audio(
                            label="Nh\u1ea1c n\u1ec1n (tu\u1ef3 ch\u1ecdn)",
                            type="filepath",
                            sources=["upload"],
                        )

                generate_btn = gr.Button(
                    "T\u1ea1o Video",
                    variant="primary",
                    size="lg",
                )

                with gr.Row():
                    pipeline_video = gr.Video(
                        label="Video \u0111\u1ea7u ra",
                        format="mp4",
                    )
                    pipeline_video_status = gr.Textbox(
                        label="K\u1ebft qu\u1ea3",
                        interactive=False,
                        lines=4,
                    )

                # --- Event wiring: slide management ---
                add_btn.click(
                    fn=_add_slide,
                    inputs=[pipeline_state],
                    outputs=[pipeline_state, html_editor, html_preview, slide_selector, pipeline_status],
                ).then(
                    fn=lambda state: [gr.update(visible=(i < len(state["slides"]))) for i in range(MAX_SLIDES)],
                    inputs=[pipeline_state],
                    outputs=effect_dropdowns,
                )

                remove_btn.click(
                    fn=_remove_slide,
                    inputs=[pipeline_state],
                    outputs=[pipeline_state, html_editor, html_preview, slide_selector, pipeline_status],
                ).then(
                    fn=lambda state: [gr.update(visible=(i < len(state["slides"]))) for i in range(MAX_SLIDES)],
                    inputs=[pipeline_state],
                    outputs=effect_dropdowns,
                )

                slide_selector.change(
                    fn=_switch_slide,
                    inputs=[pipeline_state, slide_selector],
                    outputs=[pipeline_state, html_editor, html_preview],
                )

                html_editor.change(
                    fn=_save_html,
                    inputs=[pipeline_state, html_editor],
                    outputs=[pipeline_state, html_preview],
                )

                # --- Event wiring: screenshot ---
                screenshot_btn.click(
                    fn=_screenshot_all,
                    inputs=[pipeline_state, screenshot_size],
                    outputs=[pipeline_state, screenshot_gallery, pipeline_status],
                )

                # --- Event wiring: generate video ---
                generate_btn.click(
                    fn=_generate_video,
                    inputs=[pipeline_state] + effect_dropdowns + [anim_duration, anim_audio, anim_size, anim_fps],
                    outputs=[pipeline_video, pipeline_video_status],
                )

            # ==============================================================
            # TAB 2: SLIDESHOW (original)
            # ==============================================================
            with gr.Tab("Slideshow"):
                gr.Markdown(
                    "### Gh\u00e9p \u1ea3nh th\u00e0nh video slideshow\n"
                    "T\u1ea3i l\u00ean \u1ea3nh \u2192 c\u1ea5u h\u00ecnh \u2192 xu\u1ea5t video."
                )

                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("### \u1ea2nh \u0111\u1ea7u v\u00e0o")
                        image_upload = gr.File(
                            label="T\u1ea3i l\u00ean \u1ea3nh (ch\u1ecdn nhi\u1ec1u file)",
                            file_types=["image"],
                            file_count="multiple",
                        )

                        gr.Markdown("### C\u1ea5u h\u00ecnh video")
                        with gr.Row():
                            size_dropdown = gr.Dropdown(
                                label="K\u00edch th\u01b0\u1edbc video",
                                choices=["1080x1920", "1920x1080", "1080x1080", "720x1280", "1280x720"],
                                value="1080x1920",
                            )
                            transition_dropdown = gr.Dropdown(
                                label="Hi\u1ec7u \u1ee9ng chuy\u1ec3n c\u1ea3nh",
                                choices=["fade", "none"],
                                value="fade",
                            )

                        with gr.Row():
                            duration_input = gr.Number(
                                label="Th\u1eddi gian m\u1ed7i \u1ea3nh (gi\u00e2y, 0 = t\u1ef1 \u0111\u1ed9ng)",
                                value=0,
                                minimum=0,
                                precision=1,
                            )
                            transition_dur_input = gr.Slider(
                                label="Th\u1eddi gian chuy\u1ec3n c\u1ea3nh (gi\u00e2y)",
                                minimum=0.1,
                                maximum=2.0,
                                step=0.1,
                                value=0.5,
                            )

                        gr.Markdown("### \u00c2m thanh (tu\u1ef3 ch\u1ecdn)")
                        audio_upload = gr.Audio(
                            label="File \u00e2m thanh (WAV / MP3)",
                            type="filepath",
                            sources=["upload"],
                        )

                        gr.Markdown("### Video PIP (tu\u1ef3 ch\u1ecdn)")
                        pip_upload = gr.File(
                            label="Video PIP (MP4)",
                            file_types=["video"],
                            file_count="single",
                        )
                        with gr.Row():
                            pip_position_dropdown = gr.Dropdown(
                                label="V\u1ecb tr\u00ed PIP",
                                choices=["bottom-right", "bottom-left", "top-right", "top-left", "center"],
                                value="bottom-right",
                            )
                            pip_size_slider = gr.Slider(
                                label="K\u00edch th\u01b0\u1edbc PIP (% chi\u1ec1u r\u1ed9ng)",
                                minimum=5,
                                maximum=80,
                                step=5,
                                value=30,
                            )

                        assemble_btn = gr.Button("T\u1ea1o video slideshow", variant="primary", size="lg")

                    with gr.Column(scale=3):
                        gr.Markdown("### K\u1ebft qu\u1ea3")
                        video_output = gr.Video(label="Video \u0111\u1ea7u ra", format="mp4")
                        status_text = gr.Textbox(label="Tr\u1ea1ng th\u00e1i", interactive=False, lines=4)

                assemble_btn.click(
                    fn=_assemble,
                    inputs=[
                        image_upload, audio_upload, duration_input,
                        transition_dropdown, transition_dur_input, size_dropdown,
                        pip_upload, pip_position_dropdown, pip_size_slider,
                    ],
                    outputs=[video_output, status_text],
                )

        gr.Markdown(
            "---\n"
            "*wfm-vidmake \u2014 WiFi Marketing Content Toolkit | Powered by FFmpeg + Playwright*"
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
        theme=gr.themes.Soft(),
        css=".slide-preview iframe { pointer-events: none; }",
    )
