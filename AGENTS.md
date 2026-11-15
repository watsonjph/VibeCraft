# AGENTS.md

VibeCraft is a Fabric mod (Minecraft 26.3, Java 25) that turns multi-agent coding into an
in-world studio: agents are NPCs that plan, code in git worktrees and ask the player before
anything is merged. Read `docs/plan/README.md` and `docs/plan/modules.md` before starting work: architecture, module
boundaries and one checklist file per phase. Tick tasks off in the phase file as you finish
them and put the task id (for example `P1-LOG-2`) in the commit message.

## Commands

```
./gradlew build        # compile and package to build/libs/
./gradlew runClient    # launch a dev Minecraft client with the mod
./gradlew runServer    # launch a dev dedicated server
./gradlew test         # once tests exist (JUnit arrives in phase 1)
```

Gradle downloads JDK 25 itself (`gradle/gradle-daemon-jvm.properties` and the toolchain in
`build.gradle`). Do not lower the Java version or remove those; Fabric Loom needs 25.

## Layout

```
src/main/java/io/github/watsonjph/vibecraft/          server-side and shared mod code
src/main/java/io/github/watsonjph/vibecraft/daemon/   the agent daemon (separate JVM)
src/client/java/io/github/watsonjph/vibecraft/client/ client-only code: screens, input
src/main/resources/fabric.mod.json                    mod metadata
gradle.properties                                     Minecraft, loader and Fabric API versions
docs/plan/                                            architecture, module map, phase checklists
```

## Hard rules

1. **The daemon package is plain Java.** Nothing under `daemon/` may import `net.minecraft`
   or `net.fabricmc`. It runs outside the game with only the JDK and Gson on its classpath.
2. **Client classes stay in `src/client`.** Code in `src/main` must run on a dedicated
   server, so no screens, rendering or `Minecraft.getInstance()` there.
3. **No remote git, ever.** No `push`, `fetch`, `pull` or PR code anywhere. Merges are local
   and happen only on an explicit player action.
4. **Never touch the user's branch or working tree** except in the merge path, and that path
   refuses a dirty tree and aborts cleanly on conflict.
5. **Never block the server tick thread** on socket, process or git work. Do it on another
   thread and hand the result back with `server.execute`.
6. **Secrets stay in the daemon.** API keys and the daemon token never go into world data,
   network packets, chat or logs.
7. **Shared access is off by default.** Any feature that lets a non-owner player reach an
   agent must go through the access check and keep the warning described in phase 7.
8. **The client never talks to the daemon directly.** Client to server by Minecraft packets,
   server to daemon by the local socket.

## Conventions

- Smallest thing that works. Prefer the JDK, then what Minecraft already ships (Gson, Netty,
  SLF4J), before adding a dependency. Ask before adding one.
- The agent is a custom mob with a client renderer. Everything else in the studio uses
  vanilla entities (Text Display, Interaction) in preference to custom blocks and
  renderers.
- Agents must be interactive, fast and compliant: react locally before any model replies,
  keep model calls off every path code can handle, and enforce limits in code, not in
  prompts. Targets are in `docs/plan/README.md`.
- No mixins unless there is no Fabric API event for the job.
- Every agent CLI adapter has a test that parses a recorded output sample from the real CLI.
  Do not guess a CLI's flags or output format: run it and check.
- Git and merge logic is tested against a temporary repo, never the working repo.
- Names in this version of Minecraft are Mojang's official ones (`Identifier`,
  `ServerLevel`). Older tutorials using Yarn names will not match.
- Commit only when asked. Never commit `run/` or `build/`.

## Verifying changes

This project uses pstack. Before saying a change works, run the `verify-vibecraft` skill
(`.claude/skills/verify-vibecraft/SKILL.md`): it launches a real dev server, drives it
through the console and captures evidence under `run/evidence/`. When you add or change a
user-facing feature, update its file under `.claude/skills/verify-vibecraft/features/` in
the same change.
