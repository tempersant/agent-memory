#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=bridge-lib.sh
source "$SCRIPT_DIR/bridge-lib.sh"

input="$(cat)"
root="$(bridge_root "$input")"
actor="$(bridge_actor "$input")"

detail="$(python3 -c "
import json, sys
d = json.loads(sys.argv[1])
tool = d.get('tool_name') or d.get('toolName') or 'unknown'
success = d.get('success', True)
print(f'tool={tool} success={success}')
" "$input")"

bridge_append_event "$root" "$actor" "tool_use" "$detail"
echo '{}'
