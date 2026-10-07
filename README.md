# Antigravity YOLO Mode

A native, standalone autonomous execution mode for **Google Antigravity (`agy`)**, completely decoupled from Coucou or other UI companions.

## Features

- **Togglable via Slash Command:**
  - `/yolo` (or `/yolo on`) — Activate autonomous mode for the current session.
  - `/yolo off` — Revert to guarded mode (standard interactive approval prompts).
  - `/yolo status` — Inspect the active session's YOLO state.
- **Session-Scoped State:**
  - Persisted in `~/.gemini/yolo_sessions.json`.
  - Sessions remain isolated; enabling YOLO in one terminal does not bypass security in others.
- **Automatic Reset on Exit:**
  - Intercepts Antigravity's `Stop` lifecycle event to automatically deactivate YOLO mode when exiting the session.
  - Every new Antigravity session **always starts in guarded mode by default**.
- **Catastrophic Action Safeguards:**
  - Hardcoded failsafes block auto-approval of destructive operations (e.g. `rm -rf /`, `mkfs`, raw device writes), forcing manual human confirmation even in YOLO mode.

## Architecture

- **`scripts/yolo_gate.py`**: The Antigravity lifecycle hook handler for `PreToolUse` and `Stop` events.
- **`scripts/toggle_yolo.py`**: State toggle utility invoked by the `/yolo` skill.
- **`SKILL.md`**: The Antigravity skill declaration mounted in the Capability Hub.

## Installation / Hook Registration

To register the lifecycle hooks in `~/.gemini/config/hooks.json`:

```json
{
  "yolo-mode": {
    "enabled": true,
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /home/a7mad-alone/starkslab/services/network-storage/internal-nas/Codex/Skills/yolo-mode/scripts/yolo_gate.py --event PreToolUse"
          }
        ]
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python3 /home/a7mad-alone/starkslab/services/network-storage/internal-nas/Codex/Skills/yolo-mode/scripts/yolo_gate.py --event Stop"
      }
    ]
  }
}
```
