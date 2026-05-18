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

STATUS_SHORT = {
    "idle": "空闲",
    "thinking": "进行",
    "needs_action": "待处理",
    "running": "进行",
    "done": "完成",
    "failed": "失败",
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

    if width == 960 and height == 540:
        return lilygo_image_from_state(state, Image, ImageDraw, ImageFont)

    image = Image.new("L", (width, height), 255)
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


def lilygo_image_from_state(state: DisplayState, image_module, image_draw, image_font):
    width = 960
    height = 540
    image = image_module.new("L", (width, height), 255)
    draw = image_draw.Draw(image)

    font_brand = load_font(image_font, 32, bold=True)
    font_title = load_font(image_font, 32, bold=True)
    font_card = load_font(image_font, 32, bold=True)
    font_status = load_font(image_font, 28, bold=True)
    font_small = load_font(image_font, 14)
    font_tiny = load_font(image_font, 14)

    agents = state.agents or state._legacy_agents()
    task = agents[0].tasks[0].to_dict() if agents and agents[0].tasks else state.task.to_dict()
    updated = state.updated_at[:19]

    margin = 20
    draw.rectangle((10, 10, width - 10, height - 10), outline=0, width=1)
    draw.text((margin + 8, 54), "hiClaude", font=font_brand, fill=0, anchor="ls")
    draw.text((margin + 300, 46), f"{len(agents[:2])} agents / Wi-Fi JSON", font=font_tiny, fill=0, anchor="ls")
    draw.text((width - margin - 88, 46), task["status_label"], font=font_small, fill=0, anchor="ls")
    draw.line((margin, 82, width - margin, 82), fill=0, width=1)

    column_gap = 20
    column_w = (width - margin * 2 - column_gap) // 2
    for index in range(2):
        x = margin + index * (column_w + column_gap)
        agent = agents[index] if index < len(agents) else None
        tasks_for_column = [task.to_dict() for task in agent.tasks[:3]] if agent else []
        extra_count = max(0, len(agent.tasks) - 3) if agent else 0
        quotas_for_column = [quota.to_dict() for quota in agent.quotas[:2]] if agent else []
        draw_agent_column(draw, x, 104, column_w, 380, agent, quotas_for_column, tasks_for_column, extra_count, font_title, font_card, font_status, font_small, font_tiny)

    draw.line((margin, 506, width - margin, 506), fill=0, width=1)
    draw.text((margin, 524), f"updated {updated}", font=font_tiny, fill=0, anchor="ls")
    draw.text((width - margin, 524), "4.7in / 960x540", font=font_tiny, fill=0, anchor="rs")
    return image


def draw_agent_column(draw, x: int, y: int, w: int, h: int, agent, quotas, tasks, extra_count: int, font_title, font_card, font_status, font_small, font_tiny) -> None:
    draw.rectangle((x, y, x + w, y + h), outline=0, width=1)

    label = fit_text(draw, agent.label if agent else "Agent", font_title, w - 44)
    draw.text((x + 22, y + 52), label, font=font_title, fill=0, anchor="ls")

    for index in range(2):
        quota = quotas[index] if index < len(quotas) else None
        quota_y = y + 94 + index * 42  # baseline coordinate
        label_text = fit_text(draw, (quota["label"] or quota["window"] or "额度") if quota else "额度", font_small, 110)
        value_text = f'{quota["remaining"]:.0f}/{quota["limit"]:.0f}' if quota else "--"
        reset_text = quota.get("reset_at", "") if quota else ""
        percent = int(quota["percent"]) if quota else 0
        draw.text((x + 24, quota_y), label_text, font=font_small, fill=0, anchor="ls")
        if reset_text:
            draw.text((x + 130, quota_y), reset_text, font=font_tiny, fill=0, anchor="ls")
        draw.text((x + w - 24, quota_y), value_text, font=font_small, fill=0, anchor="rs")
        draw_progress(draw, x + 24, quota_y + 12, w - 48, 16, percent)

    draw.line((x + 22, y + 180, x + w - 22, y + 180), fill=0, width=1)

    row_w = w - 44
    for index in range(3):
        task = tasks[index] if index < len(tasks) else None
        row_x = x + 22
        row_y = y + 190 + index * 60

        status = STATUS_SHORT.get(task["status"], "等待") if task else "等待"
        title_font = font_card
        title = fit_text(draw, task["name"] if task else "等待任务", title_font, row_w - 108)
        draw.text((row_x + 4, row_y + 40), status, font=font_status, fill=0, anchor="ls")
        draw.text((row_x + 92, row_y + 40), title, font=title_font, fill=0, anchor="ls")
        if index < 2:
            draw.line((row_x + 92, row_y + 58, row_x + row_w - 8, row_y + 58), fill=0, width=1)

    if extra_count > 0:
        draw.text((x + w - 30, y + 362), f"+{extra_count} 任务运行中", font=font_tiny, fill=0, anchor="rs")


def draw_progress(draw, x: int, y: int, w: int, h: int, percent: int) -> None:
    percent = max(0, min(100, int(percent)))
    draw.rectangle((x, y, x + w, y + h), outline=0, width=1)
    fill_w = round((w - 4) * percent / 100)
    if fill_w > 0:
        draw.rectangle((x + 2, y + 2, x + 2 + fill_w, y + h - 2), fill=0)


def fit_text(draw, text: str, font, max_width: int) -> str:
    value = str(text)
    if text_width(draw, value, font) <= max_width:
        return value
    placeholder = "..."
    while value and text_width(draw, value + placeholder, font) > max_width:
        value = value[:-1]
    return value + placeholder if value else placeholder


def text_width(draw, text: str, font) -> int:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return right - left


def load_font(image_font, size: int, bold: bool = False):
    home = str(Path.home())
    candidates = [
        f"{home}/Library/Fonts/NotoSansCJKsc-Bold.otf" if bold else f"{home}/Library/Fonts/NotoSansCJKsc-Regular.otf",
        "/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/PingFang.ttc",
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
