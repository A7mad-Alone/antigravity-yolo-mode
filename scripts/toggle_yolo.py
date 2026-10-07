#!/usr/bin/env python3
"""
toggle_yolo.py — Toggle YOLO Mode for the active Antigravity session.
Coordinates:
1. settings.json: toolPermission ("always-proceed" vs "request-review")
2. yolo_sessions.json: Session tracking and state storage
3. yolo_watchdog.py: Background process supervisor that auto-resets on session exit
"""

import sys
import os
import json
import subprocess
import signal
import argparse
from pathlib import Path

SETTINGS_FILE = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
STATE_FILE = Path.home() / ".gemini" / "yolo_sessions.json"
PID_FILE = Path.home() / ".gemini" / "yolo_watchdog.pid"
SCRIPT_DIR = Path(__file__).parent.resolve()
WATCHDOG_SCRIPT = SCRIPT_DIR / "yolo_watchdog.py"

def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_settings(data: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

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

def find_agy_pid() -> int | None:
    """Find the active agy process, prioritizing ancestors or running agy instances."""
    # Check parent PID chain
    try:
        curr = os.getpid()
        for _ in range(10):
            stat_file = Path(f"/proc/{curr}/stat")
            if not stat_file.exists():
                break
            with open(stat_file, "r") as f:
                parts = f.read().split()
            comm = parts[1].strip("()")
            ppid = int(parts[3])
            if comm == "agy":
                return curr
            if ppid <= 1:
                break
            curr = ppid
    except Exception:
        pass

    # Search running processes for agy
    try:
        for proc_dir in Path("/proc").iterdir():
            if proc_dir.name.isdigit():
                try:
                    comm_file = proc_dir / "comm"
                    if comm_file.exists() and comm_file.read_text().strip() == "agy":
                        return int(proc_dir.name)
                except Exception:
                    continue
    except Exception:
        pass

    return None

def stop_watchdog():
    if PID_FILE.exists():
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        try:
            PID_FILE.unlink()
        except Exception:
            pass

def start_watchdog(target_pid: int | None):
    stop_watchdog()
    if not WATCHDOG_SCRIPT.exists():
        return
    cmd = [sys.executable, str(WATCHDOG_SCRIPT)]
    if target_pid:
        cmd.append(str(target_pid))
    try:
        subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True
        )
    except Exception:
        pass

def activate_yolo(session_id: str):
    # 1. Update settings.json to always-proceed
    settings = load_settings()
    settings["toolPermission"] = "always-proceed"
    save_settings(settings)

    # 2. Locate agy PID and spawn watchdog
    agy_pid = find_agy_pid()
    start_watchdog(agy_pid)

    # 3. Update session state
    state = load_state()
    state["active"] = True
    state["pid"] = agy_pid
    sessions = state.setdefault("sessions", {})
    sessions[session_id] = True
    sessions["current"] = True
    save_state(state)

    print(f"⚡ YOLO Mode ACTIVATED for session [{session_id}].")
    print("   Autonomous tool execution enabled (toolPermission = always-proceed).")
    if agy_pid:
        print(f"   Supervisor attached to agy (PID: {agy_pid}). Auto-resets to Guarded on exit.")

def deactivate_yolo(session_id: str):
    # 1. Update settings.json to request-review
    settings = load_settings()
    settings["toolPermission"] = "request-review"
    save_settings(settings)

    # 2. Stop watchdog
    stop_watchdog()

    # 3. Update state
    state = load_state()
    state["active"] = False
    state["pid"] = None
    sessions = state.setdefault("sessions", {})
    sessions[session_id] = False
    sessions["current"] = False
    save_state(state)

    print(f"🛡️ YOLO Mode DEACTIVATED for session [{session_id}].")
    print("   Guarded mode restored (toolPermission = request-review). Prompts active.")

def reset_default():
    settings = load_settings()
    settings["toolPermission"] = "request-review"
    save_settings(settings)
    stop_watchdog()
    state = load_state()
    state["active"] = False
    state["pid"] = None
    sessions = state.setdefault("sessions", {})
    sessions["current"] = False
    save_state(state)

def print_status(session_id: str):
    settings = load_settings()
    tool_perm = settings.get("toolPermission", "request-review")
    state = load_state()
    is_active = state.get("active", False) or tool_perm == "always-proceed"
    print(f"YOLO Mode Status:")
    print(f"  Session ID       : {session_id}")
    print(f"  Active Status    : {'⚡ ENABLED (Autonomous)' if is_active else '🛡️ DISABLED (Guarded)'}")
    print(f"  toolPermission   : {tool_perm}")
    print(f"  Supervisor PID   : {state.get('pid', 'None')}")

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
        settings = load_settings()
        if settings.get("toolPermission") == "always-proceed":
            deactivate_yolo(session_id)
        else:
            activate_yolo(session_id)

if __name__ == "__main__":
    main()
