#!/usr/bin/env python3
"""
yolo_watchdog.py — Background process supervisor for Antigravity YOLO Mode.
Monitors the active Antigravity (agy) session PID.
When the agy process exits, this watchdog automatically resets tool permissions
in settings.json back to 'request-review' (Guarded mode), ensuring that subsequent
sessions never inherit YOLO mode by default.
"""

import os
import sys
import time
import json
import signal
from pathlib import Path

SETTINGS_FILE = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
STATE_FILE = Path.home() / ".gemini" / "yolo_sessions.json"
PID_FILE = Path.home() / ".gemini" / "yolo_watchdog.pid"

def is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def reset_to_guarded_mode():
    """Reset settings.json toolPermission back to request-review and mark state inactive."""
    # 1. Update settings.json
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            if data.get("toolPermission") != "request-review":
                data["toolPermission"] = "request-review"
                with open(SETTINGS_FILE, "w") as f:
                    json.dump(data, f, indent=2)
        except Exception:
            pass

    # 2. Update yolo_sessions.json
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            state["active"] = False
            state["pid"] = None
            if "sessions" in state:
                state["sessions"]["current"] = False
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

def clean_pid_file():
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
    except Exception:
        pass

def handle_signal(sig, frame):
    clean_pid_file()
    sys.exit(0)

def main():
    target_pid = None
    if len(sys.argv) > 1:
        try:
            target_pid = int(sys.argv[1])
        except ValueError:
            target_pid = None

    # Write own pid to PID_FILE
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        while True:
            time.sleep(1.0)
            if target_pid:
                if not is_pid_alive(target_pid):
                    # Target agy process died
                    reset_to_guarded_mode()
                    break
            else:
                # If no specific target PID was passed, check if any agy process exists
                # Read /proc or check pgrep
                # If no agy process is alive on the machine, revert to guarded
                try:
                    agy_running = False
                    for proc_dir in Path("/proc").iterdir():
                        if proc_dir.name.isdigit():
                            try:
                                comm_file = proc_dir / "comm"
                                if comm_file.exists() and comm_file.read_text().strip() == "agy":
                                    agy_running = True
                                    break
                            except Exception:
                                continue
                    if not agy_running:
                        reset_to_guarded_mode()
                        break
                except Exception:
                    pass
    finally:
        clean_pid_file()

if __name__ == "__main__":
    main()
