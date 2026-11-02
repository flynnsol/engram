---
type: meta
tags: [meta, conventions]
up: "[[Meta Overview]]"
created: {{init_date}}
updated: {{init_date}}
---

# Conventions

Up: [[Meta Overview]] · [[INDEX]]

The rules that keep the vault navigable for a human and for Claude.

## Linking

1. **Every note has an `up` property** linking to its parent overview, and a `Up: [[...]]` line under the title. Following `up` repeatedly always reaches [[INDEX]].
2. **Every overview lists its children** and every child is listed in exactly one overview. A note missing from its overview is effectively lost.
3. **Link related notes with `[[wikilinks]]`** in the body: a decision to its project, an idea to the project it became, a memory to the project it concerns. Prefer a link over restating.
4. **Filenames are unique** across the vault so `[[Name]]` never resolves ambiguously. Overviews are named `<Scope> Overview`.
5. Link to a heading with `[[Note#Heading]]` when only a part is relevant.

## Frontmatter

```yaml
---
type: scratch | project-overview | project-plan | epic | ticket | decision | idea | knowledge | memory | journal | overview | meta
status: active | paused | done | archived   # projects, plans
status: backlog | todo | doing | review | done | blocked   # epics, tickets
tags: []
up: "[[Parent Overview]]"
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Memory notes also carry `memory_type: user | feedback | project | reference`. Update `updated` on every edit.

## Structure

- Section folders are numbered (`00-` to `05-`, `99-`) so sort order is stable. Do not rename them.
- Projects: `01-Projects/<Name>/` holds `<Name> Overview`, `<Name> Plan`, epics (`<Name> E1 Title`), tickets (`<Name> T1 Title`), and decision/log notes. A ticket's `up` is its epic, an epic's `up` is the Overview. Change a ticket's `status` and tick it in its epic's list in the same step. Archive by setting `status: archived` and moving the entry in [[Projects Overview]]; do not delete.
- Inbox notes may have no structure. Anywhere else, follow the templates.

## Maintaining overviews

Claude maintains the lists that follow each `<!-- engram:... -->` marker; humans may edit anything. Keep entries as `- [[Note]] — one-line summary`. The `dataview` blocks are optional live views (need the Dataview plugin); the static lists are the source of truth for Claude.

## Writing style

Short and specific. One fact or idea per note. For feedback and project memories, include a **Why** and **How to apply**.
