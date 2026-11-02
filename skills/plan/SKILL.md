---
name: plan
description: Use this first for any planning. Plan a project, an epic (one feature, 2 weeks or less) or a single ticket in the Engram vault through a short guided interview, then create the notes. Use when the user describes a new project, product, roadmap or feature, says "plan", "scope", "break down" or "where do we start", or wants to file one bug, task or chore. Creates nothing until the user confirms.
---

# plan

Turn an idea into vault notes: a project (`<Name> Overview` + `<Name> Plan`), epics, and small tickets. Interview first, create last. Follow `engram:conventions` and `engram:principles`.

## Pick the level

| Request | Level |
|---|---|
| A product, roadmap or multi-week effort | **Project**: suggest epics, then tickets |
| One feature, up to 2 weeks for one engineer | **Epic**: interview, then tickets |
| One bug, task or chore | **Ticket** |

If unsure, ask once. If a "ticket" is really a feature, plan it as an epic; if an "epic" is over 10 working days, split it.

## Before asking

Get the vault (`${CLAUDE_PLUGIN_ROOT}/scripts/engram.sh get`) and use `engram:recall` for the project: its Overview, Plan, existing epics and tickets, and related decisions. Read the repo too if the project has one. Skip questions already answered.

## Interview

One or two questions at a time; use `AskUserQuestion` for choices. Restate in a sentence and get a yes.

| Level | Need |
|---|---|
| Project | Purpose and audience, "first usable version", in/out of scope, constraints, risks |
| Epic | Goal, scope in/out, done-when, where in the code, constraints, risks, effort in working days, owner |
| Ticket | What and why, parent epic, files touched, blockers |

Vague answer: ask for a concrete example. "You decide": propose a default and get a yes.

## Break down

- **Project**: propose epics as thin shippable slices in build order, each 10 days or less, risky work early, with dependencies. Let the user pick (`AskUserQuestion`, `multiSelect`, groups of 4). Unchosen epics go in the Plan note under *Later*. Then break each chosen epic down: guided (full epic interview), automatic (draft it, state assumptions) or later (epic note only).
- **Epic**: list tickets, each fitting one commit or PR (under 200 lines, 5 files); split any that do not. Order them, mark `blocked_by`, estimate in half-day steps, add them up with buffer for named unknowns. Over 10 days: do not create; propose a split and create the first epic only.

Show a compact summary (epics with ticket titles and days) and get a yes.

## Create

1. **Project** (if new): folder `01-Projects/<Name>/` with `<Name> Overview` and `<Name> Plan` from the templates; list it in `[[Projects Overview]]` and `[[INDEX]]`.
2. **Epics**: `<Name> E<n> <Title>.md` from *Epic Template*, in the project folder, `status: backlog`, listed in the Overview under *Epics*.
3. **Tickets**: `<Name> T<n> <Short title>.md` from *Ticket Template*, `up` and `epic` pointing at the epic, `status: backlog`. Numbers continue from the highest existing for that project (search the folder first). Imperative titles ("Add OAuth callback handler").
4. Fill the epic's `<!-- engram:tickets -->` list with `- [ ] [[Ticket]] — summary`.
5. Add `[[Epic]]` entries to the project Overview and Plan; refresh `[[INDEX]]` "Recently updated".
6. Build the roadmap with `engram:roadmap`.
7. Report the epics and tickets as `[[links]]`.

## Rules

- Create nothing before the final yes; if the user stops midway, say what is left.
- Link decisions and ideas to the plan with wikilinks instead of copying them.
- Write `blocked_by` as quoted wikilinks, `blocked_by: ["[[Name]]"]`, so the roadmap can draw the arrows.
- Statuses: `backlog`, `todo`, `doing`, `review`, `done`, plus optional `blocked`.
