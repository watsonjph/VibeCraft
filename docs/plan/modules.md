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
| MCP | `daemon.mcp` | Stdio MCP server exposing `ask_user`, the peer-mode tools and the play-mode world tools; relays to the daemon socket | PROTO, CONFIG | 3 |
| ORCH | `daemon.orchestrator` | Goals, plan, task state machine, scheduler, budget enforcement | all daemon modules | 3 |
| BUDGET | `daemon.budget` | Usage ledger, limits per scope and period, price table, warnings, enforcement | PROTO, CONFIG, LOG | 3 |
| LIFE | `daemon.lifecycle` | `DaemonMain` wiring, single-instance lock, idle exit, crash recovery | all daemon modules | 1 |

## Mod server modules (`src/main/java/...`, runs on integrated and dedicated servers)

| Id | Package | Owns | May import | First phase |
|---|---|---|---|---|
| BRIDGE | `bridge` | Starting the daemon, the socket client, thread handoff to the server tick, state mirror | PROTO, Minecraft server | 1 |
| CMD | `command` | `/vibe` command tree | BRIDGE, ACCESS, STUDIO | 1 |
| STUDIO | `studio` | Studio anchor, layout maths, world saved data | Minecraft server | 2 |
| NPC | `npc` | The agent mob (custom entity with vanilla pathfinding), movement, status-to-behaviour mapping | STUDIO, BRIDGE | 2 |
| DISPLAY | `display` | Monitors and the wall: text displays, interaction entities, click routing | STUDIO, BRIDGE | 2 |
| PACKET | `network` | Custom payloads between server and client, paging of large data | PROTO, BRIDGE, ACCESS | 2 |
| WORLD | `world` and sub-packages | Play mode: observations, game-data lookups, movement, routines, standing jobs, building and schematics, farming, defence, rules (see [world-tools.md](world-tools.md)) | NPC, STUDIO, BRIDGE | 9 |
| ACCESS | `access` | Who may view or act, the sharing warning, attribution of actions to players | CONFIG via BRIDGE | 1 (owner-only stub), 7 |

## Client modules (`src/client/java/.../client/`)

| Id | Package | Owns | May import | First phase |
|---|---|---|---|---|
| CSTATE | `client.state` | Client-side cache of what the server sent; packet handlers | PACKET, PROTO | 2 |
| RENDER | `client.render` | Agent mob renderer: player model, skins, held item, speech bubble | CSTATE | 2 |
| SCREEN | `client.screen` | All screens: transcript, task detail, plan approval, diff, agent settings, setup check | CSTATE | 2 |

## Dependency rules

1. Daemon modules never import mod packages, `net.minecraft` or `net.fabricmc`.
2. Mod code imports exactly one daemon package: `daemon.protocol`.
3. Only BRIDGE opens the socket. Only GIT runs git. Only AGENT spawns agent CLIs.
4. Only ORCH changes task or goal state; everything else requests a change through it.
5. Client modules never import BRIDGE; they see the world only through PACKET.
6. Every player-initiated action passes through ACCESS before reaching BRIDGE.
7. Only WORLD changes blocks or items on an agent's behalf, and only through normal game
   rules (never by setting blocks directly).

## Team modes

A project setting, overridable per goal. All modes share worktrees, the task state machine,
the wall and review; they differ only in who creates tasks and who talks to whom.

| Mode | Who plans | Who codes | Agent-to-agent talk | Use it for |
|---|---|---|---|---|
| `auto` (default) | The first agent decides: do it alone, or write a plan | That agent, or workers if it planned | No | Everything, until you know better |
| `solo` | Nobody | One agent | No | Small changes, lowest cost |
| `lead` | A lead agent, with your approval | Workers in parallel (the lead too, if allowed) | Through the lead's plan only | Larger goals that split cleanly |
| `peer` | The agents, by adding and claiming tasks | Every agent | Yes, direct messages | Exploratory work; experimental, costs the most |

Defaults: `auto`, at most 3 agents in parallel, plan approval asked only when a plan has
more than one task, the lead may also code.

## Budgets and cost warnings

Every agent run, coding or play, is metered. Users set limits; the daemon warns as a limit
approaches and acts when it is reached.

**What is measured**

| Billing type (per agent preset) | Measured in | Source |
|---|---|---|
| `api` | Money and tokens | The cost the CLI reports; if it reports only tokens, tokens times a price table the user can edit. Estimated figures are marked as estimates |
| `subscription` | Tokens, agent-minutes, and the plan's own rate-limit state when the CLI reports it | The CLI. Money is not shown, because it is not what a subscription runs out of |
| `local` | Tokens and agent-minutes | The CLI. Free, but still capped if the user wants to limit machine time |

**Where a limit can be set**

| Scope | Example |
|---|---|
| Everything | 5.00 a day across all agents |
| Per project | 20.00 a week on this repo |
| Per agent | "Rook" may use 500k tokens a day |
| Per goal or play session | This goal may cost at most 2.00 |
| Per guest (phase 7) | Each friend may use 100k tokens a day |

Periods: per goal or session, day, week, month (local time). Several limits can apply at
once; the first one reached wins.

**What happens**

| Point | Default | Behaviour |
|---|---|---|
| Notice | 50% | Meter changes colour. No interruption |
| Warning | 80% | Chat message, sound, the wall header and the agent's roster line show it, the NPC mentions it once |
| Reached | 100% | The action set for that limit (below), and a `budget.reached` event |

Actions when a limit is reached: `ask` (default: affected agents pause at their next step
and one walks over; the player chooses raise the limit, allow this one to finish, or stop),
`pause` (pause without asking; resume when the period resets or the limit is raised),
`stop` (end the runs; work so far stays in the worktree).

**Rules**

- A limit is enforced during a run, not only before one starts. Usage is reported per step,
  so a run can overshoot by at most one step; the percentages shown include that step.
- An agent blocked by a limit shows `blocked` with the reason on its card and above its
  head. It never fails silently and never retries in a loop.
- Before a goal starts, the player sees what is left in each applicable limit.
- First use asks the player to pick a daily limit or to choose "no limit" explicitly. There
  is no silent unlimited default for `api` agents.
- `companion` play sessions and shared access cannot be turned on without a limit.
- Raising or removing a limit is owner-only and is logged as `budget.changed`.
- The ledger is kept on disk per month, so limits survive restarts and the game being
  closed.

## Wire protocol (mod server to daemon)

One JSON object per line, UTF-8. Every object has `"t"` (type).

| Direction | Type | Fields | Meaning |
|---|---|---|---|
| to daemon | `hello` | `token`, `protocol`, `cursors` (goalId to last seq) | First line; wrong token or protocol closes the socket |
| to client | `welcome` | `protocol`, `daemonVersion` | Handshake accepted; replay follows |
| to daemon | `cmd` | `id`, `name`, `args`, `actor` (player uuid and name) | A request, e.g. `goal.create`, `task.cancel` |
| to client | `reply` | `id`, `ok`, `error?`, `data?` | Answer to one `cmd` |
| to client | `event` | `goal`, `seq`, `ts`, `type`, `task?`, `agent?`, `data` | One log entry, live or replayed |
| to client | `stream` | `agent`, `text` | Partial reply text for speech bubbles and monitors. Not logged, not replayed, may be dropped |
| to client | `replay.done` | `goal`, `seq` | Replay finished for that goal; live events follow |
| to client | `world.req` | `id`, `agent`, `tool`, `args` | Play mode: the daemon asks the game to observe or act |
| to daemon | `world.res` | `id`, `ok`, `text` | The result, or the refusal, as one short text |

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
| `agent.peer_message` | from, to, text (peer mode) | MCP |
| `goal.mode` | mode chosen, and for `auto` which path it took | ORCH |
| `agent.permission` | requestId, what the agent wants to do (command or path) | AGENT |
| `task.check` | command, passed, output tail | ORCH |
| `task.gate` | passed, findings (out-of-scope files, repo changes) | ORCH |
| `agent.question` | questionId, text, options? | MCP |
| `question.answered` | questionId, answer, actor | ORCH |
| `task.ready_for_review` | filesChanged, added, removed | ORCH |
| `task.merged` / `task.discarded` | commit? , actor | GIT via ORCH |
| `usage` | inputTokens, outputTokens, costUsd?, estimated | AGENT |
| `budget.warning` | scope, period, used, limit, percent | BUDGET |
| `budget.reached` | scope, period, used, limit, action taken | BUDGET |
| `budget.changed` | scope, old and new limit, actor | BUDGET |
| `job.started` / `job.progress` / `job.done` / `job.stuck` | job, agent, detail (play mode) | WORLD via BRIDGE |
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
  agents/<agentId>.json            agent presets: name, skin, personality, adapter, model, billing type
  usage/<yyyy-mm>.jsonl            usage ledger: one line per usage report
  prices.json                      editable price table per model, for estimates
  projects/<projectId>/project.json            repo path, base branch
  projects/<projectId>/goals/<goalId>/events.jsonl
  projects/<projectId>/goals/<goalId>/plan.json
  worktrees/<projectId>/<taskId>/  one git worktree per task, outside the user's repo
  logs/daemon.log
```

World data holds only the studio anchor, its project id and which agent preset sits at which
desk. No transcripts, paths to keys, or tokens.
