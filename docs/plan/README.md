# VibeCraft plan

An agent IDE inside Minecraft. You type a goal; a lead agent reads your repo, writes a plan
and pins tasks to a wall. Worker NPCs sit at desks and code in their own git worktrees while
their monitors stream what they read and change. An agent walks over when a decision is
yours. You review the real diff and press Merge. Nothing touches your branch without that
click, and nothing is ever pushed. Close the game and the agents keep working; open it again
and the studio catches up.

Primary target is singleplayer. A dedicated server can run the mod so friends can watch and
interact; that is off by default and behind a warning (phase 7).

## How to use this plan

- [modules.md](modules.md) is the map: every code module, what it owns, what it may depend
  on, plus the wire protocol, event catalogue and on-disk layout. Read it first.
- Each phase file splits its work by module. Task ids look like `P1-LOG-2` (phase 1, module
  LOG, task 2). Use the id in commit messages and PR titles.
- A task is done when its checkbox is ticked in the phase file and its test (if it names
  one) passes. A phase is done when its exit criteria hold in a real game session.
- Within a phase, modules can be built in parallel unless a task lists `needs:`.
- Anything marked **verify** is an assumption about an external tool or the game. Check it
  against the real thing before building on it, and correct this plan if it was wrong.

## Architecture

```
 Minecraft client          Minecraft server              Daemon (own JVM)         Agent CLIs
 (screens, input)  <---->  (integrated or dedicated) <-> (sessions, worktrees, -> claude / codex /
   src/client       MC       src/main, not daemon/   TCP   event log, merge)       opencode
                  packets                           localhost   daemon/ package   one process per agent
```

- **Daemon.** A separate JVM started from the mod's own jar, on the machine that hosts the
  world. It owns every agent process, worktree and piece of state, which is why agents
  survive the game closing. JDK plus Gson only.
- **Transport.** Newline-delimited JSON over a TCP socket on 127.0.0.1, authenticated with a
  token from a file in the state directory.
- **Event log.** Every event is appended to a JSONL file per goal with a sequence number. A
  client connects with the last sequence it saw and receives the rest. Live streaming and
  catch-up are one code path.
- **Server side of the mod.** Holds the daemon connection, mirrors state into the world and
  enforces who may do what. In singleplayer this is the integrated server.
- **Client side of the mod.** Screens only. It never talks to the daemon directly.
- **Agents.** No agent loop of our own. Each adapter wraps an existing coding CLI in headless
  mode and translates its output into our events, so subscriptions work through the login
  the user already has.
- **Questions.** A small stdio MCP server offering `ask_user`, registered with each CLI, so
  "agent needs you" works the same across adapters.

## Phases

| # | Phase | Delivers | Needs |
|---|---|---|---|
| 0 | Init | Building Fabric scaffold (done) | |
| 1 | [The pipe](phase-1-pipe.md) | One agent in a worktree, events in chat, replay after restart | 0 |
| 2 | [The studio](phase-2-studio.md) | NPC, desk, live monitor in the world | 1 |
| 3 | [Orchestration](phase-3-orchestration.md) | Lead agent, task wall, parallel workers, questions | 2 |
| 4 | [Review and merge](phase-4-review-merge.md) | Diff screen, Merge / Request changes / Discard | 3 |
| 5 | [Models and identity](phase-5-models-identity.md) | Codex and opencode adapters, agent customisation | 1 (adapters), 3 (UI) |
| 6 | [Lifecycle](phase-6-lifecycle.md) | Catch-up summary, crash recovery, many projects | 4 |
| 7 | [Friends on a server](phase-7-multiplayer.md) | Shared access with warning, allowlist, budgets | 4 |
| 8 | [Release](phase-8-release.md) | README, CI, Modrinth | 4, ideally 5 to 7 |

Phases 5, 6 and 7 are independent of each other and can be done in any order after 4.

## Not planned

- Our own agent loop or direct provider API calls.
- Push, pull requests or any remote git operation by the mod or daemon.
- NeoForge or multi-loader support.
- OS-level sandboxing of agents (revisit after phase 4).

## Open risks

1. **CLI formats.** Headless flags and stream formats of all three CLIs are unverified here
   and change between releases. Every adapter starts from a recorded sample of real output.
2. **Mannequin limits.** If the vanilla Mannequin cannot walk or sit convincingly, phase 2
   needs a custom entity and renderer.
3. **Provider terms.** Driving a subscription CLI headlessly on your own machine is the
   supported path; sharing it with friends may not be.
4. **Minecraft updates.** Entity and screen code breaks across versions. Keeping the daemon
   free of Minecraft code limits how much has to be redone.
5. **"Never pushed" is a default, not a sandbox.** The daemon has no push code and CLIs are
   launched with `git push` denied, but an agent with a shell is not contained.
