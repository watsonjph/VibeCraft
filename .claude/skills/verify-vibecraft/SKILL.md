---
name: verify-vibecraft
description: Launch and drive the VibeCraft Fabric mod on a real dev dedicated Minecraft server through its console, and run the agent daemon from the packaged jar, to prove a change works. Use after any change to mod or daemon code, before claiming it works, and whenever asked to run, test or verify VibeCraft.
---

# Verify VibeCraft

VibeCraft is a Minecraft Fabric mod plus an agent daemon that runs as a separate JVM from
the same jar. This skill drives both for real. Everything goes through one helper,
`.claude/skills/verify-vibecraft/vc.sh`, run from the repo root in Git Bash or any POSIX
shell. Read `features/README.md` next, then the feature file for what you changed.

Surfaces:

- **Dedicated server console** (primary, headless): `./gradlew runServer` with commands
  written to its stdin and results read from `run/logs/latest.log`.
- **Daemon entry point**: `DaemonMain` run from `build/libs/vibecraft-*.jar`.
- **Game client** (`./gradlew runClient`): not driven by this skill. It needs a display and
  a human. Screens and rendering are unverified by anything here; say so in your report
  when a change touches `src/client`.

## Launch

```
./gradlew build                                # always first: the daemon runs from the jar
.claude/skills/verify-vibecraft/vc.sh launch   # starts the dev server, returns when ready
```

`launch` writes `run/eula.txt` and, if absent, `run/server.properties` (port 25599, offline
mode, flat world). Both are verification scaffolding inside the git-ignored `run/`
directory. It returns after the log shows `Done (…)! For help`, which is when the console
accepts commands; allow up to 5 minutes on a first run while Minecraft downloads. On
failure it prints the tail of `run/verify/server.out`.

The daemon is not a server yet: each `vc.sh daemon` call is one short-lived process.

**One instance only.** The server uses the single `run/` directory and port 25599. `launch`
refuses if this harness already has a server up. Do not start a second one, and do not drive
a server you did not launch (a developer's own `runServer` uses the same directory).

## Doctor

```
.claude/skills/verify-vibecraft/vc.sh doctor
```

Read-only. Exit 0 means: the launcher process this harness started is alive, the server
finished starting, the log contains `VibeCraft loaded`, and port 25599 accepts connections.
It also prints the mod version from the log. Run it first whenever something looks off. If
it fails, run `stop`, then `launch` again.

## Drive

```
vc.sh send <console command>          # e.g. vc.sh send "say probe-7f3a"
vc.sh wait-log <regex> [seconds]      # blocks until latest.log matches, default 60s
vc.sh daemon [args]                   # runs DaemonMain from the packaged jar on JDK 25
```

- Console commands are written without a leading slash.
- `wait-log` searches the whole log, so it also matches lines from before your command. Put
  a unique marker in what you send (`say probe-<random>`) or match text that cannot have
  appeared earlier.
- Console input is not echoed to the log; only its effect is. The harness records what was
  sent in `run/verify/cmds`.
- No player is online. Commands that need a player (`execute as @p`, anything targeting the
  executor's position) have nothing to act on; use absolute coordinates and the console as
  the source.
- `vc.sh daemon` uses the JDK 25 that Gradle downloaded under `~/.gradle/jdks`, because the
  system `java` may be older than the class files.

## Evidence

```
vc.sh evidence <name>      # prints the directory it wrote
```

Writes `run/evidence/<name>/` with `latest.log` (server log), `console-input.txt` (every
command sent), `commit.txt` and `dirty-files.txt` (what code was running). For daemon runs,
redirect the output yourself: `vc.sh daemon > run/evidence/<name>/daemon.out 2>&1; echo $?`.

Proof standards:

- Drive the path a player or server owner uses: console commands and the packaged jar. Do
  not call mod classes from a test and present that as verification.
- Capture the action and the result: the command in `console-input.txt` and the log line or
  file it caused.
- Check side effects where they land: files under `run/world/`, the state directory, git
  refs in a scratch repository. A chat message saying "done" is not proof.
- Quote the exact log lines in your report, with the evidence path.
- Anything that needs the client is reported as not verified, never as passed.

## Cleanup

```
.claude/skills/verify-vibecraft/vc.sh stop
```

Sends `stop` to the console, waits for the process to exit, then ends the helper `tail` it
started. It only ever signals the two process ids it recorded in `run/verify/`. It does not
touch `run/evidence/`; confirm your evidence directory still exists afterwards. Run `stop`
after a failed attempt too. To reset the world as well, delete `run/world/` after `stop`.

## Keeping this current

When a feature is added or changed, add or update its file under `features/` in the same
change. `/pstack:maintain-verification-skill` audits the map against the code.
