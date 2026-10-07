---
name: yolo-mode
description: >-
  Toggle autonomous YOLO Mode for the current Antigravity session via slash command /yolo.
  When active, Antigravity executes tools, scripts, and file modifications automatically without asking for manual permission confirmation.
---

# YOLO Mode for Antigravity

YOLO Mode allows Antigravity to run fully autonomously within a specific session, bypassing interactive confirmation prompts for commands and tool executions.

## Triggering / Usage

You can invoke this skill using the slash command or request:
- `/yolo` or `/yolo-mode`
- `/yolo on` — Activate autonomous mode for the current session.
- `/yolo off` — Revert to guarded mode (standard HITL confirmations).
- `/yolo status` — Check the current session's autonomous status.

## Execution Procedure

When the user types `/yolo`, `/yolo on`, `/yolo off`, or `/yolo status`, execute the helper script:

1. Run the toggle script:
   ```bash
   python3 /home/a7mad-alone/starkslab/services/network-storage/internal-nas/Codex/Skills/yolo-mode/scripts/toggle_yolo.py [on|off|status|toggle]
   ```

2. Confirm the state change to Mr. Stark:
   - If activated: Report that autonomous tool execution is now live.
   - If deactivated: Report that safety guards and approval prompts are re-engaged.

## Safety Rails in YOLO Mode

Even in YOLO mode, critical catastrophic commands (`rm -rf /`, `mkfs`, device overwrites) remain guarded and will prompt for confirmation to prevent accidental system destruction.
