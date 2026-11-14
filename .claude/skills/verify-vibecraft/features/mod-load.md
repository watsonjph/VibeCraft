# Mod loads on a server

A server owner who installs VibeCraft sees it listed among the loaded mods, sees its
start-up line in the log, and gets a server that starts and accepts console commands as
usual.

## Sub-features

- `load-listed` Fabric lists `vibecraft` with its version.
- `load-init` the main initialiser runs and logs `VibeCraft loaded`.
- `load-usable` the server reaches `Done` and still executes console commands.

## How to get to it (user POV)

- Start a dedicated server with the mod installed (here: `./gradlew runServer`).
- Open a singleplayer world with the mod installed. This goes through the client and is not
  driven by this harness.

## Driving it with vc.sh

Preconditions:

- `./gradlew build` succeeded.
- No server from this harness is running.

- **Start.** Run `vc.sh launch`. It prints `ready on port 25599`.
- **Health.** Run `vc.sh doctor`. Exit code 0 and four `ok` lines.
- **Listed.** Run `grep -n -- '- vibecraft ' run/logs/latest.log`. One line reading
  `- vibecraft <version>` matching `version` in `gradle.properties`.
- **Initialised.** Run `grep -n 'VibeCraft loaded' run/logs/latest.log`. Exactly one line,
  logged by `(vibecraft)`.
- **Usable.** Run `vc.sh send "say probe-<random>"` then `vc.sh wait-log 'probe-<random>' 15`.
  Exit code 0 and the log has `[Server] probe-<random>`.
- **No errors.** Run `grep -nE 'ERROR|Exception' run/logs/latest.log`. No lines that mention
  `vibecraft`.
- **Proof.** Run `vc.sh evidence mod-load`, then `vc.sh stop`. `run/evidence/mod-load/`
  still holds `latest.log` and `console-input.txt`.

## Gotchas

- `wait-log` matches anywhere in the log. Reusing a probe string from an earlier step
  passes without proving anything.
- The first launch downloads and remaps Minecraft and can take minutes; later ones take
  seconds.
- A `Done` line alone does not show the mod loaded. Check `load-listed` and `load-init`.
- The singleplayer entry point is not covered. Do not report it verified from the server
  run.
