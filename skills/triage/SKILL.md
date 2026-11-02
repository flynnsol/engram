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
7. Refresh `[[INDEX]]` "Recently updated" and report: what moved where, using `[[links]]`.
