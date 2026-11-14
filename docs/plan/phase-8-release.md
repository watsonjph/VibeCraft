# Phase 8: release

Make it installable and understandable by someone who has never seen the repo.

**Exit criteria**

1. A new user can go from download to a merged change by following the README alone.
2. CI builds and tests every push and attaches the jar to tagged releases.
3. The mod is published with an accurate description of what it can and cannot guarantee.

## DOCS

- [ ] `P8-DOCS-1` README: what it is, a short demo clip or screenshots, requirements
      (Minecraft and Fabric versions, git, at least one agent CLI).
- [ ] `P8-DOCS-2` Setup per provider: Claude Code, Codex, opencode with OpenRouter. Each
      ends with "the setup screen shows a green row".
- [ ] `P8-DOCS-3` Safety model, stated plainly: what runs on your machine, where state
      lives, what "nothing touches your branch" and "never pushed" mean and their limits,
      what is logged.
- [ ] `P8-DOCS-4` The sharing warning from phase 7, verbatim, in the multiplayer section.
- [ ] `P8-DOCS-5` Troubleshooting: daemon will not start, CLI not found, not logged in,
      merge refused, studio will not place. Each entry names the log file to look at.
- [ ] `P8-DOCS-6` Command and settings reference generated from, or checked against, the
      code.
- [ ] `P8-DOCS-7` CONTRIBUTING pointing at `AGENTS.md` and `docs/plan/`.

## BUILD

- [ ] `P8-BUILD-1` GitHub Actions: build and test on Linux and Windows for every push and
      pull request.
- [ ] `P8-BUILD-2` Release workflow on tag: build, attach the jar and sources jar.
- [ ] `P8-BUILD-3` Mod icon and complete `fabric.mod.json` metadata (homepage, sources,
      issues).
- [ ] `P8-BUILD-4` Licence check: GPL-3.0 notice in the jar; confirm nothing bundled
      conflicts with it.
- [ ] `P8-BUILD-5` Verify the released jar (not the dev environment) can launch the daemon
      from itself on Windows, macOS and Linux.

## PUBLISH

- [ ] `P8-PUBLISH-1` Modrinth project: description, gallery, environment marked as client
      and server, dependency on Fabric API.
- [ ] `P8-PUBLISH-2` Version policy: which Minecraft versions are supported and for how
      long; one maintained version unless demand says otherwise.
- [ ] `P8-PUBLISH-3` Changelog from task ids in commit messages.
- [ ] `P8-PUBLISH-4` Issue templates: bug (asks for mod, Minecraft and CLI versions, and the
      daemon log), feature request.

## QUALITY

- [ ] `P8-QA-1` Full manual run on a clean machine account for each supported provider.
- [ ] `P8-QA-2` Run alongside a few popular mods (a minimap, a performance mod, a large
      content mod) and note conflicts.
- [ ] `P8-QA-3` Performance pass: server tick time with eight agents streaming; client
      frame time facing the wall.
- [ ] `P8-QA-4` Accessibility basics on screens: keyboard navigation, readable contrast in
      the diff view, no information carried by colour alone.

## Things to consider

- Mod platforms review mods that start external processes. Describe the daemon up front in
  the listing instead of leaving it to be discovered.
- Anti-virus tools may flag a game spawning a detached Java process. Document what the
  process is and where its files live.
- Do not claim sandboxing. The honest description is "local merges only on your click, no
  push code, push denied to agents by default".
- Minecraft releases frequently. Decide whether to track every version before publishing,
  because users will ask on day one.
