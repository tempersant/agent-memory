#!/usr/bin/env bash
# Shared helpers for Agent Bridge hooks
set -euo pipefail

bridge_root() {
  local input="${1:-}"
  python3 -c "
import json, sys, os
raw = sys.argv[1] if len(sys.argv) > 1 else ''
data = json.loads(raw) if raw.strip() else {}
roots = data.get('workspace_roots') or data.get('workspaceRoots') or []
root = roots[0] if roots else os.getcwd()
print(root)
" "$input"
}

bridge_append_event() {
  local root="$1" actor="$2" event="$3" detail="${4:-}"
  python3 - "$root" "$actor" "$event" "$detail" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path

root, actor, event, detail = sys.argv[1:5]
events = Path(root) / ".agent" / "events.jsonl"
events.parent.mkdir(parents=True, exist_ok=True)
row = {
    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "actor": actor,
    "event": event,
    "detail": detail,
}
with events.open("a") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
PY
}

bridge_read_handoff_context() {
  local root="$1"
  python3 - "$root" <<'PY'
import json, sys
from pathlib import Path

root = Path(sys.argv[1])
parts = []
for name in ("HANDOFF.md", "state.json"):
    p = root / ".agent" / name
    if p.is_file():
        parts.append(f"### .agent/{name}\n{p.read_text()[:8000]}")
if parts:
    print("\n\n".join(parts))
PY
}

bridge_actor() {
  local input="${1:-}"
  python3 -c "
import json, sys
data = json.loads(sys.argv[1]) if sys.argv[1].strip() else {}
cid = data.get('conversation_id') or data.get('conversationId') or 'unknown'
print(f'cursor-local:{cid[:8]}')
" "$input"
}
