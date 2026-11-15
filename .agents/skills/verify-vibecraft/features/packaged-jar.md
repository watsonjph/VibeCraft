# Packaged jar

The file a player drops into their mods folder is one jar that Fabric accepts on both
client and server and that also contains the daemon.

## Sub-features

- `jar-built` `./gradlew build` produces `build/libs/vibecraft-<version>.jar`.
- `jar-metadata` `fabric.mod.json` inside it has the mod id, the real version and both
  entrypoints.
- `jar-classes` the main, client and daemon classes are all inside.

## How to get to it (user POV)

- Run `./gradlew build` and take the jar from `build/libs/`.
- Download a release (not published yet; plan phase 8).

## Driving it with vc.sh

Preconditions:

- A JDK-capable shell at the repo root. No server needed.

- **Build.** Run `./gradlew build --console=plain`. Output ends with `BUILD SUCCESSFUL`.
- **Present.** Run `ls build/libs/`. Lists `vibecraft-<version>.jar` and a `-sources.jar`.
- **Metadata.** Run `unzip -p build/libs/vibecraft-<version>.jar fabric.mod.json`. `"id"` is
  `vibecraft`, `"version"` is the number from `gradle.properties` (not `${version}`), and
  `entrypoints` names `VibeCraft` and `client.VibeCraftClient`.
- **Classes.** Run `unzip -l build/libs/vibecraft-<version>.jar | grep -E 'VibeCraft|DaemonMain'`.
  Lists `VibeCraft.class`, `client/VibeCraftClient.class` and `daemon/DaemonMain.class`.
- **Proof.** Save both outputs under `run/evidence/packaged-jar/`.

## Gotchas

- `build/libs/` keeps jars from older versions. Check the one matching the current version.
- The dev server (`runServer`) loads classes from the build directory, not this jar. A
  passing server run does not prove the jar is complete.
- Loading this jar in a real, non-dev Minecraft install is not covered here; it is plan
  task `P8-BUILD-5`.
