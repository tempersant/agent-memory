---
name: agent-bridge
description: >-
  Git-native handoff between Cursor local, Cloud Agent, Codex, and Antigravity.
  Use when starting or ending agent work, updating process stage, syncing skills/MCP,
  or delegating a stage to Cloud Agent via cloud-handoff.py.
---

# Agent Bridge

## Handoff protocol

1. Read `.agent/HANDOFF.md` and `.agent/state.json`
2. Work on the current or user-requested stage only
3. Update state + HANDOFF + events before finishing
4. Commit `.agent/`

See `AGENTS.md` for full contract.

## Bootstrap (sync manifest → environment)

```bash
.agent/bootstrap/install.sh
```

Requires `pyyaml` (`pip install pyyaml`).

## Cloud ↔ Antigravity

```bash
python3 scripts/handoff.py status
python3 scripts/handoff.py --to antigravity
export CURSOR_API_KEY="cursor_..."
python3 scripts/handoff.py --to cloud --repo owner/repo
python3 scripts/handoff.py sync
```

## Customize stages

Edit `.agent/state.json` `stages` object and `.agent/manifest.yaml` `default_stages` for your workflow.
