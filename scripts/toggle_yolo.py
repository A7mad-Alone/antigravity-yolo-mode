#!/usr/bin/env python3
"""
toggle_yolo.py — Per-Tmux-Session YOLO Mode for Antigravity

Controls:
1. yolo_sessions.json: Session tracking, active state, and mode ('session' or 'task') per tmux session.
2. yolo_tmux_engine.py: Starts/stops the background supervisor daemon when any session is active.
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

def get_current_session_id() -> str:
    """Detect current tmux session name, or fallback to AGY_CONVERSATION_ID / 'default'."""
    try:
        # Check if inside tmux
        out = subprocess.check_output(
            ["tmux", "display-message", "-p", "#{session_name}"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        if out:
            return out
    except Exception:
        pass

    return os.environ.get("AGY_CONVERSATION_ID", "default")

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Ensure sessions dict exists
                    data.setdefault("sessions", {})
                    return data
        except Exception:
            pass
    return {"sessions": {}}

def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def is_any_session_active(state: dict) -> bool:
    for sess_info in state.get("sessions", {}).values():
        if isinstance(sess_info, dict) and sess_info.get("active", False):
            return True
        elif sess_info is True:
            return True
    return False

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
    state["sessions"][session_id] = {
        "active": True,
        "mode": mode
    }
    # Keep legacy top-level active for backwards compat
    state["active"] = is_any_session_active(state)
    save_state(state)

    # Ensure background engine daemon is running
    start_tmux_engine()

    mode_label = "TASK (auto-deactivates when current task finishes)" if mode == "task" else "SESSION (active until /yolo off)"
    print(f"⚡ YOLO Mode ACTIVATED [{mode.upper()}] for tmux session [{session_id}].")
    print(f"   Scope: {mode_label}")
    print("   Autonomous tool execution enabled via high-speed Tmux Engine.")
    print("   🛡️ Catastrophic safeguards active: destructive commands remain guarded.")

def deactivate_yolo(session_id: str, reason: str = ""):
    state = load_state()
    if session_id in state["sessions"]:
        if isinstance(state["sessions"][session_id], dict):
            state["sessions"][session_id]["active"] = False
        else:
            state["sessions"][session_id] = False

    # Check if any other sessions are still active
    any_active = is_any_session_active(state)
    state["active"] = any_active
    save_state(state)

    # If no sessions remain active, stop the daemon
    if not any_active:
        stop_tmux_engine()

    reason_msg = f" ({reason})" if reason else ""
    print(f"🛡️ YOLO Mode DEACTIVATED{reason_msg} for tmux session [{session_id}].")
    print("   Guarded mode restored. Standard interactive confirmations active.")

def finish_task(session_id: str):
    """Called after a task completes. If mode for this session was 'task', deactivates YOLO."""
    state = load_state()
    sess_info = state.get("sessions", {}).get(session_id)
    if isinstance(sess_info, dict) and sess_info.get("active", False) and sess_info.get("mode") == "task":
        deactivate_yolo(session_id, reason="Task completed")
        return True
    return False

def reset_default():
    state = {"sessions": {}}
    save_state(state)
    stop_tmux_engine()
    print("YOLO state reset for all sessions.")

def print_status(session_id: str):
    state = load_state()
    sess_info = state.get("sessions", {}).get(session_id)
    is_active = False
    mode = "session"
    if isinstance(sess_info, dict):
        is_active = sess_info.get("active", False)
        mode = sess_info.get("mode", "session")
    elif sess_info is True:
        is_active = True

    engine_active = is_engine_running()
    print("YOLO Mode Status:")
    print(f"  Tmux Session     : {session_id}")
    print(f"  Autonomous Mode  : {'⚡ ENABLED' if is_active else '🛡️ DISABLED (Guarded)'}")
    print(f"  Scope / Flavor   : {mode.upper() if is_active else 'N/A'}")
    print(f"  Tmux Supervisor  : {'🟢 RUNNING' if engine_active else '⚪ STOPPED'}")
    print("\nAll Sessions Overview:")
    for name, data in state.get("sessions", {}).items():
        if isinstance(data, dict):
            status = '⚡ ON (' + data.get('mode', 'session').upper() + ')' if data.get('active') else '🛡️ OFF'
        else:
            status = '⚡ ON' if data else '🛡️ OFF'
        print(f"  - {name}: {status}")

def main():
    parser = argparse.ArgumentParser(description="Toggle YOLO Mode for an Antigravity tmux session")
    parser.add_argument("action", nargs="?", choices=["on", "off", "status", "toggle", "finish-task", "reset-default"], default="toggle")
    parser.add_argument("mode", nargs="?", choices=["session", "task"], default=None, help="Mode flavor for 'on' (session or task)")
    parser.add_argument("--mode", dest="opt_mode", choices=["session", "task"], default=None, help="Alternative flag for mode flavor")
    parser.add_argument("--session-id", default=None, help="Specific session/conversation ID")
    args = parser.parse_args()

    session_id = args.session_id or get_current_session_id()
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
        sess_info = state.get("sessions", {}).get(session_id)
        currently_active = False
        if isinstance(sess_info, dict):
            currently_active = sess_info.get("active", False)
        elif sess_info is True:
            currently_active = True

        if currently_active:
            deactivate_yolo(session_id)
        else:
            activate_yolo(session_id, mode=target_mode)

if __name__ == "__main__":
    main()
