# Phase 1: the pipe

Prove the whole chain with text only: game command, daemon, one agent CLI in a worktree,
events back in chat, and replay after a restart. No entities or screens yet.

**Exit criteria**

1. `/vibe run <prompt>` in singleplayer makes a Claude Code agent edit files in a new
   worktree, with its reads, edits and messages appearing in chat as they happen.
2. Quit the game mid-run, wait, reopen the world: the missed events replay in order with no
   duplicates, and the agent finished while the game was closed.
3. `./gradlew test` passes.

## TEST: test setup

- [ ] `P1-TEST-1` Add JUnit 5 to `build.gradle` for the main source set; `./gradlew test`
      runs.
- [ ] `P1-TEST-2` Helper that creates a throwaway git repo in a temp directory with one
      commit. All git tests use it; none touch the working repo.

## PROTO: protocol records

- [ ] `P1-PROTO-1` Records for `hello`, `welcome`, `cmd`, `reply`, `event`, `replay.done` as
      in [modules.md](modules.md); `PROTOCOL_VERSION = 1`.
- [ ] `P1-PROTO-2` Codec: object to one JSON line and back. Unknown fields are ignored and
      unknown event types are kept as raw data, so an older mod survives a newer daemon.
- [ ] `P1-PROTO-3` Test: round-trip every record; a line with an unknown type does not
      throw.

## CONFIG: state directory

- [ ] `P1-CONFIG-1` `StatePaths`: resolves `~/.vibecraft/` and every path in the layout;
      overridable with a system property so tests use a temp directory.
- [ ] `P1-CONFIG-2` Token: create 32 random bytes on first run, restrict the file to the
      owner (POSIX permissions where supported, ACL on Windows), read on later runs.
- [ ] `P1-CONFIG-3` `config.json` load with defaults when missing; unknown keys preserved on
      save. Phase 1 keys: `claudeCommand` (path override), `maxEventLineBytes`.

## LOG: event log

- [ ] `P1-LOG-1` `EventLog.append(goal, event)` assigns the next seq, writes one line,
      flushes. One writer thread per goal file.
- [ ] `P1-LOG-2` `EventLog.replay(goal, afterSeq, consumer)` streams lines after a seq
      without loading the file into memory.
- [ ] `P1-LOG-3` On open, recover the last seq by reading the tail; a torn final line (crash
      mid-write) is dropped, not fatal.
- [ ] `P1-LOG-4` Tests: append then replay from 0 and from the middle; torn last line;
      two goals do not share sequence numbers.

## NET: socket server

- [ ] `P1-NET-1` Listen on `127.0.0.1` with an ephemeral port; write it to `daemon.port`.
- [ ] `P1-NET-2` Handshake: first line must be `hello` with the right token and protocol
      within 5 seconds, else close. Compare tokens in constant time.
- [ ] `P1-NET-3` After `welcome`: replay each goal from the client's cursor, send
      `replay.done`, then subscribe the session to live events. No event may be lost or
      doubled across the switch from replay to live (hold the log lock or buffer live events
      during replay).
- [ ] `P1-NET-4` Route `cmd` lines to a handler table and send `reply`. A handler exception
      becomes `ok:false`, never a dropped connection.
- [ ] `P1-NET-5` Slow or dead clients: bounded per-session queue; on overflow drop the
      session (it will reconnect and replay), never block the agents.
- [ ] `P1-NET-6` Tests with a real socket: bad token rejected; replay then live with a
      concurrent appender yields a gapless sequence.

## GIT: worktrees

- [ ] `P1-GIT-1` `Git.run(dir, args)`: runs the `git` binary with a timeout, captures
      output, returns exit code. The argument list rejects `push`, `fetch`, `pull`, `remote`
      outright.
- [ ] `P1-GIT-2` `createWorktree(repo, taskId)`: branch `vibecraft/<taskId>` from the repo's
      current HEAD, worktree under the state directory. Fails clearly if the path is not a
      git repo or has no commits.
- [ ] `P1-GIT-3` `removeWorktree(repo, taskId, deleteBranch)`.
- [ ] `P1-GIT-4` Tests: create, commit inside, remove; the user's checkout and branch are
      untouched throughout; the deny-list throws.

## AGENT: runner and Claude Code adapter

- [ ] `P1-AGENT-1` **verify** the installed Claude Code CLI's headless invocation: prompt
      flag, streaming JSON output flag, how to set the working directory, permission mode
      for unattended edits, how to deny `git push`, how to resume a session. Record the CLI
      version and the exact command in the adapter's class comment.
- [ ] `P1-AGENT-2` Capture a real run's raw output into `src/test/resources/fixtures/` (a
      read, an edit, a shell command, a final message, usage numbers).
- [ ] `P1-AGENT-3` `AgentAdapter` interface: `command(spec)` builds the process arguments;
      `parse(line)` turns one output line into zero or more events. Nothing else.
- [ ] `P1-AGENT-4` `AgentProcess`: spawns in the worktree, reads stdout line by line on its
      own thread, feeds the adapter, appends events, captures stderr to the daemon log,
      emits `agent.status done` or `error` with the exit code.
- [ ] `P1-AGENT-5` Cancel kills the whole process tree (`ProcessHandle.descendants`), then
      the root. On Windows resolve `.cmd` shims and launch through `cmd /c`.
- [ ] `P1-AGENT-6` `ClaudeCodeAdapter` mapping stream lines to `agent.read`, `agent.edit`,
      `agent.command`, `agent.message`, `usage`.
- [ ] `P1-AGENT-7` CLI missing or not logged in yields one `error` event with a message the
      player can act on.
- [ ] `P1-AGENT-8` Tests: adapter against the fixture produces the expected event list;
      a fake "CLI" script proves cancel leaves no child process.

## LIFE: daemon main

- [ ] `P1-LIFE-1` `DaemonMain`: take `daemon.lock` with `FileChannel.tryLock`; if held, exit
      0 quietly. Then start CONFIG, LOG, NET.
- [ ] `P1-LIFE-2` Phase 1 command handlers: `project.set`, `run.start` (creates a one-task
      goal, worktree and agent), `run.stop`, `status`.
- [ ] `P1-LIFE-3` Log to `logs/daemon.log`; uncaught exceptions are logged, and the daemon
      keeps running unless NET itself is dead.
- [ ] `P1-LIFE-4` Clean shutdown on SIGTERM leaves agents running only if detached is
      intended; decide and document (default: daemon exit stops its agents).

## BRIDGE: mod side

- [ ] `P1-BRIDGE-1` `DaemonLauncher`: if `daemon.port` is missing or connection refused,
      start `java -cp <mod jar><sep><gson jar> ...DaemonMain` using the JVM binary of the
      current process, detached, with output redirected to the log. Jar locations come from
      each class's code source, which also works in the dev environment.
- [ ] `P1-BRIDGE-2` `DaemonClient`: connect, send `hello` with stored cursors, read lines on
      a dedicated thread, reconnect with backoff.
- [ ] `P1-BRIDGE-3` Every incoming line is handed to the server thread with
      `server.execute`; nothing on the tick thread waits on the socket.
- [ ] `P1-BRIDGE-4` Cursors (goal to last seq) persisted in world saved data so a reopened
      world resumes where it stopped.
- [ ] `P1-BRIDGE-5` Start on server started, close on server stopping. Closing the world
      must not stop the daemon.

## CMD and ACCESS

- [ ] `P1-ACCESS-1` `Access.canAct(player)`: true only for the singleplayer host or a
      server operator. Every command calls it. Phase 7 replaces the body, not the call
      sites.
- [ ] `P1-CMD-1` `/vibe project <path>`: validates it is a git repo, stores it.
- [ ] `P1-CMD-2` `/vibe run <prompt>`, `/vibe stop`, `/vibe status`.
- [ ] `P1-CMD-3` Event-to-chat formatter: one short line per event, edits show the path and
      +/- counts, long messages truncated.

## Things to consider

- A detached child on Windows can still die with the launcher's job object. Test by closing
  the game from the launcher, not only from the dev environment.
- Paths with spaces and non-ASCII characters in the user name, the repo path and prompts.
- Windows path length: worktree paths under the home directory plus deep repos can exceed
  260 characters. Keep task ids short.
- The game's JVM may be newer or older than what the daemon code needs; compile the daemon
  for the same Java release as the mod and it will match.
- Chat is a poor log viewer. Rate-limit event lines to chat (collapse bursts) so a busy
  agent does not flood it; the monitor in phase 2 replaces this.
- Decide now whether prompts are logged in full in `events.jsonl`. They may contain
  secrets the user pasted. Default: logged, and the README says where.
