---
name: work
description: Execute planned work (planned means a project folder exists under 01-Projects; for anything new, run engram:plan first) from the Engram vault - show the board, pick up the next ticket, move tickets between backlog/todo/doing/review/done/blocked, and close tickets, epics and projects when done. Use when the user says what's next, what's in progress, start or pick up a ticket, or that a ticket, PR, feature or epic is done, merged or shipped.
---

# work

Tickets and epics are vault notes (see `engram:plan`). Status lives in each note's `status` frontmatter; moving work means editing it and keeping the lists in sync. Follow `engram:conventions` and `engram:principles`.

Statuses: `backlog` → `todo` → `doing` → `review` → `done`, optional `blocked`, and `archived` for retired tickets (skipped by `ready`, the digest and lint; no checked box needed).

## Commands (use these, not hand edits)

`${CLAUDE_PLUGIN_ROOT}/scripts/engram.sh` does the mechanical bookkeeping and rebuilds the roadmap canvas each time:

- `ticket "<Project> T12" <status> [--force]`: sets the status, bumps `updated`, ticks or unticks the epic's checklist line, starts the epic (`doing`) with its first active ticket, and refuses to start a ticket whose `blocked_by` are not done. Prints `n of m tickets done`.
- `ready "<Project>" [--epic "<epic>"] [--waves]`: read-only. Lists the tickets that can start now (not blocked, `touches` disjoint from each other and from work in flight) with their `role`, and why any other is held. `--waves` prints the epic's waves. A ticket with no `touches` is treated as colliding with everything.
- `close-epic "<Project> E3"`: refuses while tickets are open; sets the epic `done`, marks it in the project Overview, and says how many *Done when* items are still unticked.
- `close-project "<Project>"`: refuses while epics are open; sets the Overview `done` and moves it to the done lists in `[[Projects Overview]]` and `[[INDEX]]`.

You still do the judgment parts: ask before closing, tick *Done when* items that are met, write the summary, and refresh `[[INDEX]]` "Recently updated". Run `engram.sh lint` after a batch of changes.

## Gate

Work only starts on planned work. If the user asks to build something that has no project folder or ticket in the vault, stop and run `engram:plan` first; a go-ahead such as "let's do it" does not replace a plan. If a ticket is growing past one commit or PR, stop and split it with `engram:plan`.

## Board / what's next

Find tickets with Grep on `type: ticket` and `status:` under `01-Projects/<Name>/`. Report briefly, grouped by status: `doing` and `blocked` first, then the next `todo` (or `backlog`) ticket whose `blocked_by` are all `done`. The project Overview may carry a live board:

````
```dataview
TABLE status, epic, estimate_days FROM "01-Projects/<Name>" WHERE type = "ticket" AND status != "done" SORT status ASC
```
````

## Run tickets in parallel

Use this when `engram.sh ready` returns two or more tickets. For one ticket, use *Start a ticket*.

1. Run `engram.sh ready "<Project>"`. Confirm the batch with the user the first time.
2. For each ticket, run `engram.sh ticket "<ticket>" doing`, then spawn one subagent in its own git worktree (`isolation: "worktree"`), in a single message so they run together.
3. Choose the agent by the ticket's `role`: an installed agent whose name matches (`engineer`, `reviewer`, `tester`, for example from a separate agents plugin), else `general-purpose`. Brief it with the ticket text, its *Acceptance* checks, its `touches`, and the rule: stay inside `touches`, make one commit, do not touch the vault.
4. **Only you (the orchestrator) change ticket status or write to the vault.** Subagents report back; you run `engram.sh ticket`.
5. When a subagent finishes, run `engram.sh ticket "<ticket>" review` and send the diff to a `reviewer` agent (else `general-purpose`) to check it against *Acceptance*. Pass: merge, then `done`. Fail: back to `doing` with the findings, one retry, then ask the user.
6. Merge the worktree branches one at a time, run the tests after each, then run `engram.sh ready` again for the next wave.

## Start a ticket

1. Confirm which ticket (from the user's words, branch name, or the next unblocked one). Read it and its epic.
2. Check `blocked_by` are done; if not, say so and ask.
3. Run `engram.sh ticket "<ticket>" doing`, and work it. Keep to one commit or PR under 200 lines and 5 files; if it is growing past that, stop and split it (new tickets via `engram:plan`).
4. When opening a PR, run `engram.sh ticket "<ticket>" review` and note the commit or PR link under *Notes*.

## Ticket done

1. Check the commit or PR is merged (`git log`, `gh pr view`). If not, say so and ask.
2. Run `engram.sh ticket "<ticket>" done`. It updates the note, the epic checklist and the roadmap.
3. Report `n of m` done in the epic and the next open ticket.

## Epic done

When the last ticket is done:

1. List any open tickets still pointing at the epic; ask whether to move or close them.
2. Check each *Done when* item; ask about any that look unmet and tick the rest.
3. Run `engram.sh close-epic "<epic>"`.
4. Offer a three-line summary: append to today's `[[Journal Overview]]` note, or record a decision with the Decision template if a choice was made along the way.

## Project done

When every epic is done, run `engram.sh close-project "<Project>"` (never delete notes), and offer a short wrap-up. If the user-level `readme-builder` skill is available and the project has a repo, offer to run it to update the README and repo metadata, using the Overview and Plan as source material.

## Rules

- Never mark done without the user's yes, unless they just said it is done.
- Do not close a ticket whose PR is unmerged unless the user says to.
- Keep reports to a few lines; refresh `[[INDEX]]` "Recently updated".
