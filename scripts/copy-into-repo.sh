#!/usr/bin/env bash
# Copy Agent Bridge template into the current git repository.
set -euo pipefail

TEMPLATE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"

if [[ ! -d "$TARGET/.git" ]] && [[ "$TARGET" != "$(pwd)" ]]; then
  echo "WARN: $TARGET is not a git repo — files will still be copied" >&2
fi

copy_if_missing() {
  local src="$1" dest="$2"
  if [[ -e "$dest" ]]; then
    echo "skip (exists): $dest"
  else
    mkdir -p "$(dirname "$dest")"
    cp -R "$src" "$dest"
    echo "copied: $dest"
  fi
}

merge_file() {
  local src="$1" dest="$2"
  if [[ ! -f "$dest" ]]; then
    cp "$src" "$dest"
    echo "copied: $dest"
    return
  fi
  echo "skip (exists): $dest — merge manually if needed"
}

echo "Template: $TEMPLATE_DIR"
echo "Target:   $TARGET"

copy_if_missing "$TEMPLATE_DIR/.agent" "$TARGET/.agent"
copy_if_missing "$TEMPLATE_DIR/.cursor/hooks" "$TARGET/.cursor/hooks"
copy_if_missing "$TEMPLATE_DIR/.cursor/skills/agent-bridge" "$TARGET/.cursor/skills/agent-bridge"
copy_if_missing "$TEMPLATE_DIR/scripts" "$TARGET/scripts"

merge_file "$TEMPLATE_DIR/AGENTS.md" "$TARGET/AGENTS.md"
merge_file "$TEMPLATE_DIR/GEMINI.md" "$TARGET/GEMINI.md"
merge_file "$TEMPLATE_DIR/.agent/rules/agent-bridge.md" "$TARGET/.agent/rules/agent-bridge.md"
merge_file "$TEMPLATE_DIR/.cursor/hooks.json" "$TARGET/.cursor/hooks.json"
merge_file "$TEMPLATE_DIR/.cursor/rules/agent-bridge.mdc" "$TARGET/.cursor/rules/agent-bridge.mdc"
merge_file "$TEMPLATE_DIR/.cursor/mcp.json" "$TARGET/.cursor/mcp.json"

chmod +x "$TARGET/.agent/bootstrap/"*.sh "$TARGET/.cursor/hooks/"*.sh "$TARGET/scripts/"*.sh 2>/dev/null || true

echo ""
echo "Done. Next steps:"
echo "  1. cd $TARGET"
echo "  2. Customize .agent/state.json and .agent/manifest.yaml"
echo "  3. .agent/bootstrap/install.sh"
echo "  4. git add .agent .cursor AGENTS.md scripts && git commit -m 'chore: add agent bridge'"
