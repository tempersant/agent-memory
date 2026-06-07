#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=bridge-lib.sh
source "$SCRIPT_DIR/bridge-lib.sh"

input="$(cat)"
root="$(bridge_root "$input")"
actor="$(bridge_actor "$input")"

bridge_append_event "$root" "$actor" "session_start" "Agent session started"

context="$(bridge_read_handoff_context "$root")"
if [[ -z "$context" ]]; then
  echo '{"continue": true}'
  exit 0
fi

python3 -c "
import json, sys
ctx = sys.argv[1]
payload = {
    'continue': True,
    'additional_context': (
        '## Agent Bridge — injected at session start\n'
        'Follow AGENTS.md handoff protocol. Update .agent/state.json and '
        '.agent/HANDOFF.md before you finish.\n\n' + ctx
    ),
}
print(json.dumps(payload, ensure_ascii=False))
" "$context"
