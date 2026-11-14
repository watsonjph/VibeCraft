# Phase 6: lifecycle

Make "close the game and the agents keep working" dependable: catching up, crashing,
rebooting, growing logs and more than one project.

**Exit criteria**

1. Rejoining after an hour away shows a summary of what happened and a studio in the
   correct current state within a few seconds.
2. Killing the daemon mid-run and restarting it loses no completed work and offers to
   resume interrupted tasks.
3. The daemon exits by itself when there is nothing to do.
4. Two projects can run in two studios, in the same or different worlds.

## LIFE: daemon lifecycle

- [ ] `P6-LIFE-1` Idle exit: no running agents, no pending questions and no connected
      client for a configured time means a clean exit.
- [ ] `P6-LIFE-2` Startup recovery: rebuild goal and task state by replaying event logs.
      Tasks that were `working` with no live process become `failed` with reason
      `interrupted`, or resume automatically if the adapter supports resume and the setting
      allows.
- [ ] `P6-LIFE-3` Orphan processes: record agent process ids; on startup kill any that are
      still alive from a previous daemon before resuming.
- [ ] `P6-LIFE-4` Orphan worktrees: on startup list worktrees with no matching task and
      report them; remove only on an explicit command.
- [ ] `P6-LIFE-5` Version handshake: mod and daemon versions differ after a mod update.
      If the running daemon is older and idle, the mod asks it to exit and starts the new
      one; if it is busy, keep it and warn.
- [ ] `P6-LIFE-6` `/vibe daemon status|stop|restart` and a `daemon.shutdown` command.
- [ ] `P6-LIFE-7` Tests: recovery from a log that ends mid-task; idle exit timer.

## LOG: growth

- [ ] `P6-LOG-1` Snapshot: on goal completion write a compact summary (final task states,
      totals) so loading a finished goal does not replay everything.
- [ ] `P6-LOG-2` Archive: finished goals older than a configured age are compressed;
      `/vibe history` lists them.
- [ ] `P6-LOG-3` Size guard: a per-goal log size ceiling; beyond it, message bodies are
      truncated on write and a warning event is emitted.

## BRIDGE, DISPLAY, NPC: catching up

- [ ] `P6-BRIDGE-1` Fast-forward: during replay, apply events to `StudioMirror` without
      driving animations or sounds; render once at `replay.done`.
- [ ] `P6-BRIDGE-2` "While you were away" summary built from replayed events: tasks
      finished, tasks waiting for review, questions waiting, tokens used. Shown in chat and
      on the wall header.
- [ ] `P6-NPC-1` After fast-forward, NPCs appear at their correct places instead of walking
      there from their old ones.
- [ ] `P6-BRIDGE-3` Connection status: a visible indicator on the wall when the daemon is
      unreachable, with the reason.

## ORCH, CONFIG, STUDIO: many projects

- [ ] `P6-CONFIG-1` Project registry: id, repo path, display name. Detect a moved or
      deleted repo and say so.
- [ ] `P6-ORCH-1` Per-project scheduler limits plus a global `maxParallelAgents`.
- [ ] `P6-STUDIO-1` Several studios per world, each bound to one project; commands take the
      nearest studio by default.
- [ ] `P6-STUDIO-2` The same project opened from two worlds shows the same state in both.
- [ ] `P6-ORCH-2` Goal queue: a second goal on a project waits or runs alongside, by
      setting. Default: one active goal per project.

## Notifications

- [ ] `P6-NOTIFY-1` Optional desktop notification from the daemon when a question or a
      review is waiting and no client is connected (uses the JDK's system tray support;
      skip silently where unsupported).

## Things to consider

- A reboot ends everything. Whether to start the daemon at login is a user decision; offer
  the instructions, do not install anything automatically.
- A laptop going to sleep looks like a hung CLI. Use wall-clock gaps to detect resume from
  sleep and avoid declaring tasks dead.
- The user may delete a worktree or branch by hand. Treat missing ones as a failed task,
  not a daemon error.
- Event replay must be idempotent: applying the same event twice to `StudioMirror` gives
  the same state.
- Long absences mean large replays. Measure replay of a 100,000-event log and keep it
  under a few seconds, or lean on snapshots.
