"""
core.py — Pure business logic for wfm-vidmake.

All video assembly is performed through FFmpeg subprocess calls.
The encoder is auto-detected via shared.platform.detect_ffmpeg_encoder().

Slideshow pipeline
------------------
1. Scale each image to the target *size* (pad to fill, letterbox if needed).
2. Apply a fade-in / fade-out transition at each slide boundary when
   transition="fade".  "none" skips transitions entirely.
3. Concatenate all slides into a single video stream.
4. If *audio_path* is given, mux the audio and trim the video to audio
   length (or pad silence when the video is shorter).
5. If *pip_video* is given, overlay it at *pip_position* scaled to
   *pip_size* percent of the frame width.

Error messages are in Vietnamese.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

# Supported transitions
_TRANSITIONS = {"fade", "none"}

# PIP position anchor map: (x_expr, y_expr) in FFmpeg overlay filter syntax
_PIP_POSITIONS: dict[str, tuple[str, str]] = {
    "top-left":     ("10",                 "10"),
    "top-right":    ("main_w-overlay_w-10", "10"),
    "bottom-left":  ("10",                 "main_h-overlay_h-10"),
    "bottom-right": ("main_w-overlay_w-10", "main_h-overlay_h-10"),
    "center":       ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_slideshow(
    images: list[str],
    output_path: str,
    audio_path: str | None = None,
    duration_per_slide: float | None = None,
    transition: str = "fade",
    transition_duration: float = 0.5,
    size: str = "1080x1920",
    pip_video: str | None = None,
    pip_position: str = "bottom-right",
    pip_size: int = 30,
) -> dict[str, Any]:
    """
    Create a slideshow video from a list of images.

    Parameters
    ----------
    images:
        Ordered list of image file paths (JPG / PNG).
    output_path:
        Destination path for the output MP4 file.
    audio_path:
        Optional path to an audio file (WAV / MP3).  When provided, the
        slideshow is trimmed / extended to match the audio duration unless
        *duration_per_slide* is set explicitly.
    duration_per_slide:
        Duration in seconds each image is displayed.  When None and
        *audio_path* is given, timing is divided equally across slides.
        When None and no audio is provided, defaults to 3.0 seconds.
    transition:
        Transition style: ``"fade"`` | ``"none"``.
    transition_duration:
        Duration in seconds of each transition (only used when
        transition="fade").  Must be less than *duration_per_slide*.
    size:
        Output frame size as ``"WxH"`` (e.g. ``"1080x1920"``).
    pip_video:
        Optional path to a video to overlay as picture-in-picture.
    pip_position:
        Corner for the PIP: ``"top-left"`` | ``"top-right"`` |
        ``"bottom-left"`` | ``"bottom-right"`` | ``"center"``.
    pip_size:
        Width of the PIP as a percentage of the output frame width (1-100).

    Returns
    -------
    dict with keys:
        ``success`` (bool), ``output_path`` (str), ``duration_seconds`` (float),
        ``slide_count`` (int), ``encoder`` (str), ``error`` (str, on failure).
    """
    # ------------------------------------------------------------------
    # Validate inputs
    # ------------------------------------------------------------------
    if not images:
        return {"success": False, "error": "Danh sách ảnh không được để trống."}

    missing = [p for p in images if not Path(p).exists()]
    if missing:
        return {
            "success": False,
            "error": f"Các file ảnh sau không tồn tại: {', '.join(missing[:5])}",
        }

    if audio_path and not Path(audio_path).exists():
        return {"success": False, "error": f"File âm thanh không tồn tại: {audio_path}"}

    if pip_video and not Path(pip_video).exists():
        return {"success": False, "error": f"File video PIP không tồn tại: {pip_video}"}

    if not shutil.which("ffmpeg"):
        return {
            "success": False,
            "error": "FFmpeg chưa được cài đặt hoặc không có trong PATH.",
        }

    transition = transition.lower()
    if transition not in _TRANSITIONS:
        return {
            "success": False,
            "error": f"Transition không hợp lệ: '{transition}'. Hỗ trợ: {', '.join(_TRANSITIONS)}.",
        }

    pip_position = pip_position.lower()
    if pip_video and pip_position not in _PIP_POSITIONS:
        return {
            "success": False,
            "error": f"Vị trí PIP không hợp lệ: '{pip_position}'. "
                     f"Hỗ trợ: {', '.join(_PIP_POSITIONS)}.",
        }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Resolve timing
    # ------------------------------------------------------------------
    audio_duration: float | None = None
    if audio_path:
        audio_duration = _get_audio_duration(audio_path)
        if audio_duration is None:
            return {
                "success": False,
                "error": f"Không thể đọc thời lượng file âm thanh: {audio_path}",
            }

    if duration_per_slide is None:
        if audio_duration is not None:
            duration_per_slide = audio_duration / len(images)
        else:
            duration_per_slide = 3.0

    # Clamp transition so it's always less than slide duration
    if transition == "fade":
        transition_duration = min(transition_duration, duration_per_slide * 0.45)

    # ------------------------------------------------------------------
    # Detect encoder
    # ------------------------------------------------------------------
    try:
        from shared.platform import detect_ffmpeg_encoder
        encoder = detect_ffmpeg_encoder()
    except Exception:
        encoder = "libx264"

    # ------------------------------------------------------------------
    # Build and run FFmpeg command
    # ------------------------------------------------------------------
    try:
        result = _build_and_run_ffmpeg(
            images=images,
            output_path=str(out),
            audio_path=audio_path,
            audio_duration=audio_duration,
            duration_per_slide=duration_per_slide,
            transition=transition,
            transition_duration=transition_duration,
            size=size,
            encoder=encoder,
            pip_video=pip_video,
            pip_position=pip_position,
            pip_size=pip_size,
        )
    except Exception as exc:
        return {"success": False, "error": f"Lỗi khi chạy FFmpeg: {exc}"}

    if not result["success"]:
        return result

    total_duration = duration_per_slide * len(images)
    return {
        "success": True,
        "output_path": str(out.resolve()),
        "duration_seconds": round(total_duration, 2),
        "slide_count": len(images),
        "encoder": encoder,
    }


# ---------------------------------------------------------------------------
# Internal: FFmpeg command builder
# ---------------------------------------------------------------------------


def _build_and_run_ffmpeg(
    images: list[str],
    output_path: str,
    audio_path: str | None,
    audio_duration: float | None,
    duration_per_slide: float,
    transition: str,
    transition_duration: float,
    size: str,
    encoder: str,
    pip_video: str | None,
    pip_position: str,
    pip_size: int,
) -> dict[str, Any]:
    """Construct the FFmpeg command and execute it."""
    width, height = _parse_size(size)
    n = len(images)

    # ---- Build input arguments ----
    cmd: list[str] = ["ffmpeg", "-y"]

    # Add each image as a loop input
    for img in images:
        cmd += ["-loop", "1", "-t", str(duration_per_slide), "-i", img]

    # Add audio input
    if audio_path:
        cmd += ["-i", audio_path]
    audio_input_idx = n  # index of the audio stream (if present)

    # Add PIP video input
    pip_input_idx: int | None = None
    if pip_video:
        cmd += ["-stream_loop", "-1", "-i", pip_video]
        pip_input_idx = n + (1 if audio_path else 0)

    # ---- Build filter_complex ----
    filter_parts: list[str] = []

    # Step 1: Scale each image to target size (scale-and-pad / crop)
    for i in range(n):
        # Scale to fill, keeping aspect ratio, then pad to exact size
        filter_parts.append(
            f"[{i}:v]"
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"setsar=1,"
            f"fps=25"
            f"[scaled{i}]"
        )

    # Step 2: Fade transitions or plain concat
    if transition == "fade" and n > 1:
        video_stream = _build_fade_chain(
            n=n,
            duration_per_slide=duration_per_slide,
            transition_duration=transition_duration,
            filter_parts=filter_parts,
        )
    else:
        # No transition — simple concat
        concat_inputs = "".join(f"[scaled{i}]" for i in range(n))
        filter_parts.append(f"{concat_inputs}concat=n={n}:v=1:a=0[video_raw]")
        video_stream = "[video_raw]"

    # Step 3: PIP overlay
    if pip_video and pip_input_idx is not None:
        pip_w = f"iw*{pip_size}/100"
        pip_h = "-1"  # maintain aspect ratio
        x_expr, y_expr = _PIP_POSITIONS.get(pip_position, ("main_w-overlay_w-10", "main_h-overlay_h-10"))
        filter_parts.append(
            f"[{pip_input_idx}:v]scale={pip_w}:{pip_h}[pip_scaled]"
        )
        filter_parts.append(
            f"{video_stream}[pip_scaled]overlay={x_expr}:{y_expr}:shortest=1[video_final]"
        )
        final_video_stream = "[video_final]"
    else:
        # Rename for consistency
        if video_stream != "[video_final]":
            filter_parts.append(f"{video_stream}null[video_final]")
        final_video_stream = "[video_final]"

    filter_complex = "; ".join(filter_parts)
    cmd += ["-filter_complex", filter_complex]

    # ---- Map streams ----
    cmd += ["-map", final_video_stream]
    if audio_path:
        cmd += ["-map", f"{audio_input_idx}:a"]

    # ---- Encoding options ----
    cmd += ["-c:v", encoder]
    if encoder == "libx264":
        cmd += ["-preset", "fast", "-crf", "23"]
    elif encoder == "h264_videotoolbox":
        cmd += ["-b:v", "4M"]
    elif encoder == "h264_nvenc":
        cmd += ["-preset", "fast", "-b:v", "4M"]

    if audio_path:
        cmd += ["-c:a", "aac", "-b:a", "192k"]

    # Trim to audio duration when provided
    if audio_duration is not None:
        cmd += ["-t", str(audio_duration)]

    cmd += ["-movflags", "+faststart", output_path]

    # ---- Execute ----
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "FFmpeg vượt quá thời gian cho phép (600s). Thử với ít ảnh hơn.",
        }
    except FileNotFoundError:
        return {"success": False, "error": "Không tìm thấy lệnh ffmpeg trong PATH."}

    if proc.returncode != 0:
        stderr_snippet = (proc.stderr or "")[-1000:]
        return {
            "success": False,
            "error": f"FFmpeg kết thúc với mã lỗi {proc.returncode}.\n{stderr_snippet}",
        }

    return {"success": True}


def _build_fade_chain(
    n: int,
    duration_per_slide: float,
    transition_duration: float,
    filter_parts: list[str],
) -> str:
    """
    Build cross-fade transition filters for n slides.

    Returns the label of the final merged video stream.
    Appends filter fragments to *filter_parts* in place.
    """
    td = transition_duration

    # Fade-out each slide at its end, fade-in at start
    for i in range(n):
        filters: list[str] = []
        if i > 0:
            filters.append(f"fade=t=in:st=0:d={td}")
        if i < n - 1:
            fo_start = max(0.0, duration_per_slide - td)
            filters.append(f"fade=t=out:st={fo_start:.4f}:d={td}")

        if filters:
            chain = ",".join(filters)
            filter_parts.append(f"[scaled{i}]{chain}[faded{i}]")
        else:
            filter_parts.append(f"[scaled{i}]null[faded{i}]")

    # Concatenate faded streams
    concat_inputs = "".join(f"[faded{i}]" for i in range(n))
    filter_parts.append(f"{concat_inputs}concat=n={n}:v=1:a=0[video_raw]")
    return "[video_raw]"


# ---------------------------------------------------------------------------
# Internal: media info
# ---------------------------------------------------------------------------


def _get_audio_duration(path: str) -> float | None:
    """
    Return the duration in seconds of an audio file using ffprobe.

    Returns None if the file cannot be read.
    """
    if not shutil.which("ffprobe"):
        return None
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if proc.returncode != 0:
            return None
        data = json.loads(proc.stdout)
        duration_str = data.get("format", {}).get("duration")
        if duration_str:
            return float(duration_str)
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Internal: utilities
# ---------------------------------------------------------------------------


def _parse_size(size: str) -> tuple[int, int]:
    """Parse '1080x1920' into (1080, 1920).  Returns (1080, 1920) on error."""
    try:
        w, h = size.lower().split("x")
        return int(w), int(h)
    except Exception:
        return 1080, 1920
