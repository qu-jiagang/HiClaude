from __future__ import annotations

import argparse
import json
from pathlib import Path

from .model import DisplayState, Quota, Task, TaskStatus
from .render import render_svg
from .storage import load_state, save_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update or preview the agent e-paper display state.")
    parser.add_argument("--state", type=Path, default=None, help="State JSON path. Defaults to ~/.agent-epaper/state.json")
    sub = parser.add_subparsers(dest="command", required=True)

    task = sub.add_parser("task", help="Update task status.")
    add_state_arg(task)
    task.add_argument("--name", required=True)
    task.add_argument("--status", choices=[item.value for item in TaskStatus], required=True)
    task.add_argument("--progress", type=int, default=0)
    task.add_argument("--detail", default="")

    quota = sub.add_parser("quota", help="Update quota usage.")
    add_state_arg(quota)
    quota.add_argument("--agent", required=True)
    quota.add_argument("--label", default="")
    quota.add_argument("--used", type=float, required=True)
    quota.add_argument("--limit", type=float, required=True)
    quota.add_argument("--reset", default="")

    msg = sub.add_parser("message", help="Update footer message.")
    add_state_arg(msg)
    msg.add_argument("text")

    demo = sub.add_parser("demo", help="Write a representative demo state.")
    add_state_arg(demo)
    show = sub.add_parser("show", help="Print current JSON state.")
    add_state_arg(show)
    show.add_argument("--svg", action="store_true", help="Print SVG instead of JSON.")
    return parser


def add_state_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state", type=Path, default=argparse.SUPPRESS, help=argparse.SUPPRESS)


def cmd_task(args: argparse.Namespace) -> None:
    state = load_state(args.state)
    state.task = Task(
        name=args.name,
        status=TaskStatus(args.status),
        progress=args.progress,
        detail=args.detail,
    )
    state.touch()
    print(save_state(state, args.state))


def cmd_quota(args: argparse.Namespace) -> None:
    state = load_state(args.state)
    replacement = Quota(
        agent=args.agent.lower(),
        label=args.label or args.agent.title(),
        used=args.used,
        limit=args.limit,
        reset_at=args.reset,
    )
    state.quotas = [item for item in state.quotas if item.agent.lower() != replacement.agent]
    state.quotas.append(replacement)
    state.quotas.sort(key=lambda item: item.agent)
    state.touch()
    print(save_state(state, args.state))


def cmd_message(args: argparse.Namespace) -> None:
    state = load_state(args.state)
    state.message = args.text
    state.touch()
    print(save_state(state, args.state))


def cmd_demo(args: argparse.Namespace) -> None:
    state = DisplayState(
        task=Task(
            name="实现墨水屏桌面摆件",
            status=TaskStatus.THINKING,
            progress=38,
            detail="规划硬件、程序、支架和验证流程",
        ),
        quotas=[
            Quota(agent="claude", label="Claude Code", used=42, limit=100, reset_at="明日 08:00"),
            Quota(agent="codex", label="Codex", used=18, limit=50, reset_at="明日 08:00"),
        ],
        message="本地预览模式",
    )
    state.touch()
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
        "show": cmd_show,
    }[args.command](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
