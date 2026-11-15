# Phase 2: the studio

Put the pipe in the world: a placed studio, an NPC per agent that walks to a desk, and a
monitor that tails the real stream. First client screen and first custom packets.

**Exit criteria**

1. `/vibe studio here` creates a studio; it survives leaving and rejoining the world.
2. `/vibe run` makes an NPC walk to its desk and sit; its monitor shows live event lines.
3. Clicking the monitor opens a scrollable transcript. Right-clicking the NPC lets you send
   it a message.
4. Removing the mod and loading the world shows no broken entities or blocks.

## SPIKE: prove the pieces first

Decided: the agent is a custom mob, not the vanilla Mannequin, because agents must walk
across real terrain and (in play mode) act in the world.

- [ ] `P2-SPIKE-1` **verify** a custom mob built on the vanilla path-finding mob base:
      registers on a dedicated server, navigates to a position around obstacles, can be
      seated on an invisible seat, is not saved with the world.
- [ ] `P2-SPIKE-2` **verify** the client renderer: the vanilla player model and animations
      on that mob, a skin from a Mojang username, a name tag, a held item.
- [ ] `P2-SPIKE-3` **verify** Text Display (multi-line text, background, line width, update
      rate without flicker) and Interaction entities (left and right click reach the server
      with the clicking player).
- [ ] `P2-SPIKE-4` Write what was learned into this file before building on it.

## STUDIO: anchor, layout, persistence

- [ ] `P2-STUDIO-1` `StudioData` in world saved data: anchor position, facing, dimension,
      project id, desk-to-agent assignments. Versioned codec.
- [ ] `P2-STUDIO-2` `StudioLayout`: pure function from anchor, facing and desk count to
      positions (desks, seats, monitor faces, the wall, the lead's spot, the gathering
      point). No world access, so it is unit-testable.
- [ ] `P2-STUDIO-3` `/vibe studio here [desks]`: checks the footprint is clear; if not,
      lists what is in the way and refuses unless `force` is given. Never replaces
      blocks silently.
- [ ] `P2-STUDIO-4` `/vibe studio remove`: removes entities and saved data, leaves the world
      as it was.
- [ ] `P2-STUDIO-5` `StudioEntities`: spawns all studio entities from `StudioData` when the
      chunk loads or the server starts, tags each with a studio id, and removes orphans with
      that tag. All are marked not to be saved.
- [ ] `P2-STUDIO-6` Furniture: decide between purely decorative vanilla blocks placed once
      (and removed on studio removal) or none at all. Default: none, entities only, so the
      studio is reversible.
- [ ] `P2-STUDIO-7` Tests for `StudioLayout`: positions for 1, 4 and 8 desks, all four
      facings, no overlaps.

## NPC: agent entities

- [ ] `P2-NPC-1` `AgentMob`: the custom entity type, registered in `src/main`, with no
      vanilla AI goals of its own. `AgentNpc` wraps one per agent and holds its desk, target
      and state (`idle`, `walking`, `seated`, `approaching_player`).
- [ ] `P2-NPC-2` Movement uses vanilla navigation to layout points and players. If no path
      is found or progress stalls for a few seconds, teleport and log why.
- [ ] `P2-NPC-3` Behaviour table from agent status: `working` statuses mean seated at the
      desk, `idle` means standing at the gathering point, `done` means stand up and face the
      wall.
- [ ] `P2-NPC-4` Head tracking: look at the monitor while working, at the nearest player
      when idle and one is close.
- [ ] `P2-NPC-5` NPCs are invulnerable, not pushable, do not drop items, do not count for
      mob caps, and ignore other mods' AI goals as far as possible.
- [ ] `P2-NPC-6` Right-click opens the message screen for that agent (through PACKET).
- [ ] `P2-NPC-7` Instant acknowledgement: in the tick a player addresses an agent it turns
      to face them and shows a thinking indicator. This is local behaviour and must never
      wait for the model.
- [ ] `P2-NPC-8` Talking without a screen: say the agent's name in chat within earshot
      ("Rook, how is it going?") and the rest of the line goes to that agent. Replies appear
      in chat and in a speech bubble.
- [ ] `P2-NPC-9` Idle life without model calls: glance at passing players, shift posture,
      look at the wall when a card changes. Costs no tokens.

## RENDER: client

- [ ] `P2-RENDER-1` Renderer for `AgentMob` using the player model: walk, sit and
      head-turn animations, name tag, skin lookup by username with a default skin while
      loading or offline.
- [ ] `P2-RENDER-2` Speech bubble above the head, filled from `stream` text as it arrives
      and fading after the reply ends.
- [ ] `P2-RENDER-3` Status marker above the head: thinking, working, needs you.

## DISPLAY: monitors

- [ ] `P2-DISPLAY-1` `Monitor`: a Text Display per desk showing the last N event lines
      (default 10), newest at the bottom, fixed line width, colour per event kind.
- [ ] `P2-DISPLAY-2` Throttle: at most a few text updates per second per monitor; coalesce
      bursts.
- [ ] `P2-DISPLAY-3` An Interaction entity over the monitor; a click asks PACKET to open the
      transcript screen for that agent.
- [ ] `P2-DISPLAY-4` Status line above the desk: agent name, status, current file.
- [ ] `P2-DISPLAY-5` Shared formatter with the phase 1 chat formatter (move it, do not copy
      it). Chat output of events becomes opt-in.

## PACKET: server and client payloads

- [ ] `P2-PACKET-1` Register payload types: open-transcript, transcript-page request and
      reply, send-message-to-agent, state-sync (agents and statuses).
- [ ] `P2-PACKET-2` Paging: transcript replies carry at most a fixed number of lines and a
      cursor; never one packet per event to every client.
- [ ] `P2-PACKET-3` Every serverbound payload goes through `Access` before BRIDGE.
- [ ] `P2-PACKET-4` Validate serverbound input: lengths, ids that exist, rate limit per
      player.

## CSTATE and SCREEN: client

- [ ] `P2-CSTATE-1` `ClientStudioState`: agents, statuses and transcript pages received so
      far; cleared on disconnect.
- [ ] `P2-SCREEN-1` `TranscriptScreen`: scrollable, loads older pages on scroll up, follows
      the tail when at the bottom.
- [ ] `P2-SCREEN-2` `MessageScreen`: a text field and send; shows the last few messages.

## BRIDGE: additions

- [ ] `P2-BRIDGE-1` `StudioMirror`: in-memory model of goals, tasks and agents built from
      events on the server thread. NPC and DISPLAY read from it; they do not parse events.
- [ ] `P2-BRIDGE-2` Daemon command `agent.message` with a delivery choice: `next` (default:
      the agent sees it at its next step and keeps working) or `interrupt` (stop what it is
      doing and read this now). Uses the session from `P1-AGENT-3`.

## Things to consider

- Chunk loading: the daemon keeps running while the studio's chunks are unloaded. Entities
  must be rebuilt from `StudioMirror` on load, not from the last thing they showed.
- Dedicated servers have no client classes. Run `./gradlew runServer` in this phase to catch
  an accidental client import early.
- Text Displays are visible through walls at some settings and have a view range; set both
  deliberately.
- A custom entity type means every client joining a server with the mod needs the mod
  too. That is accepted; say it in the README.
- Players will build around and inside the studio. Blocked desks should degrade to a
  teleport, not a stuck NPC.
- Name tags and monitor text come from agent output. Strip formatting codes and control
  characters before display.
