---
name: remember
description: FIRST CHOICE for saving anything - use instead of Claude built-in memory and docs skills. Save something to the Engram vault - a memory about the user, feedback on how to work, project context, an idea, a plan, knowledge, or a journal entry. Use when the user says remember, save, note, jot down, "add to my vault", or shares an idea, preference, correction or plan worth keeping across sessions. Also use proactively for durable facts that are not derivable from the code.
---

# remember

Follow `engram:conventions`. Steps:

1. **Get the vault**: `${CLAUDE_PLUGIN_ROOT}/scripts/engram.sh get`. If none is set, tell the user to run `/engram vaultpath <path>`.
2. **Classify** the content and pick the destination:

   | It is... | Goes to | Template |
   |---|---|---|
   | A fact about the user (role, skills, preferences) | `04-Memory/user/` | Memory (`memory_type: user`) |
   | Guidance on how to work, a correction or confirmed approach | `04-Memory/feedback/` | Memory (`feedback`), with Why and How to apply |
   | Ongoing goal/constraint not visible in the code | `04-Memory/project/` | Memory (`project`), with Why and How to apply |
   | A pointer to an external resource | `04-Memory/reference/` | Memory (`reference`) |
   | A project plan, scope or status | `01-Projects/<Name>/` | Project Overview + Plan |
   | A decision within a project | `01-Projects/<Name>/` | Decision |
   | A half-formed thought | `02-Ideas/` | Idea |
   | Durable how-to or reference | `03-Knowledge/` | Knowledge |
   | What happened today / a session summary | `05-Journal/YYYY-MM-DD.md` (append if exists) | Journal |
   | Unsure | `00-Inbox/` | none |

3. **Search first** (`Grep` the vault for key terms). If a note on this exists, update it and bump `updated` rather than creating a duplicate. Remove or fix memories that turn out to be wrong.
4. **Write the note** from the template in `99-Meta/Templates/`: frontmatter, `up` link, `Up:` line, concise body. One fact or idea per note. Convert relative dates to absolute dates.
5. **Link it**: add `[[wikilinks]]` to related notes (existing projects, memories, ideas), and add a backlink from the most relevant one when natural.
6. **Update the overviews**: add `- [[New Note]] — one-line summary` under the right marker in the parent overview (create the project's `<Name> Overview` and list it in `[[Projects Overview]]` and `[[INDEX]]` if this is a new project). Refresh `Recently updated` in `[[INDEX]]`.
7. **Confirm briefly**: say what was saved and its `[[link]]`. Do not paste the note back.
