#!/usr/bin/env python3
"""
yolo_gate.py — Antigravity Lifecycle Hook for YOLO Mode
Handles:
1. PreToolUse:
   - Catastrophic filter: Hard blocks / forces manual confirmation for catastrophic commands
     (e.g. rm -rf /, mkfs, fork bombs, raw disk overwrites) even in YOLO mode.
   - Standard operations: Returns {"decision": "allow"}.
     * When YOLO is ON (toolPermission: "always-proceed"), actions run autonomously.
     * When YOLO is OFF (toolPermission: "request-review"), the CLI prompts for confirmation normally.
   - Guaranteed deadlock-free: Always returns a valid decision string to satisfy Antigravity's contract.
2. Stop:
   - Emits empty object ({}) to allow normal turn completion.
"""

import sys
import os
import json
import argparse
from pathlib import Path

SETTINGS_FILE = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
STATE_FILE = Path.home() / ".gemini" / "yolo_sessions.json"

# Strict safety rules even in YOLO mode (prevent catastrophic accidental destruction)
CATASTROPHIC_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    ":(){ :|:& };:",
    "> /dev/sda",
    "> /dev/nvme",
    "dd if=/dev/zero of=/dev/sd",
]

def is_catastrophic(tool_name: str, args: dict) -> bool:
    if tool_name == "run_command":
        cmd = args.get("CommandLine", "").strip().lower()
        for pattern in CATASTROPHIC_PATTERNS:
            if pattern in cmd:
                return True
    return False

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"active": False, "sessions": {}}

def is_yolo_active(conversation_id: str) -> bool:
    # 1. Check yolo_sessions.json
    state = load_state()
    if state.get("active", False) is True:
        return True
    sessions = state.get("sessions", {})
    if sessions.get(conversation_id, False) is True:
        return True
    if sessions.get("current", False) is True:
        return True

    # 2. Check settings.json
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
            if settings.get("toolPermission") == "always-proceed":
                return True
        except Exception:
            pass

    return False

def handle_pre_tool_use(data: dict):
    conversation_id = data.get("conversationId", "current")
    tool_call = data.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})

    if is_catastrophic(tool_name, tool_args):
        out = {
            "decision": "force_ask",
            "reason": "🛡️ Action flagged as potentially catastrophic. Manual confirmation required even in YOLO mode."
        }
    elif is_yolo_active(conversation_id):
        out = {
            "decision": "allow",
            "reason": "⚡ Auto-approved by YOLO Mode."
        }
    else:
        # Guarded mode: pass to CLI tool_confirmation_manager
        out = {
            "decision": "allow"
        }

    sys.stdout.write(json.dumps(out) + "\n")
    sys.stdout.flush()

def handle_stop(data: dict):
    # Turn stop: allow exit cleanly
    sys.stdout.write("{}\n")
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", choices=["PreToolUse", "Stop"], default="PreToolUse")
    args = parser.parse_args()

    raw_input = sys.stdin.read()
    data = {}
    if raw_input.strip():
        try:
            data = json.loads(raw_input)
        except Exception:
            pass

    if args.event == "PreToolUse":
        handle_pre_tool_use(data)
    elif args.event == "Stop":
        handle_stop(data)

if __name__ == "__main__":
    main()
