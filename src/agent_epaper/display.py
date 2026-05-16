from __future__ import annotations

import argparse
import json
import time
import urllib.request
from importlib import import_module
from pathlib import Path

from .model import DisplayState
from .storage import load_state


SCREEN_MODULES = {
    "lilygo_t5_47": ("lilygo_t5_47", 960, 540),
    "waveshare_4in2": ("epd4in2_V2", 400, 300),
    "waveshare_7in5": ("epd7in5_V2", 800, 480),
    "waveshare_7in5_hd": ("epd7in5_HD", 880, 528),
}


def fetch_state(url: str) -> DisplayState:
    with urllib.request.urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return DisplayState.from_dict(payload)


def image_from_state(state: DisplayState, width: int, height: int):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SystemExit("Pillow is required for real display output: python3 -m pip install pillow") from exc

    image = Image.new("1", (width, height), 255)
    draw = ImageDraw.Draw(image)
    font_big = load_font(ImageFont, 26 if width <= 400 else 30 if width <= 800 else 42)
    font = load_font(ImageFont, 16 if width <= 400 else 20 if width <= 800 else 26)
    font_small = load_font(ImageFont, 12 if width <= 400 else 16 if width <= 800 else 20)
    margin = 32
    task = state.task.to_dict()
    progress = max(0, min(100, int(task["progress"])))
    bar_w = width - margin * 2

    draw.rectangle((0, 0, width - 1, height - 1), outline=0)
    draw.text((margin, 28), "Agent Desk", font=font_big, fill=0)
    draw.text((width - margin - 160, 30), task["status_label"], font=font_small, fill=0)
    draw.line((margin, 80, width - margin, 80), fill=0, width=3)
    draw.text((margin, 114), task["name"][:48], font=font, fill=0)
    draw.text((margin, 156), (task["detail"] or state.message or "状态已同步")[:72], font=font_small, fill=0)
    draw.rectangle((margin, 200, width - margin, 228), outline=0)
    draw.rectangle((margin, 200, margin + round(bar_w * progress / 100), 228), fill=0)
    draw.text((width - margin - 80, 178), f"{progress}%", font=font_small, fill=0)

    y = 280
    for quota in state.quotas[:3]:
        q = quota.to_dict()
        draw.text((margin, y), q["label"][:24], font=font, fill=0)
        draw.text((width - margin - 140, y), f'{q["remaining"]:.0f}/{q["limit"]:.0f}', font=font_small, fill=0)
        draw.rectangle((margin, y + 22, width - margin, y + 38), outline=0)
        draw.rectangle((margin, y + 22, margin + round(bar_w * q["percent"] / 100), y + 38), fill=0)
        y += 70

    draw.text((margin, height - 28), state.updated_at[:19].replace("T", " "), font=font_small, fill=0)
    return image


def load_font(image_font, size: int):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return image_font.truetype(candidate, size)
    return image_font.load_default()


def load_epd(screen: str):
    module_name, width, height = SCREEN_MODULES[screen]
    if screen == "lilygo_t5_47":
        raise SystemExit(
            "LilyGo T5 is driven by ESP32 firmware (epdiy), not PC-side Python. "
            "Use --output to render a PNG preview instead."
        )
    try:
        module = import_module(f"waveshare_epd.{module_name}")
    except ImportError as exc:
        raise SystemExit(
            f"Cannot import waveshare_epd.{module_name}. Install Waveshare's Python driver first."
        ) from exc
    return module.EPD(), width, height


def run_once(url: str, screen: str, output: Path | None, state_path: Path | None = None) -> None:
    state = load_state(state_path) if state_path else fetch_state(url)
    _, width, height = SCREEN_MODULES[screen]
    image = image_from_state(state, width, height)
    if output:
        image.save(output)
        return
    epd, _, _ = load_epd(screen)
    epd.init()
    epd.display(epd.getbuffer(image))
    epd.sleep()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render state to an e-paper display.")
    parser.add_argument("--url", default="http://127.0.0.1:8765/state.json")
    parser.add_argument("--state", type=Path, default=None, help="Read local state JSON instead of fetching --url.")
    parser.add_argument("--screen", choices=sorted(SCREEN_MODULES), default="lilygo_t5_47")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--output", type=Path, default=None, help="Write a PNG instead of touching hardware.")
    args = parser.parse_args(argv)

    while True:
        run_once(args.url, args.screen, args.output, args.state)
        if args.once or args.output:
            return 0
        time.sleep(max(15, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
