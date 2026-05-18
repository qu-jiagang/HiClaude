from agent_epaper.model import AgentState, DisplayState, Quota, Task, TaskStatus
from agent_epaper.render import render_svg


def test_quota_percent_is_clamped() -> None:
    assert Quota(agent="codex", used=120, limit=100).percent == 100
    assert Quota(agent="codex", used=-1, limit=100).percent == 0


def test_state_round_trip() -> None:
    state = DisplayState(
        agents=[
            AgentState(
                agent="claude",
                label="Claude Code",
                tasks=[
                    Task(name="测试", status=TaskStatus.RUNNING),
                    Task(name="第二个任务", status=TaskStatus.DONE),
                    Task(name="第三个任务", status=TaskStatus.IDLE),
                    Task(name="第四个任务", status=TaskStatus.RUNNING),
                ],
                quotas=[Quota(agent="claude", window="5h", label="5小时", used=1, limit=2)],
            )
        ],
    )
    payload = state.to_dict()
    assert "groups" not in payload
    assert "schema_version" not in payload
    assert "agents" not in payload
    assert "claude_code" in payload
    assert "quota" in payload["claude_code"]
    assert "five_hour" in payload["claude_code"]["quota"]
    loaded = DisplayState.from_dict(state.to_dict())
    assert loaded.task.status == TaskStatus.RUNNING
    assert len(loaded.tasks) == 4
    assert loaded.tasks[1].status == TaskStatus.DONE
    assert loaded.agents[0].quotas[0].percent == 50


def test_state_accepts_legacy_single_task() -> None:
    loaded = DisplayState.from_dict({"task": {"name": "旧任务", "status": "running"}})
    assert loaded.task.name == "旧任务"
    assert len(loaded.tasks) == 1


def test_svg_contains_status_label() -> None:
    state = DisplayState(
        agents=[
            AgentState(
                agent="claude",
                label="Claude Code",
                tasks=[
                    Task(name="测试任务", status=TaskStatus.NEEDS_ACTION),
                    Task(name="第二任务", status=TaskStatus.DONE),
                    Task(name="第三任务", status=TaskStatus.IDLE),
                    Task(name="第四任务", status=TaskStatus.RUNNING),
                ],
            )
        ],
    )
    svg = render_svg(state)
    assert "需要操作" in svg
    assert "测试任务" in svg
    assert "第二任务" in svg
    assert "第三任务" in svg
    assert "+1 任务运行中" in svg
    assert "第四任务" not in svg
    assert "等待" in svg
    assert "progress" not in svg
