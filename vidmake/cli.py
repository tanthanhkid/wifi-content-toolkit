"""
cli.py — Click-based command-line interface for wfm-vidmake.

All progress, logs, and status messages are written to stderr via Rich.
Stdout receives only the output file path (plain mode) or a JSON object
(when --json flag is provided).

Commands
--------
create  — Assemble a slideshow video from images (+ optional audio / PIP).
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
from rich.table import Table

err_console = Console(stderr=True, highlight=False)


JSON_FLAG = click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Xuất kết quả JSON ra stdout thay vì đường dẫn đơn thuần.",
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
@click.version_option(package_name="wfm-vidmake")
def main() -> None:
    """WiFi Marketing Video Maker — ghép ảnh thành video slideshow bằng FFmpeg."""


# ---------------------------------------------------------------------------
# create command
# ---------------------------------------------------------------------------


_TRANSITION_CHOICES = click.Choice(["fade", "none"], case_sensitive=False)
_SIZE_CHOICES = click.Choice(
    ["1080x1920", "1920x1080", "1080x1080", "720x1280", "1280x720"],
    case_sensitive=False,
)
_PIP_POSITION_CHOICES = click.Choice(
    ["top-left", "top-right", "bottom-left", "bottom-right", "center"],
    case_sensitive=False,
)


@main.command("create")
@click.argument(
    "images",
    nargs=-1,
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--audio", "-a", "audio_path",
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              default=None,
              help="File âm thanh (WAV / MP3). Nếu không có, video không có tiếng.")
@click.option("--duration-per-slide", "-d", "duration_per_slide",
              type=float, default=None,
              help="Thời gian hiển thị mỗi ảnh (giây). "
                   "Mặc định: tính từ thời lượng audio (nếu có) hoặc 3.0 giây.")
@click.option("--transition", "-t", type=_TRANSITION_CHOICES, default="fade", show_default=True,
              help="Hiệu ứng chuyển cảnh: fade (mờ dần) hoặc none (không hiệu ứng).")
@click.option("--transition-duration", type=float, default=0.5, show_default=True,
              help="Thời gian hiệu ứng chuyển cảnh (giây, chỉ áp dụng khi --transition fade).")
@click.option("--size", type=_SIZE_CHOICES, default="1080x1920", show_default=True,
              help="Kích thước video đầu ra (WxH).")
@click.option("--pip", "pip_video",
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              default=None,
              help="Video phủ lên góc màn hình (picture-in-picture).")
@click.option("--pip-position", type=_PIP_POSITION_CHOICES, default="bottom-right",
              show_default=True,
              help="Vị trí video PIP trên màn hình.")
@click.option("--pip-size", type=click.IntRange(5, 80), default=30, show_default=True,
              help="Chiều rộng video PIP theo % chiều rộng khung hình (5-80).")
@click.option("--output", "-o", required=True,
              help="Đường dẫn file MP4 đầu ra.")
@JSON_FLAG
def create_cmd(
    images: tuple[Path, ...],
    audio_path: Path | None,
    duration_per_slide: float | None,
    transition: str,
    transition_duration: float,
    size: str,
    pip_video: Path | None,
    pip_position: str,
    pip_size: int,
    output: str,
    as_json: bool,
) -> None:
    """Ghép danh sách IMAGES thành video slideshow.

    \b
    Ví dụ:
        vidmake create slide1.jpg slide2.jpg slide3.jpg --audio narration.wav -o output/video.mp4
        vidmake create *.jpg --audio bg.mp3 --transition fade --size 1920x1080 -o out.mp4
        vidmake create img1.png img2.png --pip talking.mp4 --pip-position bottom-right -o out.mp4
    """
    from vidmake.core import create_slideshow

    img_list = [str(p) for p in images]
    aud_str = str(audio_path) if audio_path else None
    pip_str = str(pip_video) if pip_video else None

    # -- Status panel --
    panel_lines = [
        f"[bold cyan]Số ảnh:[/bold cyan] [yellow]{len(img_list)}[/yellow]",
        f"[bold cyan]Âm thanh:[/bold cyan] {aud_str or '(không có)'}",
        f"[bold cyan]Thời gian/ảnh:[/bold cyan] {duration_per_slide or 'tự động'}s",
        f"[bold cyan]Chuyển cảnh:[/bold cyan] {transition} ({transition_duration}s)",
        f"[bold cyan]Kích thước:[/bold cyan] {size}",
    ]
    if pip_str:
        panel_lines.append(f"[bold cyan]PIP:[/bold cyan] {pip_str} ({pip_position}, {pip_size}%)")
    panel_lines.append(f"[bold cyan]Đầu ra:[/bold cyan] [green]{output}[/green]")

    err_console.print(Panel(
        "\n".join(panel_lines),
        title="[bold]wfm-vidmake create[/bold]",
        border_style="blue",
    ))

    # -- Progress --
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=err_console,
        transient=True,
    ) as progress:
        progress.add_task(
            f"Đang ghép {len(img_list)} ảnh thành video (FFmpeg)...",
            total=None,
        )
        result = create_slideshow(
            images=img_list,
            output_path=output,
            audio_path=aud_str,
            duration_per_slide=duration_per_slide,
            transition=transition,
            transition_duration=transition_duration,
            size=size,
            pip_video=pip_str,
            pip_position=pip_position,
            pip_size=pip_size,
        )

    if result["success"]:
        dur = result.get("duration_seconds", 0.0)
        enc = result.get("encoder", "?")
        err_console.print(
            f"[bold green]✓ Hoàn thành[/bold green] "
            f"([cyan]{dur:.1f}s[/cyan], encoder: [cyan]{enc}[/cyan]): "
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
@click.option("--port", default=7864, show_default=True, type=int,
              help="Cổng cho Gradio UI.")
@click.option("--host", default="0.0.0.0", show_default=True,
              help="Địa chỉ host lắng nghe.")
@click.option("--share", is_flag=True, default=False,
              help="Tạo link public qua Gradio share.")
def ui_cmd(port: int, host: str, share: bool) -> None:
    """Khởi động giao diện web Gradio cho wfm-vidmake."""
    from vidmake.ui import build_ui

    err_console.print(Panel(
        f"[bold cyan]Host:[/bold cyan] {host}\n"
        f"[bold cyan]Port:[/bold cyan] {port}\n"
        f"[bold cyan]Share:[/bold cyan] {'Có' if share else 'Không'}",
        title="[bold]wfm-vidmake UI[/bold]",
        border_style="blue",
    ))

    app = build_ui()
    app.launch(
        server_name=host,
        server_port=port,
        share=share,
        show_api=True,
    )
