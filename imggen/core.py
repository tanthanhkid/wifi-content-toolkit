"""
core.py — Pure business logic for WiFi Marketing Image Generation.

No CLI or UI imports. All public functions return structured dicts so that
both the CLI and the Gradio UI can consume them uniformly.

Return dict schema
------------------
Success::

    {
        "success": True,
        "output_path": "/absolute/path/to/image.png",
        "prompt": "<prompt used>",
        "model": "<model id>",
        "template_id": "<id or None>",
    }

Failure::

    {
        "success": False,
        "error": "<Vietnamese error message>",
        "output_path": None,
        "prompt": "<prompt used or None>",
        "model": "<model id>",
        "template_id": "<id or None>",
    }
"""

from __future__ import annotations

import time
import os
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "gemini-2.0-flash-exp-image-generation"
DEFAULT_ASPECT_RATIO = "9:16"
DEFAULT_BATCH_DELAY = 6.0  # seconds between requests to respect rate limits


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_parent(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _save_image_bytes(image_bytes: bytes, output_path: Path) -> None:
    """Write raw image bytes to disk, converting to PNG via Pillow if needed."""
    from PIL import Image
    import io

    img = Image.open(io.BytesIO(image_bytes))
    # Ensure PNG output regardless of source format
    if output_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        output_path = output_path.with_suffix(".png")
    img.save(str(output_path))


def _call_gemini(
    prompt: str,
    output_path: Path,
    api_key: str,
    model: str,
) -> bytes:
    """
    Call the Gemini API and return raw image bytes.

    Raises RuntimeError (with a Vietnamese message) on any failure.
    """
    try:
        from google import genai  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Không thể import thư viện google-genai. "
            "Vui lòng cài đặt: pip install google-genai>=1.0.0"
        ) from exc

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            ),
        )
    except Exception as exc:
        raise RuntimeError(
            f"Lỗi khi gọi Gemini API: {exc}"
        ) from exc

    # Extract first image part
    try:
        candidates = response.candidates
        if not candidates:
            raise RuntimeError("Gemini API không trả về kết quả nào (candidates rỗng).")

        parts = candidates[0].content.parts
        for part in parts:
            if part.inline_data is not None:
                return part.inline_data.data

        raise RuntimeError(
            "Gemini API không trả về dữ liệu hình ảnh. "
            "Kiểm tra lại model và cấu hình response_modalities."
        )
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Lỗi khi xử lý phản hồi từ Gemini API: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_image(
    prompt: str,
    output_path: str | Path,
    api_key: str,
    model: str = DEFAULT_MODEL,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
) -> dict[str, Any]:
    """
    Generate a single image from a free-form prompt using Gemini.

    Parameters
    ----------
    prompt:
        The full image generation prompt.
    output_path:
        Destination file path (PNG recommended). Parent directories are created
        automatically.
    api_key:
        Google Gemini API key.
    model:
        Gemini model ID supporting image generation.
    aspect_ratio:
        Informational; the prompt should already specify canvas dimensions.

    Returns
    -------
    dict
        Structured result dict (see module docstring).
    """
    output_path = _ensure_parent(output_path)

    result: dict[str, Any] = {
        "success": False,
        "output_path": None,
        "prompt": prompt,
        "model": model,
        "template_id": None,
    }

    try:
        image_bytes = _call_gemini(prompt, output_path, api_key, model)
        _save_image_bytes(image_bytes, output_path)
        result["success"] = True
        result["output_path"] = str(output_path.resolve())
    except RuntimeError as exc:
        result["error"] = str(exc)
    except Exception as exc:
        result["error"] = f"Lỗi không xác định: {exc}"

    return result


def generate_from_template(
    template_id: str,
    fields: dict[str, Any],
    output_path: str | Path,
    api_key: str,
    brand: dict[str, Any] | None = None,
    model: str = DEFAULT_MODEL,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
) -> dict[str, Any]:
    """
    Generate an image using a named marketing template.

    Parameters
    ----------
    template_id:
        One of: ``quote``, ``carousel``, ``before_after``, ``promo``, ``case_study``.
    fields:
        Dict of field key -> value(s) matching the template's field definitions.
    output_path:
        Destination file path.
    api_key:
        Google Gemini API key.
    brand:
        Optional brand configuration (name, primary_color, secondary_color, font, logo_url).
    model:
        Gemini model ID.
    aspect_ratio:
        Aspect ratio hint.

    Returns
    -------
    dict
        Structured result dict (see module docstring).
    """
    from imggen.templates import get_template

    result: dict[str, Any] = {
        "success": False,
        "output_path": None,
        "prompt": None,
        "model": model,
        "template_id": template_id,
    }

    try:
        template = get_template(template_id)
    except KeyError as exc:
        result["error"] = str(exc)
        return result

    try:
        prompt = template.build_prompt(fields, brand=brand)
    except Exception as exc:
        result["error"] = f"Lỗi khi tạo prompt từ template '{template_id}': {exc}"
        return result

    result["prompt"] = prompt
    inner = generate_image(
        prompt=prompt,
        output_path=output_path,
        api_key=api_key,
        model=model,
        aspect_ratio=aspect_ratio,
    )
    # Merge inner result but keep template_id
    result.update(inner)
    result["template_id"] = template_id
    return result


def batch_generate(
    items: list[dict[str, Any]],
    output_dir: str | Path,
    api_key: str,
    delay: float = DEFAULT_BATCH_DELAY,
) -> list[dict[str, Any]]:
    """
    Generate multiple images in sequence with a configurable delay between requests.

    Each item in ``items`` must be a dict with the following keys:

    * ``filename`` (str) — output filename (relative to ``output_dir``).
    * ``prompt`` (str, optional) — free-form prompt (used when ``template_id`` is absent).
    * ``template_id`` (str, optional) — template to use instead of a raw prompt.
    * ``fields`` (dict, optional) — template field values (required when ``template_id`` set).
    * ``brand`` (dict, optional) — brand configuration for template rendering.
    * ``model`` (str, optional) — override model for this item only.

    Parameters
    ----------
    items:
        List of generation item dicts.
    output_dir:
        Directory where all output images will be saved.
    api_key:
        Google Gemini API key.
    delay:
        Seconds to wait between consecutive API calls (default 6.0).

    Returns
    -------
    list[dict]
        List of result dicts, one per input item, in the same order.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []

    for idx, item in enumerate(items):
        filename = item.get("filename")
        if not filename:
            results.append(
                {
                    "success": False,
                    "error": f"Mục #{idx + 1} thiếu trường 'filename'.",
                    "output_path": None,
                    "prompt": None,
                    "model": item.get("model", DEFAULT_MODEL),
                    "template_id": item.get("template_id"),
                    "index": idx,
                }
            )
            continue

        output_path = output_dir / filename
        model = item.get("model", DEFAULT_MODEL)
        template_id = item.get("template_id")

        if template_id:
            res = generate_from_template(
                template_id=template_id,
                fields=item.get("fields", {}),
                output_path=output_path,
                api_key=api_key,
                brand=item.get("brand"),
                model=model,
            )
        else:
            prompt = item.get("prompt", "")
            if not prompt:
                res = {
                    "success": False,
                    "error": f"Mục #{idx + 1} không có 'prompt' hoặc 'template_id'.",
                    "output_path": None,
                    "prompt": None,
                    "model": model,
                    "template_id": None,
                }
            else:
                res = generate_image(
                    prompt=prompt,
                    output_path=output_path,
                    api_key=api_key,
                    model=model,
                )

        res["index"] = idx
        results.append(res)

        # Delay between requests (skip after last item)
        if idx < len(items) - 1 and delay > 0:
            time.sleep(delay)

    return results
