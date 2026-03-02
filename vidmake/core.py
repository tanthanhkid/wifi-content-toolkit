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
    # Detect encoder (filter-safe: h264_mf hangs on filter_complex)
    # ------------------------------------------------------------------
    try:
        from shared.platform import detect_ffmpeg_encoder_for_filter
        encoder = detect_ffmpeg_encoder_for_filter()
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
    elif encoder == "h264_mf":
        cmd += ["-b:v", "4M"]

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


# ---------------------------------------------------------------------------
# Ken Burns animated slideshow
# ---------------------------------------------------------------------------

# Available Ken Burns animation effects
ANIMATION_EFFECTS = [
    "zoom_in",
    "zoom_out",
    "pan_right",
    "pan_down",
    "zoom_topleft",
]


def _build_zoompan_filter(effect: str, frames: int, size: str, fps: int) -> str:
    """Return the zoompan filter string for the given Ken Burns effect."""
    w, h = _parse_size(size)
    base = f"d={frames}:s={w}x{h}:fps={fps}"

    filters = {
        "zoom_in": (
            f"zoompan=z='min(zoom+0.003,1.5)'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':{base}"
        ),
        "zoom_out": (
            f"zoompan=z='if(lte(zoom,1.001),1.5,max(1.001,zoom-0.003))'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':{base}"
        ),
        "pan_right": (
            f"zoompan=z=1.3"
            f":x='if(lte(on,1),0,min(x+2,iw-iw/zoom))'"
            f":y='ih/2-(ih/zoom/2)':{base}"
        ),
        "pan_down": (
            f"zoompan=z=1.2"
            f":x='iw/2-(iw/zoom/2)'"
            f":y='if(lte(on,1),0,min(y+1.5,ih-ih/zoom))':{base}"
        ),
        "zoom_topleft": (
            f"zoompan=z='min(zoom+0.004,2.0)'"
            f":x='iw*0.2':y='ih*0.15':{base}"
        ),
    }
    return filters.get(effect, filters["zoom_in"])


def _animate_single_slide(
    image_path: str,
    output_path: str,
    effect: str,
    duration: float,
    size: str,
    fps: int,
    encoder: str,
) -> dict[str, Any]:
    """Apply a Ken Burns animation to a single image and produce an MP4 clip."""
    frames = int(duration * fps)
    zoompan = _build_zoompan_filter(effect, frames, size, fps)

    # Add fade in/out
    fade_in = "fade=t=in:st=0:d=0.5"
    fade_out = f"fade=t=out:st={duration - 0.5:.1f}:d=0.5"
    vf = f"{zoompan},{fade_in},{fade_out}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-vf", vf,
        "-t", str(duration),
        "-c:v", encoder,
        "-pix_fmt", "yuv420p",
    ]

    if encoder == "libx264":
        cmd += ["-preset", "fast", "-crf", "23"]
    elif encoder == "h264_videotoolbox":
        cmd += ["-b:v", "4M"]
    elif encoder == "h264_nvenc":
        cmd += ["-preset", "fast", "-b:v", "4M"]
    elif encoder == "h264_mf":
        cmd += ["-b:v", "4M"]

    cmd.append(output_path)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Timeout animating {image_path}"}
    except FileNotFoundError:
        return {"success": False, "error": "FFmpeg not found in PATH."}

    if proc.returncode != 0:
        return {
            "success": False,
            "error": f"FFmpeg error ({proc.returncode}): {(proc.stderr or '')[-500:]}",
        }
    return {"success": True, "output_path": output_path}


def add_facecam_overlay(
    video_path: str,
    facecam_path: str,
    output_path: str,
    position: str = "middle-left",
    size: int = 30,
    border_radius: int = 20,
    margin: int = 20,
) -> dict[str, Any]:
    """
    Overlay a facecam video onto the main video with rounded corners.

    The facecam is automatically looped if shorter than the main video.

    Parameters
    ----------
    video_path:
        Path to the main video (MP4).
    facecam_path:
        Path to the facecam video (MP4) to overlay.
    output_path:
        Destination path for the output MP4.
    position:
        Placement: ``"middle-left"`` | ``"top-left"`` | ``"top-right"`` |
        ``"bottom-left"`` | ``"bottom-right"``.
    size:
        Width of the facecam as a percentage of the main video width (1-100).
    border_radius:
        Corner radius in pixels for rounded rectangle mask.
    margin:
        Distance in pixels from the video edge.

    Returns
    -------
    dict with ``success``, ``output_path``, ``error`` (on failure).
    """
    # Validate
    if not Path(video_path).exists():
        return {"success": False, "error": f"Video chính không tồn tại: {video_path}"}
    if not Path(facecam_path).exists():
        return {"success": False, "error": f"Video facecam không tồn tại: {facecam_path}"}
    if not shutil.which("ffmpeg"):
        return {"success": False, "error": "FFmpeg chưa được cài đặt."}

    position = position.lower()
    valid_positions = {"top-left", "top-right", "bottom-left", "bottom-right", "middle-left"}
    if position not in valid_positions:
        return {
            "success": False,
            "error": f"Vị trí không hợp lệ: '{position}'. Hỗ trợ: {', '.join(valid_positions)}.",
        }

    size = max(1, min(100, size))
    border_radius = max(0, border_radius)
    margin = max(0, margin)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Detect encoder (filter-safe: h264_mf hangs on filter_complex)
    try:
        from shared.platform import detect_ffmpeg_encoder_for_filter
        encoder = detect_ffmpeg_encoder_for_filter()
    except Exception:
        encoder = "libx264"

    # Position expressions — margin controls Y (bottom/top distance),
    # X margin is fixed at 20px for left/right edge positions.
    x_margin = 20
    positions = {
        "top-left":     (f"{x_margin}", f"{margin}"),
        "top-right":    (f"main_w-overlay_w-{x_margin}", f"{margin}"),
        "bottom-left":  (f"{x_margin}", f"main_h-overlay_h-{margin}"),
        "bottom-right": (f"main_w-overlay_w-{x_margin}", f"main_h-overlay_h-{margin}"),
        "middle-left":  (f"{x_margin}", f"(main_h-overlay_h)/2"),
    }
    x_expr, y_expr = positions[position]

    # Build filter_complex:
    # 1. Scale facecam to target width (size% of main), keep aspect ratio
    # 2. Create rounded corners using geq alpha mask with st()/ld() variables
    # 3. Overlay on main video
    pip_w_expr = f"iw*{size}/100"
    r = border_radius

    filter_parts = [
        # Scale facecam, force even dimensions
        f"[1:v]scale={pip_w_expr}:-2,setsar=1[pip_scaled]",
        # Apply rounded corners via alpha mask:
        # st(0..3) = distance into each corner radius zone
        # st(4) = hypotenuse to nearest corner center
        # If hypot > radius → transparent (outside corner)
        (
            f"[pip_scaled]format=yuva420p,"
            f"geq="
            f"lum='lum(X,Y)':"
            f"cb='cb(X,Y)':"
            f"cr='cr(X,Y)':"
            f"a='st(0,max(0,{r}-X));"
            f"st(1,max(0,X-(W-{r})));"
            f"st(2,max(0,{r}-Y));"
            f"st(3,max(0,Y-(H-{r})));"
            f"if(gt(hypot(max(ld(0),ld(1)),max(ld(2),ld(3))),{r}),0,255)'"
            f"[pip_rounded]"
        ),
        # Overlay on main video
        f"[0:v][pip_rounded]overlay={x_expr}:{y_expr}:shortest=1[vout]",
    ]

    filter_complex = "; ".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-stream_loop", "-1", "-i", facecam_path,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a?",
        "-c:v", encoder,
        "-c:a", "copy",
    ]

    if encoder == "libx264":
        cmd += ["-preset", "fast", "-crf", "23"]
    elif encoder == "h264_videotoolbox":
        cmd += ["-b:v", "4M"]
    elif encoder == "h264_nvenc":
        cmd += ["-preset", "fast", "-b:v", "4M"]
    elif encoder == "h264_mf":
        cmd += ["-b:v", "4M"]

    cmd += ["-movflags", "+faststart", "-pix_fmt", "yuv420p", str(out)]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "FFmpeg vượt quá thời gian cho phép (600s)."}
    except FileNotFoundError:
        return {"success": False, "error": "Không tìm thấy lệnh ffmpeg trong PATH."}

    if proc.returncode != 0:
        stderr_snippet = (proc.stderr or "")[-1000:]
        return {
            "success": False,
            "error": f"FFmpeg lỗi ({proc.returncode}):\n{stderr_snippet}",
        }

    return {
        "success": True,
        "output_path": str(out.resolve()),
    }


def mix_audio_with_ducking(
    video_path: str,
    voiceover_path: str,
    music_path: str,
    output_path: str,
    music_volume: float = 0.15,
    voice_volume: float = 1.0,
    duck_level: float = 0.1,
    fade_out: float = 2.0,
) -> dict[str, Any]:
    """
    Combine video + voiceover + background music with automatic ducking.

    Uses FFmpeg sidechaincompress so music ducks when voice is speaking
    and returns to normal volume during silent transitions.

    Parameters
    ----------
    video_path:
        Path to the input video (MP4, typically merged slides with no audio).
    voiceover_path:
        Path to the voiceover audio file (MP3/WAV).
    music_path:
        Path to the background music file (MP3/WAV).
    output_path:
        Destination path for the output MP4 file.
    music_volume:
        Base volume for background music before ducking (default 0.15).
    voice_volume:
        Volume for the voiceover track (default 1.0).
    duck_level:
        How aggressively to duck music when voice is detected.
        Lower = more ducking. Range 0.01-1.0 (default 0.1).
    fade_out:
        Fade out music at end of video, in seconds (default 2.0).
        Set to 0.0 to disable.

    Returns
    -------
    dict with ``success``, ``output_path``, ``duration_seconds``, ``error`` (on failure).
    """
    # Validate inputs
    if not Path(video_path).exists():
        return {"success": False, "error": f"Video không tồn tại: {video_path}"}
    if not Path(voiceover_path).exists():
        return {"success": False, "error": f"File voiceover không tồn tại: {voiceover_path}"}
    if not Path(music_path).exists():
        return {"success": False, "error": f"File nhạc nền không tồn tại: {music_path}"}
    if not shutil.which("ffmpeg"):
        return {"success": False, "error": "FFmpeg chưa được cài đặt."}

    duck_level = max(0.01, min(1.0, duck_level))
    music_volume = max(0.0, min(2.0, music_volume))
    voice_volume = max(0.0, min(2.0, voice_volume))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Get video duration to trim music
    video_duration = _get_audio_duration(video_path)
    if video_duration is None:
        # Fallback: use ffprobe on video
        try:
            proc = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", video_path],
                capture_output=True, text=True, timeout=15,
            )
            data = json.loads(proc.stdout)
            video_duration = float(data.get("format", {}).get("duration", 60))
        except Exception:
            video_duration = 60.0

    # Detect encoder (mix uses -c:v copy but keep filter-safe for consistency)
    try:
        from shared.platform import detect_ffmpeg_encoder_for_filter
        encoder = detect_ffmpeg_encoder_for_filter()
    except Exception:
        encoder = "libx264"

    # Build FFmpeg filter_complex for sidechain ducking:
    # [1] voiceover → aformat → volume adjust → [voice]
    # [2] music → aformat → volume → trim to video length → [music_base]
    # [music_base][voice] sidechaincompress → [music_ducked]
    # [voice][music_ducked] amix → [final_audio]
    music_filters = f"aformat=fltp:44100:stereo,volume={music_volume}"
    music_filters += f",atrim=0:{video_duration:.2f},asetpts=PTS-STARTPTS"
    if fade_out > 0:
        fade_start = max(0, video_duration - fade_out)
        music_filters += f",afade=t=out:st={fade_start:.2f}:d={fade_out:.2f}"

    # Map duck_level (0.01-1.0) to sidechaincompress parameters:
    # Lower duck_level → higher ratio → more aggressive ducking
    # duck_level=0.1 → ratio=20 (heavy ducking)
    # duck_level=0.5 → ratio=6 (moderate ducking)
    # duck_level=1.0 → ratio=2 (light ducking)
    sc_ratio = max(2, min(20, int(2 / duck_level)))
    sc_threshold = 0.015  # low threshold to catch even soft speech

    filter_complex = (
        f"[1:a]aformat=fltp:44100:stereo,volume={voice_volume},asplit=2[voice_mix][voice_sc];"
        f"[2:a]{music_filters}[music_base];"
        f"[music_base][voice_sc]sidechaincompress="
        f"level_in=1:threshold={sc_threshold}:ratio={sc_ratio}:"
        f"attack=5:release=200:makeup=1[music_ducked];"
        f"[voice_mix][music_ducked]amix=inputs=2:duration=first:dropout_transition=2[final_audio]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", voiceover_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "0:v:0",
        "-map", "[final_audio]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(out),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "FFmpeg vượt quá thời gian cho phép (300s)."}
    except FileNotFoundError:
        return {"success": False, "error": "Không tìm thấy lệnh ffmpeg trong PATH."}

    if proc.returncode != 0:
        stderr_snippet = (proc.stderr or "")[-1000:]
        return {
            "success": False,
            "error": f"FFmpeg lỗi ({proc.returncode}):\n{stderr_snippet}",
        }

    return {
        "success": True,
        "output_path": str(out.resolve()),
        "duration_seconds": round(video_duration, 2),
    }


def record_html_video(
    html_content: str,
    output_path: str,
    width: int = 1080,
    height: int = 1920,
    duration: float = 5.0,
    fps: int = 30,
    encoder: str | None = None,
) -> dict[str, Any]:
    """Record a browser playing CSS animations → MP4 video.

    Instead of screenshotting a static PNG, this uses Playwright's video
    recording to capture CSS @keyframes animations running in the browser,
    then re-encodes the WebM to MP4 via FFmpeg.

    Parameters
    ----------
    html_content:
        Full HTML document with CSS animations (@keyframes).
    output_path:
        Destination path for the output MP4 file.
    width:
        Viewport width (default 1080).
    height:
        Viewport height (default 1920).
    duration:
        How long to record in seconds (default 5.0).
    fps:
        Target frames per second (default 30).
    encoder:
        H.264 encoder. Auto-detected if None.

    Returns
    -------
    dict with ``success``, ``output_path``, ``duration``, ``error`` (on failure).
    """
    if not html_content or not html_content.strip():
        return {"success": False, "error": "HTML content không được để trống."}
    if not shutil.which("ffmpeg"):
        return {"success": False, "error": "FFmpeg chưa được cài đặt."}

    import asyncio

    coro = _record_html_video_async(
        html_content, output_path, width, height, duration, fps, encoder,
    )
    try:
        asyncio.get_running_loop()
        # Inside an async event loop (MCP server) — offload to thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        # No running loop — safe to use asyncio.run directly
        return asyncio.run(coro)


async def _record_html_video_async(
    html_content: str,
    output_path: str,
    width: int,
    height: int,
    duration: float,
    fps: int,
    encoder: str | None,
) -> dict[str, Any]:
    """Async implementation: Playwright video recording → FFmpeg re-encode."""
    from playwright.async_api import async_playwright

    if encoder is None:
        try:
            from shared.platform import detect_ffmpeg_encoder
            encoder = detect_ffmpeg_encoder()
        except Exception:
            encoder = "libx264"

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    tmpdir = tempfile.mkdtemp(prefix="vidmake_record_")
    webm_path = None

    try:
        import os as _os

        # Write HTML to temp file so local file:// references work
        html_file = Path(tmpdir) / "page.html"
        html_file.write_text(html_content, encoding="utf-8")

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                viewport={"width": width, "height": height},
                record_video_dir=tmpdir,
                record_video_size={"width": width, "height": height},
            )
            page = await context.new_page()

            await page.goto(
                f"file://{html_file}", wait_until="networkidle",
            )

            # Let CSS animations play for the specified duration
            await page.wait_for_timeout(int(duration * 1000))

            # Close page + context to finalize the video file
            webm_path = await page.video.path()
            await page.close()
            await context.close()
            await browser.close()

        if not webm_path or not Path(webm_path).exists():
            return {"success": False, "error": "Playwright không tạo được file video."}

        # Re-encode WebM → MP4 (h264, yuv420p)
        bitrate = "6M"
        cmd = [
            "ffmpeg", "-y",
            "-i", str(webm_path),
            "-c:v", encoder,
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-t", str(duration),
        ]

        if encoder == "libx264":
            cmd += ["-preset", "fast", "-crf", "20"]
        elif encoder == "h264_videotoolbox":
            cmd += ["-b:v", bitrate]
        elif encoder == "h264_nvenc":
            cmd += ["-preset", "fast", "-b:v", bitrate]
        elif encoder == "h264_mf":
            cmd += ["-b:v", bitrate]

        cmd += ["-movflags", "+faststart", "-an", str(out)]

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if proc.returncode != 0:
            stderr_snippet = (proc.stderr or "")[-500:]
            return {
                "success": False,
                "error": f"FFmpeg re-encode lỗi ({proc.returncode}):\n{stderr_snippet}",
            }

        return {
            "success": True,
            "output_path": str(out.resolve()),
            "duration": duration,
        }

    except Exception as exc:
        return {"success": False, "error": f"Lỗi khi quay video: {exc}"}

    finally:
        import shutil as _shutil
        _shutil.rmtree(tmpdir, ignore_errors=True)


def batch_record_html_videos(
    slides: list[dict],
    encoder: str | None = None,
    fps: int = 30,
) -> list[dict[str, Any]]:
    """Record multiple CSS-animated HTML slides using ONE shared browser.

    Each slide dict must have:
      - html (str): Full HTML content
      - output_path (str): Destination MP4 path
      - width (int): Viewport width
      - height (int): Viewport height
      - duration (float): Recording duration in seconds

    This is ~3-4x faster than calling record_html_video() per slide because
    the browser is launched only once.
    """
    import asyncio

    coro = _batch_record_async(slides, encoder, fps)
    try:
        asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        return asyncio.run(coro)


async def _batch_record_async(
    slides: list[dict],
    encoder: str | None,
    fps: int,
) -> list[dict[str, Any]]:
    """Async: record all slides with one browser launch."""
    from playwright.async_api import async_playwright

    if encoder is None:
        try:
            from shared.platform import detect_ffmpeg_encoder
            encoder = detect_ffmpeg_encoder()
        except Exception:
            encoder = "libx264"

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()

        for slide in slides:
            html_content = slide["html"]
            output_path = slide["output_path"]
            width = slide.get("width", 1080)
            height = slide.get("height", 1920)
            duration = slide.get("duration", 5.0)

            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            tmpdir = tempfile.mkdtemp(prefix="vidmake_batch_")

            try:
                html_file = Path(tmpdir) / "page.html"
                html_file.write_text(html_content, encoding="utf-8")

                context = await browser.new_context(
                    viewport={"width": width, "height": height},
                    record_video_dir=tmpdir,
                    record_video_size={"width": width, "height": height},
                )
                page = await context.new_page()
                await page.goto(
                    f"file://{html_file}", wait_until="networkidle",
                )
                await page.wait_for_timeout(int(duration * 1000))

                webm_path = await page.video.path()
                await page.close()
                await context.close()

                if not webm_path or not Path(webm_path).exists():
                    results.append({"success": False, "error": "No video file"})
                    continue

                bitrate = "6M"
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(webm_path),
                    "-c:v", encoder,
                    "-pix_fmt", "yuv420p",
                    "-r", str(fps),
                    "-t", str(duration),
                ]
                if encoder == "libx264":
                    cmd += ["-preset", "fast", "-crf", "20"]
                elif encoder == "h264_videotoolbox":
                    cmd += ["-b:v", bitrate]
                elif encoder == "h264_nvenc":
                    cmd += ["-preset", "fast", "-b:v", bitrate]
                elif encoder == "h264_mf":
                    cmd += ["-b:v", bitrate]
                cmd += ["-movflags", "+faststart", "-an", str(out)]

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if proc.returncode != 0:
                    results.append({"success": False, "error": (proc.stderr or "")[-300:]})
                else:
                    results.append({"success": True, "output_path": str(out.resolve()), "duration": duration})

            except Exception as exc:
                results.append({"success": False, "error": str(exc)})
            finally:
                import shutil as _shutil
                _shutil.rmtree(tmpdir, ignore_errors=True)

        await browser.close()

    return results


def create_animated_slideshow(
    images: list[str],
    output_path: str,
    effects: list[str] | None = None,
    duration_per_slide: float = 5.0,
    audio_path: str | None = None,
    size: str = "1080x1920",
    fps: int = 30,
) -> dict[str, Any]:
    """Create a video with Ken Burns animations applied per slide.

    Parameters
    ----------
    images:
        Ordered list of image file paths (PNG/JPG).
    output_path:
        Destination MP4 path.
    effects:
        Per-slide animation effect names. If None or shorter than images,
        cycles through ANIMATION_EFFECTS.
    duration_per_slide:
        Seconds each slide is displayed.
    audio_path:
        Optional background music file.
    size:
        Output resolution as 'WxH'.
    fps:
        Frames per second.

    Returns
    -------
    dict with success, output_path, duration_seconds, slide_count, encoder, error.
    """
    if not images:
        return {"success": False, "error": "Danh sách ảnh không được để trống."}

    missing = [p for p in images if not Path(p).exists()]
    if missing:
        return {"success": False, "error": f"File không tồn tại: {', '.join(missing[:5])}"}

    if audio_path and not Path(audio_path).exists():
        return {"success": False, "error": f"File âm thanh không tồn tại: {audio_path}"}

    if not shutil.which("ffmpeg"):
        return {"success": False, "error": "FFmpeg chưa được cài đặt."}

    # Resolve effects list
    if not effects:
        effects = []
    resolved_effects: list[str] = []
    for i in range(len(images)):
        if i < len(effects) and effects[i] in ANIMATION_EFFECTS:
            resolved_effects.append(effects[i])
        else:
            resolved_effects.append(ANIMATION_EFFECTS[i % len(ANIMATION_EFFECTS)])

    # Detect encoder (filter-safe: h264_mf hangs on filter_complex)
    try:
        from shared.platform import detect_ffmpeg_encoder_for_filter
        encoder = detect_ffmpeg_encoder_for_filter()
    except Exception:
        encoder = "libx264"

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    tmpdir = tempfile.mkdtemp(prefix="vidmake_anim_")
    clip_paths: list[str] = []

    try:
        # Step 1: Animate each slide
        for i, (img, effect) in enumerate(zip(images, resolved_effects)):
            clip_path = str(Path(tmpdir) / f"clip_{i:03d}.mp4")
            result = _animate_single_slide(
                image_path=img,
                output_path=clip_path,
                effect=effect,
                duration=duration_per_slide,
                size=size,
                fps=fps,
                encoder=encoder,
            )
            if not result["success"]:
                return result
            clip_paths.append(clip_path)

        # Step 2: Concat all clips
        concat_list = Path(tmpdir) / "clips.txt"
        with open(concat_list, "w") as f:
            for cp in clip_paths:
                f.write(f"file '{cp}'\n")

        merged_path = str(Path(tmpdir) / "merged.mp4")
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "copy",
            merged_path,
        ]
        proc = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0:
            return {
                "success": False,
                "error": f"Lỗi ghép clips: {(proc.stderr or '')[-500:]}",
            }

        # Step 3: Add audio if provided
        if audio_path:
            final_cmd = [
                "ffmpeg", "-y",
                "-i", merged_path,
                "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                "-map", "0:v:0", "-map", "1:a:0",
                "-movflags", "+faststart",
                str(out),
            ]
            proc = subprocess.run(final_cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": f"Lỗi thêm nhạc: {(proc.stderr or '')[-500:]}",
                }
        else:
            import shutil as _shutil
            _shutil.copy2(merged_path, str(out))

    finally:
        # Cleanup temp dir
        import shutil as _shutil
        _shutil.rmtree(tmpdir, ignore_errors=True)

    total_duration = duration_per_slide * len(images)
    return {
        "success": True,
        "output_path": str(out.resolve()),
        "duration_seconds": round(total_duration, 2),
        "slide_count": len(images),
        "encoder": encoder,
        "effects": resolved_effects,
    }
