#!/usr/bin/env python3
"""
toggle_yolo.py — Toggle YOLO Mode for Antigravity (Tmux Autonomous Engine + Native Safety)

Controls:
1. yolo_sessions.json: Session tracking, active state, and mode ('session' or 'task')
2. yolo_tmux_engine.py: Starts/stops the high-speed background tmux supervisor
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
    return {"active": False, "mode": "session", "sessions": {}}

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

def activate_yolo(session_id: str, mode: str = "session"):
    mode = mode.lower()
    if mode not in ("session", "task"):
        mode = "session"

    state = load_state()
    state["active"] = True
    state["mode"] = mode
    sessions = state.setdefault("sessions", {})
    sessions[session_id] = True
    sessions["current"] = True
    save_state(state)

    # Launch background tmux approver engine
    start_tmux_engine()

    mode_label = "TASK (auto-deactivates when current task finishes)" if mode == "task" else "SESSION (active until /yolo off)"
    print(f"⚡ YOLO Mode ACTIVATED [{mode.upper()}] for session [{session_id}].")
    print(f"   Mode Scope: {mode_label}")
    print("   Autonomous tool execution enabled via high-speed Tmux Engine.")
    print("   🛡️ Catastrophic safeguards active: destructive commands (rm -rf /, git push -f, etc.) remain guarded.")

def deactivate_yolo(session_id: str, reason: str = ""):
    state = load_state()
    state["active"] = False
    state["mode"] = "session"
    sessions = state.setdefault("sessions", {})
    sessions[session_id] = False
    sessions["current"] = False
    save_state(state)

    stop_tmux_engine()

    reason_msg = f" ({reason})" if reason else ""
    print(f"🛡️ YOLO Mode DEACTIVATED{reason_msg} for session [{session_id}].")
    print("   Guarded mode restored. Standard interactive confirmations active.")

def finish_task(session_id: str):
    """Called after a task completes. If mode was 'task', deactivates YOLO."""
    state = load_state()
    if state.get("active", False) and state.get("mode") == "task":
        deactivate_yolo(session_id, reason="Task completed")
        return True
    return False

def reset_default():
    state = load_state()
    state["active"] = False
    state["mode"] = "session"
    sessions = state.setdefault("sessions", {})
    sessions["current"] = False
    save_state(state)
    stop_tmux_engine()

def print_status(session_id: str):
    state = load_state()
    is_active = state.get("active", False)
    mode = state.get("mode", "session")
    engine_active = is_engine_running()
    print("YOLO Mode Status:")
    print(f"  Session ID       : {session_id}")
    print(f"  Autonomous Mode  : {'⚡ ENABLED' if is_active else '🛡️ DISABLED (Guarded)'}")
    print(f"  Scope / Flavor   : {mode.upper() if is_active else 'N/A'}")
    print(f"  Tmux Engine      : {'🟢 RUNNING' if engine_active else '⚪ STOPPED'}")

def main():
    parser = argparse.ArgumentParser(description="Toggle YOLO Mode for an Antigravity session")
    parser.add_argument("action", nargs="?", choices=["on", "off", "status", "toggle", "finish-task", "reset-default"], default="toggle")
    parser.add_argument("mode", nargs="?", choices=["session", "task"], default=None, help="Mode flavor for 'on' (session or task)")
    parser.add_argument("--mode", dest="opt_mode", choices=["session", "task"], default=None, help="Alternative flag for mode flavor")
    parser.add_argument("--session-id", default=None, help="Specific session/conversation ID")
    args = parser.parse_args()

    session_id = args.session_id or os.environ.get("AGY_CONVERSATION_ID", "current")
    target_mode = args.mode or args.opt_mode or "session"

    if args.action == "on":
        activate_yolo(session_id, mode=target_mode)
    elif args.action == "off":
        deactivate_yolo(session_id)
    elif args.action == "finish-task":
        finish_task(session_id)
    elif args.action == "reset-default":
        reset_default()
    elif args.action == "status":
        print_status(session_id)
    elif args.action == "toggle":
        state = load_state()
        if state.get("active", False):
            deactivate_yolo(session_id)
        else:
            activate_yolo(session_id, mode=target_mode)

if __name__ == "__main__":
    main()
