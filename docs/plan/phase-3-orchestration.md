# Phase 3: orchestration

From one agent to a team: a lead that plans, a wall of tasks, workers in parallel, and
questions that walk over to the player.

**Exit criteria**

1. `/vibe goal <text>` produces a plan the player can approve, edit or reject.
2. After approval, several workers run at once in separate worktrees and the wall shows each
   task moving through its columns.
3. An agent calling `ask_user` makes its NPC walk to the player; the answer unblocks it.
4. A daily budget cap stops new agent runs when reached and says so.

## ORCH: goals, plan, scheduler

- [ ] `P3-ORCH-1` Task state machine as a single transition table (from, trigger, to).
      Illegal transitions throw. Every transition appends `task.status`.
- [ ] `P3-ORCH-2` `GoalService.create`: writes `goal.created`, starts the lead.
- [ ] `P3-ORCH-3` Lead run: read-only permissions, prompt asks for a JSON plan (tasks with
      id, title, brief, files likely touched, dependsOn). Prompt text lives in a resource
      file, not in code.
- [ ] `P3-ORCH-4` Plan validation: parses, ids unique, dependencies exist, no cycles, task
      count within a configured maximum. On failure send the error back to the lead once;
      a second failure fails the goal with a readable reason.
- [ ] `P3-ORCH-5` Plan approval: `plan.ready` waits for `plan.approve`, `plan.reject` or
      `plan.edit` (add, remove, reword tasks). A config flag can auto-approve.
- [ ] `P3-ORCH-6` Scheduler: a task is ready when all dependencies are `merged` (default) or
      `review` (config, see considerations). Assign ready tasks to idle agents up to
      `maxParallelAgents`.
- [ ] `P3-ORCH-7` Worker prompt: task brief, goal, plan summary, personality (if set),
      instructions to commit work in the worktree and to call `ask_user` only for decisions
      that are the user's.
- [ ] `P3-ORCH-8` Completion: when a worker exits cleanly with commits on its branch, move
      to `review` with diff stats; with no commits, `failed` with the last message.
- [ ] `P3-ORCH-9` Task commands: `task.cancel`, `task.retry`, `task.pause` (stop and keep
      the worktree), `task.reassign`, `task.message`.
- [ ] `P3-ORCH-10` Budget: sum `usage` per day; before every spawn check the cap; on breach
      emit `error` and set waiting tasks to `planned` with reason `budget`.
- [ ] `P3-ORCH-11` Rate-limit and auth failures from a CLI set the agent `blocked` with the
      reason and retry on a backoff with a ceiling, not in a tight loop.
- [ ] `P3-ORCH-12` Tests: transition table; plan validation cases; scheduler with a fake
      adapter (dependencies respected, parallel limit respected, budget stop).

## MCP: ask_user

- [ ] `P3-MCP-1` **verify** how each supported CLI registers a stdio MCP server per run
      (config file or flag) and how tool results are returned.
- [ ] `P3-MCP-2` `AskUserServer`: a `main` that speaks MCP over stdio (`initialize`,
      `tools/list`, `tools/call`) with one tool, `ask_user(question, options?)`. Launched
      by the CLI from the mod jar.
- [ ] `P3-MCP-3` The tool call connects to the daemon socket (token from the state
      directory, task id from an environment variable), raises `agent.question`, and blocks
      until answered or cancelled.
- [ ] `P3-MCP-4` ORCH side: question registry, `question.answer` command, task goes to
      `needs_you` and back to `working`.
- [ ] `P3-MCP-5` Timeouts: none by default (the player may be away for hours); confirm the
      CLI does not kill a long tool call, otherwise end the run and resume the session with
      the answer.
- [ ] `P3-MCP-6` Test: drive `AskUserServer` over pipes with a scripted client.

## AGENT: additions

- [ ] `P3-AGENT-1` Run spec gains: permission profile (`read_only`, `edit`), MCP servers,
      extra system prompt, model.
- [ ] `P3-AGENT-2` Session resume for follow-up messages and retries.
- [ ] `P3-AGENT-3` Agent pool: a list of configured agents (preset id, adapter, model); one
      is marked lead.

## GIT: additions

- [ ] `P3-GIT-1` `diffStat(repo, taskId)`: files changed, lines added and removed against
      the branch point.
- [ ] `P3-GIT-2` Create a worktree from another task's branch (for dependent tasks).

## DISPLAY: the wall

- [ ] `P3-DISPLAY-1` Wall layout: header (goal text, progress count, total cost), six
      columns: Planned, Working, Needs You, Review, Merged, Failed.
- [ ] `P3-DISPLAY-2` Task card: title, assignee name, model, +/- lines, elapsed time, cost;
      colour by status. One Text Display and one Interaction per card.
- [ ] `P3-DISPLAY-3` Overflow: a column shows a fixed number of cards and "+N more"; the
      full list is in the board screen.
- [ ] `P3-DISPLAY-4` Roster panel beside the wall: per agent name, status, current file,
      model, cost today.
- [ ] `P3-DISPLAY-5` Question marker: an icon above the NPC and the Needs You card pulses.

## NPC: additions

- [ ] `P3-NPC-1` Lead behaviour: stands at the wall while planning, "pins" cards (walks
      along the wall as tasks appear).
- [ ] `P3-NPC-2` Question behaviour: walk to the asking player's position (or the owner),
      stop two blocks away, play a sound, face them. If the player is far or in another
      dimension, wait at the studio and send a chat notice instead.
- [ ] `P3-NPC-3` Return to the desk when answered.

## PACKET, CSTATE, SCREEN

- [ ] `P3-PACKET-1` Payloads: board state sync (incremental), plan approval actions, task
      actions, question answer.
- [ ] `P3-SCREEN-1` `PlanScreen`: task list with briefs and dependencies; approve, reject,
      edit.
- [ ] `P3-SCREEN-2` `TaskScreen`: brief, status history, transcript tab, action buttons.
- [ ] `P3-SCREEN-3` `QuestionScreen`: the question, option buttons if given, free text.
      Also answerable by chatting to the NPC.
- [ ] `P3-SCREEN-4` `BoardScreen`: the full wall as a UI for when in-world text is too
      small, opened by clicking the wall header.

## CMD

- [ ] `P3-CMD-1` `/vibe goal <text>`, `/vibe plan approve|reject`, `/vibe answer <text>`,
      `/vibe agents`, `/vibe budget [amount]`.

## Things to consider

- Dependent tasks: waiting for `merged` is safe but slow because the player gates each
  step. Starting from a dependency's `review` branch is faster but means a rejected
  dependency invalidates its dependants. Default to waiting; make the other a setting.
- Two workers touching the same file: ask the lead to split by file, and accept that some
  conflicts appear at merge time (phase 4 handles them).
- A lead that explores a large repo can spend a lot before any work starts. Show the lead's
  usage on the wall header and include it in the budget.
- Cost data: subscription CLIs may report tokens but not money. Budget in tokens when cost
  is absent.
- Questions are interruptions. Tell workers to batch questions and to proceed on reversible
  choices; make the "ask threshold" part of the worker prompt, tuned by trying it.
- Prompt injection: a repo file can tell an agent to do things. Workers run with edit
  permissions inside the worktree only; anything beyond that should prompt through
  `ask_user`.
