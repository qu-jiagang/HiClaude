from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from .model import AgentState, DisplayState, Quota, Task, TaskStatus

_CLAUDE_KEYCHAIN_SERVICE = "Claude Code-credentials"
_CODEX_KEYCHAIN_SERVICE = "Codex Auth"

# In-memory cache: (fetched_at, quotas)
_claude_quota_cache: tuple[float, list[Quota]] | None = None
_codex_quota_cache: tuple[float, list[Quota]] | None = None
_QUOTA_TTL = 600  # 10 minutes

_FILE_CACHE = Path.home() / ".agent-epaper" / "quota-cache.json"
_ANTHROPIC_USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
_CODEX_USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _file_cache_read(agent: str, ignore_ttl: bool = False) -> list[Quota] | None:
    try:
        data = json.loads(_FILE_CACHE.read_text())
        entry = data.get(agent, {})
        if ignore_ttl or time.time() - entry.get("ts", 0) < _QUOTA_TTL:
            quotas = entry.get("quotas", [])
            if quotas:
                return [Quota.from_dict(q) for q in quotas]
    except Exception:
        pass
    return None


def _file_cache_write(agent: str, quotas: list[Quota]) -> None:
    try:
        _FILE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(_FILE_CACHE.read_text())
        except Exception:
            data = {}
        data[agent] = {"ts": time.time(), "quotas": [q.to_dict() for q in quotas]}
        _FILE_CACHE.write_text(json.dumps(data, ensure_ascii=False))
    except Exception:
        pass


def _keychain_json(service: str) -> dict:
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-w"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return json.loads(result.stdout.strip())
    except Exception:
        pass
    return {}


def _fmt_reset(dt: datetime) -> str:
    local = dt.astimezone()
    now = datetime.now().astimezone()
    delta = (local.date() - now.date()).days
    t = local.strftime("%H:%M")
    if delta == 0:
        return f"今日 {t}"
    if delta == 1:
        return f"明日 {t}"
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return f"{weekdays[local.weekday()]} {t}"


def _get(url: str, headers: dict) -> dict | None:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Claude Code
# ---------------------------------------------------------------------------

def _claude_token() -> str:
    creds = _keychain_json(_CLAUDE_KEYCHAIN_SERVICE)
    if not creds:
        try:
            creds = json.loads((Path.home() / ".claude" / ".credentials.json").read_text())
        except Exception:
            creds = {}
    oauth = creds.get("claudeAiOauth", {})
    expires_at = oauth.get("expiresAt", 0)
    if expires_at and expires_at < datetime.now().timestamp() * 1000:
        return ""
    return oauth.get("accessToken", "")


def collect_claude_quotas() -> list[Quota]:
    global _claude_quota_cache
    now = time.monotonic()
    if _claude_quota_cache and now - _claude_quota_cache[0] < _QUOTA_TTL:
        return _claude_quota_cache[1]

    cached = _file_cache_read("claude")
    if cached is not None:
        _claude_quota_cache = (now, cached)
        return cached

    token = _claude_token()
    if not token:
        return _file_cache_read("claude", ignore_ttl=True) or []
    data = _get(_ANTHROPIC_USAGE_URL, {
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
    })
    if not data:
        stale = (_claude_quota_cache[1] if _claude_quota_cache else None) or _file_cache_read("claude", ignore_ttl=True)
        return stale or []

    quotas: list[Quota] = []
    window_map = [
        ("five_hour", "five_hour", "5小时额度"),
        ("seven_day",  "weekly",    "7日额度"),
    ]
    for api_key, window, label in window_map:
        entry = data.get(api_key) or {}
        util = entry.get("utilization")
        if util is None:
            continue
        resets_at = ""
        raw = entry.get("resets_at")
        if raw:
            resets_at = _fmt_reset(datetime.fromisoformat(raw))
        quotas.append(Quota(
            agent="claude", window=window, label=label,
            used=float(util), limit=100.0, reset_at=resets_at,
        ))
    _claude_quota_cache = (now, quotas)
    _file_cache_write("claude", quotas)
    return quotas


def collect_claude_tasks() -> list[Task]:
    """Return one Task per alive Claude session.

    Sorted by priority (running > metadata-busy > idle) then by transcript
    recency, so a still-busy session is never masked by a just-finished one.
    """
    sessions_dir = Path.home() / ".claude" / "sessions"
    if not sessions_dir.exists():
        return []

    projects_dir = Path.home() / ".claude" / "projects"

    entries: list[tuple[int, float, Task]] = []
    for f in sessions_dir.glob("*.json"):
        try:
            meta = json.loads(f.read_text())
            pid = meta.get("pid")
            sid = meta.get("sessionId")
            if not (pid and sid):
                continue
            os.kill(pid, 0)   # raises if the process is dead
            proc_start = meta.get("procStart")
            if proc_start:
                actual_start = Path(f"/proc/{pid}/stat").read_text().split()[21]
                if str(proc_start) != actual_start:
                    continue
        except Exception:
            continue
        matches = list(projects_dir.glob(f"**/{sid}.jsonl"))
        if not matches:
            continue
        jsonl = max(matches, key=lambda p: p.stat().st_mtime)
        mtime = jsonl.stat().st_mtime
        task = _claude_task_from_jsonl(jsonl)
        if task is None:
            continue
        cwd = meta.get("cwd")
        if cwd:
            task.detail = Path(cwd).name
        entries.append((_claude_session_priority(meta, task), mtime, task))

    entries.sort(key=lambda e: (e[0], e[1]), reverse=True)
    return [task for _, _, task in entries]


def collect_claude_task() -> Task | None:
    tasks = collect_claude_tasks()
    return tasks[0] if tasks else None


def _claude_session_priority(meta: dict, task: Task) -> int:
    if task.status == TaskStatus.RUNNING:
        return 2
    if meta.get("status") == "busy":
        return 1
    return 0


def _claude_user_text(obj: dict) -> str:
    if obj.get("isMeta"):
        return ""
    content = obj.get("message", {}).get("content")
    text = ""
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = str(item.get("text", "")).strip()
                if text:
                    break
    if _is_claude_internal_user_text(text):
        return ""
    return text


def _is_claude_internal_user_text(text: str) -> bool:
    if not text:
        return True
    stripped = text.lstrip()
    internal_prefixes = (
        "<task-notification",
        "<ide_opened_file",
        "<command-name",
        "<command-message",
        "<local-command-stdout",
        "<local-command-stderr",
    )
    return stripped.startswith(internal_prefixes)


def _claude_task_from_jsonl(path: Path) -> Task | None:
    last_user_text: str | None = None
    last_type: str | None = None
    last_ts: str | None = None
    last_stop: str | None = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            t = obj.get("type")
            if t not in ("user", "assistant"):
                continue
            if t == "user" and not _claude_user_text(obj):
                continue
            if last_type is None:
                last_type = t
                last_ts = obj.get("timestamp")
                if t == "assistant":
                    last_stop = obj.get("message", {}).get("stop_reason")
            if t == "user" and not last_user_text:
                last_user_text = _claude_user_text(obj)
            if last_user_text and last_type:
                break
    except Exception:
        return None

    if not last_user_text:
        return None

    # 3-state: running (working) / needs_action (turn ended, waiting for you).
    # idle is only emitted by collect()'s fallback when no session is alive.
    status = TaskStatus.RUNNING
    if last_type == "assistant" and last_stop != "tool_use":
        status = TaskStatus.NEEDS_ACTION

    name = last_user_text.replace("\n", " ")[:50]
    return Task(name=name, status=status)


# ---------------------------------------------------------------------------
# Codex
# ---------------------------------------------------------------------------

def _codex_main_sessions() -> list[Path]:
    """Return main (non-subagent) Codex session files, newest last."""
    files = sorted(Path.home().glob(".codex/sessions/**/*.jsonl"))
    result = []
    for f in files:
        try:
            first = json.loads(f.open().readline())
            if first.get("payload", {}).get("source") == "vscode":
                result.append(f)
        except Exception:
            continue
    return result


def _codex_latest_rate_limits() -> dict | None:
    """Newest account-wide rate_limits across ALL codex sessions.

    Rate limits are account-scoped, so quota may be consumed in cli/subagent
    sessions that ``_codex_main_sessions`` (vscode-only) ignores. The most
    recently modified session file holds the freshest token_count.
    """
    files = sorted(
        Path.home().glob(".codex/sessions/**/*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for f in files:
        rate_limits: dict | None = None
        try:
            for line in f.open():
                obj = json.loads(line)
                if obj.get("type") == "event_msg":
                    p = obj.get("payload", {})
                    if p.get("type") == "token_count" and p.get("rate_limits"):
                        rate_limits = p["rate_limits"]
        except Exception:
            continue
        if rate_limits:
            return rate_limits
    return None


def _codex_auth() -> tuple[str, str]:
    """(access_token, account_id) from mac keychain or ~/.codex/auth.json."""
    creds = _keychain_json(_CODEX_KEYCHAIN_SERVICE)
    tokens = creds.get("tokens") if isinstance(creds, dict) else None
    if not tokens:
        try:
            data = json.loads((Path.home() / ".codex" / "auth.json").read_text())
            tokens = data.get("tokens", {})
        except Exception:
            tokens = {}
    if not isinstance(tokens, dict):
        return "", ""
    return tokens.get("access_token", ""), tokens.get("account_id", "")


def _codex_quotas_from_api() -> list[Quota] | None:
    """Live, real-time quota — same endpoint the Codex IDE uses.

    Session-log token_count only snapshots the *last completed turn*, so it
    lags behind actual consumption. The usage API is authoritative.
    """
    token, account_id = _codex_auth()
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    if account_id:
        headers["chatgpt-account-id"] = account_id
    data = _get(_CODEX_USAGE_URL, headers)
    if not data:
        return None
    rl = data.get("rate_limit") or {}
    quotas: list[Quota] = []
    api_map = [
        ("primary_window",   "five_hour", "5小时额度"),
        ("secondary_window", "weekly",    "7日额度"),
    ]
    for key, window, label in api_map:
        entry = rl.get(key) or {}
        used = entry.get("used_percent")
        if used is None:
            continue
        resets_at = ""
        ts = entry.get("reset_at")
        if ts:
            resets_at = _fmt_reset(datetime.fromtimestamp(ts, tz=timezone.utc))
        quotas.append(Quota(
            agent="codex", window=window, label=label,
            used=float(used), limit=100.0, reset_at=resets_at,
        ))
    return quotas or None


def collect_codex_quotas() -> list[Quota]:
    global _codex_quota_cache
    now = time.monotonic()
    if _codex_quota_cache and now - _codex_quota_cache[0] < _QUOTA_TTL:
        return _codex_quota_cache[1]

    cached = _file_cache_read("codex")
    if cached is not None:
        _codex_quota_cache = (now, cached)
        return cached

    api_quotas = _codex_quotas_from_api()
    if api_quotas:
        _codex_quota_cache = (now, api_quotas)
        _file_cache_write("codex", api_quotas)
        return api_quotas

    # Fallback: stale session-log snapshot (only if the API is unreachable).
    rate_limits = _codex_latest_rate_limits()

    if not rate_limits:
        stale = (_codex_quota_cache[1] if _codex_quota_cache else None) or _file_cache_read("codex", ignore_ttl=True)
        return stale or []

    quotas: list[Quota] = []
    window_map = [
        ("primary",   "five_hour", "5小时额度"),
        ("secondary", "weekly",    "7日额度"),
    ]
    for key, window, label in window_map:
        entry = rate_limits.get(key) or {}
        used = entry.get("used_percent")
        if used is None:
            continue
        resets_at = ""
        ts = entry.get("resets_at")
        if ts:
            resets_at = _fmt_reset(datetime.fromtimestamp(ts, tz=timezone.utc))
        quotas.append(Quota(
            agent="codex", window=window, label=label,
            used=float(used), limit=100.0, reset_at=resets_at,
        ))
    _codex_quota_cache = (now, quotas)
    _file_cache_write("codex", quotas)
    return quotas


def collect_codex_task() -> Task | None:
    sessions = _codex_main_sessions()
    if sessions:
        task = _codex_task_from_jsonl(sessions[-1])
        if task is not None:
            return task

    db_path = Path.home() / ".codex" / "state_5.sqlite"
    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        rows = conn.execute(
            """SELECT first_user_message, created_at, updated_at
               FROM threads
               WHERE source = 'vscode' AND thread_source = 'user'
               ORDER BY rowid DESC LIMIT 1"""
        ).fetchall()
        conn.close()
    except Exception:
        return None

    if not rows:
        return None

    first_msg, created_at, updated_at = rows[0]
    if not first_msg:
        return None

    # Determine status from latest session JSONL
    status = _codex_status_from_jsonl() or TaskStatus.IDLE

    name = str(first_msg).replace("\n", " ")[:50]
    return Task(name=name, status=status)


def _codex_task_from_jsonl(path: Path) -> Task | None:
    last_user_text: str | None = None
    last_task_event: str | None = None
    try:
        for line in path.open(encoding="utf-8"):
            obj = json.loads(line)
            if obj.get("type") != "event_msg":
                continue
            payload = obj.get("payload", {})
            if not isinstance(payload, dict):
                continue
            payload_type = payload.get("type")
            if payload_type == "user_message":
                text = str(payload.get("message", "")).strip()
                if text:
                    last_user_text = text
            elif payload_type in ("task_started", "task_complete"):
                last_task_event = payload_type
    except Exception:
        return None

    if not last_user_text:
        return None

    status = TaskStatus.IDLE
    if last_task_event == "task_started":
        status = TaskStatus.RUNNING
    elif last_task_event == "task_complete":
        status = TaskStatus.NEEDS_ACTION

    name = last_user_text.replace("\n", " ")[:50]
    return Task(name=name, status=status)


def _codex_status_from_jsonl() -> TaskStatus | None:
    sessions = _codex_main_sessions()
    if not sessions:
        return None
    latest = sessions[-1]
    last_task_event: str | None = None
    try:
        for line in latest.open():
            obj = json.loads(line)
            if obj.get("type") == "event_msg":
                pt = obj.get("payload", {}).get("type", "")
                if pt in ("task_started", "task_complete"):
                    last_task_event = pt
    except Exception:
        return None

    if last_task_event == "task_started":
        return TaskStatus.RUNNING
    if last_task_event == "task_complete":
        return TaskStatus.NEEDS_ACTION
    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def collect() -> DisplayState:
    """Collect real-time quota and task data from Claude Code and Codex."""
    claude_quotas = collect_claude_quotas()
    claude_tasks = collect_claude_tasks() or [Task(name="等待任务", status=TaskStatus.IDLE)]
    codex_quotas = collect_codex_quotas()
    codex_task = collect_codex_task() or Task(name="等待任务", status=TaskStatus.IDLE)

    agents = [
        AgentState(agent="claude", label="Claude Code",
                   tasks=claude_tasks, quotas=claude_quotas),
        AgentState(agent="codex", label="Codex",
                   tasks=[codex_task], quotas=codex_quotas),
    ]
    state = DisplayState(agents=agents)
    state.touch()
    return state
