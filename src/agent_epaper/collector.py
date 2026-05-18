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


def collect_claude_task() -> Task | None:
    sessions_dir = Path.home() / ".claude" / "sessions"
    if not sessions_dir.exists():
        return None

    projects_dir = Path.home() / ".claude" / "projects"

    # Among ALL alive sessions, pick the one whose transcript JSONL was most
    # recently modified — i.e. the conversation actually in use right now.
    # (Old code took the first glob hit, which could lock onto a stale
    # session whose transcript no longer exists and then give up.)
    best_transcript: Path | None = None
    best_mtime = -1.0
    for f in sessions_dir.glob("*.json"):
        try:
            meta = json.loads(f.read_text())
            pid = meta.get("pid")
            sid = meta.get("sessionId")
            if not (pid and sid):
                continue
            os.kill(pid, 0)   # raises if the process is dead
        except Exception:
            continue
        matches = list(projects_dir.glob(f"**/{sid}.jsonl"))
        if not matches:
            continue
        jsonl = max(matches, key=lambda p: p.stat().st_mtime)
        mtime = jsonl.stat().st_mtime
        if mtime > best_mtime:
            best_mtime, best_transcript = mtime, jsonl

    if best_transcript is None:
        return None

    # Walk the transcript backwards: capture the latest human prompt (task
    # name) and the type/stop_reason/timestamp of the most recent turn.
    last_user_text: str | None = None
    last_type: str | None = None
    last_ts: str | None = None
    last_stop: str | None = None
    try:
        lines = best_transcript.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            t = obj.get("type")
            if t not in ("user", "assistant"):
                continue
            if last_type is None:
                last_type = t
                last_ts = obj.get("timestamp")
                if t == "assistant":
                    last_stop = obj.get("message", {}).get("stop_reason")
            if t == "user" and not last_user_text:
                for c in obj.get("message", {}).get("content", []):
                    if isinstance(c, dict) and c.get("type") == "text":
                        txt = c["text"].strip()
                        if txt:
                            last_user_text = txt
                            break
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
        recent = False
        if last_ts:
            try:
                ts = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                recent = (datetime.now(timezone.utc) - ts).total_seconds() <= 20
            except Exception:
                recent = False
        if not recent:
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


def collect_codex_quotas() -> list[Quota]:
    global _codex_quota_cache
    now = time.monotonic()
    if _codex_quota_cache and now - _codex_quota_cache[0] < _QUOTA_TTL:
        return _codex_quota_cache[1]

    cached = _file_cache_read("codex")
    if cached is not None:
        _codex_quota_cache = (now, cached)
        return cached

    sessions = _codex_main_sessions()
    if not sessions:
        stale = (_codex_quota_cache[1] if _codex_quota_cache else None) or _file_cache_read("codex", ignore_ttl=True)
        return stale or []

    # Walk sessions newest-first until we find rate_limits
    rate_limits: dict | None = None
    for f in reversed(sessions):
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
            break

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
    claude_task = collect_claude_task() or Task(name="等待任务", status=TaskStatus.IDLE)
    codex_quotas = collect_codex_quotas()
    codex_task = collect_codex_task() or Task(name="等待任务", status=TaskStatus.IDLE)

    agents = [
        AgentState(agent="claude", label="Claude Code",
                   tasks=[claude_task], quotas=claude_quotas),
        AgentState(agent="codex", label="Codex",
                   tasks=[codex_task], quotas=codex_quotas),
    ]
    state = DisplayState(agents=agents)
    state.touch()
    return state
