# Agent Memory

Git-native **память агентов** — handoff между Cursor IDE, Cloud Agent, Antigravity и Codex.

📖 **Полная инструкция:** [INSTRUCTION_RU.md](./INSTRUCTION_RU.md)  
📋 **Конспект диалога (для Claude / Antigravity):** [CONSPECT_RU.md](./CONSPECT_RU.md)

**Layers included (0–3):** `.agent/` state, bootstrap, Cursor hooks, Cloud SDK orchestrator.  
**Not included:** Bridge API (level 4).

## Quick start — new repo

Use this directory as-is, or copy into an existing project:

```bash
/path/to/agent-bridge-template/scripts/copy-into-repo.sh /path/to/your-repo
cd /path/to/your-repo
.agent/bootstrap/install.sh
```

## Quick start — existing repo

```bash
cd your-repo
~/Documents/Projects/agent-bridge-template/scripts/copy-into-repo.sh .
```

## Layout

```
.agent/
  manifest.yaml    # skills, rules, MCP declaration
  state.json       # process stages + actors
  HANDOFF.md       # context for next agent
  events.jsonl     # audit log
  bootstrap/       # install.sh → install.py
.cursor/
  hooks.json       # sessionStart, postToolUse, stop
  hooks/*.sh
  rules/agent-bridge.mdc
  skills/agent-bridge/
scripts/
  cloud-handoff.py # Cloud Agent orchestrator
  copy-into-repo.sh
AGENTS.md          # protocol for all models
```

## Cloud ↔ Antigravity bridge

```bash
python3 scripts/handoff.py status
python3 scripts/handoff.py --to antigravity --dry-run
python3 scripts/handoff.py --to antigravity

# Cloud (needs cursor-sdk + API key)
pip install -r scripts/requirements.txt
export CURSOR_API_KEY="cursor_..."
python3 scripts/handoff.py --to cloud --repo owner/repo --dry-run
python3 scripts/handoff.py --to cloud --repo owner/repo

# After Cloud PR merged
python3 scripts/handoff.py sync
```

**Antigravity** reads `GEMINI.md` + `AGENTS.md` automatically.  
**Cloud** gets prompt via SDK and commits `.agent/*` in a PR.

## Customize

1. Edit `.agent/state.json` — rename stages for your pipeline
2. Edit `.agent/manifest.yaml` — add skills, MCP, plugins
3. Re-run `.agent/bootstrap/install.sh`

## Hooks note

`sessionStart` injects HANDOFF via `additional_context`. If Cursor drops it (known IDE bug), the `agent-bridge.mdc` rule (`alwaysApply: true`) enforces the same protocol.
