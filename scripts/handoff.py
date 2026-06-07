#!/usr/bin/env python3
"""Unified Agent Bridge: Cloud ↔ Antigravity handoff.

Usage:
  python3 scripts/handoff.py status
  python3 scripts/handoff.py --to antigravity [--stage NAME] [--dry-run]
  python3 scripts/handoff.py --to cloud --repo owner/repo [--stage NAME] [--dry-run]
  python3 scripts/handoff.py sync
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from handoff_lib import (
    ANTIGRAVITY_PROMPT_PATH,
    ROOT,
    append_event,
    build_antigravity_prompt,
    build_cloud_prompt,
    find_next_pending,
    handoff_text,
    load_state,
    save_state,
    utc_now,
)


def cmd_status() -> int:
    state = load_state()
    print(f"process_id: {state.get('process_id')}")
    print(f"current stage: {state.get('stage')}")
    print(f"active_agent: {state.get('active_agent')}")
    print("\nStages:")
    for name, info in state.get("stages", {}).items():
        print(
            f"  - {name}: {info.get('status')} "
            f"(actor={info.get('actor')}, at={info.get('at')})"
        )
    print("\n--- HANDOFF preview ---")
    print(handoff_text()[:2000])
    return 0


def cmd_to_antigravity(stage: str | None, dry_run: bool) -> int:
    state = load_state()
    stage_name = find_next_pending(state, stage)

    if dry_run:
        print(f"# dry-run: antigravity stage={stage_name}")
        print(build_antigravity_prompt(state, stage_name))
        return 0

    state["stage"] = stage_name
    state["stages"].setdefault(stage_name, {})
    state["stages"][stage_name]["status"] = "in_progress"
    state["stages"][stage_name]["actor"] = "antigravity"
    state["stages"][stage_name]["at"] = utc_now()
    state["active_agent"] = {
        "runtime": "antigravity",
        "stage": stage_name,
        "started_at": utc_now(),
    }
    save_state(state)

    prompt = build_antigravity_prompt(state, stage_name)
    ANTIGRAVITY_PROMPT_PATH.write_text(prompt + "\n")
    append_event("handoff-cli", "delegate_antigravity", f"stage={stage_name}")

    print(f"[handoff] antigravity stage={stage_name}")
    print(f"[handoff] prompt saved: {ANTIGRAVITY_PROMPT_PATH}")
    print()
    print("Next steps:")
    print("  1. git add .agent/ && git commit -m 'agent: delegate to antigravity'")
    print("  2. Open this repo in Antigravity IDE")
    print("  3. Agent auto-loads GEMINI.md + AGENTS.md")
    print("  4. Optional: paste .agent/ANTIGRAVITY_PROMPT.md into chat")
    print("  5. After work — commit .agent/, then:")
    print("     python3 scripts/handoff.py --to cloud --repo owner/repo")
    return 0


def cmd_to_cloud(repo: str, stage: str | None, model: str, dry_run: bool) -> int:
    state = load_state()
    stage_name = find_next_pending(state, stage)
    prompt = build_cloud_prompt(state, stage_name)

    if dry_run:
        print(f"# dry-run: cloud stage={stage_name} repo={repo}")
        print(prompt)
        return 0

    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        print("CURSOR_API_KEY is required", file=sys.stderr)
        return 1

    try:
        from cursor_sdk import Agent, CloudAgentOptions, CursorAgentError
    except ImportError:
        print("pip install -r scripts/requirements.txt", file=sys.stderr)
        return 1

    state["stage"] = stage_name
    state["stages"].setdefault(stage_name, {})
    state["stages"][stage_name]["status"] = "in_progress"
    state["stages"][stage_name]["at"] = utc_now()
    state["active_agent"] = {"runtime": "cloud", "stage": stage_name, "started_at": utc_now()}
    save_state(state)
    append_event("handoff-cli", "delegate_cloud", f"stage={stage_name} repo={repo}")

    print(f"[handoff] cloud stage={stage_name} repo={repo}")
    try:
        with Agent.create(
            model=model,
            api_key=api_key,
            cloud=CloudAgentOptions(repos=[repo], auto_create_pr=True),
        ) as agent:
            print(f"[handoff] agent_id={agent.agent_id}")
            state["active_agent"]["agent_id"] = agent.agent_id
            save_state(state)

            run = agent.send(prompt)
            print(f"[handoff] run_id={run.id}")
            for message in run.messages():
                if message.type == "assistant":
                    for block in message.message.content:
                        if block.type == "text":
                            print(block.text, end="", flush=True)

            result = run.wait()
            print(f"\n[handoff] status={result.status}")
            if result.status == "error":
                state["stages"][stage_name]["status"] = "blocked"
                save_state(state)
                return 2
            print("\nNext steps:")
            print("  1. Review and merge Cloud Agent PR")
            print("  2. python3 scripts/handoff.py sync")
            print("  3. python3 scripts/handoff.py --to antigravity")
            return 0
    except CursorAgentError as err:
        print(f"[handoff] startup failed: {err.message}", file=sys.stderr)
        state["stages"][stage_name]["status"] = "pending"
        save_state(state)
        return 1


def cmd_sync(no_pull: bool) -> int:
    if not no_pull:
        try:
            subprocess.run(["git", "pull", "--rebase"], check=True, cwd=ROOT)
        except subprocess.CalledProcessError:
            print("git pull failed — resolve manually", file=sys.stderr)
            return 1
    print(handoff_text())
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Bridge: Cloud ↔ Antigravity")
    parser.add_argument("command", nargs="?", choices=["status", "sync"], help="Quick commands")
    parser.add_argument("--to", choices=["cloud", "antigravity"], help="Delegate to runtime")
    parser.add_argument("--repo", help="GitHub repo owner/name (required for --to cloud)")
    parser.add_argument("--stage", help="Stage name (default: first pending)")
    parser.add_argument("--model", default="composer-2.5")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-pull", action="store_true", help="For sync: skip git pull")
    args = parser.parse_args()

    try:
        if args.command == "status":
            return cmd_status()
        if args.command == "sync":
            return cmd_sync(args.no_pull)
        if args.to == "antigravity":
            return cmd_to_antigravity(args.stage, args.dry_run)
        if args.to == "cloud":
            if not args.repo:
                print("--repo owner/repo is required for --to cloud", file=sys.stderr)
                return 1
            return cmd_to_cloud(args.repo, args.stage, args.model, args.dry_run)
        parser.print_help()
        return 1
    except FileNotFoundError as err:
        print(err, file=sys.stderr)
        return 1
    except ValueError as err:
        print(err, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
