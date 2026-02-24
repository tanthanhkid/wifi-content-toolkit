"""
cli.py — Click-based command-line interface for wfm-imggen.

All progress, logs, and status messages are written to stderr via Rich.
Stdout receives only the output file path (plain mode) or a JSON object
(when --json flag is provided).

Commands
--------
create   — Generate an image from a free-form prompt.
template — Generate an image from a built-in marketing template.
batch    — Process a JSON batch file of generation requests.
ui       — Launch the Gradio web UI.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

# Stderr-only console (all progress / logs go here)
err_console = Console(stderr=True, highlight=False)

# ---------------------------------------------------------------------------
# Shared options / utilities
# ---------------------------------------------------------------------------

def _resolve_api_key(ctx, param, value):
    if value:
        return value
    try:
        from shared.config import get_api_key
        return get_api_key()
    except Exception:
        raise click.MissingParameter(param_hint="'--api-key' / '-k'", param_type="option")

API_KEY_OPTION = click.option(
    "--api-key",
    "-k",
    envvar="WFM_GEMINI_API_KEY",
    default=None,
    callback=_resolve_api_key,
    is_eager=False,
    expose_value=True,
    help="Gemini API key. Also from WFM_GEMINI_API_KEY env or ~/.wfm/config.json.",
)

MODEL_OPTION = click.option(
    "--model",
    "-m",
    default="gemini-2.0-flash-exp-image-generation",
    show_default=True,
    help="Gemini model ID to use for image generation.",
)

JSON_FLAG = click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Output structured JSON to stdout instead of plain text.",
)


def _emit_result(result: dict[str, Any], as_json: bool) -> None:
    """Write the final result to stdout."""
    if as_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("success"):
            click.echo(result["output_path"])
        else:
            # Still write error to stdout so scripts can detect it
            click.echo(f"ERROR: {result.get('error', 'Lỗi không xác định')}", err=False)


def _exit_code(result: dict[str, Any]) -> int:
    return 0 if result.get("success") else 1


# ---------------------------------------------------------------------------
# Main group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="wfm-imggen")
def main() -> None:
    """WiFi Marketing Image Generator — tạo hình ảnh marketing bằng Gemini AI."""


# ---------------------------------------------------------------------------
# create command
# ---------------------------------------------------------------------------

@main.command("create")
@click.argument("prompt")
@click.option(
    "--output", "-o",
    required=True,
    help="Đường dẫn file đầu ra (ví dụ: output/image.png).",
)
@API_KEY_OPTION
@MODEL_OPTION
@JSON_FLAG
def create_cmd(prompt: str, output: str, api_key: str, model: str, as_json: bool) -> None:
    """Generate an image from a free-form PROMPT.

    \b
    Example:
        imggen create "Hình ảnh WiFi marketing chuyên nghiệp" -o out/img.png
    """
    from imggen.core import generate_image

    err_console.print(Panel(
        f"[bold cyan]Generating image[/bold cyan]\n"
        f"Model: [yellow]{model}[/yellow]\n"
        f"Output: [green]{output}[/green]",
        title="[bold]wfm-imggen create[/bold]",
        border_style="blue",
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=err_console,
        transient=True,
    ) as progress:
        progress.add_task("Đang tạo hình ảnh với Gemini...", total=None)
        result = generate_image(
            prompt=prompt,
            output_path=output,
            api_key=api_key,
            model=model,
        )

    if result["success"]:
        err_console.print(f"[bold green]✓ Hoàn thành:[/bold green] {result['output_path']}")
    else:
        err_console.print(f"[bold red]✗ Lỗi:[/bold red] {result.get('error')}")

    _emit_result(result, as_json)
    sys.exit(_exit_code(result))


# ---------------------------------------------------------------------------
# template command
# ---------------------------------------------------------------------------

_TEMPLATE_CHOICES = click.Choice(
    ["quote", "carousel", "before_after", "promo", "case_study"],
    case_sensitive=False,
)


@main.command("template")
@click.option(
    "-t", "--template-id",
    type=_TEMPLATE_CHOICES,
    required=True,
    help="Template ID to use.",
)
@click.option("--output", "-o", required=True, help="Đường dẫn file đầu ra.")
@API_KEY_OPTION
@MODEL_OPTION
@JSON_FLAG
# --- shared fields ---
@click.option("--headline", default=None, help="Tiêu đề chính (quote, carousel, before_after, promo, case_study).")
@click.option("--subtext", default=None, help="Phụ đề (carousel).")
# quote
@click.option("--quote", default=None, help="Nội dung trích dẫn (quote).")
@click.option("--author", default=None, help="Tên tác giả (quote).")
@click.option("--context", default=None, help="Ngữ cảnh / phụ đề (quote).")
# carousel
@click.option("--slides", multiple=True, help="Các điểm nội dung slide (carousel). Có thể lặp lại nhiều lần.")
# before_after
@click.option("--before-title", default=None, help="Nhãn cột Trước (before_after).")
@click.option("--before-points", multiple=True, help="Điểm phần Trước (before_after). Lặp lại nhiều lần.")
@click.option("--after-title", default=None, help="Nhãn cột Sau (before_after).")
@click.option("--after-points", multiple=True, help="Điểm phần Sau (before_after). Lặp lại nhiều lần.")
# promo
@click.option("--offer", default=None, help="Nội dung ưu đãi nổi bật (promo).")
@click.option("--details", multiple=True, help="Chi tiết ưu đãi (promo). Lặp lại nhiều lần.")
@click.option("--cta", default=None, help="Văn bản nút kêu gọi hành động (promo, case_study).")
@click.option("--urgency", default=None, help="Thông điệp khẩn cấp / hạn chót (promo).")
# case_study
@click.option("--client", default=None, help="Tên khách hàng (case_study).")
@click.option("--duration", default=None, help="Thời gian chiến dịch (case_study).")
@click.option("--metrics", multiple=True, help="Chỉ số kết quả (case_study). Lặp lại nhiều lần.")
@click.option("--testimonial", default=None, help="Lời chứng thực của khách hàng (case_study).")
# brand
@click.option("--brand-name", default=None, help="Tên thương hiệu.")
@click.option("--brand-primary-color", default=None, help="Màu chủ đạo (ví dụ: #0055A4).")
@click.option("--brand-secondary-color", default=None, help="Màu phụ.")
@click.option("--brand-font", default=None, help="Font chữ thương hiệu.")
def template_cmd(
    template_id: str,
    output: str,
    api_key: str,
    model: str,
    as_json: bool,
    headline: str | None,
    subtext: str | None,
    quote: str | None,
    author: str | None,
    context: str | None,
    slides: tuple[str, ...],
    before_title: str | None,
    before_points: tuple[str, ...],
    after_title: str | None,
    after_points: tuple[str, ...],
    offer: str | None,
    details: tuple[str, ...],
    cta: str | None,
    urgency: str | None,
    client: str | None,
    duration: str | None,
    metrics: tuple[str, ...],
    testimonial: str | None,
    brand_name: str | None,
    brand_primary_color: str | None,
    brand_secondary_color: str | None,
    brand_font: str | None,
) -> None:
    """Generate an image from a built-in marketing template.

    \b
    Examples:
        imggen template -t quote --quote "Thành công đến từ sự kiên trì" --author "Khuyết danh" -o out/quote.png
        imggen template -t promo --headline "Flash Sale" --offer "Giảm 50%" --cta "Đặt ngay" -o out/promo.png
        imggen template -t carousel --headline "5 lợi ích WiFi" --slides "Tốc độ cao" --slides "Ổn định" -o out/slide.png
    """
    from imggen.core import generate_from_template

    # Build fields dict from options
    fields: dict[str, Any] = {}

    def _set(key: str, value: Any) -> None:
        if value is not None and value != ():
            fields[key] = value

    _set("headline", headline)
    _set("subtext", subtext)
    _set("quote", quote)
    _set("author", author)
    _set("context", context)
    _set("slides", list(slides) if slides else None)
    _set("before_title", before_title)
    _set("before_points", list(before_points) if before_points else None)
    _set("after_title", after_title)
    _set("after_points", list(after_points) if after_points else None)
    _set("offer", offer)
    _set("details", list(details) if details else None)
    _set("cta", cta)
    _set("urgency", urgency)
    _set("client", client)
    _set("duration", duration)
    _set("metrics", list(metrics) if metrics else None)
    _set("testimonial", testimonial)

    # Brand config
    brand: dict[str, Any] | None = None
    if any([brand_name, brand_primary_color, brand_secondary_color, brand_font]):
        brand = {}
        if brand_name:
            brand["name"] = brand_name
        if brand_primary_color:
            brand["primary_color"] = brand_primary_color
        if brand_secondary_color:
            brand["secondary_color"] = brand_secondary_color
        if brand_font:
            brand["font"] = brand_font

    err_console.print(Panel(
        f"[bold cyan]Template:[/bold cyan] [yellow]{template_id}[/yellow]\n"
        f"[bold cyan]Model:[/bold cyan] [yellow]{model}[/yellow]\n"
        f"[bold cyan]Output:[/bold cyan] [green]{output}[/green]",
        title="[bold]wfm-imggen template[/bold]",
        border_style="blue",
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=err_console,
        transient=True,
    ) as progress:
        progress.add_task(f"Đang tạo hình ảnh từ template '{template_id}'...", total=None)
        result = generate_from_template(
            template_id=template_id,
            fields=fields,
            output_path=output,
            api_key=api_key,
            brand=brand,
            model=model,
        )

    if result["success"]:
        err_console.print(f"[bold green]✓ Hoàn thành:[/bold green] {result['output_path']}")
    else:
        err_console.print(f"[bold red]✗ Lỗi:[/bold red] {result.get('error')}")

    _emit_result(result, as_json)
    sys.exit(_exit_code(result))


# ---------------------------------------------------------------------------
# batch command
# ---------------------------------------------------------------------------

@main.command("batch")
@click.argument("batch_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--output-dir", "-d",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Thư mục lưu các hình ảnh đầu ra.",
)
@API_KEY_OPTION
@MODEL_OPTION
@click.option(
    "--delay",
    default=6.0,
    show_default=True,
    type=float,
    help="Số giây chờ giữa các yêu cầu API (để tránh rate limit).",
)
@JSON_FLAG
def batch_cmd(
    batch_file: Path,
    output_dir: Path,
    api_key: str,
    model: str,
    delay: float,
    as_json: bool,
) -> None:
    """Process a JSON batch file and generate multiple images.

    \b
    BATCH_FILE must be a JSON array. Each element supports:
      {
        "filename": "output.png",
        "prompt": "Free-form prompt",          // OR use template fields below
        "template_id": "promo",                // optional
        "fields": { "headline": "...", ... },  // required if template_id set
        "brand": { "name": "...", ... },       // optional
        "model": "gemini-2.0-flash-..."        // optional override
      }

    \b
    Example:
        imggen batch requests.json -d ./output --delay 8
    """
    from imggen.core import batch_generate

    try:
        raw = json.loads(batch_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        err_console.print(f"[bold red]✗ Lỗi đọc file JSON:[/bold red] {exc}")
        sys.exit(1)

    if not isinstance(raw, list):
        err_console.print("[bold red]✗ Batch file phải là một JSON array.[/bold red]")
        sys.exit(1)

    # Apply default model to items that don't specify one
    for item in raw:
        item.setdefault("model", model)

    total = len(raw)
    err_console.print(Panel(
        f"[bold cyan]Batch file:[/bold cyan] {batch_file}\n"
        f"[bold cyan]Items:[/bold cyan] {total}\n"
        f"[bold cyan]Output dir:[/bold cyan] [green]{output_dir}[/green]\n"
        f"[bold cyan]Delay:[/bold cyan] {delay}s",
        title="[bold]wfm-imggen batch[/bold]",
        border_style="blue",
    ))

    results: list[dict[str, Any]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=err_console,
    ) as progress:
        task = progress.add_task(f"Đang xử lý 0/{total}...", total=total)

        for idx, item in enumerate(raw):
            fname = item.get("filename", f"item_{idx+1}.png")
            progress.update(task, description=f"[{idx+1}/{total}] {fname}")

            # batch_generate processes one at a time; call it for this item only
            # (so we can update progress per item)
            from imggen.core import batch_generate as _bg
            single = _bg([item], output_dir, api_key, delay=0.0)
            res = single[0]
            results.append(res)

            if res["success"]:
                err_console.print(
                    f"  [green]✓[/green] [{idx+1}/{total}] {res['output_path']}"
                )
            else:
                err_console.print(
                    f"  [red]✗[/red] [{idx+1}/{total}] {fname}: {res.get('error')}"
                )

            progress.advance(task)

            # Delay between requests (skip after last)
            if idx < total - 1 and delay > 0:
                import time
                time.sleep(delay)

    # Summary table
    success_count = sum(1 for r in results if r.get("success"))
    fail_count = total - success_count

    table = Table(title="Kết quả Batch", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("File", style="cyan")
    table.add_column("Trạng thái", justify="center")
    table.add_column("Ghi chú")

    for r in results:
        idx_str = str(r.get("index", "?") + 1)
        path = r.get("output_path") or raw[r.get("index", 0)].get("filename", "?")
        status = "[green]✓ OK[/green]" if r.get("success") else "[red]✗ Lỗi[/red]"
        note = r.get("error", "") if not r.get("success") else ""
        table.add_row(idx_str, str(path), status, note)

    err_console.print(table)
    err_console.print(
        f"\n[bold]Tổng kết:[/bold] {success_count} thành công, "
        f"[red]{fail_count} thất bại[/red] / {total} tổng cộng."
    )

    if as_json:
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if r.get("output_path"):
                click.echo(r["output_path"])

    sys.exit(0 if fail_count == 0 else 1)


# ---------------------------------------------------------------------------
# ui command
# ---------------------------------------------------------------------------

@main.command("ui")
@click.option("--port", default=7860, show_default=True, type=int, help="Cổng cho Gradio UI.")
@click.option("--host", default="0.0.0.0", show_default=True, help="Địa chỉ host lắng nghe.")
@click.option("--share", is_flag=True, default=False, help="Tạo link public qua Gradio share.")
@API_KEY_OPTION
def ui_cmd(port: int, host: str, share: bool, api_key: str) -> None:
    """Launch the Gradio web UI for image generation."""
    from imggen.ui import build_ui

    err_console.print(Panel(
        f"[bold cyan]Host:[/bold cyan] {host}\n"
        f"[bold cyan]Port:[/bold cyan] {port}\n"
        f"[bold cyan]Share:[/bold cyan] {'Yes' if share else 'No'}",
        title="[bold]wfm-imggen UI[/bold]",
        border_style="blue",
    ))

    app = build_ui(api_key=api_key)
    app.launch(
        server_name=host,
        server_port=port,
        share=share,
        show_api=True,
    )
