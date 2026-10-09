# Antigravity YOLO Mode (Tmux Autonomous Engine)

A native, standalone autonomous execution mode for **Google Antigravity (`agy`)**, completely decoupled from Coucou or other UI companions, built specifically for tmux-based workflows with catastrophic command safety.

## Key Features

- **Togglable via Slash Command:**
  - `/yolo` (or `/yolo on`) — Activate autonomous mode for the current session.
  - `/yolo off` — Revert to guarded mode (standard interactive approval prompts).
  - `/yolo status` — Inspect the active session's YOLO state.
- **Tmux Autonomous Approver (`yolo_tmux_engine.py`):**
  - Monitors the active Antigravity tmux pane buffer in real time (0.15s polling).
  - Automatically identifies tool confirmation modals (`Run this command?`, `Allow creation of this file?`, `Allow access to this URL?`).
  - Sends immediate affirmative keystrokes (`1\n`) directly to the TUI pane.
- **Catastrophic Security Guardrails:**
  - Hardcoded regex patterns block auto-approval of destructive operations:
    - Recursive root deletions (`rm -rf /`, `rm -rf /*`)
    - Filesystem formatting (`mkfs`)
    - Fork bombs (`:(){ :|:& };:`)
    - Direct disk/partition block overwrites (`> /dev/sda`, `dd if=/dev/zero of=/dev/sd*`)
    - Wide permission escalations (`chmod -R 777 /`, `chown -R ... /`)
  - Catastrophic operations pause automatically for human review even in YOLO mode.
- **Zero-Failure Reset on Session Exit:**
  - When exiting the session, `~/.bashrc` wrapper automatically deactivates YOLO mode.
  - Every new Antigravity session **always starts in guarded mode by default**.

## Architecture

- **`scripts/yolo_tmux_engine.py`**: Background supervisor daemon that scans tmux panes and handles prompt responses with safety checks.
- **`scripts/toggle_yolo.py`**: State toggle utility invoked by the `/yolo` skill to activate/deactivate the tmux engine.
- **`SKILL.md`**: The Antigravity skill declaration mounted in the Capability Hub.

## Usage

Inside any Antigravity session running in `tmux`:
```bash
/yolo on     # ⚡ Autonomous mode enabled
/yolo off    # 🛡️ Guarded mode restored
/yolo status # Check current mode
```

Or start a dedicated autonomous session directly:
```bash
agy --dangerously-skip-permissions
```
