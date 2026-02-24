"""Rich console logging — all modules use this."""

from rich.console import Console

err_console = Console(stderr=True)
out_console = Console()


def info(msg: str):
    err_console.print(f"[blue]ℹ[/] {msg}")


def success(msg: str):
    err_console.print(f"[green]✓[/] {msg}")


def warn(msg: str):
    err_console.print(f"[yellow]![/] {msg}")


def error(msg: str):
    err_console.print(f"[red]✗[/] {msg}")


def hint(msg: str):
    err_console.print(f"[dim]💡 {msg}[/]")
