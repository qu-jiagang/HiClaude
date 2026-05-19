import json

from agent_epaper.collector import _claude_session_priority, _claude_task_from_jsonl, _codex_task_from_jsonl
from agent_epaper.model import Task, TaskStatus


def write_jsonl(path, items):
    path.write_text("\n".join(json.dumps(item) for item in items), encoding="utf-8")


def test_codex_task_uses_latest_user_message(tmp_path) -> None:
    session = tmp_path / "session.jsonl"
    write_jsonl(session, [
        {"type": "session_meta", "payload": {"source": "vscode"}},
        {"type": "event_msg", "payload": {"type": "user_message", "message": "old task"}},
        {"type": "event_msg", "payload": {"type": "task_complete"}},
        {"type": "event_msg", "payload": {"type": "user_message", "message": "current codex task\n"}},
        {"type": "event_msg", "payload": {"type": "task_started"}},
    ])

    task = _codex_task_from_jsonl(session)

    assert task is not None
    assert task.name == "current codex task"
    assert task.status == TaskStatus.RUNNING


def test_codex_task_marks_completed_turn_as_needs_action(tmp_path) -> None:
    session = tmp_path / "session.jsonl"
    write_jsonl(session, [
        {"type": "session_meta", "payload": {"source": "vscode"}},
        {"type": "event_msg", "payload": {"type": "user_message", "message": "review result"}},
        {"type": "event_msg", "payload": {"type": "task_complete"}},
    ])

    task = _codex_task_from_jsonl(session)

    assert task is not None
    assert task.name == "review result"
    assert task.status == TaskStatus.NEEDS_ACTION


def test_claude_task_skips_meta_loop_and_tool_results(tmp_path) -> None:
    transcript = tmp_path / "claude.jsonl"
    write_jsonl(transcript, [
        {
            "type": "user",
            "isMeta": True,
            "message": {
                "content": [{"type": "text", "text": "# /loop internal prompt"}],
            },
        },
        {
            "type": "user",
            "message": {
                "content": [{"type": "tool_result", "content": "tool output"}],
            },
        },
        {
            "type": "user",
            "message": {"content": "real claude task"},
        },
        {
            "type": "assistant",
            "message": {"stop_reason": "tool_use"},
        },
    ])

    task = _claude_task_from_jsonl(transcript)

    assert task is not None
    assert task.name == "real claude task"
    assert task.status == TaskStatus.RUNNING


def test_claude_task_skips_internal_notifications(tmp_path) -> None:
    transcript = tmp_path / "claude.jsonl"
    write_jsonl(transcript, [
        {
            "type": "user",
            "message": {"content": "real user task"},
        },
        {
            "type": "assistant",
            "message": {"stop_reason": "end_turn"},
        },
        {
            "type": "user",
            "message": {"content": "<task-notification> <task-id>abc</task-id> <summary>monitor event</summary>"},
        },
    ])

    task = _claude_task_from_jsonl(transcript)

    assert task is not None
    assert task.name == "real user task"


def test_claude_task_marks_completed_turn_as_needs_action_immediately(tmp_path) -> None:
    transcript = tmp_path / "claude.jsonl"
    write_jsonl(transcript, [
        {
            "type": "user",
            "message": {"content": "finished claude task"},
        },
        {
            "type": "assistant",
            "timestamp": "2999-01-01T00:00:00.000Z",
            "message": {"stop_reason": "end_turn"},
        },
    ])

    task = _claude_task_from_jsonl(transcript)

    assert task is not None
    assert task.name == "finished claude task"
    assert task.status == TaskStatus.NEEDS_ACTION


def test_claude_session_priority_prefers_running_then_busy() -> None:
    running = Task(name="running", status=TaskStatus.RUNNING)
    waiting = Task(name="waiting", status=TaskStatus.NEEDS_ACTION)

    assert _claude_session_priority({}, running) > _claude_session_priority({"status": "busy"}, waiting)
    assert _claude_session_priority({"status": "busy"}, waiting) > _claude_session_priority({}, waiting)
