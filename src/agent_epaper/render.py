from __future__ import annotations

from datetime import datetime
from html import escape

from .model import DisplayState, TaskStatus


STATUS_ICON = {
    TaskStatus.IDLE.value: "○",
    TaskStatus.THINKING.value: "...",
    TaskStatus.NEEDS_ACTION.value: "!",
    TaskStatus.RUNNING.value: "▶",
    TaskStatus.DONE.value: "✓",
    TaskStatus.FAILED.value: "×",
}

STATUS_SHORT = {
    TaskStatus.IDLE.value: "空闲",
    TaskStatus.THINKING.value: "进行",
    TaskStatus.NEEDS_ACTION.value: "等待",
    TaskStatus.RUNNING.value: "进行",
    TaskStatus.DONE.value: "完成",
    TaskStatus.FAILED.value: "失败",
}

ZONE_BRAND_X  = 195
ZONE_AGENT0_X = 500
ZONE_AGENT1_X = 770
HEADER_BOTTOM = 82


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def ellipsize_text(value: str, max_chars: int) -> str:
    text = str(value)
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3] + "..."


def _glyph_w(ch: str, font_px: float) -> float:
    # CJK / fullwidth glyphs are ~1em; Latin/ASCII ~0.56em.
    return font_px * (1.0 if ord(ch) > 0x2E80 else 0.56)


def ellipsize_to_width(value: str, max_px: float, font_px: float) -> str:
    """Trim to fit a pixel width, mirroring firmware ellipsizeUtf8ToWidth()."""
    text = str(value)
    if sum(_glyph_w(c, font_px) for c in text) <= max_px:
        return text
    budget = max_px - sum(_glyph_w(c, font_px) for c in "...")
    out, acc = "", 0.0
    for ch in text:
        cw = _glyph_w(ch, font_px)
        if acc + cw > budget:
            break
        out += ch
        acc += cw
    return (out + "...") if out else "..."


def _agent_status(agent) -> tuple[str, bool]:
    if agent and agent.tasks:
        st = agent.tasks[0].to_dict()["status"]
        return STATUS_SHORT.get(st, "空闲"), st in ("running", "thinking", "needs_action")
    return "空闲", False


def _status_dot_svg(cx: int, cy: int, active: bool) -> str:
    if active:
        return f'<circle cx="{cx}" cy="{cy}" r="7" fill="#000"/>'
    return f'<circle cx="{cx}" cy="{cy}" r="7" fill="none" stroke="#000" stroke-width="1.5"/>'


def _agent_column_svg(agent, x: int, y: int, w: int) -> str:
    label = escape(ellipsize_text(agent.label, 13)) if agent else "Agent"
    quotas = [quota.to_dict() for quota in agent.quotas[:2]] if agent else []

    quota_rows = []
    for quota_idx in range(2):
        q = quotas[quota_idx] if quota_idx < len(quotas) else None
        quota_y = y + 94 + quota_idx * 54
        quota_label = escape(ellipsize_text(q["label"] or q["window"] or "额度", 5)) if q else "额度"
        quota_text = f'{q["remaining"]:.0f}/{q["limit"]:.0f}' if q else "--"
        quota_reset = escape(q.get("reset_at", "")) if q else ""
        quota_percent = clamp(int(q["percent"]), 0, 100) if q else 0
        quota_fill = round((w - 52) * quota_percent / 100)
        reset_elem = f'<text x="{x + 130}" y="{quota_y}" class="tiny ink">{quota_reset}</text>' if quota_reset else ""
        quota_rows.append(
            f'<text x="{x + 24}" y="{quota_y}" class="quota ink">{quota_label}</text>\n'
            f'  {reset_elem}\n'
            f'  <text x="{x + w - 24}" y="{quota_y}" text-anchor="end" class="quota bold ink">{quota_text}</text>\n'
            f'  <rect x="{x + 24}" y="{quota_y + 14}" width="{w - 48}" height="16" class="bar"/>\n'
            f'  <rect x="{x + 26}" y="{quota_y + 16}" width="{quota_fill}" height="12" class="fill"/>'
        )

    all_tasks = [task.to_dict() for task in agent.tasks] if agent else []
    tasks = all_tasks[:3]
    extra_task_count = max(0, len(all_tasks) - 3)

    task_rows = []
    for row_idx in range(3):
        row_task = tasks[row_idx] if row_idx < len(tasks) else None
        row_status = escape(STATUS_SHORT.get(row_task["status"], "等待")) if row_task else "等待"
        # Last row shares its baseline with the "+N 任务运行中" marker; reserve
        # room for it so the title never overlaps the marker.
        title_px = w - 144
        if row_idx == 2 and extra_task_count > 0:
            title_px -= 130
        row_title = escape(ellipsize_to_width(row_task["name"] or "等待任务", title_px, 24)) if row_task else "等待任务"
        row_y = y + 202 + row_idx * 60
        separator = (
            f'<line x1="{x + 114}" y1="{row_y + 58}" x2="{x + w - 30}" y2="{row_y + 58}" class="taskline"/>'
            if row_idx < 2 else ""
        )
        task_rows.append(
            f'<text x="{x + 26}" y="{row_y + 40}" class="status bold ink">{row_status}</text>\n'
            f'  <text x="{x + 114}" y="{row_y + 40}" class="tasktitle bold ink">{row_title}</text>\n'
            f'  {separator}'
        )

    extra_marker = (
        f'<text x="{x + w - 30}" y="{y + 362}" text-anchor="end" class="tiny bold ink">+{extra_task_count} 任务运行中</text>'
        if extra_task_count > 0 else ""
    )

    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="380" class="hair"/>\n'
        f'  <text x="{x + 22}" y="{y + 52}" class="title ink">{label}</text>\n'
        f'  {"  ".join(quota_rows)}\n'
        f'  <line x1="{x + 22}" y1="{y + 192}" x2="{x + w - 22}" y2="{y + 192}" class="line"/>\n'
        f'  {"  ".join(task_rows)}\n'
        f'  {extra_marker}'
    )


def _agent_tasks_full_svg(agent, x: int, y: int, w: int) -> str:
    """Full-screen detail column: 5-hour quota bar in the header + 5 tasks.

    Mirrors firmware drawAgentTasksFull() geometry so web == device.
    """
    label = escape(ellipsize_text(agent.label, 12)) if agent else "Agent"
    all_tasks = [t.to_dict() for t in agent.tasks] if agent else []
    tasks = all_tasks[:5]

    # 5-hour quota bar in the empty header space right of the title.
    # quotas[0] is five_hour (collector emits it first; same as overview).
    quota_block = ""
    quotas = [q.to_dict() for q in agent.quotas[:1]] if agent else []
    if quotas:
        q = quotas[0]
        bar_right = x + w - 24
        bar_left = bar_right - 380
        bar_w = bar_right - bar_left
        q_label = escape(ellipsize_text(q["label"] or "5小时额度", 6))
        q_pct = clamp(int(q["percent"]), 0, 100)
        info = f'{q_pct}%'
        if q.get("reset_at"):
            info += f'  重置 {escape(q["reset_at"])}'
        fill_w = round((bar_w - 4) * q_pct / 100)
        quota_block = (
            f'<text x="{bar_left}" y="{y + 38}" class="quota ink">{q_label}</text>\n'
            f'  <text x="{bar_right}" y="{y + 38}" text-anchor="end" class="quota bold ink">{info}</text>\n'
            f'  <rect x="{bar_left}" y="{y + 48}" width="{bar_w}" height="18" class="bar"/>\n'
            f'  <rect x="{bar_left + 2}" y="{y + 50}" width="{fill_w}" height="14" class="fill"/>'
        )

    row_h = 58
    task_rows = []
    for i, task in enumerate(tasks):
        row_y = y + 86 + i * row_h
        row_status = escape(STATUS_SHORT.get(task["status"], "空闲"))
        row_title = escape(ellipsize_to_width(task["name"] or "等待任务", w - 144, 24))
        has_sep = i + 1 < len(tasks)
        separator = (
            f'<line x1="{x + 114}" y1="{row_y + 56}" x2="{x + w - 30}" y2="{row_y + 56}" class="taskline"/>'
            if has_sep else ""
        )
        task_rows.append(
            f'<text x="{x + 26}" y="{row_y + 40}" class="status bold ink">{row_status}</text>\n'
            f'  <text x="{x + 114}" y="{row_y + 40}" class="tasktitle bold ink">{row_title}</text>\n'
            f'  {separator}'
        )

    empty = (
        f'<text x="{x + 26}" y="{y + 126}" class="small ink">等待任务</text>'
        if not tasks else ""
    )

    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="380" class="hair"/>\n'
        f'  <text x="{x + 22}" y="{y + 52}" class="title ink">{label}</text>\n'
        f'  {quota_block}\n'
        f'  <line x1="{x + 22}" y1="{y + 76}" x2="{x + w - 22}" y2="{y + 76}" class="line"/>\n'
        f'  {"  ".join(task_rows)}\n'
        f'  {empty}'
    )


def render_svg(state: DisplayState, width: int = 960, height: int = 540,
               mode: str = "overview") -> str:
    margin = 20
    right = width - margin
    agents = state.agents or state._legacy_agents()
    clock_str = escape(datetime.now().strftime("%H:%M"))

    agent0 = agents[0] if agents else None
    agent1 = agents[1] if len(agents) > 1 else None
    a0_label = escape(ellipsize_text(agent0.label if agent0 else "Agent", 12))
    a1_label = escape(ellipsize_text(agent1.label if agent1 else "Agent", 12))
    a0_status, a0_active = _agent_status(agent0)
    a1_status, a1_active = _agent_status(agent1)

    # Zone 0: brand in overview, back link in full-screen modes
    if mode == "overview":
        zone0_content = f'<text x="{margin + 8}" y="54" class="brand ink">hiClaude</text>'
    else:
        zone0_content = (
            f'<a href="screen.svg">'
            f'<rect x="10" y="10" width="{ZONE_BRAND_X - 10}" height="{HEADER_BOTTOM - 10}" fill="transparent"/>'
            f'<text x="{margin + 12}" y="50" class="small ink">&lt; 返回概览</text>'
            f'</a>'
        )

    # Zone 1 click target (toggle agent-0 full)
    zone1_href = "screen.svg" if mode == "agent0" else "screen.svg?mode=agent0"
    zone1_target = (
        f'<a href="{zone1_href}">'
        f'<rect x="{ZONE_BRAND_X}" y="10" width="{ZONE_AGENT0_X - ZONE_BRAND_X}" height="{HEADER_BOTTOM - 10}" fill="transparent"/>'
        f'</a>'
    )

    # Zone 2 click target (toggle agent-1 full)
    zone2_href = "screen.svg" if mode == "agent1" else "screen.svg?mode=agent1"
    zone2_target = (
        f'<a href="{zone2_href}">'
        f'<rect x="{ZONE_AGENT0_X}" y="10" width="{ZONE_AGENT1_X - ZONE_AGENT0_X}" height="{HEADER_BOTTOM - 10}" fill="transparent"/>'
        f'</a>'
    )

    # Zone 3 click target (refresh: reload overview)
    zone3_target = (
        f'<a href="screen.svg">'
        f'<rect x="{ZONE_AGENT1_X}" y="10" width="{right - ZONE_AGENT1_X}" height="{HEADER_BOTTOM - 10}" fill="transparent"/>'
        f'</a>'
    )

    # Body
    column_y = 104
    if mode == "agent0":
        body = _agent_tasks_full_svg(agent0, margin, column_y, right - margin)
    elif mode == "agent1":
        body = _agent_tasks_full_svg(agent1, margin, column_y, right - margin)
    else:
        column_gap = 20
        column_w = (width - margin * 2 - column_gap) // 2
        body = (
            _agent_column_svg(agent0, margin, column_y, column_w) + "\n  " +
            _agent_column_svg(agent1, margin + column_w + column_gap, column_y, column_w)
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .bg {{ fill: #fff; }}
    .ink {{ fill: #000; }}
    .line {{ stroke: #000; stroke-width: 1; fill: none; }}
    .taskline {{ stroke: #000; stroke-width: 1; fill: none; }}
    .hair {{ stroke: #000; stroke-width: 1; fill: none; }}
    .bar {{ fill: #fff; stroke: #000; stroke-width: 1; }}
    .fill {{ fill: #000; }}
    .brand {{ font: 700 32px "Noto Sans CJK SC", "Heiti SC", sans-serif; }}
    .title {{ font: 700 32px "Noto Sans CJK SC", "Heiti SC", sans-serif; }}
    .tasktitle {{ font: 700 24px "Noto Sans CJK SC", "Heiti SC", sans-serif; }}
    .status {{ font: 700 24px "Noto Sans CJK SC", "Heiti SC", sans-serif; }}
    .zone {{ font: 28px "Noto Sans CJK SC", "Heiti SC", sans-serif; }}
    .medium {{ font: 700 26px "Noto Sans CJK SC", "Heiti SC", sans-serif; }}
    .quota {{ font: 16px "Noto Sans CJK SC", "Heiti SC", sans-serif; }}
    .small {{ font: 14px "Noto Sans CJK SC", "Heiti SC", sans-serif; }}
    .tiny {{ font: 14px "Noto Sans CJK SC", "Heiti SC", sans-serif; }}
    .bold {{ font-weight: 700; }}
  </style>
  <rect width="100%" height="100%" class="bg"/>
  <rect x="10" y="10" width="{width - 20}" height="{height - 20}" class="hair"/>
  <line x1="{ZONE_BRAND_X}" y1="10" x2="{ZONE_BRAND_X}" y2="{HEADER_BOTTOM}" class="line"/>
  <line x1="{ZONE_AGENT0_X}" y1="10" x2="{ZONE_AGENT0_X}" y2="{HEADER_BOTTOM}" class="line"/>
  <line x1="{ZONE_AGENT1_X}" y1="10" x2="{ZONE_AGENT1_X}" y2="{HEADER_BOTTOM}" class="line"/>
  {zone0_content}
  {_status_dot_svg(ZONE_BRAND_X + 18, 44, a0_active)}
  <text x="{ZONE_BRAND_X + 36}" y="54" class="zone bold ink">{a0_label}</text>
  <text x="{ZONE_AGENT0_X - 14}" y="54" text-anchor="end" class="zone ink">{escape(a0_status)}</text>
  {_status_dot_svg(ZONE_AGENT0_X + 18, 44, a1_active)}
  <text x="{ZONE_AGENT0_X + 36}" y="54" class="zone bold ink">{a1_label}</text>
  <text x="{ZONE_AGENT1_X - 14}" y="54" text-anchor="end" class="zone ink">{escape(a1_status)}</text>
  <text x="{ZONE_AGENT1_X + 30}" y="54" class="zone ink">{clock_str}</text>
  {zone1_target}
  {zone2_target}
  {zone3_target}
  <line x1="{margin}" y1="{HEADER_BOTTOM}" x2="{right}" y2="{HEADER_BOTTOM}" class="line"/>
  {body}
  <line x1="{margin}" y1="506" x2="{right}" y2="506" class="line"/>
  <text x="{margin}" y="524" class="tiny ink">updated {escape(state.updated_at[:19])}</text>
  <text x="{right}" y="524" text-anchor="end" class="tiny ink">4.7in / 960x540</text>
</svg>
"""
