"""Config management: ~/.wfm/config.json"""

import json
import os
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".wfm"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "gemini_model": "gemini-2.0-flash-exp-image-generation",
    "brand": {
        "name": "WiFi Smart",
        "primary_color": "#1A56DB",
        "accent_color": "#FFD700",
    },
    "viettts_url": "http://localhost:8298",
    "sadtalker_dir": "",
    "default_output_dir": "./output",
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            saved = json.load(f)
        merged = {**DEFAULT_CONFIG, **saved}
        merged["brand"] = {**DEFAULT_CONFIG["brand"], **saved.get("brand", {})}
        return merged
    return dict(DEFAULT_CONFIG)


def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_api_key() -> str:
    key = os.environ.get("WFM_GEMINI_API_KEY", "")
    if key:
        return key
    cfg = load_config()
    key = cfg.get("gemini_api_key", "")
    if key:
        return key
    raise ValueError(
        "Chưa có Gemini API key.\n"
        "Cách fix: đặt biến môi trường WFM_GEMINI_API_KEY hoặc chạy `wfm-setup`."
    )


def setup_wizard():
    from rich.console import Console
    from rich.prompt import Prompt

    console = Console(stderr=True)
    console.print("\n[bold blue]WiFi Marketing Content Toolkit — Setup[/]\n")

    cfg = load_config()

    cfg["gemini_api_key"] = Prompt.ask(
        "Gemini API key", default=cfg.get("gemini_api_key", "") or None
    ) or ""
    cfg["brand"]["name"] = Prompt.ask(
        "Brand name", default=cfg["brand"]["name"]
    )
    cfg["brand"]["primary_color"] = Prompt.ask(
        "Primary color (hex)", default=cfg["brand"]["primary_color"]
    )
    cfg["viettts_url"] = Prompt.ask(
        "VietTTS server URL", default=cfg["viettts_url"]
    )
    cfg["sadtalker_dir"] = Prompt.ask(
        "SadTalker directory", default=cfg.get("sadtalker_dir", "")
    ) or ""

    save_config(cfg)
    console.print(f"\n[green]Đã lưu config tại {CONFIG_FILE}[/]\n")

    # Check tools
    from shared.platform import check_ffmpeg, check_viettts

    if check_ffmpeg():
        console.print("[green]✓[/] FFmpeg OK")
    else:
        console.print("[red]✗[/] FFmpeg chưa cài. Cần cài FFmpeg.")

    if check_viettts(cfg["viettts_url"]):
        console.print("[green]✓[/] VietTTS OK")
    else:
        console.print("[yellow]![/] VietTTS chưa chạy (cần cho module tts)")


def _setup_cli():
    import argparse

    parser = argparse.ArgumentParser(description="WiFi Marketing Toolkit — Setup")
    parser.parse_args()
    setup_wizard()
