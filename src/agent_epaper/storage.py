from __future__ import annotations

import json
import os
from pathlib import Path

from .model import DisplayState


def default_state_path() -> Path:
    custom = os.environ.get("AGENT_EPAPER_STATE")
    if custom:
        return Path(custom).expanduser()
    return Path.home() / ".agent-epaper" / "state.json"


def load_state(path: Path | None = None) -> DisplayState:
    state_path = path or default_state_path()
    if not state_path.exists():
        state = DisplayState()
        save_state(state, state_path)
        return state
    with state_path.open("r", encoding="utf-8") as handle:
        return DisplayState.from_dict(json.load(handle))


def save_state(state: DisplayState, path: Path | None = None) -> Path:
    state_path = path or default_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = state_path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(state.to_dict(), handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    tmp_path.replace(state_path)
    return state_path
