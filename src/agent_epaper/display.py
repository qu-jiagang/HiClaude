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
    font_big = load_font(ImageFont, 26 if width <= 400 else 34)
    font = load_font(ImageFont, 16 if width <= 400 else 22)
    font_small = load_font(ImageFont, 12 if width <= 400 else 16)
    margin = 18
    task = state.task.to_dict()
    progress = max(0, min(100, int(task["progress"])))
    bar_w = width - margin * 2

    draw.rectangle((0, 0, width - 1, height - 1), outline=0)
    draw.text((margin, 20), "Agent Desk", font=font_big, fill=0)
    draw.text((width - margin - 92, 22), task["status_label"], font=font_small, fill=0)
    draw.line((margin, 52, width - margin, 52), fill=0, width=2)
    draw.text((margin, 78), task["name"][:28], font=font, fill=0)
    draw.text((margin, 104), (task["detail"] or state.message or "状态已同步")[:36], font=font, fill=0)
    draw.rectangle((margin, 132, width - margin, 152), outline=0)
    draw.rectangle((margin, 132, margin + round(bar_w * progress / 100), 152), fill=0)
    draw.text((width - margin - 42, 112), f"{progress}%", font=font_small, fill=0)

    y = 170
    for quota in state.quotas[:3]:
        q = quota.to_dict()
        draw.text((margin, y), q["label"][:18], font=font, fill=0)
        draw.text((width - margin - 80, y), f'{q["remaining"]:.0f}/{q["limit"]:.0f}', font=font_small, fill=0)
        draw.rectangle((margin, y + 18, width - margin, y + 30), outline=0)
        draw.rectangle((margin, y + 18, margin + round(bar_w * q["percent"] / 100), y + 30), fill=0)
        y += 48

    draw.text((margin, height - 20), state.updated_at[:19].replace("T", " "), font=font_small, fill=0)
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
    parser = argparse.ArgumentParser(description="Render state to a Waveshare e-paper display.")
    parser.add_argument("--url", default="http://127.0.0.1:8765/state.json")
    parser.add_argument("--state", type=Path, default=None, help="Read local state JSON instead of fetching --url.")
    parser.add_argument("--screen", choices=sorted(SCREEN_MODULES), default="waveshare_4in2")
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
