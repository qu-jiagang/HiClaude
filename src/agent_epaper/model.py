from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    NEEDS_ACTION = "needs_action"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


STATUS_LABELS = {
    TaskStatus.IDLE: "空闲",
    TaskStatus.THINKING: "思考中",
    TaskStatus.NEEDS_ACTION: "需要操作",
    TaskStatus.RUNNING: "执行中",
    TaskStatus.DONE: "任务完成",
    TaskStatus.FAILED: "任务失败",
}


@dataclass(slots=True)
class Quota:
    agent: str
    used: float
    limit: float
    reset_at: str = ""
    label: str = ""

    @property
    def percent(self) -> int:
        if self.limit <= 0:
            return 0
        return max(0, min(100, round((self.used / self.limit) * 100)))

    @property
    def remaining(self) -> float:
        return max(0.0, self.limit - self.used)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "label": self.label or self.agent.title(),
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "percent": self.percent,
            "reset_at": self.reset_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Quota":
        return cls(
            agent=str(data.get("agent", "")),
            label=str(data.get("label", "")),
            used=float(data.get("used", 0)),
            limit=float(data.get("limit", 0)),
            reset_at=str(data.get("reset_at", "")),
        )


@dataclass(slots=True)
class Task:
    name: str
    status: TaskStatus = TaskStatus.IDLE
    progress: int = 0
    detail: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "status_label": STATUS_LABELS[self.status],
            "progress": max(0, min(100, int(self.progress))),
            "detail": self.detail,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        raw_status = str(data.get("status", TaskStatus.IDLE.value))
        status = TaskStatus(raw_status) if raw_status in TaskStatus._value2member_map_ else TaskStatus.IDLE
        return cls(
            name=str(data.get("name", "等待任务")),
            status=status,
            progress=int(data.get("progress", 0)),
            detail=str(data.get("detail", "")),
            updated_at=str(data.get("updated_at", "")),
        )


@dataclass(slots=True)
class DisplayState:
    task: Task = field(default_factory=lambda: Task(name="等待任务"))
    quotas: list[Quota] = field(default_factory=list)
    message: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.task.updated_at = self.updated_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task.to_dict(),
            "quotas": [quota.to_dict() for quota in self.quotas],
            "message": self.message,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DisplayState":
        return cls(
            task=Task.from_dict(data.get("task", {})),
            quotas=[Quota.from_dict(item) for item in data.get("quotas", [])],
            message=str(data.get("message", "")),
            updated_at=str(data.get("updated_at", "")) or datetime.now(timezone.utc).isoformat(),
        )
