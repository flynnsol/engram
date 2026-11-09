---
name: plan
description: MANDATORY first step before creating, scaffolding or building any new project, repo, app, tool, site, plugin or feature, even when the user says "let's do it" or "go ahead". Plan a project, an epic (one feature, 2 weeks or less) or a single ticket in the Engram vault through a short guided interview, then create the notes. Use when the user describes a new project, product, roadmap or feature, asks to create or make something, says "plan", "scope", "break down" or "where do we start", or wants to file one bug, task or chore. Creates nothing until the user confirms.
---

# plan

Turn an idea into vault notes: a project (`<Name> Overview` + `<Name> Plan`), epics, and small tickets. Interview first, create last. Follow `engram:conventions` and `engram:principles`.

## Hard gate (read first)

This skill is **required, not advisory**. Run it, and get the user's confirmation, **before** any of these:

- writing code or config for a new project, repo, app, tool, site, plugin or feature
- running a scaffold command (`cargo new`, `dx new`, `npm create`, `uv init`, `rails new`, ...) or creating the project folder
- brainstorming a plan in chat instead of in the vault

Rules that close the usual loopholes:

- **A go-ahead is not a plan.** "Let's do it", "sounds good", "go ahead" and picking a name approve the *idea*. They never skip the interview and the vault notes.
- **Planning in chat does not count.** The plan must exist as notes under `01-Projects/<Name>/` (an Overview and a Plan at minimum).
- **Do it first, not afterwards.** Do not scaffold now and promise to backfill later. If you already did, say so plainly, then run this skill.
- **Smallest exception:** a tiny edit inside a project that already has a folder under `01-Projects` needs no new plan (use `engram:work`). If unsure whether something is "new", ask once.
- If the user explicitly says to skip planning, create the minimal notes (Overview and Plan, no epics) and carry on. Do not skip the vault.

A `PreToolUse` gate backs this up: it denies new-project scaffolding and new manifest files (`Cargo.toml`, `package.json`, `pyproject.toml`, ...) until the project has a folder under `01-Projects`. If the gate denies a call, run this skill; do not look for a way around it.

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
| Ticket | What and why, parent epic, files touched, blockers, role, how to check it is done |

Vague answer: ask for a concrete example. "You decide": propose a default and get a yes.

## Break down

- **Project**: propose epics as thin shippable slices in build order, each 10 days or less, risky work early, with dependencies. Let the user pick (`AskUserQuestion`, `multiSelect`, groups of 4). Unchosen epics go in the Plan note under *Later*. Then break each chosen epic down: guided (full epic interview), automatic (draft it, state assumptions) or later (epic note only).
- **Epic**: list tickets, each fitting one commit or PR (under 200 lines, 5 files); split any that do not. Order them, mark `blocked_by`, estimate in half-day steps, add them up with buffer for named unknowns. Over 10 days: do not create; propose a split and create the first epic only.

- **Plan for parallel work**: give every ticket `touches` (the paths it changes) and a `role` (`engineer`, `reviewer`, `tester`; default `engineer`). Tickets that touch the same paths must be ordered with `blocked_by`, or merged. Put shared types, APIs and schemas in the first ticket so later tickets build against them. Write *Acceptance* as checks a test or command can confirm, since an agent cannot ask questions mid-ticket. For epics with 3 or more tickets, fill the epic's *Orchestration* section with the waves.

Show a compact summary (epics with ticket titles and days) and get a yes.

## Create

1. **Project** (if new): folder `01-Projects/<Name>/` with `<Name> Overview` and `<Name> Plan` from the templates; list it in `[[Projects Overview]]` and `[[INDEX]]`.
2. **Epics**: one folder per epic, `01-Projects/<Name>/Epics/<Name> E<n> <Title>/`, holding the epic's note of the same name (`<Name> E<n> <Title>.md`, from *Epic Template*, `status: backlog`). Listed in the Overview under *Epics*. Create the `Epics/` folder if it is missing.
3. **Tickets**: inside their epic's folder, `01-Projects/<Name>/Epics/<epic>/Tickets/<Name> T<n> <Short title>.md` (create the epic's `Tickets/` if missing), from *Ticket Template*, `up` and `epic` pointing at the epic, `status: backlog`. Numbers continue from the highest existing for that project (numbering is project-wide, so search every `Tickets/` folder in the project first). Imperative titles ("Add OAuth callback handler").
4. Fill the epic's `<!-- engram:tickets -->` list with `- [ ] [[Ticket]] — summary`.
5. Add `[[Epic]]` entries to the project Overview and Plan; refresh `[[INDEX]]` "Recently updated".
6. Build the roadmap with `engram:roadmap`, then run `engram.sh lint` and fix any ERROR it reports for the new notes.
7. Report the epics and tickets as `[[links]]`.

## Rules

- Create nothing before the final yes; if the user stops midway, say what is left.
- Link decisions and ideas to the plan with wikilinks instead of copying them.
- Write `touches` as a list of repo paths or globs, `touches: ["scripts/work.py", "tests/"]`, and `role: engineer` unless the ticket is a review or test pass.
- Write `blocked_by` as quoted wikilinks, `blocked_by: ["[[Name]]"]`, so the roadmap can draw the arrows.
- Statuses: `backlog`, `todo`, `doing`, `review`, `done`, plus optional `blocked`.
