# Modules

Base package: `io.github.watsonjph.vibecraft`. A module is one package with one job. The
"may import" column is the whole allowed list besides the JDK; anything else is a design
change, so raise it before doing it.

## Daemon modules (`src/main/java/.../daemon/`, plain Java, no Minecraft)

| Id | Package | Owns | May import | First phase |
|---|---|---|---|---|
| PROTO | `daemon.protocol` | Event, command and reply records; JSON codec; version constant | Gson | 1 |
| CONFIG | `daemon.config` | State directory paths, `config.json`, token file, agent presets, budgets | PROTO | 1 |
| LOG | `daemon.log` | Append-only event log per goal, sequence numbers, replay | PROTO, CONFIG | 1 |
| NET | `daemon.net` | Socket server, auth handshake, client sessions, fan-out of events | PROTO, CONFIG, LOG | 1 |
| GIT | `daemon.git` | Running git: worktrees, branches, diff, merge, cleanup | PROTO | 1 |
| AGENT | `daemon.agent` | Adapter interface, process runner, one adapter class per CLI | PROTO, CONFIG | 1 |
| MCP | `daemon.mcp` | Stdio MCP server exposing `ask_user`; relays to the daemon socket | PROTO, CONFIG | 3 |
| ORCH | `daemon.orchestrator` | Goals, plan, task state machine, scheduler, budget enforcement | all daemon modules | 3 |
| LIFE | `daemon.lifecycle` | `DaemonMain` wiring, single-instance lock, idle exit, crash recovery | all daemon modules | 1 |

## Mod server modules (`src/main/java/...`, runs on integrated and dedicated servers)

| Id | Package | Owns | May import | First phase |
|---|---|---|---|---|
| BRIDGE | `bridge` | Starting the daemon, the socket client, thread handoff to the server tick, state mirror | PROTO, Minecraft server | 1 |
| CMD | `command` | `/vibe` command tree | BRIDGE, ACCESS, STUDIO | 1 |
| STUDIO | `studio` | Studio anchor, layout maths, world saved data | Minecraft server | 2 |
| NPC | `npc` | Agent entities, movement, status-to-behaviour mapping | STUDIO, BRIDGE | 2 |
| DISPLAY | `display` | Monitors and the wall: text displays, interaction entities, click routing | STUDIO, BRIDGE | 2 |
| PACKET | `network` | Custom payloads between server and client, paging of large data | PROTO, BRIDGE, ACCESS | 2 |
| ACCESS | `access` | Who may view or act, the sharing warning, attribution of actions to players | CONFIG via BRIDGE | 1 (owner-only stub), 7 |

## Client modules (`src/client/java/.../client/`)

| Id | Package | Owns | May import | First phase |
|---|---|---|---|---|
| CSTATE | `client.state` | Client-side cache of what the server sent; packet handlers | PACKET, PROTO | 2 |
| SCREEN | `client.screen` | All screens: transcript, task detail, plan approval, diff, agent settings, setup check | CSTATE | 2 |

## Dependency rules

1. Daemon modules never import mod packages, `net.minecraft` or `net.fabricmc`.
2. Mod code imports exactly one daemon package: `daemon.protocol`.
3. Only BRIDGE opens the socket. Only GIT runs git. Only AGENT spawns agent CLIs.
4. Only ORCH changes task or goal state; everything else requests a change through it.
5. Client modules never import BRIDGE; they see the world only through PACKET.
6. Every player-initiated action passes through ACCESS before reaching BRIDGE.

## Wire protocol (mod server to daemon)

One JSON object per line, UTF-8. Every object has `"t"` (type).

| Direction | Type | Fields | Meaning |
|---|---|---|---|
| to daemon | `hello` | `token`, `protocol`, `cursors` (goalId to last seq) | First line; wrong token or protocol closes the socket |
| to client | `welcome` | `protocol`, `daemonVersion` | Handshake accepted; replay follows |
| to daemon | `cmd` | `id`, `name`, `args`, `actor` (player uuid and name) | A request, e.g. `goal.create`, `task.cancel` |
| to client | `reply` | `id`, `ok`, `error?`, `data?` | Answer to one `cmd` |
| to client | `event` | `goal`, `seq`, `ts`, `type`, `task?`, `agent?`, `data` | One log entry, live or replayed |
| to client | `replay.done` | `goal`, `seq` | Replay finished for that goal; live events follow |

Bulk data (diffs, full transcripts) is never pushed as events. The client asks with a `cmd`
and gets a paged `reply`.

## Event catalogue

| Type | Data | Emitted by |
|---|---|---|
| `goal.created` | text, project, actor | ORCH |
| `plan.ready` / `plan.approved` / `plan.rejected` | tasks with briefs and dependencies | ORCH |
| `task.created` | title, brief, dependsOn | ORCH |
| `task.status` | status, reason? | ORCH |
| `task.assigned` | agent, branch | ORCH |
| `agent.status` | status, file? | AGENT |
| `agent.read` | path | AGENT |
| `agent.edit` | path, added, removed | AGENT |
| `agent.command` | command, exitCode? | AGENT |
| `agent.message` | text (truncated; full text by request) | AGENT |
| `agent.question` | questionId, text, options? | MCP |
| `question.answered` | questionId, answer, actor | ORCH |
| `task.ready_for_review` | filesChanged, added, removed | ORCH |
| `task.merged` / `task.discarded` | commit? , actor | GIT via ORCH |
| `usage` | inputTokens, outputTokens, costUsd? | AGENT |
| `error` | where, message | any |

Task status: `planned`, `working`, `needs_you`, `review`, `merged`, `failed`, `discarded`.
Agent status: `idle`, `thinking`, `reading`, `editing`, `running`, `waiting_on_you`,
`blocked`, `done`.

## State directory

```
~/.vibecraft/
  config.json                      settings, budgets, sharing access
  token                            socket auth token, readable by the owner only
  daemon.lock                      held while a daemon runs (single instance)
  daemon.port                      port of the running daemon
  agents/<agentId>.json            agent presets: name, skin, personality, adapter, model
  projects/<projectId>/project.json            repo path, base branch
  projects/<projectId>/goals/<goalId>/events.jsonl
  projects/<projectId>/goals/<goalId>/plan.json
  worktrees/<projectId>/<taskId>/  one git worktree per task, outside the user's repo
  logs/daemon.log
```

World data holds only the studio anchor, its project id and which agent preset sits at which
desk. No transcripts, paths to keys, or tokens.
