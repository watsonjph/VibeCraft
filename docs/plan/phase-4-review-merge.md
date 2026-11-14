# Phase 4: review and merge

Close the loop: read the real diff in game and decide. This phase holds the project's
central promise, so its git paths are the most heavily tested code in the repo.

**Exit criteria**

1. A task in Review opens a diff screen showing every changed file.
2. Merge creates a merge commit on the branch the player has checked out, and only then.
3. Request changes sends the note to the worker and the task returns to Working.
4. Discard removes the branch and worktree.
5. A dirty working tree or a conflict never leaves the player's repo in a changed state.

## GIT: diff and merge

- [ ] `P4-GIT-1` `diff(repo, taskId)`: list of files with status (added, modified, deleted,
      renamed), then per-file unified diff on request. Binary files reported as binary.
- [ ] `P4-GIT-2` Diff size limits: per-file and total caps; beyond them return stats and
      "too large to show", with the worktree path so the player can open it outside.
- [ ] `P4-GIT-3` `preflight(repo)`: working tree clean, no merge or rebase in progress, HEAD
      is a branch (not detached), task branch exists. Each failure has its own message.
- [ ] `P4-GIT-4` `merge(repo, taskId)`: preflight, then `merge --no-ff --no-edit` with a
      message naming the task. On any non-zero exit run `merge --abort` and verify HEAD and
      the tree are what they were before.
- [ ] `P4-GIT-5` `discard(repo, taskId)`: remove worktree, delete branch.
- [ ] `P4-GIT-6` Post-merge cleanup: remove the worktree, delete the merged branch.
- [ ] `P4-GIT-7` Commit identity: merges use the user's own git config; agent commits keep
      whatever the CLI sets. Never write to the user's git config.
- [ ] `P4-GIT-8` Tests against temp repos: clean merge; conflict aborts and leaves HEAD and
      status identical; dirty tree refused; detached HEAD refused; discard removes both;
      hooks that fail the merge are treated as a failed merge.

## ORCH: review flow

- [ ] `P4-ORCH-1` Commands `review.merge`, `review.request_changes(note)`,
      `review.discard`. Only valid from `review`.
- [ ] `P4-ORCH-2` Merge conflict path: task returns to `working` with an instruction to the
      worker to merge the current base branch into its branch and resolve; then back to
      `review`. Cap the number of automatic attempts.
- [ ] `P4-ORCH-3` Request changes: resume the worker's session with the note.
- [ ] `P4-ORCH-4` After a merge, mark other tasks in `review` as possibly stale and recompute
      their diff stats against the new base.
- [ ] `P4-ORCH-5` Unblock dependants of the merged task.
- [ ] `P4-ORCH-6` One merge at a time per repository (a lock), since merges change the base
      for everything else.

## ACCESS

- [ ] `P4-ACCESS-1` `review.merge` and `review.discard` require the owner in every access
      mode. Write this as its own check so phase 7 cannot loosen it by accident.

## PACKET, SCREEN

- [ ] `P4-PACKET-1` Payloads: file list, per-file diff pages, review actions and their
      results.
- [ ] `P4-SCREEN-1` `ReviewScreen`: file list on the left with +/- counts; unified diff on
      the right with added and removed colouring, line numbers, horizontal scroll or wrap
      toggle.
- [ ] `P4-SCREEN-2` Buttons: Merge (needs a second click to confirm), Request changes
      (opens a note field), Discard (confirm). Results and git error messages shown in
      place.
- [ ] `P4-SCREEN-3` Keyboard: next and previous file, next and previous hunk.

## DISPLAY, NPC

- [ ] `P4-DISPLAY-1` Review cards show "ready" and open `ReviewScreen` on click.
- [ ] `P4-NPC-1` A worker with work ready stands by the wall; on merge a small celebration
      (particles, sound), on discard it returns to idle.

## CMD

- [ ] `P4-CMD-1` `/vibe review <task>`, `/vibe merge <task>`, `/vibe discard <task>` as
      text fallbacks for the screen.

## Things to consider

- The player may be working in the repo at the same time, in an editor outside the game.
  Preflight runs immediately before the merge, not when the screen opens.
- The player may switch branches between starting a goal and merging. Merge goes into
  whatever is checked out now; show that branch name on the Merge button.
- Git hooks in the user's repo run on merge commits and can be slow or fail. Give merges a
  generous timeout and show hook output.
- Submodules, LFS and very large repos: out of scope for now, but fail with a clear message
  instead of a half-done operation.
- Line endings on Windows can make whole files appear changed. Do not "fix" it; show the
  diff as git reports it.
- "Never pushed": the daemon has no remote code and the GIT deny-list blocks it. Agents are
  launched with push denied in their CLI permissions. State in the UI that this is a
  default and not a sandbox.
