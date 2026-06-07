#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=bridge-lib.sh
source "$SCRIPT_DIR/bridge-lib.sh"

input="$(cat)"
root="$(bridge_root "$input")"
actor="$(bridge_actor "$input")"

status="$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('status','unknown'))" "$input")"
bridge_append_event "$root" "$actor" "session_stop" "status=$status"

echo '{}'
