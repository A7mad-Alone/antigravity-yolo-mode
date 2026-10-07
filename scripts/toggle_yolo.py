#!/usr/bin/env python3
"""
toggle_yolo.py — Toggle YOLO Mode for the active Antigravity session.
Saves session state into ~/.gemini/yolo_sessions.json
"""

import sys
import os
import json
import argparse
from pathlib import Path

STATE_FILE = Path.home() / ".gemini" / "yolo_sessions.json"

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
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Toggle YOLO Mode for an Antigravity session")
    parser.add_argument("action", nargs="?", choices=["on", "off", "status", "toggle"], default="toggle")
    parser.add_argument("--session-id", default=None, help="Specific session/conversation ID")
    args = parser.parse_args()

    # Determine conversation ID if not explicitly provided
    # Fallback to 'current' or environment/default
    session_id = args.session_id or os.environ.get("AGY_CONVERSATION_ID", "current")

    state = load_state()
    sessions = state.setdefault("sessions", {})
    current_status = sessions.get(session_id, False)

    if args.action == "on":
        sessions[session_id] = True
        new_status = True
    elif args.action == "off":
        sessions[session_id] = False
        new_status = False
    elif args.action == "toggle":
        new_status = not current_status
        sessions[session_id] = new_status
    else: # status
        new_status = current_status

    save_state(state)

    if args.action == "status":
        print(f"YOLO Mode for session [{session_id}]: {'⚡ ENABLED (Autonomous)' if new_status else '🛡️ DISABLED (Guarded)'}")
    else:
        if new_status:
            print(f"⚡ YOLO Mode ACTIVATED for session [{session_id}].")
            print("   Autonomous tool execution enabled. Antigravity will auto-approve tools without confirmation.")
        else:
            print(f"🛡️ YOLO Mode DEACTIVATED for session [{session_id}].")
            print("   Safety guards active. Antigravity will prompt for sensitive actions.")

if __name__ == "__main__":
    main()
