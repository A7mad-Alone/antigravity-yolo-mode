#!/usr/bin/env python3
"""
yolo_gate.py — Antigravity Lifecycle Hook for YOLO Mode
Handles two events:
1. PreToolUse:
   If YOLO is ON for this conversationId/session, auto-approves actions (except catastrophic commands).
   If YOLO is OFF, delegates back to default permissions.
2. Stop:
   When an Antigravity session terminates/exits, automatically cleans up and deactivates YOLO mode
   for that session, ensuring the next session starts safely in Guarded mode by default.
"""

import sys
import os
import json
import argparse
from pathlib import Path

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
    return {"sessions": {}}

def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

def is_yolo_active(conversation_id: str) -> bool:
    state = load_state()
    sessions = state.get("sessions", {})
    if sessions.get(conversation_id, False) is True:
        return True
    if sessions.get("current", False) is True:
        return True
    return False

def clear_session_yolo(conversation_id: str):
    """Clean up and reset YOLO mode when session exits."""
    state = load_state()
    sessions = state.get("sessions", {})
    modified = False

    if conversation_id in sessions:
        sessions.pop(conversation_id, None)
        modified = True

    if "current" in sessions:
        sessions["current"] = False
        modified = True

    if modified:
        save_state(state)

def handle_pre_tool_use(data: dict):
    conversation_id = data.get("conversationId", "current")
    tool_call = data.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})

    if is_yolo_active(conversation_id):
        if is_catastrophic(tool_name, tool_args):
            out = {
                "decision": "force_ask",
                "reason": "🛡️ Action flagged as potentially catastrophic. Manual confirmation required even in YOLO mode."
            }
        else:
            out = {
                "decision": "allow",
                "reason": "⚡ Auto-approved by YOLO Mode."
            }
        sys.stdout.write(json.dumps(out) + "\n")
    else:
        # Pass-through to default Antigravity permissions
        sys.stdout.write(json.dumps({"decision": "ask"}) + "\n")
    sys.stdout.flush()

def handle_stop(data: dict):
    conversation_id = data.get("conversationId", "current")
    clear_session_yolo(conversation_id)
    # Stop hook expects empty or decision object; allow exit
    sys.stdout.write(json.dumps({}) + "\n")
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
