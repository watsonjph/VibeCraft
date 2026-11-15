# Claude Code fixtures

Real output from the Claude Code CLI, recorded with `record.py`. The Claude Code adapter
and its tests are built against these files, not against documentation or memory.

Recorded with Claude Code 2.1.325 on Windows, on a subscription login, model `haiku`.
Paths, the user name and account details are replaced; everything else is as the CLI
printed it, re-serialised as compact JSON.

| File | What it is |
|---|---|
| `oneshot.jsonl` | Stdout of one headless run, one JSON object per line: a read, an edit, a shell command, a final message |
| `session.jsonl` | A live two-way session. Each line is `{"dir": "in" or "out", "t": seconds, "msg": {...}}`; `in` is what we wrote to stdin, `out` is one stdout line |
| `record.py` | Re-records both. Run it after a CLI update; a diff in the fixtures shows what changed |

## Commands

One-shot:

```
claude -p "<prompt>" --output-format stream-json --verbose --include-partial-messages
  --permission-mode acceptEdits --allowedTools Read Edit "Bash(python:*)"
  --disallowedTools "Bash(git push:*)" --setting-sources "" --strict-mcp-config
  --no-session-persistence --model haiku --max-budget-usd 0.50
```

Live session (prompts go to stdin as JSON lines; closing stdin ends it with exit code 0):

```
claude -p --input-format stream-json --output-format stream-json --verbose
  --include-partial-messages --permission-prompt-tool stdio --allowedTools Read
  --disallowedTools "Bash(git push:*)" --setting-sources "" --strict-mcp-config
  --model haiku --max-budget-usd 0.50
```

The working directory is the process's current directory. Every `CLAUDE*` environment
variable is removed before launch.

## What the recordings establish

Observed in these files:

- **Line types on stdout.** `system` (`init`, `status`), `stream_event` (partial output),
  `assistant` (a complete message: text or tool use), `user` (tool results),
  `rate_limit_event`, `result`, and in a live session `control_request` and
  `control_response`.
- **Tool activity.** An `assistant` line carries `tool_use` blocks with `name` (`Read`,
  `Edit`, `Bash`) and `input`; the matching `user` line carries the `tool_result`. This is
  the source for our `agent.read`, `agent.edit` and `agent.command` events.
- **Partial text.** `stream_event` lines with `event.delta.type == "text_delta"` carry the
  reply as it is written. This is the source for `stream` messages.
- **Usage and cost.** Each `result` has `total_cost_usd`, `usage` and `modelUsage`. On a
  subscription login (`apiKeySource: "none"`) a cost figure is still reported.
- **Subscription limits.** `rate_limit_event` reports `status`, `resetsAt` and utilisation
  of the five-hour and seven-day windows. This is what the budget module needs for
  subscription warnings.
- **Follow-up messages.** A second and third user message on stdin run in the same process
  and session. Each turn begins with a fresh `system/init` line and ends with a `result`.
- **Permission requests.** With `--permission-prompt-tool stdio`, a tool that is not
  pre-allowed produces a `control_request` with `subtype: "can_use_tool"`, the tool name
  and its input. Answering with a `control_response` of `behavior: "allow"` lets it run.
- **Interrupt.** A `control_request` with `subtype: "interrupt"` is acknowledged and the
  turn ends with a `result` whose `terminal_reason` is `aborted_streaming`. The session
  then accepts the next message.

Not yet tested: denying a permission request, resuming a session after the process exits,
registering an MCP server per run, sending a message while a turn is still running without
interrupting, and behaviour on an API key instead of a subscription.

## Settings isolation

`--setting-sources ""` keeps the user's own hooks, plugins and project settings out of the
run. Without it, whatever the user has configured for Claude Code runs inside every agent.
Whether agents should inherit the user's settings is a product decision still to make; the
fixtures are recorded without them so they are reproducible.

`--bare` is not usable for subscription logins: it reads no stored login at all.
`--restricted` removes the command-running tools and confines file tools to the working
directory, which is the likely basis for play-mode and strict-guardrail sessions.
