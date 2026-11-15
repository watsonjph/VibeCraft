# Phase 3: orchestration

From one agent to a team: a lead that plans, a wall of tasks, workers in parallel, and
questions that walk over to the player.

**Exit criteria**

1. `/vibe goal <text>` produces a plan the player can approve, edit or reject.
2. After approval, several workers run at once in separate worktrees and the wall shows each
   task moving through its columns.
3. An agent calling `ask_user` makes its NPC walk to the player; the answer unblocks it.
4. With a limit set, the player is warned at 80%, and at 100% the affected agents pause
   mid-run and one asks what to do. A per-agent limit stops only that agent.
5. The same goal can be run in `solo`, `lead` and `peer` mode by changing one setting, and
   `auto` picks solo for a one-file change and a plan for a multi-part one.

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
- [ ] `P3-ORCH-10` Budget hooks: ORCH asks BUDGET before every spawn and resume, and acts on
      its decisions (pause, ask, stop). The rules live in BUDGET (section below).
- [ ] `P3-ORCH-11` Rate-limit and auth failures from a CLI set the agent `blocked` with the
      reason and retry on a backoff with a ceiling, not in a tight loop.
- [ ] `P3-ORCH-12` Tests: transition table; plan validation cases; scheduler with a fake
      adapter (dependencies respected, parallel limit respected, budget stop).

## ORCH: team modes

How a goal is worked is a setting, per project, changeable per goal. See "Team modes" in
[modules.md](modules.md) for the definitions. The scheduler, state machine, worktrees and
review flow are shared; a mode only decides who creates tasks and who talks to whom.

- [ ] `P3-ORCH-13` `TeamMode` setting: `auto` (default), `solo`, `lead`, `peer`. Stored in
      project config; `goal.create` may override it for one goal.
- [ ] `P3-ORCH-14` `solo`: no planning step. The goal becomes one task for one agent in one
      worktree. This is the phase 1 path kept as a first-class mode.
- [ ] `P3-ORCH-15` `lead`: the flow in the section above (lead plans, workers execute).
      Option `leadAlsoCodes` lets the lead take a task itself once planning is done.
- [ ] `P3-ORCH-16` `peer`: no lead. Every agent starts with the goal and the shared task
      list (empty at first) and coordinates through the peer tools (see MCP below). A task
      exists once an agent adds it; an agent works only on tasks it has claimed. The goal is
      finished when no task is open and every agent has reported it has nothing to add.
- [ ] `P3-ORCH-17` `auto`: one agent starts and triages. It answers with either "I will do
      this myself" (continue as `solo` in the same session, so nothing is re-read) or a plan
      (continue as `lead`). The triage instruction: split only when the parts are
      independent enough to merge separately.
- [ ] `P3-ORCH-18` Defaults, in one place: mode `auto`, `maxParallelAgents` 3, plan approval
      required when a plan has more than one task and skipped for a single task,
      `leadAlsoCodes` on, dependants wait for `merged`.
- [ ] `P3-ORCH-19` Peer safety limits: a cap on messages per agent per goal and on total
      tasks, and a no-progress detector (messages exchanged, no commits for a set time) that
      pauses the goal and asks the player.
- [ ] `P3-ORCH-20` Tests with a fake adapter: each mode reaches `review` on a scripted goal;
      `auto` takes the solo path and the lead path; a peer loop trips the limit.

## BUDGET: limits and cost warnings

The behaviour is specified under "Budgets and cost warnings" in [modules.md](modules.md).

- [ ] `P3-BUDGET-1` Usage ledger: every `usage` event appended to `usage/<yyyy-mm>.jsonl`
      with agent, project, goal, actor, billing type, tokens, cost and whether the cost is
      an estimate. Totals rebuilt from the ledger on start.
- [ ] `P3-BUDGET-2` Billing type per agent preset (`api`, `subscription`, `local`), set in
      the agent settings and guessed from the adapter's login state when it can be.
- [ ] `P3-BUDGET-3` Price table `prices.json`: per model input and output price, shipped
      with current values, editable, used only when the CLI reports no cost. Estimated
      figures carry an "est." mark everywhere they are shown.
- [ ] `P3-BUDGET-4` Limit model: scope (all, project, agent, goal or session, guest), period
      (goal, day, week, month), unit (money, tokens, agent-minutes), thresholds, action.
      Stored in `config.json`; any number of limits.
- [ ] `P3-BUDGET-5` Evaluation on every usage event and before every spawn: all applicable
      limits checked, the first reached wins, results cached so it costs nothing per tick.
- [ ] `P3-BUDGET-6` Thresholds: notice at 50%, warning at 80%, reached at 100%, each
      adjustable per limit. Each fires once per period per limit (no repeated warnings).
- [ ] `P3-BUDGET-7` Enforcement during a run: on reached, pause affected sessions at their
      next step through the session interface; `stop` ends them. Verify the overshoot is at
      most one step.
- [ ] `P3-BUDGET-8` The `ask` flow: reuses the question flow. Choices: raise the limit (by
      a chosen amount), let this run finish, stop. Owner-only.
- [ ] `P3-BUDGET-9` Subscription signals: when a CLI reports its plan's rate-limit state or
      a "limit reached, resets at" message, surface it as a warning or reached event with
      the reset time (**verify** what each CLI exposes). Agents wait for the reset instead
      of retrying.
- [ ] `P3-BUDGET-10` Period reset at local midnight, week start and month start; paused
      agents resume if their limit's action was `pause`.
- [ ] `P3-BUDGET-11` First-use prompt: choose a daily limit from a few suggestions or enter
      one, or choose "no limit" explicitly. Until answered, `api` agents do not start.
- [ ] `P3-BUDGET-12` Pre-flight line when a goal or play session starts: what remains in
      each applicable limit.
- [ ] `P3-BUDGET-13` Commands: `/vibe budget` (show all limits and usage),
      `/vibe budget set <scope> <amount> <period>`, `/vibe budget remove <scope>`,
      `/vibe usage [agent|project|today|month]`.
- [ ] `P3-BUDGET-14` Display: a meter on the wall header for the tightest limit, a meter
      per agent on the roster, colour change at each threshold, "est." where estimated,
      and the blocked reason on cards and above the NPC.
- [ ] `P3-BUDGET-15` `BudgetScreen`: list of limits with add, edit and remove; usage by
      agent, project and day; the price table.
- [ ] `P3-BUDGET-16` Tests with `FakeAdapter` usage: warning fires once at 80%; reached
      pauses mid-run with at most one step of overshoot; per-agent limit blocks only that
      agent; reset resumes; ledger totals survive a daemon restart; estimates are marked.

## ORCH: speed

- [ ] `P3-ORCH-22` Repository brief: the first agent to explore a repo writes a short
      summary (layout, build and test commands, conventions). It is cached per project and
      commit, refreshed when the base moves, and handed to every later agent so workers do
      not each re-explore.
- [ ] `P3-ORCH-23` Role models: triage and planning may use a different, cheaper or faster
      model than coding. Default: same model for everything until measurements say
      otherwise; the setting exists from the start.
- [ ] `P3-ORCH-27` Start workers while the player reads the plan when approval is skipped;
      create worktrees in parallel; never run setup for a task that is not about to start.

## ORCH: compliance

Rules are enforced by the daemon and by each CLI's permission system. The prompt explains
the rules; it is never the only thing holding them.

- [ ] `P3-ORCH-21` Guardrail presets, per project: `strict` (every command and every write
      outside the task's listed files asks first), `balanced` (default: edits inside the
      worktree and a per-project list of safe commands run freely, anything else asks),
      `autonomous` (asks only for what is always denied). Always denied in every preset:
      remote git, writes outside the worktree, changing git config or hooks.
- [ ] `P3-ORCH-24` Check command: an optional per-project command (tests, lint, build) the
      daemon runs in the worktree when a worker says it is done. Failure sends the output
      back to the worker, a bounded number of times, then the task goes to Review marked
      "checks failing". Emits `task.check`.
- [ ] `P3-ORCH-25` Gate before Review, run by the daemon, not the agent: commits exist only
      on the task's branch; the user's checkout, HEAD, other branches, remotes, git config
      and hooks are unchanged since the task started; files touched are compared with the
      files the brief named and extras are flagged as out of scope. Emits `task.gate`. A
      repo-integrity failure fails the task; out-of-scope files only flag the card.
- [ ] `P3-ORCH-26` House rules: a per-project text (and the repo's own agent instruction
      files, which the CLIs already read) given to every agent, lead and worker alike.
- [ ] `P3-ORCH-28` Permission requests from a CLI become `agent.permission` events and
      follow the question flow: the NPC walks over, the player picks allow once, always
      allow for this project, or deny.
- [ ] `P3-ORCH-29` Tests: each preset allows and refuses the right scripted actions; the
      gate catches a commit on the wrong branch, an edited hook and an added remote.

## MCP: ask_user

- [ ] `P3-MCP-1` **verify** how each supported CLI registers an MCP server per run and which
      transports it accepts. Prefer one HTTP endpoint inside the daemon (no extra process
      per agent, faster start); fall back to a stdio server launched from the mod jar if a
      CLI only supports that.
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
- [ ] `P3-MCP-7` Peer tools, offered only in `peer` mode: `list_tasks`, `add_task(title,
      brief)`, `claim_task(id)`, `message_agent(agent, text)`, `read_messages`.
- [ ] `P3-MCP-8` `claim_task` is atomic in ORCH: two agents claiming the same task get one
      winner and one refusal.
- [ ] `P3-MCP-9` Message delivery: a message to a running agent is returned by its next
      `read_messages` call; a message to an idle agent resumes its session with the text.
      Each message is logged as `agent.peer_message`.

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
- [ ] `P3-GIT-3` Worktree setup: a per-project setup command (install dependencies,
      generate code) and an optional list of untracked paths to link or copy in. Without
      this, agents in fresh worktrees cannot build or test most real projects. Copying
      secret files such as `.env` is off unless the owner lists them.

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
- [ ] `P3-NPC-4` Mode-specific staging: `solo` shows one NPC and no lead; `peer` has no
      lead spot, and an agent messaging another walks to that agent's desk and back.

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
- [ ] `P3-CMD-2` `/vibe mode [auto|solo|lead|peer]` shows or sets the project's team mode;
      `/vibe goal --mode <mode> <text>` overrides it once.
- [ ] `P3-CMD-3` `/vibe stop all` and a stop lever in the studio: every agent process ends
      within 2 seconds, tasks become `planned` with reason `stopped`, worktrees are kept.
      `/vibe pause` and `/vibe resume` do the same without discarding session state.
- [ ] `P3-SCREEN-5` Team mode section in the board screen: mode picker with a one-line
      description of each, parallel-agent limit, plan approval and `leadAlsoCodes` toggles.
      The wall header shows the mode a goal is running in.

## Things to consider

- Why `auto` is the default: most goals are small, and a lead plus workers on a small goal
  costs several times the tokens of one agent for the same result. Check this with real
  runs before release and change the default if the numbers disagree.
- `peer` is the most expensive and least predictable mode: agents can talk in circles.
  Label it as experimental in the UI and keep its limits on by default.
- Mode changes apply to the next goal, never to one that is running.
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
