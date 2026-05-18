from __future__ import annotations

import json
import os
import tempfile
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
    tmp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=state_path.parent,
            prefix=f".{state_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_name = handle.name
            json.dump(state.to_dict(), handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        Path(tmp_name).replace(state_path)
    finally:
        if tmp_name:
            tmp_path = Path(tmp_name)
            if tmp_path.exists():
                tmp_path.unlink()
    return state_path
