"""
core.py — Pure rendering logic for the poster module.

Renders Jinja2 HTML templates and captures PNG screenshots via
headless Chromium (Playwright). No CLI or UI concerns here.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import async_playwright

# ---------------------------------------------------------------------------
# Template environment
# ---------------------------------------------------------------------------

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

# ---------------------------------------------------------------------------
# Playwright helpers
# ---------------------------------------------------------------------------


async def _screenshot(
    html_content: str,
    output_path: str | os.PathLike,
    width: int = 1080,
    height: int = 1920,
) -> None:
    """Render *html_content* in a headless browser and save a PNG screenshot."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.set_content(html_content, wait_until="networkidle")
        await page.screenshot(path=str(output_path), full_page=False)
        await browser.close()


def screenshot_sync(
    html_content: str,
    output_path: str | os.PathLike,
    width: int = 1080,
    height: int = 1920,
) -> None:
    """Synchronous wrapper around :func:`_screenshot`."""
    asyncio.run(_screenshot(html_content, output_path, width, height))


# ---------------------------------------------------------------------------
# Size helper
# ---------------------------------------------------------------------------


def _parse_size(size: str) -> tuple[int, int]:
    """Parse a ``'WxH'`` string and return ``(width, height)`` integers."""
    try:
        w, h = size.lower().split("x")
        return int(w), int(h)
    except (ValueError, AttributeError) as exc:
        raise ValueError(
            f"Invalid size format '{size}'. Expected 'WIDTHxHEIGHT', e.g. '1080x1920'."
        ) from exc


# ---------------------------------------------------------------------------
# Default brand values
# ---------------------------------------------------------------------------

_DEFAULT_BRAND = {
    "brand_name": "",
    "brand_primary_color": "#6C63FF",
    "brand_accent_color": "#FF6584",
    "brand_text_color": "#FFFFFF",
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_poster(
    template_id: str,
    fields: dict[str, Any],
    output_path: str | os.PathLike,
    brand: dict[str, Any] | None = None,
    size: str = "1080x1920",
) -> dict[str, Any]:
    """Render a single poster and save it as a PNG file.

    Parameters
    ----------
    template_id:
        Name of the Jinja2 template file (without the ``.html`` extension),
        e.g. ``"quote"``, ``"carousel"``, ``"before_after"``, ``"promo"``,
        ``"case_study"``.
    fields:
        Template-specific context variables (headline, subtext, slides, …).
    output_path:
        Destination path for the rendered PNG.
    brand:
        Optional brand overrides.  Missing keys fall back to :data:`_DEFAULT_BRAND`.
    size:
        Viewport size as ``'WIDTHxHEIGHT'``.  Defaults to ``'1080x1920'``.

    Returns
    -------
    dict
        ``{"status": "ok", "output_path": str, "template_id": str, "size": str}``
        or ``{"status": "error", "error": str, ...}`` on failure.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Merge brand defaults
    ctx: dict[str, Any] = {**_DEFAULT_BRAND}
    if brand:
        ctx.update(brand)
    ctx.update(fields)

    try:
        template = _jinja_env.get_template(f"{template_id}.html")
    except Exception as exc:
        return {
            "status": "error",
            "error": f"Template '{template_id}' not found: {exc}",
            "output_path": str(output_path),
            "template_id": template_id,
            "size": size,
        }

    try:
        html_content = template.render(**ctx)
    except Exception as exc:
        return {
            "status": "error",
            "error": f"Template render failed: {exc}",
            "output_path": str(output_path),
            "template_id": template_id,
            "size": size,
        }

    width, height = _parse_size(size)

    try:
        screenshot_sync(html_content, output_path, width=width, height=height)
    except Exception as exc:
        return {
            "status": "error",
            "error": f"Screenshot failed: {exc}",
            "output_path": str(output_path),
            "template_id": template_id,
            "size": size,
        }

    return {
        "status": "ok",
        "output_path": str(output_path),
        "template_id": template_id,
        "size": size,
    }


def batch_render(
    items: list[dict[str, Any]],
    output_dir: str | os.PathLike,
) -> list[dict[str, Any]]:
    """Render multiple posters in sequence.

    Parameters
    ----------
    items:
        Each item is a dict with keys:
        ``template_id``, ``fields``, ``filename``
        (output filename, e.g. ``"poster_01.png"``),
        and optionally ``brand`` and ``size``.
    output_dir:
        Directory where all rendered PNGs will be saved.

    Returns
    -------
    list[dict]
        One result dict per item (same shape as :func:`render_poster`).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for idx, item in enumerate(items):
        template_id = item.get("template_id", "quote")
        fields = item.get("fields", {})
        filename = item.get("filename") or f"poster_{idx + 1:03d}.png"
        brand = item.get("brand")
        size = item.get("size", "1080x1920")

        result = render_poster(
            template_id=template_id,
            fields=fields,
            output_path=output_dir / filename,
            brand=brand,
            size=size,
        )
        results.append(result)

    return results
