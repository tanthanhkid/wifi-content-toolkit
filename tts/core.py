"""
core.py — Pure business logic for wfm-tts.

All functions are side-effect-free with respect to global state.
Network calls go to the VietTTS server (default http://localhost:8298).
Error messages are written in Vietnamese.
"""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def text_to_speech(
    text: str,
    output_path: str,
    server_url: str = "http://localhost:8298",
    voice: str = "cdteam",
    speed: float = 1.0,
) -> dict[str, Any]:
    """
    Synthesise *text* to speech and save the result as a WAV file.

    Calls ``POST {server_url}/v1/audio/speech`` with a JSON body and writes
    the raw audio bytes to *output_path*.

    Parameters
    ----------
    text:
        Vietnamese (or any supported) text to synthesise.
    output_path:
        Destination path for the WAV file.  Parent directories are created
        automatically.
    server_url:
        Base URL of the running VietTTS server.
    voice:
        Voice identifier recognised by the server (e.g. ``"cdteam"``).
    speed:
        Playback speed multiplier (1.0 = normal).

    Returns
    -------
    dict with keys:
        ``success`` (bool), ``output_path`` (str), ``duration_seconds`` (float),
        ``voice`` (str), ``speed`` (float), ``error`` (str, only on failure).
    """
    import requests

    if not text or not text.strip():
        return {"success": False, "error": "Văn bản đầu vào không được để trống."}

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "input": text.strip(),
        "voice": voice,
        "speed": speed,
        "response_format": "wav",
    }

    try:
        resp = requests.post(
            f"{server_url.rstrip('/')}/v1/audio/speech",
            json=payload,
            timeout=120,
        )
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": f"Không thể kết nối đến máy chủ VietTTS tại {server_url}. "
                     "Hãy chắc chắn máy chủ đang chạy.",
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Hết thời gian chờ phản hồi từ máy chủ VietTTS (timeout 120s).",
        }
    except requests.exceptions.RequestException as exc:
        return {"success": False, "error": f"Lỗi kết nối: {exc}"}

    if resp.status_code != 200:
        return {
            "success": False,
            "error": f"Máy chủ VietTTS trả về lỗi HTTP {resp.status_code}: {resp.text[:300]}",
        }

    audio_bytes = resp.content
    if not audio_bytes:
        return {"success": False, "error": "Máy chủ trả về dữ liệu âm thanh rỗng."}

    try:
        out.write_bytes(audio_bytes)
    except OSError as exc:
        return {"success": False, "error": f"Không thể ghi file âm thanh: {exc}"}

    duration = _get_wav_duration(str(out))

    return {
        "success": True,
        "output_path": str(out.resolve()),
        "duration_seconds": duration,
        "voice": voice,
        "speed": speed,
    }


def clone_and_speak(
    text: str,
    output_path: str,
    reference_audio: str,
    server_url: str = "http://localhost:8298",
) -> dict[str, Any]:
    """
    Synthesise *text* using the timbre of *reference_audio* (voice cloning).

    Calls ``POST {server_url}/v1/tts`` as a multipart/form-data request with
    the text field and the reference audio file.

    Parameters
    ----------
    text:
        Text to synthesise.
    output_path:
        Destination path for the output WAV file.
    reference_audio:
        Path to a WAV or MP3 file whose voice timbre should be cloned.
    server_url:
        Base URL of the running VietTTS server.

    Returns
    -------
    dict with keys:
        ``success`` (bool), ``output_path`` (str), ``duration_seconds`` (float),
        ``reference_audio`` (str), ``error`` (str, only on failure).
    """
    import requests

    if not text or not text.strip():
        return {"success": False, "error": "Văn bản đầu vào không được để trống."}

    ref = Path(reference_audio)
    if not ref.exists():
        return {
            "success": False,
            "error": f"File âm thanh tham chiếu không tồn tại: {reference_audio}",
        }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        with ref.open("rb") as audio_fh:
            resp = requests.post(
                f"{server_url.rstrip('/')}/v1/tts",
                data={"text": text.strip()},
                files={"audio_file": (ref.name, audio_fh, _mime_for(ref))},
                timeout=180,
            )
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": f"Không thể kết nối đến máy chủ VietTTS tại {server_url}.",
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Hết thời gian chờ phản hồi từ máy chủ VietTTS (timeout 180s).",
        }
    except requests.exceptions.RequestException as exc:
        return {"success": False, "error": f"Lỗi kết nối: {exc}"}

    if resp.status_code != 200:
        return {
            "success": False,
            "error": f"Máy chủ VietTTS trả về lỗi HTTP {resp.status_code}: {resp.text[:300]}",
        }

    audio_bytes = resp.content
    if not audio_bytes:
        return {"success": False, "error": "Máy chủ trả về dữ liệu âm thanh rỗng."}

    try:
        out.write_bytes(audio_bytes)
    except OSError as exc:
        return {"success": False, "error": f"Không thể ghi file âm thanh: {exc}"}

    duration = _get_wav_duration(str(out))

    return {
        "success": True,
        "output_path": str(out.resolve()),
        "duration_seconds": duration,
        "reference_audio": str(ref.resolve()),
    }


def list_voices(server_url: str = "http://localhost:8298") -> list[str]:
    """
    Retrieve the list of voice identifiers from the VietTTS server.

    Calls ``GET {server_url}/v1/voices``.

    Returns
    -------
    list of str
        Voice identifiers.  Returns an empty list on error so callers can
        degrade gracefully.
    """
    import requests

    try:
        resp = requests.get(
            f"{server_url.rstrip('/')}/v1/voices",
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            # Accept both {"voices": [...]} and a plain list
            if isinstance(data, list):
                return [str(v) for v in data]
            if isinstance(data, dict):
                voices = data.get("voices") or data.get("data") or []
                return [str(v) for v in voices]
        return []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_wav_duration(path: str) -> float:
    """
    Return the duration in seconds of the WAV file at *path*.

    Returns 0.0 if the file cannot be read or is not a valid WAV.
    """
    try:
        with wave.open(path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return frames / rate
        return 0.0
    except Exception:
        return 0.0


def _mime_for(path: Path) -> str:
    """Return a suitable MIME type for the audio file."""
    suffix = path.suffix.lower()
    return {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }.get(suffix, "audio/wav")
