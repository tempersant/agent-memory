# Antigravity — Agent Bridge

Antigravity-specific instructions. Universal protocol is in `AGENTS.md`.

## Session start (every task)

1. Read `.agent/HANDOFF.md` and `.agent/state.json` before any edits.
2. If `.agent/ANTIGRAVITY_PROMPT.md` exists — follow that task prompt.
3. Work only on the current `stage` unless the user overrides.

## Session end (before you stop)

1. Update `.agent/state.json`:
   - `actor`: `antigravity`
   - stage `status`, `at` (ISO UTC), `artifacts`
2. Rewrite `.agent/HANDOFF.md` — sections: Current stage, Done, Next step, Do not touch
3. Append one line to `.agent/events.jsonl`
4. Tell the user to commit:
   ```bash
   git add .agent/
   git commit -m "agent: handoff <stage>"
   ```

## Handoff to Cloud

After commit and push:

```bash
export CURSOR_API_KEY="cursor_..."
python3 scripts/handoff.py --to cloud --repo owner/repo
```

## Handoff from Cloud

After Cloud PR is merged:

```bash
python3 scripts/handoff.py sync
```

Then continue in Antigravity — HANDOFF.md has the latest context.
