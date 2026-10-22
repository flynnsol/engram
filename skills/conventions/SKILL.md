---
name: conventions
description: Rules for reading and writing the Engram vault - section layout, frontmatter, the `up` link chain to INDEX, wikilinks, and keeping overviews current. Use before creating, moving or editing any note in the Engram vault, alongside engram:remember and engram:triage-inbox.
---

# Engram conventions

Get the vault path with `${CLAUDE_PLUGIN_ROOT}/scripts/engram.sh get`. The vault's own copy of these rules is `<vault>/99-Meta/Conventions.md`; if the two differ, the vault's copy wins (the user may have edited it).

## Layout

```
INDEX.md          root overview, links to every section overview
00-Inbox/         unsorted, human-created scratch; Claude triages it
01-Projects/<Name>/   <Name> Overview, <Name> Plan, decisions, logs
02-Ideas/         one note per idea
03-Knowledge/     durable reference, optional topic subfolders
04-Memory/        user/ feedback/ project/ reference/  (one fact per note)
05-Journal/       YYYY-MM-DD notes
99-Meta/          Conventions, Templates/
```

## The link chain (most important rule)

- Every note has `up: "[[Parent Overview]]"` in frontmatter and an `Up: [[Parent Overview]]` line under the title.
- Every overview lists all of its children as `- [[Note]] — one-line summary`, and links up. Following `up` always reaches `[[INDEX]]`.
- When you create, move, rename, archive or retire a note, update its parent overview in the same step. Update `[[INDEX]]`'s "Active projects" and "Recently updated" when relevant.
- Add body wikilinks to related notes (decision → project, memory → project, idea → project it became). Link generously.
- Filenames are unique vault-wide so `[[Name]]` never collides. Overviews are `<Scope> Overview`.

## Frontmatter

`type`, `tags`, `up`, `created`, `updated`, plus `status` where it applies and `memory_type` on memory notes. Bump `updated` on every edit. Full schema in `99-Meta/Conventions.md`.

## Editing rules

- Fill templates from `99-Meta/Templates/` rather than inventing structure.
- Edit list entries under `<!-- engram:... -->` markers in overviews; leave `dataview` blocks and any human-written text alone.
- Never delete notes. Archive by setting `status: archived` and moving the entry to the archived list in the overview.
- Before creating a note, search for an existing one on the same topic and update it instead of duplicating.
- Never store secrets (tokens, passwords) in the vault.
