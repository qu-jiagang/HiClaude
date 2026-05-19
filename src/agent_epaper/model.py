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
    TaskStatus.NEEDS_ACTION: "等待",
    TaskStatus.RUNNING: "执行中",
    TaskStatus.DONE: "任务完成",
    TaskStatus.FAILED: "任务失败",
}

GROUP_LABELS = {
    "claude_code": "Claude Code",
    "codex": "Codex",
}

AGENT_TO_GROUP = {
    "claude": "claude_code",
    "claude_code": "claude_code",
    "codex": "codex",
}

GROUP_TO_AGENT = {
    "claude_code": "claude",
    "codex": "codex",
}

QUOTA_WINDOW_KEYS = {
    "5h": "five_hour",
    "five_hour": "five_hour",
    "week": "weekly",
    "weekly": "weekly",
}

QUOTA_WINDOW_LABELS = {
    "five_hour": "5小时额度",
    "weekly": "周额度",
}


def group_key(agent: str) -> str:
    key = str(agent).lower()
    return AGENT_TO_GROUP.get(key, key)


def quota_window_key(window: str) -> str:
    key = str(window).lower()
    return QUOTA_WINDOW_KEYS.get(key, key or "quota")


@dataclass(slots=True)
class Quota:
    agent: str
    used: float
    limit: float
    reset_at: str = ""
    label: str = ""
    window: str = ""

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
            "window": self.window,
            "used": self.used,
            "limit": self.limit,
            "remaining": self.remaining,
            "percent": self.percent,
            "reset_at": self.reset_at,
        }

    def to_group_dict(self) -> dict[str, Any]:
        return {
            "label": self.label or QUOTA_WINDOW_LABELS.get(quota_window_key(self.window), "额度"),
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
            window=str(data.get("window", "")),
            used=float(data.get("used", 0)),
            limit=float(data.get("limit", 0)),
            reset_at=str(data.get("reset_at", "")),
        )


@dataclass(slots=True)
class Task:
    name: str
    status: TaskStatus = TaskStatus.IDLE
    detail: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "status_label": STATUS_LABELS[self.status],
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
            detail=str(data.get("detail", "")),
            updated_at=str(data.get("updated_at", "")),
        )


@dataclass(slots=True)
class AgentState:
    agent: str
    label: str
    tasks: list[Task] = field(default_factory=list)
    quotas: list[Quota] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "label": self.label or self.agent.title(),
            "tasks": [task.to_dict() for task in self.tasks],
            "quotas": [quota.to_dict() for quota in self.quotas],
        }

    def to_group_dict(self) -> dict[str, Any]:
        quota: dict[str, Any] = {}
        for item in self.quotas:
            quota[quota_window_key(item.window)] = item.to_group_dict()
        return {
            "label": self.label or GROUP_LABELS.get(group_key(self.agent), self.agent.title()),
            "quota": quota,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentState":
        agent = str(data.get("agent", ""))
        return cls(
            agent=agent,
            label=str(data.get("label", "")) or agent.title(),
            tasks=[Task.from_dict(item) for item in data.get("tasks", [])],
            quotas=[
                Quota.from_dict({**item, "agent": item.get("agent", agent)})
                for item in data.get("quotas", [])
            ],
        )


@dataclass(slots=True)
class DisplayState:
    task: Task = field(default_factory=lambda: Task(name="等待任务"))
    tasks: list[Task] = field(default_factory=list)
    quotas: list[Quota] = field(default_factory=list)
    agents: list[AgentState] = field(default_factory=list)
    message: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.task.updated_at = self.updated_at
        for task in self.tasks:
            task.updated_at = self.updated_at
        for agent in self.agents:
            for task in agent.tasks:
                task.updated_at = self.updated_at

    def to_dict(self) -> dict[str, Any]:
        agents = self.agents or self._legacy_agents()
        payload = {
            "message": self.message,
            "updated_at": self.updated_at,
        }
        payload.update({group_key(agent.agent): agent.to_group_dict() for agent in agents})
        return payload

    def _legacy_agents(self) -> list[AgentState]:
        tasks = self.tasks if self.tasks else [self.task]
        by_agent: dict[str, list[Quota]] = {}
        labels: dict[str, str] = {}
        for quota in self.quotas:
            key = quota.agent.lower() or "agent"
            by_agent.setdefault(key, []).append(quota)
            labels[key] = quota.label or key.title()
        if not by_agent:
            by_agent = {"claude": []}
            labels = {"claude": "Claude Code"}
        agents: list[AgentState] = []
        for index, (agent, quotas) in enumerate(sorted(by_agent.items())):
            agents.append(
                AgentState(
                    agent=agent,
                    label=labels.get(agent, agent.title()),
                    tasks=tasks if index == 0 else [],
                    quotas=quotas,
                )
            )
        return agents

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DisplayState":
        agents = cls._agents_from_top_level(data)
        if not agents:
            agents = cls._agents_from_groups(data.get("groups", {}))
        if not agents:
            agents = [AgentState.from_dict(item) for item in data.get("agents", [])]
        task = Task.from_dict(data.get("task", {}))
        tasks = [Task.from_dict(item) for item in data.get("tasks", [])]
        if not tasks:
            tasks = [task]
        quotas = [Quota.from_dict(item) for item in data.get("quotas", [])]
        if not agents:
            legacy = cls(task=task, tasks=tasks, quotas=quotas)
            agents = legacy._legacy_agents()
        return cls(
            task=agents[0].tasks[0] if agents and agents[0].tasks else tasks[0],
            tasks=agents[0].tasks if agents and agents[0].tasks else tasks,
            quotas=quotas,
            agents=agents,
            message=str(data.get("message", "")),
            updated_at=str(data.get("updated_at", "")) or datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _agents_from_top_level(data: dict[str, Any]) -> list[AgentState]:
        groups = {key: data[key] for key in ("claude_code", "codex") if key in data}
        return DisplayState._agents_from_groups(groups)

    @staticmethod
    def _agents_from_groups(groups: Any) -> list[AgentState]:
        if not isinstance(groups, dict):
            return []
        ordered_keys = [key for key in ("claude_code", "codex") if key in groups]
        ordered_keys.extend(key for key in groups if key not in ordered_keys)
        agents: list[AgentState] = []
        for key in ordered_keys:
            group = groups.get(key) or {}
            if not isinstance(group, dict):
                continue
            agent = GROUP_TO_AGENT.get(key, key)
            quota_data = group.get("quota", {})
            quotas: list[Quota] = []
            if isinstance(quota_data, dict):
                for window_key, value in quota_data.items():
                    if not isinstance(value, dict):
                        continue
                    normalized_window = quota_window_key(str(window_key))
                    quotas.append(
                        Quota.from_dict(
                            {
                                **value,
                                "agent": agent,
                                "window": normalized_window,
                                "label": value.get("label", QUOTA_WINDOW_LABELS.get(normalized_window, str(window_key))),
                            }
                        )
                    )
            agents.append(
                AgentState(
                    agent=agent,
                    label=str(group.get("label", "")) or GROUP_LABELS.get(key, agent.title()),
                    tasks=[Task.from_dict(item) for item in group.get("tasks", [])],
                    quotas=quotas,
                )
            )
        return agents
