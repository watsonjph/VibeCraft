# VibeCraft verification map

The maintained source for verifying VibeCraft's user-facing behaviour. Read this index
before driving anything, then use the matching feature file as the recipe. `vc.sh` means
`.claude/skills/verify-vibecraft/vc.sh`, run from the repo root.

## Baseline preconditions

- `./gradlew build` succeeded on the code under test.
- `vc.sh launch` returned `ready on port 25599` (server features only).
- `vc.sh doctor` exits 0.
- Never drive a server this run did not launch.

## Driving conventions

- Start each recipe from a freshly launched server unless it says otherwise.
- Treat every command as literal.
- Put a unique marker in anything you later match in the log.
- Stop the server with `vc.sh stop` when finished, pass or fail.

## Proof and skip reporting

- Proof is the command sent plus the log line or file it produced, saved with
  `vc.sh evidence <feature-id>`.
- Record the feature id and entry point with every artifact.
- Report an unreachable path with the command tried and the unmet precondition.
- Client-only behaviour (screens, rendering) cannot be driven here. Report it as not
  verified.

## Feature entry contract

Each feature file has an H1, one paragraph on the user-visible behaviour, then four H2s in
order: `Sub-features`, `How to get to it (user POV)`, `Driving it with vc.sh`, `Gotchas`.

## Features

- [Mod loads on a server](./mod-load.md) covers Fabric discovering the mod, the initialiser
  running, and the server staying usable.
- [Daemon entry point](./daemon-entry.md) covers starting the agent daemon from the
  packaged jar outside the game.
- [Packaged jar](./packaged-jar.md) covers the artifact a user installs: metadata, both
  entrypoints and the daemon class in one jar.

Planned features (`/vibe` commands, studio, wall, review, sharing) are in `docs/plan/`. Add
a file here in the same change that makes each one real.
