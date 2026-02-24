"""
cli.py — Click-based command-line interface for wfm-tts.

All progress, logs, and status messages are written to stderr via Rich.
Stdout receives only the output file path (plain mode) or a JSON object
(when --json flag is provided).

Commands
--------
create  — Synthesise text to speech using a named voice.
clone   — Clone a reference voice and speak the provided text.
voices  — List available voices from the VietTTS server.
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

# Stderr-only console – all progress / log messages go here
err_console = Console(stderr=True, highlight=False)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_DEFAULT_SERVER = "http://localhost:8298"

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
    envvar="VIETTTS_URL",
    help="URL của máy chủ VietTTS. Cũng đọc từ biến môi trường VIETTTS_URL.",
)


def _emit_result(result: dict[str, Any], as_json: bool) -> None:
    """Write the final result to stdout."""
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
@click.version_option(package_name="wfm-tts")
def main() -> None:
    """WiFi Marketing TTS — chuyển văn bản thành giọng nói bằng VietTTS."""


# ---------------------------------------------------------------------------
# create command
# ---------------------------------------------------------------------------


@main.command("create")
@click.argument("text", required=False, default=None)
@click.option("--voice", "-v", default="cdteam", show_default=True,
              help="Tên giọng đọc (ví dụ: cdteam, banmai).")
@click.option("--speed", "-s", default=1.0, show_default=True, type=float,
              help="Tốc độ đọc (1.0 = bình thường, 0.5 = chậm, 2.0 = nhanh).")
@click.option("--file", "-f", "text_file",
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              default=None,
              help="Đọc văn bản từ file thay vì tham số TEXT.")
@click.option("--output", "-o", required=True,
              help="Đường dẫn file WAV đầu ra (ví dụ: output/speech.wav).")
@JSON_FLAG
@SERVER_URL_OPTION
def create_cmd(
    text: str | None,
    voice: str,
    speed: float,
    text_file: Path | None,
    output: str,
    as_json: bool,
    server_url: str,
) -> None:
    """Chuyển TEXT thành giọng nói và lưu thành file WAV.

    \b
    Ví dụ:
        tts create "Xin chào, đây là thông báo từ WiFi Smart." -o output/hello.wav
        tts create --file script.txt --voice banmai -o output/speech.wav
    """
    from tts.core import text_to_speech

    # Resolve input text
    if text_file is not None:
        try:
            resolved_text = text_file.read_text(encoding="utf-8")
        except OSError as exc:
            err_console.print(f"[bold red]✗ Không thể đọc file:[/bold red] {exc}")
            sys.exit(1)
    elif text:
        resolved_text = text
    else:
        err_console.print("[bold red]✗ Phải cung cấp TEXT hoặc --file.[/bold red]")
        sys.exit(1)

    err_console.print(Panel(
        f"[bold cyan]Giọng:[/bold cyan] [yellow]{voice}[/yellow]   "
        f"[bold cyan]Tốc độ:[/bold cyan] [yellow]{speed}x[/yellow]\n"
        f"[bold cyan]Máy chủ:[/bold cyan] {server_url}\n"
        f"[bold cyan]Đầu ra:[/bold cyan] [green]{output}[/green]\n"
        f"[bold cyan]Văn bản:[/bold cyan] {resolved_text[:80]}{'…' if len(resolved_text) > 80 else ''}",
        title="[bold]wfm-tts create[/bold]",
        border_style="blue",
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=err_console,
        transient=True,
    ) as progress:
        progress.add_task("Đang tổng hợp giọng nói...", total=None)
        result = text_to_speech(
            text=resolved_text,
            output_path=output,
            server_url=server_url,
            voice=voice,
            speed=speed,
        )

    if result["success"]:
        dur = result.get("duration_seconds", 0.0)
        err_console.print(
            f"[bold green]✓ Hoàn thành:[/bold green] {result['output_path']}  "
            f"([cyan]{dur:.2f}s[/cyan])"
        )
    else:
        err_console.print(f"[bold red]✗ Lỗi:[/bold red] {result.get('error')}")

    _emit_result(result, as_json)
    sys.exit(_exit_code(result))


# ---------------------------------------------------------------------------
# clone command
# ---------------------------------------------------------------------------


@main.command("clone")
@click.argument("text")
@click.option("--reference", "-r", "reference_audio",
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              required=True,
              help="File âm thanh tham chiếu để nhân bản giọng nói (WAV/MP3).")
@click.option("--output", "-o", required=True,
              help="Đường dẫn file WAV đầu ra.")
@JSON_FLAG
@SERVER_URL_OPTION
def clone_cmd(
    text: str,
    reference_audio: Path,
    output: str,
    as_json: bool,
    server_url: str,
) -> None:
    """Nhân bản giọng nói từ file tham chiếu và đọc TEXT.

    \b
    Ví dụ:
        tts clone "Giới thiệu sản phẩm WiFi Smart 6." --reference sample.wav -o output/cloned.wav
    """
    from tts.core import clone_and_speak

    err_console.print(Panel(
        f"[bold cyan]Giọng tham chiếu:[/bold cyan] [yellow]{reference_audio}[/yellow]\n"
        f"[bold cyan]Máy chủ:[/bold cyan] {server_url}\n"
        f"[bold cyan]Đầu ra:[/bold cyan] [green]{output}[/green]\n"
        f"[bold cyan]Văn bản:[/bold cyan] {text[:80]}{'…' if len(text) > 80 else ''}",
        title="[bold]wfm-tts clone[/bold]",
        border_style="blue",
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=err_console,
        transient=True,
    ) as progress:
        progress.add_task("Đang nhân bản giọng nói...", total=None)
        result = clone_and_speak(
            text=text,
            output_path=output,
            reference_audio=str(reference_audio),
            server_url=server_url,
        )

    if result["success"]:
        dur = result.get("duration_seconds", 0.0)
        err_console.print(
            f"[bold green]✓ Hoàn thành:[/bold green] {result['output_path']}  "
            f"([cyan]{dur:.2f}s[/cyan])"
        )
    else:
        err_console.print(f"[bold red]✗ Lỗi:[/bold red] {result.get('error')}")

    _emit_result(result, as_json)
    sys.exit(_exit_code(result))


# ---------------------------------------------------------------------------
# voices command
# ---------------------------------------------------------------------------


@main.command("voices")
@SERVER_URL_OPTION
@JSON_FLAG
def voices_cmd(server_url: str, as_json: bool) -> None:
    """Liệt kê các giọng đọc có sẵn trên máy chủ VietTTS.

    \b
    Ví dụ:
        tts voices
        tts voices --server-url http://192.168.1.10:8298
    """
    from tts.core import list_voices

    err_console.print(f"[dim]Đang kết nối đến {server_url}…[/dim]")

    voices = list_voices(server_url=server_url)

    if not voices:
        err_console.print(
            "[bold yellow]![/bold yellow] Không lấy được danh sách giọng đọc. "
            "Kiểm tra máy chủ VietTTS đang chạy."
        )
        if as_json:
            click.echo(json.dumps({"voices": [], "count": 0}, ensure_ascii=False, indent=2))
        sys.exit(1)

    table = Table(title=f"Giọng đọc VietTTS ({server_url})", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Giọng", style="cyan bold")

    for idx, v in enumerate(voices, start=1):
        table.add_row(str(idx), v)

    err_console.print(table)
    err_console.print(f"[dim]Tổng cộng: {len(voices)} giọng[/dim]")

    if as_json:
        click.echo(json.dumps({"voices": voices, "count": len(voices)}, ensure_ascii=False, indent=2))
    else:
        for v in voices:
            click.echo(v)


# ---------------------------------------------------------------------------
# ui command
# ---------------------------------------------------------------------------


@main.command("ui")
@click.option("--port", default=7862, show_default=True, type=int,
              help="Cổng cho Gradio UI.")
@click.option("--host", default="0.0.0.0", show_default=True,
              help="Địa chỉ host lắng nghe.")
@click.option("--share", is_flag=True, default=False,
              help="Tạo link public qua Gradio share.")
@SERVER_URL_OPTION
def ui_cmd(port: int, host: str, share: bool, server_url: str) -> None:
    """Khởi động giao diện web Gradio cho wfm-tts."""
    from tts.ui import build_ui

    err_console.print(Panel(
        f"[bold cyan]Host:[/bold cyan] {host}\n"
        f"[bold cyan]Port:[/bold cyan] {port}\n"
        f"[bold cyan]Máy chủ VietTTS:[/bold cyan] {server_url}\n"
        f"[bold cyan]Share:[/bold cyan] {'Có' if share else 'Không'}",
        title="[bold]wfm-tts UI[/bold]",
        border_style="blue",
    ))

    app = build_ui(server_url=server_url)
    app.launch(
        server_name=host,
        server_port=port,
        share=share,
        show_api=True,
    )
