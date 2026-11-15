# Phase 9: play mode

Agents that play vanilla Minecraft with you: look around, gather and mine, craft, build
from shapes or schematics, run crop and animal farms, defend against mobs, and talk ideas
through. Separate from coding: a play session has no repository, no worktree and no shell.
It is meant to work with cheap and local models, so the model decides what to do and the
game does the doing.

The tools themselves are specified in [world-tools.md](world-tools.md). This file is the
build order. Needs phase 2 (the agent mob) and phase 3 (the MCP relay, questions, budgets);
it does not need review, merge or release.

Play mode is large, so it is built in stages. Each stage is usable when it ends.

| Stage | Delivers | Demo that ends it |
|---|---|---|
| 9.0 | Relay, observation, movement, sessions, limits | "Come here", "what do you see?", "follow me" |
| 9.1 | Gathering, crafting, knowledge | "Get me a stone pickaxe" from nothing |
| 9.2 | Storage and logistics | "Put everything away and bring me 16 torches" |
| 9.3 | Building and schematics | A previewed hut, then a `.litematic` build that resumes after a restart |
| 9.4 | Crops and animals | A wheat field and a cow pen that keep producing unattended |
| 9.5 | Defence | Surviving a night next to the player without a model call during fights |
| 9.6 | Brainstorm, plans, chores, memory | "What should we build here?" ending in an approved plan agents carry out |

## How it fits

```
 agent CLI --MCP--> WorldToolServer --> daemon --socket--> mod server --> WORLD (tick thread)
                                               world.req / world.res
```

The daemon stays free of Minecraft code: it relays tool calls to the game and results
back. If no game is connected, every world tool returns "the world is not loaded".

WORLD is split into sub-packages so each can be built and tested alone:

| Package | Owns |
|---|---|
| `world.sense` | Observations, handles, surveys, text formatting |
| `world.data` | Lookups from game data: recipes, drops, tools, crops, mobs |
| `world.move` | Navigation, following, exploring |
| `world.act` | Primitives: break, place, use, attack, container access, through the fake-player hands |
| `world.routine` | Multi-step routines: harvest, mine, craft chains, smelt, get |
| `world.job` | Standing jobs, the per-agent job queue, saving and resuming |
| `world.build` | Shapes, templates, blueprints, schematic readers, build planner, previews |
| `world.farm` | Fields, pens, crop and animal routines |
| `world.guard` | Stances, combat reflexes, threat detection |
| `world.rules` | Capability switches, area and protection checks, rate limits |

## Stage 9.0: foundation

### Spikes

- [ ] `P9-SPIKE-1` **verify** the agent's hands: a Fabric API fake player acting from the
      mob's position, so breaking, placing, using items and attacking go through normal
      game rules and fire the events protection mods listen to. Check tool speed, drops,
      durability loss, and what other mods see.
- [ ] `P9-SPIKE-2` Measure where vanilla path-finding fails for the agent mob (water, caves,
      heights, doors) so `go_to` can report those cases.
- [ ] `P9-SPIKE-3` **verify** that a small local model can drive MCP tools through a
      supported CLI. Record which models completed a three-step task.
- [ ] `P9-SPIKE-4` **verify** whether the CLIs accept a tool list that changes mid-session
      (for `use_tools`).
- [ ] `P9-SPIKE-5` Write the outcomes here and adjust the tasks below.

### Relay and sessions

- [ ] `P9-PROTO-1` `world.req` (daemon to mod: id, agent, tool, args) and `world.res` (mod
      to daemon: id, ok, text) on the existing socket. Every request gets an answer,
      including refusals.
- [ ] `P9-PROTO-2` Job events in the log: `job.started`, `job.progress` (rate limited),
      `job.done`, `job.stuck`.
- [ ] `P9-MCP-1` `WorldToolServer`: lists the tools of the agent's tool set with short,
      plain descriptions and flat arguments, and relays each call.
- [ ] `P9-MCP-2` Tool sets from [world-tools.md](world-tools.md), chosen per agent preset;
      `help(topic)`.
- [ ] `P9-MCP-3` Timeouts: a call returns within a bounded time. Long work becomes a job
      and the call returns "started".
- [ ] `P9-MCP-4` Test: a scripted client drives each tool against a fake world endpoint.
- [ ] `P9-MCP-5` `do(steps)`: an ordered list of calls run back to back, stopping at the
      first failure, so one model turn covers several actions.
- [ ] `P9-ORCH-1` `play` session type: no project, an empty scratch directory, only world
      tools and `ask_user`. Same event log and budget accounting as a coding run.
- [ ] `P9-AGENT-1` Permission profile `play`: the CLI's file, shell and network tools
      disabled (**verify** per adapter). An adapter that cannot disable them is not offered
      for play mode.
- [ ] `P9-ORCH-2` Play prompt in a resource file: identity and personality, the tool set,
      "observe before acting", "say what you are doing in one line", a step cap per
      request.
- [ ] `P9-ORCH-3` Activity setting: `on request` (default: acts when asked, then idles at
      no cost) or `companion` (also takes a turn on a timer or on events such as nightfall
      or low health). `companion` requires a budget limit and shows its running cost.
- [ ] `P9-ORCH-4` Context control for small models: keep the request, the last few results,
      the notebook and named places; summarise older turns.
- [ ] `P9-ORCH-5` One mode at a time: a coding task calls an agent back to its desk first.
- [ ] `P9-ORCH-6` Wake-ups: a job that finishes or gets stuck wakes the model with one line
      of context. Wake-ups are rate limited and counted against the budget.

### Observation, movement, results

- [ ] `P9-SENSE-1` `look_around` with handles (`tree#2`), noise control (filler blocks
      summarised as terrain) and a hard size limit.
- [ ] `P9-SENSE-2` `find`, with the fairness setting `exposed` (default) or `xray`, scans
      spread over ticks.
- [ ] `P9-SENSE-3` `inspect`, `status`, `inventory`, `time_until`, named places.
- [ ] `P9-SENSE-4` Target resolver shared by every tool: coordinates, player, named place,
      handle, direction and distance.
- [ ] `P9-SENSE-5` Name resolver: plain words to items and blocks through game tags, with a
      "did you mean" on a miss.
- [ ] `P9-SENSE-6` Result formatter: one shape for every tool, with a next-step hint on
      failure. Tests against hand-built block grids.
- [ ] `P9-MOVE-1` `go_to`, `come_here`, `go_home`, `stop`; doors, gates, ladders, swimming.
- [ ] `P9-MOVE-2` `follow` as a job, with catch-up teleport when left far behind.
- [ ] `P9-MOVE-3` Temporary scaffolding within a block limit, removed afterwards.
- [ ] `P9-MOVE-4` Hazard avoidance: lava, long falls, drowning. Stuck detection that
      reports the reason.

### Rules and body

- [ ] `P9-RULES-1` Rules mode: `survival` (default: real break times, right tool needed,
      own inventory, takes damage) or `helper` (no damage, faster, still no free items).
- [ ] `P9-RULES-2` Capability switches per tool group; a switched-off tool is not listed
      and is refused if called.
- [ ] `P9-RULES-3` Allowed area around the studio or the requesting player.
- [ ] `P9-RULES-4` Protection: every change goes through normal game checks. Never set
      blocks directly.
- [ ] `P9-RULES-5` Always off unless the owner enables each: attacking players, fire, TNT,
      lava and water sources, breaking containers that hold items, private containers.
- [ ] `P9-RULES-6` Rate limits: block changes per minute, loaded chunks, wake-ups.
- [ ] `P9-RULES-7` Tests: every tool refuses out-of-area, out-of-reach, switched-off and
      missing-item calls with a message the model can act on.
- [ ] `P9-NPC-1` Play body: inventory, armour slots, held item shown, swing animation,
      health, respawn at the studio, keep-inventory setting.
- [ ] `P9-NPC-2` Requests arrive as in the studio (`P2-NPC-8`): right-click and type, or
      say the agent's name in chat.
- [ ] `P9-NPC-3` Reflexes without the model: keep following, leave water, back away from a
      hostile mob, face the speaker.
- [ ] `P9-CMD-1` `/vibe play <agent> [request]`, `/vibe recall <agent>`,
      `/vibe play settings`.
- [ ] `P9-SCREEN-1` Play panel: rules mode, area, activity, tool set, capability switches,
      current job and queue, inventory.
- [ ] `P9-DISPLAY-1` A line above the mob showing its current action.

## Stage 9.1: gathering, crafting, knowledge

- [ ] `P9-DATA-1` `recipe` and `how_to_make`: recipe tree from the game's recipe data, with
      have and missing against inventory and storage.
- [ ] `P9-DATA-2` `what_drops`, tool requirements, `crop_info`, `mob_info` from game data.
- [ ] `P9-DATA-3` `where_to_find`: a small hand-written table for vanilla resources, the
      one piece of knowledge the game data does not hold. Checked against the current
      version.
- [ ] `P9-ACT-1` Primitives through the fake-player hands: break, place, use item, use
      block, pick up.
- [ ] `P9-ROUTINE-1` `harvest`: whole trees with sapling replanting, exposed ore veins,
      surface resources (sand, gravel, clay, flowers).
- [ ] `P9-ROUTINE-2` `mine`: `staircase`, `branch` and `quarry` methods; torches; a kept
      way out; stops for lava, water, drops and low durability.
- [ ] `P9-ROUTINE-3` `dig`, `collect`, `fish`.
- [ ] `P9-ROUTINE-4` `craft` with intermediate steps and crafting-table placement.
- [ ] `P9-ROUTINE-5` `smelt` and `cook`: load, leave, come back, collect; fuel choice.
- [ ] `P9-ROUTINE-6` `equip` and `repair_or_replace`; tool choice before every action.
- [ ] `P9-ROUTINE-7` `get`: plan from `how_to_make` (fetch, craft, smelt, harvest, mine),
      run it, report the first step that cannot be done.
- [ ] `P9-ROUTINE-8` Inventory-full handling: store or ask, never silently drop.
- [ ] `P9-ROUTINE-9` Tests on a scripted flat test world: each routine from a known start
      to a checked end state.

## Stage 9.2: storage and logistics

- [ ] `P9-STORE-1` Storage areas: the owner marks containers as agent storage or private;
      saved in world data.
- [ ] `P9-STORE-2` Container memory: what each storage container held at the agent's last
      look, shared by agents of the same studio.
- [ ] `P9-STORE-3` `storage_report`, `store`, `fetch`, `take_from`, `put_in`, `drop`.
- [ ] `P9-STORE-4` `sort_storage`.
- [ ] `P9-STORE-5` `give`, `deliver`, `hand_over`.
- [ ] `P9-STORE-6` Routines from 9.1 use storage first before gathering.

## Stage 9.3: building and schematics

- [ ] `P9-BUILD-1` Shape primitives: `place`, `fill`, `walls`, `floor`, `roof`, `stairs`,
      `pillar`, `door`, `window`, `torches`.
- [ ] `P9-BUILD-2` Templates with size and material parameters: hut, house, tower, wall
      with gate, bridge, staircase, pen, storage room, mine entrance, watchtower.
- [ ] `P9-BUILD-3` `blueprint`: a list of shapes to a block plan with a bill of materials.
- [ ] `P9-BUILD-4` Build planner: order by support and by layer, placement facing for
      oriented blocks, two-block items (doors, beds), where to stand, scaffolding.
- [ ] `P9-BUILD-5` `preview`: ghost outline on clients (a RENDER task), with approve, move,
      rotate and reject. Nothing is built without an approved preview unless the owner
      turns previews off.
- [ ] `P9-BUILD-6` `build` as a job: pulls from storage, pauses with a list when materials
      run out, saves progress per block so it resumes after a restart.
- [ ] `P9-BUILD-7` `demolish` (only what the agent built, tracked per build) and
      `save_build`.
- [ ] `P9-SCHEM-1` **verify** the three formats against real files: Litematica
      `.litematic` (regions, block-state palette, packed block array), Sponge `.schem`,
      vanilla structure `.nbt`. Note the versions supported.
- [ ] `P9-SCHEM-2` Readers for each, into the same block plan as blueprints. No dependency
      on a schematic mod.
- [ ] `P9-SCHEM-3` Schematic folders: `vibecraft/schematics`, plus Litematica's folder
      read-only when present. Name and path validation; no reading outside those folders.
- [ ] `P9-SCHEM-4` `list_schematics`, `schematic_info`, `materials_check`, `gather_for`.
- [ ] `P9-SCHEM-5` Rotation, mirroring, substitutions, and the skipped-block report
      (unobtainable blocks, fluids unless allowed, entities, container contents).
- [ ] `P9-SCHEM-6` Size cap on blocks and area per build.
- [ ] `P9-SCHEM-7` Tests: each reader on fixture files; a round trip of `save_build` then
      build; planner order on a structure with doors, stairs and torches.

## Stage 9.4: crops and animals

- [ ] `P9-FARM-1` Field model: named area, crop, water and light check; saved in world
      data.
- [ ] `P9-FARM-2` `make_field`, `plant`, `harvest_crops`, `bonemeal`, `compost`,
      `field_status`.
- [ ] `P9-FARM-3` Crop behaviours beyond simple rows: melon and pumpkin stems, sugar cane
      and bamboo (leave the base), cactus, cocoa on jungle logs, nether wart, berries,
      kelp, tree fields.
- [ ] `P9-FARM-4` `tend_field` job on a schedule that needs no model.
- [ ] `P9-FARM-5` Pen model: named area, animal, maximum; `make_pen`, `pen_status`.
- [ ] `P9-FARM-6` `herd` (lure with food, gate handling), `breed`, `feed`, `tame`.
- [ ] `P9-FARM-7` `shear`, `milk`, `collect_eggs`, bees and honey with a campfire.
- [ ] `P9-FARM-8` `cull`, behind its own switch, with a kept minimum.
- [ ] `P9-FARM-9` `tend_animals` job: breed to the maximum, collect, repair gaps, report
      predators.
- [ ] `P9-FARM-10` Tests in the scripted world: a field goes from bare ground to a stored
      harvest; a pen goes from two animals to the maximum.

## Stage 9.5: defence

- [ ] `P9-GUARD-1` Threat detection: hostile mobs in range, and dark spots where they can
      spawn; `threats`.
- [ ] `P9-GUARD-2` Stances (`passive`, `defend`, `aggressive`) and the never-attack list.
- [ ] `P9-GUARD-3` Combat reflexes, tick-driven: melee with cooldown timing, shield use,
      bow at range, creeper back-off, no chasing beyond the radius.
- [ ] `P9-GUARD-4` Self-preservation: retreat threshold, `heal`, armour and weapon
      selection.
- [ ] `P9-GUARD-5` Jobs: `guard`, `patrol`, `night_watch`.
- [ ] `P9-GUARD-6` `secure_area` (light to above spawning level, fence, close gaps) and
      `build_defences` using the stage 9.3 templates.
- [ ] `P9-GUARD-7` Player warnings in chat: threat seen, hurt, retreating, post lost.
- [ ] `P9-GUARD-8` Tests in the scripted world: summoned zombies near a guarded point are
      dealt with; a summoned villager, wolf and second player are never hit.

## Stage 9.6: brainstorm, plans, chores, memory

- [ ] `P9-TALK-1` Brainstorm session type: observation, knowledge and talking tools only.
- [ ] `P9-TALK-2` `survey` and `suggest`.
- [ ] `P9-TALK-3` `propose_plan` and the plan card: steps, materials, rough time; approve,
      edit, reject. `queue` turns approved steps into jobs.
- [ ] `P9-TALK-4` `sketch`: several ghost previews side by side to choose from.
- [ ] `P9-TALK-5` Notebook (`note`, `notes`), per agent, size-limited, kept across
      sessions.
- [ ] `P9-TALK-6` Chores board on the wall: `chores`, `add_chore`, `claim_chore`,
      `finish_chore`; `tell` between agents.
- [ ] `P9-TALK-7` Players add chores from the wall or by `/vibe chore <text>`.

## ACCESS: other players

- [ ] `P9-ACCESS-1` A separate permission, `play`, in the phase 7 table. It can be granted
      without `interact`, because play agents cannot reach the repository.
- [ ] `P9-ACCESS-2` It still spends the owner's tokens: guest budgets and rate limits
      apply, and the sharing warning is shown when it is enabled.
- [ ] `P9-ACCESS-3` On a server the allowed area defaults to around the studio. Guests
      cannot change rules, switches, storage marking or schematic files.

## Verification

- [ ] `P9-VERIFY-1` A scripted flat test world for the verification skill, set up with
      console commands (known trees, ores, a chest, animals), driven with `FakeAdapter`
      tool scripts so no tokens are spent.
- [ ] `P9-VERIFY-2` One feature file per stage under the verification skill's `features/`,
      each proving the stage's demo by block and inventory state read back with `data get`.

## Things to consider

- Small models loop. Step caps, one-line results with a next-step hint, and routines such
  as `get` matter more than prompt wording. Tune by watching real runs.
- Jobs are where the savings are. A field tended for an hour should cost zero model calls
  unless something breaks.
- Every observation costs tokens. Measure `look_around` in a forest and a cave and keep
  both small.
- Building is the hardest request. A model that cannot write a sound blueprint falls back
  to templates and schematics; do not promise freeform architecture from small models.
- Schematics are files from the internet. Treat them as untrusted input: size limits,
  bounded parsing, no code, no paths outside the schematic folders.
- A large schematic means hours of work and many loaded chunks. The size cap and the saved
  progress are what make it practical.
- Combat fairness: reflexes follow player rules (attack cooldown, reach). An agent that
  hits faster than a player can is a cheat on a shared server.
- An agent that mines and farms is automation. On servers with rules about that, the
  owner needs the switches and the area limit to stay within them.
- Chat from other players reaches the model. What it can cause is bounded by WORLD's
  rules, which is why they are enforced there.
- Local models are free per token but slow; the mob should show it is thinking and keep
  its reflexes running.
- Vanilla changes every release. The hand-written `where_to_find` table and the crop and
  mob behaviours need re-checking on each version update.
