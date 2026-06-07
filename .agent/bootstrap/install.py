#!/usr/bin/env python3
"""Agent Bridge bootstrap — sync skills, validate rules, merge MCP."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[agent-bridge] ERROR: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def log(msg: str) -> None:
    print(f"[agent-bridge] {msg}")


def warn(msg: str) -> None:
    print(f"[agent-bridge] WARN: {msg}", file=sys.stderr)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    manifest_path = root / ".agent" / "manifest.yaml"
    if not manifest_path.is_file():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    data = yaml.safe_load(manifest_path.read_text())
    skills_dir = root / ".cursor" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Skills
    for item in data.get("skills", []):
        src = Path(os.path.expanduser(item["source"]))
        optional = bool(item.get("optional"))
        name = src.name
        dest = skills_dir / name
        if not src.is_dir():
            if optional:
                warn(f"optional skill missing, skip: {item['source']}")
            else:
                warn(f"required skill missing: {item['source']}")
            continue
        src_resolved = src.resolve()
        if dest.exists() or dest.is_symlink():
            try:
                if dest.resolve() == src_resolved:
                    log(f"skill in place: {name}")
                    continue
            except OSError:
                pass
            dest.unlink()
        dest.symlink_to(src_resolved)
        log(f"skill linked: {name} → {item['source']}")

    # Rules
    for rule in data.get("rules", []):
        path = root / rule
        if path.is_file():
            log(f"rule ok: {rule}")
        else:
            warn(f"rule missing: {rule}")

    # MCP merge
    mcp_cfg = data.get("mcp", {})
    servers = mcp_cfg.get("servers", {})
    if servers:
        mcp_target = root / mcp_cfg.get("merge_into", ".cursor/mcp.json")
        mcp_target.parent.mkdir(parents=True, exist_ok=True)
        existing: dict = {"mcpServers": {}}
        if mcp_target.is_file():
            existing = json.loads(mcp_target.read_text())
        existing.setdefault("mcpServers", {})
        for name, cfg in servers.items():
            entry: dict = {"command": cfg["command"], "args": cfg.get("args", [])}
            if cfg.get("env"):
                entry["env"] = dict(cfg["env"])
            existing["mcpServers"][name] = entry
            log(f"mcp merged: {name}")
        mcp_target.write_text(json.dumps(existing, indent=2) + "\n")

    # Hooks executable
    hooks_dir = root / ".cursor" / "hooks"
    if hooks_dir.is_dir():
        for hook in hooks_dir.glob("*.sh"):
            hook.chmod(hook.stat().st_mode | 0o111)
        log("hooks chmod +x")

    log("bootstrap complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
