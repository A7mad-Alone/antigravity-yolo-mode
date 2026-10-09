#!/usr/bin/env python3
"""
toggle_yolo.py — Toggle YOLO Mode for Antigravity (Tmux Autonomous Engine + Native Safety)

Controls:
1. yolo_sessions.json: Session tracking and state storage
2. yolo_tmux_engine.py: Starts/stops the high-speed background tmux supervisor
3. settings.json: Ensures toolPermission is kept clean
"""

import sys
import os
import json
import subprocess
import signal
import argparse
from pathlib import Path

STATE_FILE = Path.home() / ".gemini" / "yolo_sessions.json"
PID_FILE = Path.home() / ".gemini" / "yolo_tmux_engine.pid"
SCRIPT_DIR = Path(__file__).parent.resolve()
TMUX_ENGINE_SCRIPT = SCRIPT_DIR / "yolo_tmux_engine.py"

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"active": False, "sessions": {}}

def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def is_engine_running() -> bool:
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            return True
        except Exception:
            pass
    return False

def start_tmux_engine():
    if is_engine_running():
        return
    if not TMUX_ENGINE_SCRIPT.exists():
        return
    try:
        subprocess.Popen(
            [sys.executable, str(TMUX_ENGINE_SCRIPT)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True
        )
    except Exception as e:
        print(f"Error starting tmux engine: {e}")

def stop_tmux_engine():
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        try:
            PID_FILE.unlink()
        except Exception:
            pass

def activate_yolo(session_id: str):
    # 1. Update state
    state = load_state()
    state["active"] = True
    sessions = state.setdefault("sessions", {})
    sessions[session_id] = True
    sessions["current"] = True
    save_state(state)

    # 2. Launch background tmux approver engine
    start_tmux_engine()

    print(f"⚡ YOLO Mode ACTIVATED for session [{session_id}].")
    print("   Autonomous tool execution enabled via high-speed Tmux Engine.")
    print("   🛡️ Catastrophic safeguards active: destructive commands will prompt for review.")

def deactivate_yolo(session_id: str):
    # 1. Update state
    state = load_state()
    state["active"] = False
    sessions = state.setdefault("sessions", {})
    sessions[session_id] = False
    sessions["current"] = False
    save_state(state)

    # 2. Stop engine
    stop_tmux_engine()

    print(f"🛡️ YOLO Mode DEACTIVATED for session [{session_id}].")
    print("   Guarded mode restored. Standard interactive confirmations active.")

def reset_default():
    state = load_state()
    state["active"] = False
    sessions = state.setdefault("sessions", {})
    sessions["current"] = False
    save_state(state)
    stop_tmux_engine()

def print_status(session_id: str):
    state = load_state()
    is_active = state.get("active", False)
    engine_active = is_engine_running()
    print("YOLO Mode Status:")
    print(f"  Session ID       : {session_id}")
    print(f"  Autonomous Mode  : {'⚡ ENABLED' if is_active else '🛡️ DISABLED (Guarded)'}")
    print(f"  Tmux Engine      : {'🟢 RUNNING' if engine_active else '⚪ STOPPED'}")

def main():
    parser = argparse.ArgumentParser(description="Toggle YOLO Mode for an Antigravity session")
    parser.add_argument("action", nargs="?", choices=["on", "off", "status", "toggle", "reset-default"], default="toggle")
    parser.add_argument("--session-id", default=None, help="Specific session/conversation ID")
    args = parser.parse_args()

    session_id = args.session_id or os.environ.get("AGY_CONVERSATION_ID", "current")

    if args.action == "on":
        activate_yolo(session_id)
    elif args.action == "off":
        deactivate_yolo(session_id)
    elif args.action == "reset-default":
        reset_default()
    elif args.action == "status":
        print_status(session_id)
    elif args.action == "toggle":
        state = load_state()
        if state.get("active", False):
            deactivate_yolo(session_id)
        else:
            activate_yolo(session_id)

if __name__ == "__main__":
    main()
