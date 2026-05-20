from __future__ import annotations

import argparse
import json
from pathlib import Path

from .model import AgentState, DisplayState, QUOTA_WINDOW_LABELS, Task, TaskStatus, Quota, quota_window_key
from .render import render_svg
from .storage import load_state, save_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update or preview the agent e-paper display state.")
    parser.add_argument("--state", type=Path, default=None, help="State JSON path. Defaults to ~/.agent-epaper/state.json")
    sub = parser.add_subparsers(dest="command", required=True)

    task = sub.add_parser("task", help="Update task status.")
    add_state_arg(task)
    task.add_argument("--agent", default="claude")
    task.add_argument("--name", required=True)
    task.add_argument("--status", choices=[item.value for item in TaskStatus], required=True)
    task.add_argument("--detail", default="")

    quota = sub.add_parser("quota", help="Update quota usage.")
    add_state_arg(quota)
    quota.add_argument("--agent", required=True)
    quota.add_argument("--window", choices=["5h", "five_hour", "week", "weekly"], default="5h")
    quota.add_argument("--label", default="")
    quota.add_argument("--used", type=float, required=True)
    quota.add_argument("--limit", type=float, required=True)
    quota.add_argument("--reset", default="")

    msg = sub.add_parser("message", help="Update footer message.")
    add_state_arg(msg)
    msg.add_argument("text")

    demo = sub.add_parser("demo", help="Write a representative demo state.")
    add_state_arg(demo)

    collect = sub.add_parser("collect", help="Collect real-time quota and task data and save state.")
    add_state_arg(collect)
    collect.add_argument("--json", action="store_true", help="Print collected JSON instead of saving.")

    show = sub.add_parser("show", help="Print current JSON state.")
    add_state_arg(show)
    show.add_argument("--svg", action="store_true", help="Print SVG instead of JSON.")
    return parser


def add_state_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state", type=Path, default=argparse.SUPPRESS, help=argparse.SUPPRESS)


def cmd_task(args: argparse.Namespace) -> None:
    state = load_state(args.state)
    task = Task(
        name=args.name,
        status=TaskStatus(args.status),
        detail=args.detail,
    )
    agent_id = args.agent.lower()
    agents = state.agents or state._legacy_agents()
    for agent in agents:
        if agent.agent.lower() == agent_id:
            agent.tasks = [task] + agent.tasks[1:]
            break
    else:
        agents.append(AgentState(agent=agent_id, label=args.agent.title(), tasks=[task]))
    state.agents = agents
    state.task = state.agents[0].tasks[0] if state.agents and state.agents[0].tasks else task
    state.tasks = state.agents[0].tasks if state.agents else [task]
    state.touch()
    print(save_state(state, args.state))


def cmd_quota(args: argparse.Namespace) -> None:
    state = load_state(args.state)
    replacement = Quota(
        agent=args.agent.lower(),
        label=args.label or QUOTA_WINDOW_LABELS.get(quota_window_key(args.window), "额度"),
        window=quota_window_key(args.window),
        used=args.used,
        limit=args.limit,
        reset_at=args.reset,
    )
    agents = state.agents or state._legacy_agents()
    for agent in agents:
        if agent.agent.lower() == replacement.agent:
            agent.quotas = [item for item in agent.quotas if item.window != replacement.window]
            agent.quotas.append(replacement)
            agent.quotas.sort(key=lambda item: item.window)
            break
    else:
        agents.append(AgentState(agent=replacement.agent, label=replacement.label, quotas=[replacement]))
    state.agents = agents
    state.quotas = [quota for agent in agents for quota in agent.quotas]
    state.touch()
    print(save_state(state, args.state))


def cmd_message(args: argparse.Namespace) -> None:
    state = load_state(args.state)
    state.message = args.text
    state.touch()
    print(save_state(state, args.state))


def cmd_demo(args: argparse.Namespace) -> None:
    claude_tasks = [
        Task(
            name="实现墨水屏桌面摆件",
            status=TaskStatus.THINKING,
            detail="规划硬件、程序和验证流程",
        ),
        Task(
            name="完善中文 README",
            status=TaskStatus.DONE,
            detail="记录固件、预览和调试流程",
        ),
        Task(
            name="等待实机拍照确认",
            status=TaskStatus.IDLE,
            detail="按照片继续微调边距和字号",
        ),
        Task(
            name="整理固件上传流程",
            status=TaskStatus.RUNNING,
            detail="保留串口和 Wi-Fi 验证步骤",
        ),
    ]
    codex_tasks = [
        Task(name="修正 JSON 协议", status=TaskStatus.RUNNING),
        Task(name="同步固件解析", status=TaskStatus.IDLE),
    ]
    agents = [
        AgentState(
            agent="claude",
            label="Claude Code",
            tasks=claude_tasks,
            quotas=[
                Quota(agent="claude", window="five_hour", label="5小时额度", used=42, limit=100, reset_at="明日 08:00"),
                Quota(agent="claude", window="weekly", label="周额度", used=210, limit=500, reset_at="周一 08:00"),
            ],
        ),
        AgentState(
            agent="codex",
            label="Codex",
            tasks=codex_tasks,
            quotas=[
                Quota(agent="codex", window="five_hour", label="5小时额度", used=18, limit=50, reset_at="明日 08:00"),
                Quota(agent="codex", window="weekly", label="周额度", used=95, limit=250, reset_at="周一 08:00"),
            ],
        ),
    ]
    state = DisplayState(
        task=claude_tasks[0],
        tasks=claude_tasks,
        agents=agents,
        quotas=[quota for agent in agents for quota in agent.quotas],
        message="本地预览模式",
    )
    state.touch()
    print(save_state(state, args.state))


def cmd_collect(args: argparse.Namespace) -> None:
    from .collector import collect
    state = collect()
    if getattr(args, "json", False):
        print(json.dumps(state.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(save_state(state, args.state))


def cmd_show(args: argparse.Namespace) -> None:
    state = load_state(args.state)
    if args.svg:
        print(render_svg(state))
    else:
        print(json.dumps(state.to_dict(), ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    {
        "task": cmd_task,
        "quota": cmd_quota,
        "message": cmd_message,
        "demo": cmd_demo,
        "collect": cmd_collect,
        "show": cmd_show,
    }[args.command](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
