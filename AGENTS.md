# Agent Bridge Protocol

Every AI agent working in this repository **must** follow this handoff protocol.
Applies to: Cursor IDE, Cursor Cloud Agent, Claude Code, Codex, Antigravity, and any other coding agent.

## On session start (required)

Read these files **before** doing any work:

1. `.agent/HANDOFF.md` — human-readable context from the previous agent
2. `.agent/state.json` — current stage, actors, artifacts
3. `.agent/manifest.yaml` — available skills, rules, MCP (if bootstrap was run)

If `state.json` shows a stage `in_progress` owned by another actor, do not take it over unless HANDOFF says to continue or reset it.

## During work

- Work only on the stage assigned in `state.json` (or the stage the user explicitly requests).
- Log significant actions mentally; hooks append to `.agent/events.jsonl` automatically in Cursor.
- Do not modify unrelated files.

## On session end (required)

Before finishing, update:

1. **`.agent/state.json`**
   - Set your stage `status`: `done` | `in_progress` | `blocked` | `pending`
   - Set `actor`: `cursor-local`, `cursor-cloud:bc-<id>`, `codex`, `antigravity`, etc.
   - Set `at`: ISO-8601 UTC timestamp
   - Update `artifacts` paths/URLs (PR links, file paths)
   - Clear or set `active_agent`

2. **`.agent/HANDOFF.md`** — rewrite with exactly these sections:
   - `## Current stage`
   - `## Done` (bullet list)
   - `## Next step` (one clear action)
   - `## Do not touch` (files/branches to avoid)

3. **`.agent/events.jsonl`** — append one summary line if hooks did not already log stop:
   ```json
   {"ts":"<ISO>","actor":"<you>","event":"handoff","stage":"<stage>","detail":"<one line>"}
   ```

4. **Commit** `.agent/*` (separate commit preferred: `agent: handoff <stage>`).

## Cloud ↔ Antigravity handoff

Unified CLI:

```bash
python3 scripts/handoff.py status
python3 scripts/handoff.py --to antigravity
python3 scripts/handoff.py --to cloud --repo owner/repo
python3 scripts/handoff.py sync          # after Cloud PR merge
```

### Antigravity → Cloud

1. Finish work, update `.agent/*`, commit and push
2. `python3 scripts/handoff.py --to cloud --repo owner/repo`

### Cloud → Antigravity

1. Merge Cloud Agent PR
2. `python3 scripts/handoff.py sync`
3. Open repo in Antigravity (reads `GEMINI.md` + this file automatically)
4. Or: `python3 scripts/handoff.py --to antigravity` to prepare `.agent/ANTIGRAVITY_PROMPT.md`

Antigravity-specific rules: `GEMINI.md` and `.agent/rules/agent-bridge.md`

## Bootstrap (sync skills / rules / MCP)

```bash
.agent/bootstrap/install.sh
```

Run after cloning or when `manifest.yaml` changes.
