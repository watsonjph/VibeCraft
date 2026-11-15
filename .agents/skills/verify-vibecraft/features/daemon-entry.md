# Daemon entry point

The agent daemon starts as its own Java process from the same jar the player installs,
without Minecraft or Fabric on its classpath. Today it is a stub that prints one line and
exits; phase 1 of the plan turns it into the long-running daemon.

## Sub-features

- `daemon-start` `DaemonMain` runs from the packaged jar and exits 0.
- `daemon-standalone` it needs nothing on the classpath except the jar itself.

## How to get to it (user POV)

- The mod will start it automatically when a world opens (not built yet; plan task
  `P1-BRIDGE-1`).
- Run it by hand: `java -cp vibecraft-<version>.jar io.github.watsonjph.vibecraft.daemon.DaemonMain`
  with Java 25 or newer.

## Driving it with vc.sh

Preconditions:

- `./gradlew build` succeeded after the last code change (the daemon runs from
  `build/libs/`, not from source).

- **Run.** Run `mkdir -p run/evidence/daemon-entry` then
  `vc.sh daemon > run/evidence/daemon-entry/daemon.out 2>&1; echo $? > run/evidence/daemon-entry/exit.txt`.
  `exit.txt` contains `0`.
- **Output.** Run `cat run/evidence/daemon-entry/daemon.out`. It starts with
  `vibecraft daemon:`.
- **Standalone.** The command line `vc.sh daemon` uses has only the mod jar after `-cp`. A
  `NoClassDefFoundError` naming `net/minecraft` or `net/fabricmc` here means the daemon
  package broke hard rule 1 in `AGENTS.md`.

## Gotchas

- A stale jar gives stale behaviour. If the output does not match the source, rebuild.
- The system `java` may be older than 25 and fail with `UnsupportedClassVersionError`;
  `vc.sh daemon` avoids that by using the JDK Gradle downloaded.
- Once the daemon needs Gson (phase 1), `vc.sh daemon` must add the Gson jar to the
  classpath the same way the mod's launcher does. Update the helper and this file together.
- When the daemon becomes long-running, this recipe needs a start, a readiness check and a
  stop that kills only the recorded process id.
