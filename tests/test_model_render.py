from agent_epaper.model import DisplayState, Quota, Task, TaskStatus
from agent_epaper.render import render_svg


def test_quota_percent_is_clamped() -> None:
    assert Quota(agent="codex", used=120, limit=100).percent == 100
    assert Quota(agent="codex", used=-1, limit=100).percent == 0


def test_state_round_trip() -> None:
    state = DisplayState(
        task=Task(name="测试", status=TaskStatus.RUNNING, progress=10),
        quotas=[Quota(agent="claude", used=1, limit=2)],
    )
    loaded = DisplayState.from_dict(state.to_dict())
    assert loaded.task.status == TaskStatus.RUNNING
    assert loaded.quotas[0].percent == 50


def test_svg_contains_status_label() -> None:
    state = DisplayState(task=Task(name="测试任务", status=TaskStatus.NEEDS_ACTION, progress=75))
    svg = render_svg(state)
    assert "需要操作" in svg
    assert "75%" in svg
