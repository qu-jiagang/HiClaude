from __future__ import annotations

from html import escape
from textwrap import shorten

from .model import DisplayState, TaskStatus


STATUS_ICON = {
    TaskStatus.IDLE.value: "○",
    TaskStatus.THINKING.value: "...",
    TaskStatus.NEEDS_ACTION.value: "!",
    TaskStatus.RUNNING.value: "▶",
    TaskStatus.DONE.value: "✓",
    TaskStatus.FAILED.value: "×",
}


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def render_svg(state: DisplayState, width: int = 400, height: int = 300) -> str:
    margin = 18
    task = state.task.to_dict()
    progress = clamp(int(task["progress"]), 0, 100)
    quota_y = 165
    quota_gap = 48
    title = escape(shorten(task["name"], width=24, placeholder="..."))
    detail = escape(shorten(task["detail"] or state.message or "状态已同步", width=36, placeholder="..."))
    icon = STATUS_ICON.get(task["status"], "?")
    status_label = escape(task["status_label"])
    progress_width = width - margin * 2
    fill_width = round(progress_width * progress / 100)

    quota_blocks = []
    for idx, quota in enumerate(state.quotas[:2]):
        q = quota.to_dict()
        y = quota_y + idx * quota_gap
        bar_w = width - margin * 2 - 96
        used_w = round(bar_w * clamp(int(q["percent"]), 0, 100) / 100)
        label = escape(shorten(q["label"], width=12, placeholder="..."))
        reset = escape(shorten(q["reset_at"], width=18, placeholder="..."))
        quota_blocks.append(
            f"""
  <text x="{margin}" y="{y}" class="small bold">{label}</text>
  <text x="{width - margin}" y="{y}" text-anchor="end" class="small">{q["remaining"]:.0f}/{q["limit"]:.0f}</text>
  <rect x="{margin}" y="{y + 10}" width="{bar_w}" height="12" class="bar"/>
  <rect x="{margin}" y="{y + 10}" width="{used_w}" height="12" class="fill"/>
  <text x="{width - margin}" y="{y + 21}" text-anchor="end" class="tiny">{reset}</text>"""
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .bg {{ fill: #fff; }}
    .ink {{ fill: #000; }}
    .line {{ stroke: #000; stroke-width: 2; fill: none; }}
    .hair {{ stroke: #000; stroke-width: 1; fill: none; }}
    .bar {{ fill: #fff; stroke: #000; stroke-width: 1.5; }}
    .fill {{ fill: #000; }}
    .title {{ font: 700 28px sans-serif; }}
    .status {{ font: 700 20px sans-serif; }}
    .body {{ font: 16px sans-serif; }}
    .small {{ font: 14px sans-serif; }}
    .tiny {{ font: 11px sans-serif; }}
    .bold {{ font-weight: 700; }}
  </style>
  <rect width="100%" height="100%" class="bg"/>
  <rect x="8" y="8" width="{width - 16}" height="{height - 16}" rx="0" class="hair"/>
  <text x="{margin}" y="42" class="title ink">Agent Desk</text>
  <text x="{width - margin}" y="40" text-anchor="end" class="status ink">{icon} {status_label}</text>
  <line x1="{margin}" y1="58" x2="{width - margin}" y2="58" class="line"/>
  <text x="{margin}" y="92" class="body bold ink">{title}</text>
  <text x="{margin}" y="119" class="small ink">{detail}</text>
  <rect x="{margin}" y="132" width="{progress_width}" height="18" class="bar"/>
  <rect x="{margin}" y="132" width="{fill_width}" height="18" class="fill"/>
  <text x="{width - margin}" y="126" text-anchor="end" class="small ink">{progress}%</text>
  {''.join(quota_blocks)}
  <text x="{margin}" y="{height - 18}" class="tiny ink">updated {escape(state.updated_at[:19].replace("T", " "))}</text>
</svg>
"""
