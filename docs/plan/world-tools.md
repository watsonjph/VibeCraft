# World tools (the play-mode MCP server)

The catalogue of what an agent can do in a vanilla Minecraft world. This is the design
reference for [phase 9](phase-9-play-mode.md); the phase file holds the task list. Tool
names and arguments here are the contract between the MCP server and the WORLD module.

## Design rules

1. **Three layers.** *Primitives* do one thing (break this block). *Routines* do one job
   end to end (chop this tree and replant). *Standing jobs* keep going with no model
   involved (tend this field, guard this player) until stopped or stuck. Models are slow
   and cost money; anything repetitive or time-critical is a routine or a job.
2. **The game supplies the knowledge.** Recipes, what a block drops, which tool it needs,
   whether a crop is ripe: all read from the game's own data and returned as text. A small
   model should never have to remember a recipe.
3. **Text in, one short text out.** Every result fits a fixed size limit and has the same
   shape: `ok` or `failed`, what happened, and when it failed, what to try next
   ("failed: need 3 more oak_planks. try: harvest oak_log 1").
4. **Few numbers.** Targets can be coordinates, but also a player name, a named place, a
   handle from the last observation (`tree#2`, `chest#1`), or a direction and distance
   ("north 10"). Item and block names accept plain words and resolve through the game's
   tags ("wood" matches any log, "pickaxe" the best one held).
5. **Small tool lists.** No agent sees the whole catalogue. A preset picks a tool set of
   at most about fifteen tools; `help(topic)` describes the rest in words.
6. **Limits live in the game, not the prompt.** Reach, break time, inventory, allowed
   area, protected blocks and capability switches are enforced by WORLD on every call.
7. **Vanilla first.** Everything here targets vanilla blocks, items and mobs. Modded
   content works where the game's registries and tags are enough, and is not promised.

## Tool sets

| Set | For | Tools |
|---|---|---|
| `basic` | Small and local models | `look_around`, `find`, `go_to`, `follow`, `harvest`, `get`, `give`, `start_job`, `stop`, `say`, `help` |
| `gatherer` | Resources | `basic` plus `mine`, `craft`, `smelt`, `how_to_make`, `store`, `fetch` |
| `builder` | Construction | `basic` plus the building and schematic groups |
| `farmer` | Crops and animals | `basic` plus the farming and animal groups |
| `guard` | Defence | `basic` plus the defence group |
| `full` | Capable models | Everything the owner has switched on |

**verify** whether the supported CLIs honour a tool list that changes during a session. If
they do, an agent can switch sets with `use_tools(set)`; if not, the set is fixed per
preset.

## Observation

| Tool | Arguments | Returns |
|---|---|---|
| `look_around` | | Position, facing, health, held item, time, weather, biome, light level, notable blocks by type with count, direction and distance, entities and players nearby, each with a handle |
| `find` | what, radius | Nearest matches with handles and coordinates. Blocks, mobs, items on the ground, players, structures the agent has seen |
| `inspect` | target | That block and its neighbours, or that entity's kind, health and what it holds; container contents if the agent may open it |
| `survey` | area or radius | Terrain summary for choosing a site: flat areas and their size, slopes, water, trees, cave openings, existing builds |
| `status` | | Health, armour, held and worn items, inventory summary, current job and its progress |
| `inventory` | filter? | Items carried with counts and tool durability |
| `places` / `remember_place` / `forget_place` | name | Named places per agent (home, mine, farm, storage) |
| `time_until` | dawn, dusk or night | How long, so an agent can plan around nightfall |

## Knowledge (read from game data, no world access)

| Tool | Arguments | Returns |
|---|---|---|
| `how_to_make` | item, count | The full recipe tree down to raw materials, what the agent already has, what is missing, and which stations are needed |
| `recipe` | item | The direct recipes only |
| `what_drops` | block or mob | Drops, and the tool needed to get them |
| `where_to_find` | item or block | Typical height range, biome and source for vanilla resources ("iron: stone layers, most common around Y 16") |
| `crop_info` | crop | How to plant it, what it needs, how to tell it is ripe |
| `mob_info` | mob | Hostile or not, how it attacks, what it is weak to, what it eats, how to breed it |
| `help` | topic | Plain description of a tool group and how to combine its tools |

## Movement

| Tool | Arguments | Returns |
|---|---|---|
| `go_to` | target | Arrived, or how far it got and what blocked it |
| `follow` | player, distance | Starts following (a standing job) |
| `come_here` | | Walks to whoever asked |
| `explore` | direction, distance | Walks out, returns a summary of what it passed: biomes, structures, resources, hazards |
| `go_home` | | Returns to the studio or the agent's home place |
| `stop` | | Cancels the current action or job |
| Movement abilities | | Opens doors and gates, climbs ladders, swims, uses a boat across water if carrying one, places and removes temporary scaffolding within a limit, avoids lava and long falls |

## Gathering

| Tool | Arguments | Returns |
|---|---|---|
| `harvest` | block or resource, count | Finds, walks, breaks and collects. Fells whole trees and replants a sapling. Follows an exposed ore vein |
| `mine` | resource, count, method? | Digs for something not exposed. Methods: `staircase` down to a level, `branch` tunnels at the right height, `quarry` an area. Places torches, keeps a way out, stops for lava, water, deep drops and low tool durability |
| `dig` | box | Clears a volume |
| `collect` | item, radius | Picks up items lying on the ground |
| `fish` | count or minutes | Fishes from the nearest water with a rod |
| `get` | item, count | The goal-level tool: works out how (fetch from storage, craft, smelt, harvest, mine) from `how_to_make` and runs the steps, reporting the first one it cannot do |

## Crafting and processing

| Tool | Arguments | Returns |
|---|---|---|
| `craft` | item, count | Crafts, making intermediate items and placing a crafting table if it has one and needs it |
| `smelt` | item, count, fuel? | Uses the nearest furnace, smoker or blast furnace: loads, waits or comes back later, collects |
| `cook` | food, count | Same for food, including a campfire |
| `equip` | item or "best" | Holds or wears it; `best` picks the best tool, weapon or armour for the next action |
| `repair_or_replace` | tool | Crafts a replacement or combines damaged ones when durability is low |
| `use_station` | station, action | Stonecutter, smithing table, loom, grindstone, composter. Anvil, enchanting and brewing are a later stage |

## Storage and logistics

| Tool | Arguments | Returns |
|---|---|---|
| `storage_report` | | What is in the containers of the agent's storage area, from its last look inside each |
| `store` | items or "all except tools" | Puts items into storage, keeping like with like |
| `fetch` | item, count | Takes from storage; says which chest it was in |
| `sort_storage` | | Regroups a storage area by item type |
| `give` | player, item, count | Walks over and hands it across |
| `take_from` / `put_in` | container, items | Direct container use |
| `drop` | item, count | Drops at its feet |
| `deliver` | item, count, place | Carries to a place and stores it there |

The owner marks which containers are the agent's storage and which are private. Private
ones are never opened.

## Building

| Tool | Arguments | Returns |
|---|---|---|
| `place` | target, item | One block from inventory, with a facing where it matters |
| `fill` | box, block | A solid box |
| `walls` / `floor` / `roof` / `stairs` / `pillar` | box or line, block, options | Parametric shapes, which models handle far better than block lists |
| `door` / `window` / `torches` | position or wall, options | Common fittings; `torches` lights an area to a target light level |
| `build_template` | name, size, origin, facing, materials | Built-in shapes: hut, house, tower, wall with gate, bridge, staircase, pen, storage room, mine entrance, watchtower |
| `blueprint` | list of shapes | A structure the model describes as shapes; returns its size and bill of materials without building |
| `preview` | blueprint, template or schematic, origin, facing | Shows a ghost outline to the player and waits for approval, a move, or a rejection |
| `build` | approved preview | Builds it as a standing job: bottom up, scaffolding as needed, pulling from storage, pausing to report missing materials |
| `demolish` | box or last build | Removes what the agent built and keeps the blocks |
| `save_build` | name, box | Saves an existing structure as a schematic for reuse |

### Schematics

Agents can build from schematic files, so players can use designs made in or for schematic
mods without those mods being required.

| Tool | Arguments | Returns |
|---|---|---|
| `list_schematics` | filter? | Names, sizes and block counts |
| `schematic_info` | name | Dimensions, bill of materials, and blocks the agent cannot place |
| `materials_check` | name | Bill of materials against inventory and storage: have, missing, and how to get each missing item |
| `preview` | name, origin, rotation, mirror | As above |
| `build` | approved preview | As above; progress is saved, so a build resumes after the game closes |
| `gather_for` | name | Runs `get` for everything `materials_check` reports missing |

- **Formats.** Litematica `.litematic`, Sponge/WorldEdit `.schem`, and vanilla structure
  `.nbt`. All three are NBT files; they are read with the game's own NBT code. No
  schematic mod is a dependency. **verify** the format versions against real files.
- **Where files come from.** A `vibecraft/schematics` folder in the game directory, plus,
  read-only, the folder Litematica itself uses if it exists. On a dedicated server only
  the server's folder is read, and only the owner can add files.
- **What it handles.** Block states with orientation (stairs, slabs, logs, doors, beds,
  trapdoors), build order so supported blocks go after their support, multi-region
  Litematica files, rotation and mirroring.
- **What it reports and skips.** Blocks it cannot obtain or place in survival (command
  blocks, bedrock, spawners), fluids unless the owner allows buckets, entities and block
  contents (chest items, sign text is kept). Skipped blocks are listed at the end.
- **Substitutions.** The player can map one block to another before building ("use
  cobblestone for stone bricks").
- **Size limit.** A cap on blocks per build and on build area, owner-set, because a large
  schematic is hours of work and a lot of loaded chunks.

## Farming: crops

| Tool | Arguments | Returns |
|---|---|---|
| `make_field` | area or size, crop | Lays out a field: water within reach of every tilled block, tilled soil, planted, optionally fenced and lit |
| `plant` | crop, area | Tills where needed and plants from inventory |
| `harvest_crops` | area or field name | Harvests only ripe plants and replants |
| `bonemeal` | area | Applies bone meal where it helps |
| `field_status` | field name | How much is ripe, growing, empty or trampled, and whether water and light are adequate |
| `compost` | items | Turns spare plant items into bone meal |
| `tend_field` (job) | field name | Checks on a schedule, harvests ripe crops, replants, stores produce, reports problems |

Supported crops and plants: wheat, carrots, potatoes, beetroot, melons, pumpkins, sugar
cane, cactus, bamboo, cocoa, nether wart, sweet berries, kelp, mushrooms, saplings and
trees (a tree farm is a field of saplings with spacing), flowers for dye.

## Farming: animals

| Tool | Arguments | Returns |
|---|---|---|
| `make_pen` | area or size, animal | Fences an area with a gate, lit, sized for the animal count |
| `herd` | animal, count, pen | Lures animals with their food into a pen and closes the gate |
| `breed` | animal, pairs | Feeds pairs; respects a per-pen maximum |
| `feed` | animal | Heals or grows young animals |
| `shear` / `milk` / `collect_eggs` | pen | Gathers the product |
| `cull` | animal, keep | Reduces a pen to a kept number, cooking the meat if asked. Off unless the owner enables it |
| `tame` | animal | Wolves, cats, horses, parrots, with the right item |
| `pen_status` | pen name | Counts of adults and young, and whether the fence is intact |
| `tend_animals` (job) | pen name | Breeds up to the maximum, collects products, repairs gaps, reports predators |

Supported: cows, sheep, pigs, chickens, rabbits, bees (hives and honey with a campfire),
horses and donkeys, wolves, cats, villagers only for trading if the owner allows it.

Automatic farms (iron farm, mob grinder, crop farm with redstone) are built from
schematics, not from special tools. The agent can then run and empty them.

## Defence

Combat is far too fast for a model. The model sets a policy; the mob fights by reflex.

| Tool | Arguments | Returns |
|---|---|---|
| `guard` (job) | player or place, radius | Stays near, attacks hostile mobs that come within range, returns to post |
| `patrol` (job) | list of places | Walks a route, deals with hostiles, reports what it met |
| `night_watch` (job) | place | `guard` from dusk to dawn, then goes back to its previous job |
| `set_stance` | passive, defend, aggressive | Passive runs away; defend fights what attacks it or its charge; aggressive hunts hostiles in range |
| `threats` | radius | Hostile mobs nearby with distance and direction, and dark spots where they can spawn |
| `secure_area` | area | Lights it above spawning level, optionally fences it and closes gaps |
| `build_defences` | area, kind | Wall, fence, ditch or watchtower from the building templates |
| `retreat` | | Disengages to the nearest safe place |
| `heal` | | Eats, or waits out of danger to recover |

Reflex rules the mob follows by itself: equip the best weapon, armour and shield; use a bow
at range if it has arrows; back away from creepers and come back after; do not chase
beyond the guard radius; retreat below a health threshold; eat when hurt and safe; warn
the player in chat when a threat appears and when it is hurt.

Never attacked, in any stance: players, tamed animals, villagers, golems, the animals in
pens. Neutral mobs (endermen, piglins, wolves, bees, iron golems) are left alone unless
they attack first. The owner can widen or narrow this list.

## Talking and planning (brainstorm)

| Tool | Arguments | Returns |
|---|---|---|
| `say` | text | Speaks in chat and a speech bubble |
| `ask_user` | question, options? | The same question flow as coding agents |
| `propose_plan` | title, steps | Shows the player a plan card with the steps, the materials and a rough time; the player approves, edits or rejects it |
| `queue` | steps | Adds approved steps to the agent's job queue |
| `sketch` | blueprint or template | Shows ghost outlines of ideas side by side so the player can pick one |
| `note` / `notes` | text | A small per-agent notebook that survives sessions (what the player likes, where things are, what is unfinished) |
| `suggest` | | Ideas based on what the agent can see and what is in storage: what could be built, what is running low, what is unsafe |

A brainstorm session offers only this group, the observation group and the knowledge
group. It changes nothing in the world, so it needs no approvals and is the cheapest way
to use a model in play mode.

## Working together

| Tool | Arguments | Returns |
|---|---|---|
| `chores` | | The shared list of play jobs on the studio wall |
| `claim_chore` / `add_chore` / `finish_chore` | id or text | Same mechanics as peer-mode tasks |
| `tell` | agent, text | A message to another agent |
| `hand_over` | agent, items | Gives items to another agent |

The wall shows a Chores board in play mode, so a player can queue "wood", "wheat field",
"wall around the base" and let agents pick them up.

## Later groups (not in the first release of play mode)

Trading with villagers; enchanting, anvil and brewing; redstone building beyond
schematics; Nether and End travel; riding and minecarts; maps and banners.

## Owner settings

- Capability switches per group: gathering, mining, building, schematics, crops, animals,
  culling, combat, containers, trading, other dimensions.
- Rules mode (`survival` or `helper`), allowed area, private containers, protected
  regions, block-change and loaded-chunk limits, build size cap.
- What happens on death: keep inventory (default) or drop it; respawn at the studio.
- Everything in [budgets](modules.md#budgets-and-cost-warnings) applies to play sessions.
