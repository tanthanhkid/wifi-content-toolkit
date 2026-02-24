"""
cli.py — Click-based command-line interface for wfm-talkhead.

All progress, logs, and status messages are written to stderr via Rich.
Stdout receives only the output file path (plain mode) or a JSON object
(when --json flag is provided).

Commands
--------
create  — Generate a talking-head video from an image and audio file.
ui      — Launch the Gradio web UI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

err_console = Console(stderr=True, highlight=False)

_DEFAULT_SERVER = "http://localhost:8299"

JSON_FLAG = click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Xuất kết quả JSON ra stdout thay vì đường dẫn đơn thuần.",
)

SERVER_URL_OPTION = click.option(
    "--server-url",
    default=_DEFAULT_SERVER,
    show_default=True,
    envvar="SADTALKER_URL",
    help="URL của máy chủ SadTalker API. Cũng đọc từ SADTALKER_URL.",
)


def _emit_result(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("success"):
            click.echo(result["output_path"])
        else:
            click.echo(f"ERROR: {result.get('error', 'Lỗi không xác định')}", err=False)


def _exit_code(result: dict[str, Any]) -> int:
    return 0 if result.get("success") else 1


# ---------------------------------------------------------------------------
# Main group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(package_name="wfm-talkhead")
def main() -> None:
    """WiFi Marketing Talking Head — tạo video đầu người nói từ ảnh và âm thanh."""


# ---------------------------------------------------------------------------
# create command
# ---------------------------------------------------------------------------


_PREPROCESS_CHOICES = click.Choice(["crop", "resize", "full"], case_sensitive=False)
_ENHANCER_CHOICES = click.Choice(["gfpgan", "RestoreFormer", "none"], case_sensitive=False)


@main.command("create")
@click.argument("image", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("audio", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--still/--no-still", default=True, show_default=True,
              help="Giảm thiểu chuyển động đầu (khuyến nghị cho talking-head).")
@click.option("--preprocess", type=_PREPROCESS_CHOICES, default="full", show_default=True,
              help="Chế độ tiền xử lý ảnh: crop / resize / full.")
@click.option("--enhancer", type=_ENHANCER_CHOICES, default="gfpgan", show_default=True,
              help="Bộ tăng cường khuôn mặt: gfpgan / RestoreFormer / none.")
@click.option("--output", "-o", required=True,
              help="Đường dẫn file MP4 đầu ra.")
@click.option("--sadtalker-dir", default=None, envvar="SADTALKER_DIR",
              help="Thư mục chứa SadTalker (có inference.py). "
                   "Mặc định đọc từ cấu hình wfm-setup hoặc biến SADTALKER_DIR.")
@JSON_FLAG
@SERVER_URL_OPTION
def create_cmd(
    image: Path,
    audio: Path,
    still: bool,
    preprocess: str,
    enhancer: str,
    output: str,
    sadtalker_dir: str | None,
    as_json: bool,
    server_url: str,
) -> None:
    """Tạo video talking-head từ ảnh IMAGE và file âm thanh AUDIO.

    \b
    Ví dụ:
        talkhead create portrait.jpg speech.wav -o output/talking.mp4
        talkhead create portrait.png speech.wav --no-still --enhancer RestoreFormer -o output/v.mp4
    """
    from talkhead.core import generate_talking_head

    enh_val = "" if enhancer == "none" else enhancer

    err_console.print(Panel(
        f"[bold cyan]Ảnh:[/bold cyan] [yellow]{image}[/yellow]\n"
        f"[bold cyan]Âm thanh:[/bold cyan] [yellow]{audio}[/yellow]\n"
        f"[bold cyan]Đứng yên:[/bold cyan] {'Có' if still else 'Không'}  "
        f"[bold cyan]Tiền xử lý:[/bold cyan] {preprocess}  "
        f"[bold cyan]Tăng cường:[/bold cyan] {enh_val or 'Không'}\n"
        f"[bold cyan]Máy chủ API:[/bold cyan] {server_url}\n"
        f"[bold cyan]Đầu ra:[/bold cyan] [green]{output}[/green]",
        title="[bold]wfm-talkhead create[/bold]",
        border_style="blue",
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=err_console,
        transient=True,
    ) as progress:
        progress.add_task("Đang tạo video talking-head (có thể mất vài phút)...", total=None)
        result = generate_talking_head(
            image_path=str(image),
            audio_path=str(audio),
            output_path=output,
            still=still,
            preprocess=preprocess,
            enhancer=enh_val,
            sadtalker_dir=sadtalker_dir,
            server_url=server_url,
        )

    if result["success"]:
        method = result.get("method", "?")
        err_console.print(
            f"[bold green]✓ Hoàn thành[/bold green] (phương thức: [cyan]{method}[/cyan]): "
            f"{result['output_path']}"
        )
    else:
        err_console.print(f"[bold red]✗ Lỗi:[/bold red] {result.get('error')}")

    _emit_result(result, as_json)
    sys.exit(_exit_code(result))


# ---------------------------------------------------------------------------
# ui command
# ---------------------------------------------------------------------------


@main.command("ui")
@click.option("--port", default=7863, show_default=True, type=int,
              help="Cổng cho Gradio UI.")
@click.option("--host", default="0.0.0.0", show_default=True,
              help="Địa chỉ host lắng nghe.")
@click.option("--share", is_flag=True, default=False,
              help="Tạo link public qua Gradio share.")
@SERVER_URL_OPTION
def ui_cmd(port: int, host: str, share: bool, server_url: str) -> None:
    """Khởi động giao diện web Gradio cho wfm-talkhead."""
    from talkhead.ui import build_ui

    err_console.print(Panel(
        f"[bold cyan]Host:[/bold cyan] {host}\n"
        f"[bold cyan]Port:[/bold cyan] {port}\n"
        f"[bold cyan]Máy chủ SadTalker:[/bold cyan] {server_url}\n"
        f"[bold cyan]Share:[/bold cyan] {'Có' if share else 'Không'}",
        title="[bold]wfm-talkhead UI[/bold]",
        border_style="blue",
    ))

    app = build_ui(server_url=server_url)
    app.launch(
        server_name=host,
        server_port=port,
        share=share,
        show_api=True,
    )
