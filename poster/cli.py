"""
cli.py — Click CLI for the poster module.

Entry point: ``poster`` (mapped via pyproject.toml).

Commands
--------
create  — Render a single poster from CLI arguments.
batch   — Render multiple posters from a JSON manifest file.
ui      — Launch the Gradio web UI on port 7861.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from .core import batch_render, render_poster

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_result(result: dict[str, Any]) -> None:
    """Pretty-print a single render result using Rich."""
    if result["status"] == "ok":
        console.print(
            f"[bold green]OK[/bold green]  {result['output_path']}  "
            f"([dim]{result['template_id']} · {result['size']}[/dim])"
        )
    else:
        console.print(
            f"[bold red]ERROR[/bold red]  {result.get('output_path', '?')}  "
            f"{result.get('error', 'Unknown error')}"
        )


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
def main() -> None:
    """wfm-poster — generate social-media poster images from templates."""


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


@main.command("create")
@click.option(
    "--template",
    "-t",
    default="quote",
    show_default=True,
    type=click.Choice(["quote", "carousel", "before_after", "promo", "case_study"]),
    help="Template to use.",
)
# ---- generic fields --------------------------------------------------------
@click.option("--headline", default="", help="Main headline text.")
@click.option("--subtext", default="", help="Secondary / supporting text.")
# ---- carousel --------------------------------------------------------------
@click.option(
    "--slides",
    multiple=True,
    metavar="TEXT",
    help="Slide texts (repeatable, for carousel template).",
)
# ---- before/after ----------------------------------------------------------
@click.option("--before-title", default="Trước", help="Before-section title.")
@click.option(
    "--before-points",
    multiple=True,
    metavar="TEXT",
    help="Before bullet points (repeatable).",
)
@click.option("--after-title", default="Sau", help="After-section title.")
@click.option(
    "--after-points",
    multiple=True,
    metavar="TEXT",
    help="After bullet points (repeatable).",
)
# ---- promo -----------------------------------------------------------------
@click.option("--offer", default="", help="Offer / discount text.")
@click.option(
    "--details",
    multiple=True,
    metavar="TEXT",
    help="Promo detail lines (repeatable).",
)
@click.option("--cta", default="", help="Call-to-action button label.")
@click.option("--urgency", default="", help="Urgency badge text (e.g. 'Chỉ hôm nay!').")
# ---- case study ------------------------------------------------------------
@click.option("--client", default="", help="Client name.")
@click.option("--duration", default="", help="Project duration.")
@click.option(
    "--metrics",
    multiple=True,
    metavar="LABEL:VALUE",
    help="Metric cards as 'Label:Value' (repeatable).",
)
@click.option("--testimonial", default="", help="Client testimonial quote.")
# ---- brand -----------------------------------------------------------------
@click.option("--brand-name", default="", help="Brand / company name.")
@click.option("--brand-primary", default="#6C63FF", help="Brand primary colour (hex).")
@click.option("--brand-accent", default="#FF6584", help="Brand accent colour (hex).")
# ---- output ----------------------------------------------------------------
@click.option(
    "--output",
    "-o",
    default="poster.png",
    show_default=True,
    help="Output PNG path.",
)
@click.option(
    "--size",
    default="1080x1920",
    show_default=True,
    help="Output size as WIDTHxHEIGHT.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Print result as JSON instead of human-readable output.",
)
def create(
    template: str,
    headline: str,
    subtext: str,
    slides: tuple[str, ...],
    before_title: str,
    before_points: tuple[str, ...],
    after_title: str,
    after_points: tuple[str, ...],
    offer: str,
    details: tuple[str, ...],
    cta: str,
    urgency: str,
    client: str,
    duration: str,
    metrics: tuple[str, ...],
    testimonial: str,
    brand_name: str,
    brand_primary: str,
    brand_accent: str,
    output: str,
    size: str,
    output_json: bool,
) -> None:
    """Render a single poster image."""

    # Parse metrics list
    parsed_metrics: list[dict[str, str]] = []
    for m in metrics:
        if ":" in m:
            label, _, value = m.partition(":")
            parsed_metrics.append({"label": label.strip(), "value": value.strip()})
        else:
            parsed_metrics.append({"label": m, "value": ""})

    fields: dict[str, Any] = {
        "headline": headline,
        "subtext": subtext,
        "slides": list(slides),
        "before_title": before_title,
        "before_points": list(before_points),
        "after_title": after_title,
        "after_points": list(after_points),
        "offer": offer,
        "details": list(details),
        "cta": cta,
        "urgency": urgency,
        "client": client,
        "duration": duration,
        "metrics": parsed_metrics,
        "testimonial": testimonial,
    }

    brand: dict[str, Any] = {
        "brand_name": brand_name,
        "brand_primary_color": brand_primary,
        "brand_accent_color": brand_accent,
    }

    result = render_poster(
        template_id=template,
        fields=fields,
        output_path=output,
        brand=brand,
        size=size,
    )

    if output_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_result(result)

    if result["status"] != "ok":
        sys.exit(1)


# ---------------------------------------------------------------------------
# batch
# ---------------------------------------------------------------------------


@main.command("batch")
@click.argument("manifest", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output-dir",
    "-d",
    default=".",
    show_default=True,
    help="Directory for rendered PNGs.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Print results as JSON.",
)
def batch(manifest: str, output_dir: str, output_json: bool) -> None:
    """Render multiple posters from a JSON MANIFEST file.

    The manifest must be a JSON array where each element has the keys:
    ``template_id``, ``fields``, ``filename`` (output filename),
    and optionally ``brand`` and ``size``.

    Example manifest:\n
    \b
    [
      {
        "template_id": "quote",
        "filename": "quote_01.png",
        "fields": {"headline": "Hello", "subtext": "World"}
      }
    ]
    """
    manifest_path = Path(manifest)
    try:
        items: list[dict[str, Any]] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        console.print(f"[red]Failed to parse manifest:[/red] {exc}")
        sys.exit(1)

    results = batch_render(items, output_dir=output_dir)

    if output_json:
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        table = Table(title="Batch Render Results", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Status", width=8)
        table.add_column("Template", width=12)
        table.add_column("Output Path")
        table.add_column("Error")

        for idx, res in enumerate(results, start=1):
            status_style = "green" if res["status"] == "ok" else "red"
            table.add_row(
                str(idx),
                f"[{status_style}]{res['status']}[/{status_style}]",
                res.get("template_id", ""),
                res.get("output_path", ""),
                res.get("error", ""),
            )

        console.print(table)

        errors = sum(1 for r in results if r["status"] != "ok")
        if errors:
            console.print(f"[red]{errors} error(s) encountered.[/red]")
            sys.exit(1)
        else:
            console.print(f"[green]All {len(results)} poster(s) rendered successfully.[/green]")


# ---------------------------------------------------------------------------
# ui
# ---------------------------------------------------------------------------


@main.command("ui")
@click.option("--port", default=7861, show_default=True, help="Port to listen on.")
@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind.")
@click.option("--share", is_flag=True, default=False, help="Create a public Gradio share link.")
def ui(port: int, host: str, share: bool) -> None:
    """Launch the Gradio web UI."""
    from .ui import build_ui

    app = build_ui()
    console.print(
        f"[bold cyan]wfm-poster UI[/bold cyan] starting on "
        f"[link=http://{host}:{port}]http://{host}:{port}[/link]"
    )
    app.launch(server_name=host, server_port=port, share=share, show_api=True)
