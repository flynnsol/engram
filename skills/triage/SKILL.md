---
name: triage
description: Sort the Engram vault's 00-Inbox - file each scratch note into the right section, add frontmatter and links, and update the overviews. Use when the user asks to triage, sort, clean up or file the inbox or scratch notes, or when the session start notice says the inbox has unsorted notes and the user agrees.
---

# triage

Follow `engram:conventions`.

1. **Get the vault**: `${CLAUDE_PLUGIN_ROOT}/scripts/engram.sh get`. List `00-Inbox/*.md` (ignore `Inbox Overview.md`). If empty, say so and stop.
2. **Read each note** and decide its destination using the table in `engram:remember` (memory, project, idea, knowledge, journal).
3. **Plan before moving**: show a short table of `note → destination (new title if renamed)` and let the user adjust. Do not move anything the user has not seen planned, unless they asked you to just do it.
4. **For each note**: move it (keeping content), add or fix frontmatter and the `up` link/`Up:` line, make the filename unique vault-wide, add wikilinks to related notes, and list it under the right marker in its destination overview. A note that is really several things becomes several notes, linked to each other.
5. **Leave anything ambiguous** in the inbox and ask about it at the end.
6. **Never delete** original content. If a note is pure noise, ask first.
7. **Tidy project folders**: in each `01-Projects/<Name>/`, find notes with `type: epic` or `type: ticket` that sit loose in the project root or in the wrong place. Move each epic into `Epics/<epic name>/<epic name>.md` (a folder per epic) and each ticket into `Epics/<its epic>/Tickets/` (the epic named in its `epic` property), creating those folders if needed. Moving by name keeps wikilinks working; if `<Name> Roadmap.canvas` exists, regenerate it with `engram:roadmap` since canvas cards use file paths. Include this in the plan shown in step 3.
8. **Old ticket format**: run `${CLAUDE_PLUGIN_ROOT}/scripts/engram.sh migrate`. If it lists open tickets without `touches`/`role` or out-of-date templates, show the list and, on a yes, run `engram.sh migrate --apply` (templates keep a `.bak`). It also lists the project prefixes, the `T<n>` to `PREFIX-<n>` ticket renames and the `kind` values it would set; `--apply` copies the whole vault to a sibling `<vault>.backup-<time>` folder first, then renames and rewrites every link and canvas (re-running does nothing). Afterwards, tell the user that `touches` are empty and are filled in when a ticket is next planned or picked up.
9. Refresh `[[INDEX]]` "Recently updated" and report: what moved where, using `[[links]]`.
