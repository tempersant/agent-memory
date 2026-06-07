"""Shared Agent Bridge state helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / ".agent" / "state.json"
HANDOFF_PATH = ROOT / ".agent" / "HANDOFF.md"
EVENTS_PATH = ROOT / ".agent" / "events.jsonl"
ANTIGRAVITY_PROMPT_PATH = ROOT / ".agent" / "ANTIGRAVITY_PROMPT.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_state() -> dict:
    if not STATE_PATH.is_file():
        raise FileNotFoundError(f"state not found: {STATE_PATH}")
    return json.loads(STATE_PATH.read_text())


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def append_event(actor: str, event: str, detail: str) -> None:
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": utc_now(),
        "actor": actor,
        "event": event,
        "detail": detail,
    }
    with EVENTS_PATH.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def find_next_pending(state: dict, explicit: str | None) -> str:
    stages: dict = state.get("stages", {})
    if explicit:
        if explicit not in stages:
            raise ValueError(f"unknown stage: {explicit}")
        return explicit
    for name, info in stages.items():
        if info.get("status") in (None, "pending"):
            return name
    raise ValueError("no pending stages")


def handoff_text() -> str:
    parts = []
    if HANDOFF_PATH.is_file():
        parts.append(HANDOFF_PATH.read_text())
    if STATE_PATH.is_file():
        parts.append("## state.json\n```json\n" + STATE_PATH.read_text() + "\n```")
    return "\n\n".join(parts) if parts else "(no handoff files)"


def build_cloud_prompt(state: dict, stage: str) -> str:
    handoff = HANDOFF_PATH.read_text() if HANDOFF_PATH.is_file() else "(no HANDOFF.md)"
    return f"""You are a Cursor Cloud Agent continuing work via Agent Bridge.

## Mandatory protocol (AGENTS.md)

1. Read `.agent/state.json`, `.agent/HANDOFF.md`, `.agent/events.jsonl`
2. Execute stage: **{stage}**
3. Update `.agent/state.json`:
   - Mark `{stage}` as `done` or `in_progress` with actor `cursor-cloud:<your-agent-id>`
   - Set `stage` field and `active_agent`
   - Add artifacts (PR URL, file paths)
4. Rewrite `.agent/HANDOFF.md` (Current stage / Done / Next step / Do not touch)
5. Append summary to `.agent/events.jsonl`
6. Commit all `.agent/` changes in your branch
7. Open or update PR with clear title: `agent: handoff {stage}`

## Current state.json

```json
{json.dumps(state, indent=2)}
```

## Current HANDOFF.md

{handoff}

Begin stage `{stage}` now. Minimal scope — only what this stage requires.
"""


def build_antigravity_prompt(state: dict, stage: str) -> str:
    return f"""Continue Agent Bridge work in Antigravity.

## Read first (already in project context)
- AGENTS.md, GEMINI.md
- .agent/HANDOFF.md
- .agent/state.json

## Your task
Execute stage: **{stage}**

## Before finishing
1. Update `.agent/state.json` — set actor to `antigravity`, stage status, artifacts
2. Rewrite `.agent/HANDOFF.md` (Current stage / Done / Next step / Do not touch)
3. Append one line to `.agent/events.jsonl`
4. Commit: `agent: handoff {stage}`

## Current stage in state.json
{state.get("stage")}

Work only on stage `{stage}`. Do not take over stages owned by cursor-cloud unless HANDOFF says so.
"""
