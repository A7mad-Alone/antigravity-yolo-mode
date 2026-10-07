# Antigravity YOLO Mode

A native, standalone autonomous execution mode for **Google Antigravity (`agy`)**, completely decoupled from Coucou or other UI companions.

## Features

- **Togglable via Slash Command:**
  - `/yolo` (or `/yolo on`) — Activate autonomous mode for the current session.
  - `/yolo off` — Revert to guarded mode (standard interactive approval prompts).
  - `/yolo status` — Inspect the active session's YOLO state.
- **Dual Engine Control:**
  - Coordinates both Antigravity's native `toolPermission: always-proceed` setting and `PreToolUse` lifecycle hooks.
  - Instantaneous real-time sync without requiring CLI restarts.
- **Automatic Reset on Session Exit:**
  - Monitored by a lightweight background supervisor (`yolo_watchdog.py`) attached to the `agy` process PID.
  - Shell exit wrapper in `~/.bashrc` provides a zero-failure guarantee.
  - Every new Antigravity session **always starts in guarded mode by default**.
- **Catastrophic Action Safeguards:**
  - Hardcoded failsafes intercept and block auto-approval of destructive operations (e.g. `rm -rf /`, `mkfs`, fork bombs, raw device writes), forcing manual human confirmation even in YOLO mode.

## Architecture

- **`scripts/toggle_yolo.py`**: State toggle utility invoked by the `/yolo` skill. Synchronizes `settings.json`, session state, and starts the supervisor.
- **`scripts/yolo_watchdog.py`**: Lightweight background process supervisor that tracks the `agy` session PID and automatically resets permissions upon session exit.
- **`scripts/yolo_gate.py`**: The Antigravity lifecycle hook handler for `PreToolUse` events with catastrophic command filtering.
- **`SKILL.md`**: The Antigravity skill declaration mounted in the Capability Hub.

## Installation & Hook Registration

Registered in `~/.gemini/config/hooks.json`:

```json
{
  "yolo-mode": {
    "enabled": true,
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/a7mad-alone/starkslab/services/network-storage/internal-nas/Codex/Skills/yolo-mode/scripts/yolo_gate.py --event PreToolUse"
          }
        ]
      }
    ]
  }
}
```

## Shell Auto-Reset Wrapper

In `~/.bashrc`:

```bash
agy() {
    command agy "$@"
    local _agy_exit=$?
    python3 /home/a7mad-alone/starkslab/services/network-storage/internal-nas/Codex/Skills/yolo-mode/scripts/toggle_yolo.py reset-default >/dev/null 2>&1 || true
    return $_agy_exit
}
```
