# Phase 5: models and identity

Bring your own model, and make each agent a character. The adapter half needs only phase 1
and can start early; the UI half needs phase 3.

**Exit criteria**

1. A team can mix agents on Claude Code, Codex and an OpenRouter model in one goal.
2. Each agent has a name, skin, personality and model set from an in-game screen, saved as
   a preset usable in any world.
3. A setup screen shows which CLIs are installed, their versions and whether they are
   logged in.

## AGENT: more adapters

- [ ] `P5-AGENT-1` **verify** Codex CLI headless mode: non-interactive command, JSON event
      output, sandbox and approval flags, MCP registration, session resume. Record a
      fixture.
- [ ] `P5-AGENT-2` `CodexAdapter` and its fixture test.
- [ ] `P5-AGENT-3` **verify** opencode headless mode: run command, JSON output, provider
      and model selection, OpenRouter key configuration, MCP registration. Record a
      fixture.
- [ ] `P5-AGENT-4` `OpenCodeAdapter` and its fixture test.
- [ ] `P5-AGENT-5` Capability flags per adapter (supports resume, reports cost, supports
      MCP, supports read-only mode). ORCH reads flags instead of checking adapter names.
- [ ] `P5-AGENT-6` `AdapterProbe`: for each adapter find the binary, read its version,
      check login state where the CLI offers a way. Results cached and refreshable.
- [ ] `P5-AGENT-7` Model listing per adapter where the CLI can list models; otherwise a
      free-text model id field.
- [ ] `P5-AGENT-8` Minimum supported version per adapter; an older CLI gives a clear
      "update needed" error.

## CONFIG: presets and keys

- [ ] `P5-CONFIG-1` Agent preset file: id, name, skin, personality text, adapter, model,
      role (lead or worker). CRUD commands on the daemon.
- [ ] `P5-CONFIG-2` API keys: prefer leaving keys in each CLI's own configuration. Where a
      key must pass through us (OpenRouter for opencode), store it in `config.json` with
      owner-only permissions and hand it to the child process by environment variable only.
- [ ] `P5-CONFIG-3` Keys are write-only from the game: the daemon never returns a key, only
      "set" or "not set".
- [ ] `P5-CONFIG-4` Redaction: any configured key value is masked in events, logs and error
      messages before they are written.
- [ ] `P5-CONFIG-5` Tests: redaction; a preset round-trip; keys absent from every reply.

## ORCH

- [ ] `P5-ORCH-1` Personality goes into the agent's system prompt as tone only; it must not
      weaken the task and safety instructions (those come last).
- [ ] `P5-ORCH-2` Lead and worker can use different adapters and models; fall back with a
      visible warning if an agent's adapter is unavailable.

## NPC, STUDIO

- [ ] `P5-NPC-1` Apply preset name and skin to the entity; changes apply without respawning
      the studio.
- [ ] `P5-NPC-2` Skin sources: Mojang username (default). Local PNG skins need a
      client-side dynamic texture and a custom renderer, so only do this if the phase 2
      spike already forced a custom entity.
- [ ] `P5-STUDIO-1` Desk assignment: which preset sits at which desk, stored in world data;
      add and remove desks from the settings screen.

## PACKET, SCREEN

- [ ] `P5-SCREEN-1` `AgentSettingsScreen`: name, skin field with preview, personality text
      box, adapter dropdown, model dropdown or field, role.
- [ ] `P5-SCREEN-2` `TeamScreen`: list of presets, assign to desks, mark the lead.
- [ ] `P5-SCREEN-3` `SetupScreen`: one row per adapter with installed, version, logged in,
      and the command to run to fix it. Opened automatically the first time `/vibe` is used
      with nothing configured.
- [ ] `P5-SCREEN-4` Key entry field that masks input and sends over the local connection
      only. On a dedicated server, key entry from the game is disabled; keys are set on the
      host machine.
- [ ] `P5-PACKET-1` Payloads for presets, probes and settings; all owner-only.

## Things to consider

- Never read, copy or relay a CLI's stored credentials. The CLI authenticates itself.
- Models differ in how well they follow the plan JSON format and the `ask_user` guidance.
  Keep prompts per role, not per model, until a specific model proves it needs its own.
- Free-text personality is user content going into a prompt. Limit its length.
- Player names used for skins are looked up against Mojang's services; handle lookups
  failing offline and cache results.
- Cost reporting differs per provider. The roster shows tokens always, money only when the
  adapter reports it.
- CLI updates will break adapters. The fixture tests tell you what changed; the version
  check tells the user why it stopped working.
