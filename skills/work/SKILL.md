---
name: work
description: Execute planned work (planned means a project folder exists under 01-Projects; for anything new, run engram:plan first) from the Engram vault - show the board, pick up the next ticket, move tickets between backlog/todo/doing/review/done/blocked, and close tickets, epics and projects when done. Use when the user says what's next, what's in progress, start or pick up a ticket, or that a ticket, PR, feature or epic is done, merged or shipped.
---

# work

Tickets and epics are vault notes (see `engram:plan`). Status lives in each note's `status` frontmatter; moving work means editing it and keeping the lists in sync. Follow `engram:conventions` and `engram:principles`.

Statuses: `backlog` → `todo` → `doing` → `review` → `done`, optional `blocked`.

## Gate

Work only starts on planned work. If the user asks to build something that has no project folder or ticket in the vault, stop and run `engram:plan` first; a go-ahead such as "let's do it" does not replace a plan. If a ticket is growing past one commit or PR, stop and split it with `engram:plan`.

## Board / what's next

Find tickets with Grep on `type: ticket` and `status:` under `01-Projects/<Name>/`. Report briefly, grouped by status: `doing` and `blocked` first, then the next `todo` (or `backlog`) ticket whose `blocked_by` are all `done`. The project Overview may carry a live board:

````
```dataview
TABLE status, epic, estimate_days FROM "01-Projects/<Name>" WHERE type = "ticket" AND status != "done" SORT status ASC
```
````

## Start a ticket

1. Confirm which ticket (from the user's words, branch name, or the next unblocked one). Read it and its epic.
2. Check `blocked_by` are done; if not, say so and ask.
3. Set `status: doing`, bump `updated`, and work it. Keep to one commit or PR under 200 lines and 5 files; if it is growing past that, stop and split it (new tickets via `engram:plan`).
4. When opening a PR, set `status: review` and note the commit or PR link under *Notes*.

## Ticket done

1. Check the commit or PR is merged (`git log`, `gh pr view`). If not, say so and ask.
2. Set `status: done`, bump `updated`.
3. In the epic's ticket list, change `- [ ] [[Ticket]]` to `- [x] [[Ticket]]`.
4. Report `n of m` done in the epic and the next open ticket.
5. Refresh the roadmap with `engram:roadmap` (also after any status change to `doing`, `review` or `blocked`).

## Epic done

When the last ticket is done:

1. List any open tickets still pointing at the epic; ask whether to move or close them.
2. Check each *Done when* item; ask about any that look unmet and tick the rest.
3. Set the epic `status: done`; update its line in the project Overview.
4. Offer a three-line summary: append to today's `[[Journal Overview]]` note, or record a decision with the Decision template if a choice was made along the way.

## Project done

When every epic is done, set the Overview `status: done`, move it to *On hold / done* in `[[Projects Overview]]` and `[[INDEX]]` (never delete), and offer a short wrap-up. If the user-level `readme-builder` skill is available and the project has a repo, offer to run it to update the README and repo metadata, using the Overview and Plan as source material.

## Rules

- Never mark done without the user's yes, unless they just said it is done.
- Do not close a ticket whose PR is unmerged unless the user says to.
- Keep reports to a few lines; refresh `[[INDEX]]` "Recently updated".
