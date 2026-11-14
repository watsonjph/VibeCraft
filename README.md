# VibeCraft

An agent IDE inside Minecraft. Multi-agent coding usually means a wall of terminal text;
VibeCraft turns it into a studio you can walk around in.

> **Status: early development.** The project builds and the mod loads, but none of the
> features below are playable yet. The [plan](docs/plan/README.md) shows what is built and
> what is next.

## The idea

You type a goal. An agent reads your repo, writes a plan and pins tasks to a wall. Workers
walk to their desks, sit down and start coding in their own git worktrees while their
monitors stream every file they read and every line they change. When a call is yours to
make, an agent walks over to you with a question. When work is ready, you review the real
diff and press Merge.

- **Nothing touches your branch without that click**, and nothing is pushed.
- **Close the game and the agents keep working.** Open it again and the studio catches up.
- **Bring your own models.** Agents run through the coding CLIs you already use, with your
  own subscription or API key.
- **Agents are characters.** Give each one a name, a skin, a personality and a model.

## How a goal gets worked

You choose how many agents are involved and how they organise. The default is `auto`.

| Mode | What happens | Good for |
|---|---|---|
| `auto` (default) | One agent looks at the goal and either does it alone or writes a plan for a team | Everything, until you know better |
| `solo` | One agent, one worktree, no planning step | Small changes, lowest cost |
| `lead` | A lead agent plans, you approve, workers code in parallel | Larger goals that split cleanly |
| `peer` | No lead; agents add and claim tasks and message each other directly | Exploratory work (experimental, costs the most) |

## Models

VibeCraft does not call model APIs itself. Each agent runs an existing coding CLI in the
background, so whatever that CLI can log in to, VibeCraft can use.

| CLI | Gives you |
|---|---|
| Claude Code | Claude subscription or API key |
| Codex CLI | ChatGPT subscription or API key |
| opencode | OpenRouter and other API-key providers |

Different agents in the same team can use different models.

## The studio

- **The wall.** Your goal across the top, then task cards in columns: Planned, Working,
  Needs You, Review, Merged, Failed. Each card shows who has it, the model, lines changed,
  time and cost.
- **Desks and monitors.** Each working agent has a desk. Its monitor tails what the agent
  is reading, editing and running; click it for the full transcript.
- **Roster.** Every agent's status, current file, model and usage.
- **Questions.** An agent that needs a decision walks to you. Answer in chat or on screen.
- **Review.** Open a finished task to read its diff, then Merge, Request changes or
  Discard.

## Safety model

- Each task gets its own git worktree and branch, kept outside your repo folder.
- A merge is a local `git merge` into the branch you have checked out, run only when you
  press Merge. It is refused if your working tree has uncommitted changes, and undone
  cleanly on conflict.
- VibeCraft contains no code that pushes, fetches or opens pull requests, and agents are
  started with `git push` denied.
- That last point is a default, not a sandbox. Agents can run commands in your project, so
  only point VibeCraft at repositories and models you would trust a coding agent with.
- API keys stay on your machine, in the CLI's own configuration or VibeCraft's local config.
  They are never stored in a world or sent to other players.

## Playing with friends

VibeCraft is built for singleplayer. It can also run on a server so friends can watch your
studio and, if you allow it, talk to your agents. Sharing is off by default.

> **Other players can use your models.** Anyone you allow can start and message agents that
> run on your account and on your machine. They can use up your API credits or subscription
> limits quickly. Their messages are instructions to agents that can read your project and
> run commands in it. Sharing a personal subscription may also be against your provider's
> terms. Only allow people you trust.

Merging, discarding, settings and keys stay with the owner at every sharing level.

## Requirements

- Minecraft 26.3 with Fabric Loader and Fabric API
- Git
- At least one supported agent CLI, installed and logged in

## Building from source

```
./gradlew build        # jar is written to build/libs/
./gradlew runClient    # dev client with the mod
./gradlew runServer    # dev dedicated server
```

Gradle downloads the JDK it needs (25); you only need some Java installed to start it.

## Contributing

Start with [AGENTS.md](AGENTS.md) for the rules of the codebase and
[docs/plan/](docs/plan/README.md) for the architecture, module map and the task list for
each phase. Changes are verified against a real dev server using the skill in
`.claude/skills/verify-vibecraft/`.

## Licence

[GPL-3.0](LICENSE)
