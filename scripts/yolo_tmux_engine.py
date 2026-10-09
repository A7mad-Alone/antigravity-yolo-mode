#!/usr/bin/env python3
"""
yolo_tmux_engine.py — High-Performance Tmux-Backed Autonomous Approver for Antigravity

Monitors Antigravity running inside tmux sessions.
When YOLO Mode is active:
- Scans tmux pane buffer every 0.15s for tool confirmation prompts.
- Inspects the command against strict catastrophic security rules.
- Whitelists safe operations (including fast-forward git push, codex edits).
- If dangerous/catastrophic (e.g. rm -rf /, git push --force): Leaves prompt untouched for Mr. Stark to review manually.
- If safe: Instantly sends '1\n' via `tmux send-keys` to auto-approve.
"""

import sys
import os
import time
import json
import re
import signal
import subprocess
from pathlib import Path

STATE_FILE = Path.home() / ".gemini" / "yolo_sessions.json"
PID_FILE = Path.home() / ".gemini" / "yolo_tmux_engine.pid"
LOG_FILE = Path.home() / ".gemini" / "yolo_tmux_engine.log"

# Catastrophic operations that must NEVER be auto-approved
CATASTROPHIC_PATTERNS = [
    r"\brm\s+-[rf]{1,4}\s+/(?:\s|$|\*)",
    r"\bmkfs\b",
    r":\(\)\s*\{\s*:\|:&\s*\}\s*;",
    r">\s*/dev/sd[a-z]",
    r">\s*/dev/nvme[0-9]",
    r"\bdd\s+if=/dev/zero\s+of=/dev/sd",
    r"\bchmod\s+-r\s+777\s+/(?:\s|$|\*)",
    r"\bchown\s+-r\s+.*\s+/(?:\s|$|\*)",
    # Guard against destructive git pushes (force pushing, delete remote branch)
    r"\bgit\s+push\b.*(--force|-f|\+refs/)",
    r"\bgit\s+push\b.*:\w+",  # git push origin :branch (branch deletion)
    r"\bgit\s+push\b.*--delete",
]

def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except Exception:
        pass

def is_catastrophic(cmd_text: str) -> bool:
    clean = cmd_text.strip().lower()
    for pat in CATASTROPHIC_PATTERNS:
        if re.search(pat, clean):
            return True
    return False

def is_yolo_active() -> bool:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
            return bool(data.get("active", False))
        except Exception:
            pass
    return False

def get_target_panes():
    """Find all tmux panes hosting an agy process."""
    try:
        lines = subprocess.check_output(
            ["tmux", "list-panes", "-a", "-F", "#{session_name}:#{window_index}.#{pane_index} #{pane_pid}"],
            stderr=subprocess.DEVNULL
        ).decode().strip().splitlines()
    except Exception:
        return []

    # Map pane_pid -> target
    pane_map = {}
    for line in lines:
        parts = line.split()
        if len(parts) == 2:
            target, pid_str = parts
            try:
                pane_map[int(pid_str)] = target
            except ValueError:
                continue

    if not pane_map:
        return []

    # Check process table for agy processes whose ancestor is a pane_pid
    agy_panes = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            stat_file = proc / "stat"
            if not stat_file.exists():
                continue
            parts = stat_file.read_text().split()
            comm = parts[1].strip("()")
            if comm != "agy":
                continue
            
            # Walk up ppid
            curr_pid = int(proc.name)
            for _ in range(8):
                if curr_pid in pane_map:
                    agy_panes.append((pane_map[curr_pid], int(proc.name)))
                    break
                p_stat = Path(f"/proc/{curr_pid}/stat")
                if not p_stat.exists():
                    break
                p_parts = p_stat.read_text().split()
                ppid = int(p_parts[3])
                if ppid <= 1:
                    break
                curr_pid = ppid
        except Exception:
            continue

    return list(set(agy_panes))

def inspect_pane_and_approve(target: str, agy_pid: int):
    """Inspect pane content for approval prompt."""
    try:
        content = subprocess.check_output(
            ["tmux", "capture-pane", "-p", "-t", target, "-S", "-30"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="replace")
    except Exception:
        return

    # Check for confirmation prompt
    has_prompt = False
    if "Run this command?" in content and ("1. Yes, run command" in content or "1. Yes" in content):
        has_prompt = True
    elif "Allow creation of this file?" in content or "Allow access to this URL?" in content:
        has_prompt = True
    elif "Run tool?" in content:
        has_prompt = True

    if not has_prompt:
        return

    # Extract command if command prompt
    cmd_text = ""
    m = re.search(r"Requesting permission for:\s*\n\s*(.*?)\s*\n\s*Run this command\?", content, re.DOTALL)
    if m:
        cmd_text = m.group(1).strip()

    # Safety check
    if cmd_text and is_catastrophic(cmd_text):
        log(f"🛡️ SAFETY INTERVENTION: Blocked auto-approval for catastrophic command on {target}: {cmd_text[:60]}")
        # Do not send keys; let Mr. Stark review manually
        return

    # Auto-approve by sending '1' then Enter
    log(f"⚡ Auto-approving tool on {target} (agy PID {agy_pid}): {cmd_text[:50] or 'file/URL action'}")
    try:
        subprocess.run(["tmux", "send-keys", "-t", target, "1", "Enter"], check=False)
        # Brief pause to avoid rapid duplicate sending
        time.sleep(0.3)
    except Exception as e:
        log(f"Error sending keys to {target}: {e}")

def main():
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    def cleanup(sig, frame):
        try:
            if PID_FILE.exists():
                PID_FILE.unlink()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    log("YOLO Tmux Engine supervisor started.")
    try:
        while True:
            if is_yolo_active():
                panes = get_target_panes()
                for target, agy_pid in panes:
                    inspect_pane_and_approve(target, agy_pid)
            time.sleep(0.15)
    finally:
        cleanup(None, None)

if __name__ == "__main__":
    main()
