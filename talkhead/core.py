"""
core.py — Pure business logic for wfm-talkhead.

Strategy
--------
1. If *server_url* is provided (not None / empty), try the HTTP API first:
   POST {server_url}/api/generate  (multipart/form-data: image + audio + params)
2. If the HTTP API fails or is unavailable, fall back to running SadTalker's
   inference.py as a subprocess.  The SadTalker directory is resolved from:
     a. The *sadtalker_dir* argument (if provided).
     b. shared.platform.get_sadtalker_path() (reads ~/.wfm/config.json).

Error messages are in Vietnamese.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_talking_head(
    image_path: str,
    audio_path: str,
    output_path: str,
    still: bool = True,
    preprocess: str = "full",
    enhancer: str = "gfpgan",
    sadtalker_dir: str | None = None,
    server_url: str = "http://localhost:8299",
) -> dict[str, Any]:
    """
    Animate *image_path* to match *audio_path* and save the result to *output_path*.

    Attempts the HTTP API first; falls back to a local subprocess call.

    Parameters
    ----------
    image_path:
        Path to the portrait image (JPG / PNG).
    audio_path:
        Path to the driving audio (WAV / MP3).
    output_path:
        Destination path for the output video (MP4).
    still:
        If True, minimise head motion (recommended for talking-head style).
    preprocess:
        SadTalker pre-process mode: ``"crop"`` | ``"resize"`` | ``"full"``.
    enhancer:
        Face enhancer to apply: ``"gfpgan"`` | ``"RestoreFormer"`` | ``""`` (none).
    sadtalker_dir:
        Explicit path to the SadTalker source directory (contains inference.py).
        If None, resolved via ``shared.platform.get_sadtalker_path()``.
    server_url:
        Base URL of a running SadTalker HTTP wrapper server.
        Pass an empty string or None to skip the HTTP attempt and go straight
        to subprocess mode.

    Returns
    -------
    dict with keys:
        ``success`` (bool), ``output_path`` (str), ``method`` (``"api"`` or
        ``"subprocess"``), ``error`` (str, only on failure).
    """
    img = Path(image_path)
    aud = Path(audio_path)

    if not img.exists():
        return {"success": False, "error": f"File ảnh không tồn tại: {image_path}"}
    if not aud.exists():
        return {"success": False, "error": f"File âm thanh không tồn tại: {audio_path}"}

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Attempt 1: HTTP API
    # ------------------------------------------------------------------
    if server_url and server_url.strip():
        api_result = _try_api(
            img=img,
            aud=aud,
            out=out,
            still=still,
            preprocess=preprocess,
            enhancer=enhancer,
            server_url=server_url.strip(),
        )
        if api_result["success"]:
            return api_result
        # Log the API error but continue to subprocess fallback
        _api_error = api_result.get("error", "")
    else:
        _api_error = ""

    # ------------------------------------------------------------------
    # Attempt 2: subprocess fallback
    # ------------------------------------------------------------------
    resolved_dir = _resolve_sadtalker_dir(sadtalker_dir)
    if isinstance(resolved_dir, dict):
        # Error dict from resolver
        err_parts = []
        if _api_error:
            err_parts.append(f"API: {_api_error}")
        err_parts.append(f"Subprocess: {resolved_dir['error']}")
        return {"success": False, "error" : " | ".join(err_parts)}

    return _run_subprocess(
        sadtalker_dir=resolved_dir,
        img=img,
        aud=aud,
        out=out,
        still=still,
        preprocess=preprocess,
        enhancer=enhancer,
    )


# ---------------------------------------------------------------------------
# Internal: HTTP API
# ---------------------------------------------------------------------------


def _try_api(
    img: Path,
    aud: Path,
    out: Path,
    still: bool,
    preprocess: str,
    enhancer: str,
    server_url: str,
) -> dict[str, Any]:
    """POST to {server_url}/api/generate and save the returned video."""
    try:
        import requests
    except ImportError:
        return {"success": False, "error": "Thư viện requests chưa được cài đặt."}

    try:
        with img.open("rb") as img_fh, aud.open("rb") as aud_fh:
            files = {
                "image": (img.name, img_fh, _mime_image(img)),
                "audio": (aud.name, aud_fh, _mime_audio(aud)),
            }
            data = {
                "still": str(still).lower(),
                "preprocess": preprocess,
                "enhancer": enhancer,
            }
            resp = requests.post(
                f"{server_url.rstrip('/')}/api/generate",
                files=files,
                data=data,
                timeout=300,
            )
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": f"Không thể kết nối đến máy chủ SadTalker API tại {server_url}.",
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Hết thời gian chờ phản hồi từ máy chủ SadTalker (timeout 300s).",
        }
    except requests.exceptions.RequestException as exc:
        return {"success": False, "error": f"Lỗi kết nối API: {exc}"}

    if resp.status_code != 200:
        return {
            "success": False,
            "error": f"Máy chủ API trả về lỗi HTTP {resp.status_code}: {resp.text[:300]}",
        }

    video_bytes = resp.content
    if not video_bytes:
        return {"success": False, "error": "Máy chủ API trả về video rỗng."}

    try:
        out.write_bytes(video_bytes)
    except OSError as exc:
        return {"success": False, "error": f"Không thể ghi file video: {exc}"}

    return {"success": True, "output_path": str(out.resolve()), "method": "api"}


# ---------------------------------------------------------------------------
# Internal: subprocess
# ---------------------------------------------------------------------------


def _run_subprocess(
    sadtalker_dir: Path,
    img: Path,
    aud: Path,
    out: Path,
    still: bool,
    preprocess: str,
    enhancer: str,
) -> dict[str, Any]:
    """Run SadTalker's inference.py as a subprocess."""
    inference_script = sadtalker_dir / "inference.py"
    if not inference_script.exists():
        return {
            "success": False,
            "error": f"Không tìm thấy inference.py trong {sadtalker_dir}.",
        }

    # SadTalker writes results to a result dir; we move the output afterwards
    with tempfile.TemporaryDirectory() as tmp_dir:
        cmd = [
            sys.executable,
            str(inference_script),
            "--driven_audio", str(aud),
            "--source_image", str(img),
            "--result_dir", tmp_dir,
            "--preprocess", preprocess,
        ]
        if still:
            cmd.append("--still")
        if enhancer:
            cmd += ["--enhancer", enhancer]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(sadtalker_dir),
                capture_output=True,
                text=True,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "SadTalker vượt quá thời gian cho phép (600s). "
                         "Thử với ảnh / âm thanh ngắn hơn.",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Không thể chạy Python tại {sys.executable}.",
            }

        if proc.returncode != 0:
            stderr_snippet = (proc.stderr or "")[-800:]
            return {
                "success": False,
                "error": f"SadTalker kết thúc với mã lỗi {proc.returncode}.\n{stderr_snippet}",
            }

        # Locate the generated video file
        tmp_path = Path(tmp_dir)
        mp4_files = sorted(tmp_path.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
        if not mp4_files:
            return {
                "success": False,
                "error": "SadTalker hoàn thành nhưng không tìm thấy file video đầu ra.",
            }

        generated = mp4_files[-1]
        try:
            import shutil
            shutil.copy2(str(generated), str(out))
        except OSError as exc:
            return {"success": False, "error": f"Không thể sao chép file video: {exc}"}

    return {"success": True, "output_path": str(out.resolve()), "method": "subprocess"}


# ---------------------------------------------------------------------------
# Internal: helpers
# ---------------------------------------------------------------------------


def _resolve_sadtalker_dir(sadtalker_dir: str | None) -> Path | dict[str, Any]:
    """
    Return a resolved Path to the SadTalker directory, or an error dict.
    """
    if sadtalker_dir:
        p = Path(sadtalker_dir)
        if not p.exists():
            return {"success": False, "error": f"Thư mục SadTalker không tồn tại: {sadtalker_dir}"}
        return p

    try:
        from shared.platform import get_sadtalker_path
        return Path(get_sadtalker_path())
    except ValueError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        return {"success": False, "error": f"Không thể lấy đường dẫn SadTalker: {exc}"}


def _mime_image(path: Path) -> str:
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(
        path.suffix.lower(), "image/jpeg"
    )


def _mime_audio(path: Path) -> str:
    return {".wav": "audio/wav", ".mp3": "audio/mpeg"}.get(
        path.suffix.lower(), "audio/wav"
    )
