---
name: yolo-mode
description: >-
  Toggle autonomous YOLO Mode for Antigravity sessions via slash command /yolo or /yolo-mode.
  Supports 'session' and 'task' mode flavors. Auto-approves prompts via the background Tmux Engine while enforcing safety filters against catastrophic commands.
---

# YOLO Mode for Antigravity (Tmux Autonomous Engine)

YOLO Mode allows Antigravity to run fully autonomously within a specific session, automatically handling confirmation prompts for tools and commands while guarding against catastrophic operations.

## Modes of Operation

1. **Session Mode (`session`)**:
   - YOLO remains active across all prompt cycles until explicitly toggled off with `/yolo off`.
2. **Task Mode (`task`)**:
   - YOLO activates strictly for the current task/request.
   - Once the agent finishes the task and returns control to the user, YOLO mode automatically disengages, restoring guarded HITL mode.

## Triggering / Usage

You can invoke this skill using the slash command or request:
- `/yolo` or `/yolo-mode` (Toggles state)
- `/yolo on` / `/yolo on session` — Activate autonomous mode for the entire session.
- `/yolo on task` / `/yolo task` — Activate autonomous mode strictly for the current task.
- `/yolo off` — Revert to guarded mode (standard HITL confirmations).
- `/yolo status` — Check the current session's autonomous status and mode.

## Execution Procedure

When the user types `/yolo`, `/yolo on [session|task]`, `/yolo off`, or `/yolo status`:

1. Run the toggle script:
   ```bash
   # Session mode (default)
   python3 /home/a7mad-alone/starkslab/services/network-storage/internal-nas/Codex/Skills/yolo-mode/scripts/toggle_yolo.py on session

   # Task mode
   python3 /home/a7mad-alone/starkslab/services/network-storage/internal-nas/Codex/Skills/yolo-mode/scripts/toggle_yolo.py on task

   # Turn off
   python3 /home/a7mad-alone/starkslab/services/network-storage/internal-nas/Codex/Skills/yolo-mode/scripts/toggle_yolo.py off

   # Finish task (agent calls this at the conclusion of a task-mode request)
   python3 /home/a7mad-alone/starkslab/services/network-storage/internal-nas/Codex/Skills/yolo-mode/scripts/toggle_yolo.py finish-task
   ```

2. Confirm the state change to Mr. Stark:
   - If activated in **session** mode: Report that autonomous tool execution is live until deactivated.
   - If activated in **task** mode: Report that autonomous execution is live for this task only, and will auto-revert upon task completion.
   - If deactivated: Report that safety guards and approval prompts are re-engaged.

## Automatic Codex Inbox & GitHub Push Protocol

- **GitHub Pushes**: Standard fast-forward `git push` commands are allowed autonomously.
- **Codex Inbox Operations**: Modifications and additions in `Codex/Inbox/` follow a mandatory two-phase sync:
  1. Synchronize before changes (`git pull --rebase origin master`).
  2. Commit and `git push` immediately after inbox modifications.

## Catastrophic Safety Rails

Even in YOLO mode, critical catastrophic commands remain strictly guarded and will prompt for manual confirmation:
- `rm -rf /`, `rm -rf /*`
- `mkfs`, raw block device writes (`/dev/sd*`, `/dev/nvme*`)
- Fork bombs (`:(){ :|:& };:`)
- Blanket root permissions (`chmod -R 777 /`, `chown -R ... /`)
- Destructive git pushes (`git push --force`, `git push -f`, deleting remote branches)
