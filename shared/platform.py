"""Platform detection and tool availability."""

import platform
import shutil
import subprocess
from pathlib import Path


def is_macos() -> bool:
    return platform.system() == "Darwin"


def is_windows() -> bool:
    return platform.system() == "Windows"


def _test_encoder(encoder: str) -> bool:
    """Test if an encoder actually works by encoding a tiny video."""
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                "color=black:s=64x64:d=0.1:r=1",
                "-c:v", encoder, "-frames:v", "1",
                "-f", "null", "-",
            ],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def detect_ffmpeg_encoder() -> str:
    try:
        result = subprocess.run(
            ["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=10
        )
        out = result.stdout
    except Exception:
        return "libx264"

    if is_macos() and "h264_videotoolbox" in out:
        if _test_encoder("h264_videotoolbox"):
            return "h264_videotoolbox"
    if is_windows():
        if "h264_nvenc" in out and _test_encoder("h264_nvenc"):
            return "h264_nvenc"
        if "h264_mf" in out and _test_encoder("h264_mf"):
            return "h264_mf"
    return "libx264"


def detect_ffmpeg_encoder_for_filter() -> str:
    """Detect encoder safe for FFmpeg filter_complex operations.

    h264_mf (Windows MediaFoundation) hangs on complex filter_complex
    pipelines (xfade, geq overlay, sidechaincompress). Fall back to
    libx264 for those operations.
    """
    encoder = detect_ffmpeg_encoder()
    if encoder == "h264_mf":
        return "libx264"
    return encoder


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def check_viettts(url: str = "http://localhost:8298") -> bool:
    try:
        import requests

        resp = requests.get(f"{url}/v1/voices", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def check_sadtalker(dir_path: str) -> bool:
    if not dir_path:
        return False
    return Path(dir_path).joinpath("inference.py").exists()


def get_sadtalker_path() -> str:
    from shared.config import load_config

    cfg = load_config()
    p = cfg.get("sadtalker_dir", "")
    if p and check_sadtalker(p):
        return p
    raise ValueError(
        "Chưa cấu hình SadTalker.\n"
        "Cách fix: chạy `wfm-setup` và nhập đường dẫn SadTalker."
    )
