# Phase 7: friends on a server

Let other players watch and, if the owner allows it, interact. Singleplayer stays the main
target; this phase adds no requirement for it. Sharing is off until the owner turns it on.

The daemon, the repository and the agent CLIs all live on the machine that hosts the world.
Other players reach them only through the server.

**Exit criteria**

1. With sharing off (the default), a non-owner can see the studio entities and nothing
   else: no screens, no commands, no agent text sent to their client.
2. Turning sharing on requires an explicit confirmation that shows the warning.
3. An allowed player can do exactly what their level permits and is attributed in the log.
4. Budget caps stop a guest's usage at the configured amount.
5. No access level lets a non-owner merge, discard, change settings or see keys.

## The warning

Shown on the enable command (which then needs `confirm`), in the server log at every start
while sharing is on, and to the owner each time an allowed player joins:

> **Other players can use your models.** Anyone you allow can start and message agents that
> run on your account and on your machine. They can use up your API credits or subscription
> limits quickly. Their messages are instructions to agents that can read your project and
> run commands in it. Sharing a personal subscription may also be against your provider's
> terms. Only allow people you trust.

## ACCESS: levels and checks

- [ ] `P7-ACCESS-1` Owner: the singleplayer host, or on a dedicated server the players
      listed in the mod's server config (not simply every operator).
- [ ] `P7-ACCESS-2` Levels: `off` (default), `view` (read the wall, transcripts and diffs),
      `interact` (also message agents and answer questions), `direct` (also create goals
      and approve plans).
- [ ] `P7-ACCESS-3` Per-player allowlist with a level each; no "everyone" setting above
      `view`.
- [ ] `P7-ACCESS-4` A permission table: every command and payload mapped to the minimum
      level. Owner-only, fixed: merge, discard, project path, agent settings, keys, budget,
      access settings, daemon control.
- [ ] `P7-ACCESS-5` `/vibe share on|off`, `/vibe share allow <player> <level>`,
      `/vibe share revoke <player>`, `/vibe share list`. `on` prints the warning and needs
      `/vibe share on confirm` within a minute.
- [ ] `P7-ACCESS-6` Warning delivery at the three points listed above.
- [ ] `P7-ACCESS-7` Test: for every row of the permission table, each level below the
      minimum is refused. The test fails if a command exists that is not in the table.

## ORCH, CONFIG: budgets and attribution

- [ ] `P7-CONFIG-1` Guest limits: the `guest` scope of the phase 3 budget model
      (`P3-BUDGET-4`), per guest per day. Sharing cannot be turned on without one. Guests
      see their own meter; warnings about a guest's limit go to the guest and the owner.
- [ ] `P7-ORCH-1` Usage is attributed to the actor who caused the run (goal creator, or the
      player whose message resumed an agent).
- [ ] `P7-ORCH-2` Enforce the guest budget before each spawn and each resumed message.
- [ ] `P7-ORCH-3` Every `cmd` carries `actor`; events record it; the wall, task screen and
      transcript show who asked for what.
- [ ] `P7-ORCH-4` Rate limits per guest: messages per minute, goals per hour.

## PACKET, CSTATE: what each client receives

- [ ] `P7-PACKET-1` State sync is filtered per player by level. At `off` nothing custom is
      sent.
- [ ] `P7-PACKET-2` In-world text is visible to everyone who can see the entities. Add a
      setting for what monitors and cards show when sharing is `off` or a viewer has no
      access: full, titles only, or blank. Default on a dedicated server: titles only.
- [ ] `P7-PACKET-3` Clients need the mod to join, because the agent is a custom entity
      type. Make the refusal message for a client without it say what to install.
- [ ] `P7-PACKET-4` Re-check access on every serverbound payload, not only when a screen
      opens; revoking takes effect immediately.

## NPC, DISPLAY

- [ ] `P7-NPC-1` Questions go to the player who started the goal if they are online and
      allowed to answer; otherwise to the owner.
- [ ] `P7-DISPLAY-1` Cards and transcript lines show the requesting player's name.
- [ ] `P7-DISPLAY-2` The roster shows per-guest usage against their budget to the owner.

## Dedicated server specifics

- [ ] `P7-SERVER-1` Server config file for owners and the project path; key entry from the
      game is disabled on dedicated servers.
- [ ] `P7-SERVER-2` Document that the CLIs must be installed and logged in for the account
      that runs the server process.
- [ ] `P7-SERVER-3` Run the full flow with `./gradlew runServer` and two clients with
      different access levels.

## Things to consider

- This is remote instruction of a shell-capable agent on the host's computer. Treat every
  rule here as a security control, and test refusals as carefully as successes.
- A guest's message can try to make an agent reveal files, keys or other players' text.
  Guests at `interact` talk to workers confined to worktrees; they never get the lead's
  repository-wide read access unless they are at `direct`.
- Chat messages to NPCs must not be broadcast to other players unless the sender chooses.
- Griefing the studio (breaking blocks around it, pushing entities) is ordinary server
  moderation; the entities themselves are invulnerable and respawn.
- Operators on a public server are not automatically people the repo owner trusts. That is
  why ownership is a separate list.
- Hosting providers often forbid or cannot run extra processes. The daemon needs a machine
  where the owner can install and log in to the CLIs.
