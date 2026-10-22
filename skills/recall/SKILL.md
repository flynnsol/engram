---
name: recall
description: Look things up in the Engram vault - past memories, project plans, ideas, decisions, or notes. Use when the user asks what we decided, what I know about them or a project, "check my vault/notes", or when prior context would help and the session has not loaded it. Navigates by overviews and wikilinks, then searches.
---

# recall

1. **Get the vault**: `${CLAUDE_PLUGIN_ROOT}/scripts/engram.sh get`. If none is set, say so and point to `/engram vaultpath <path>`.
2. **Navigate top-down**: read `<vault>/INDEX.md`, pick the relevant section overview (`Projects Overview`, `Memory Overview`, ...), then open the specific note from its list. For a project, start at its `<Name> Overview` and follow the links to the plan, decisions and log.
3. **Search when navigation isn't enough**: `Grep` the vault (exclude `.obsidian/`) for key terms, tags, or frontmatter like `status: active` or `memory_type: feedback`. Check `00-Inbox/` too, since it may hold unfiled notes.
4. **Follow wikilinks** and `up` links to gather related context; stop when you have enough.
5. **Answer with sources**: cite the notes as `[[Note Name]]`. Say plainly if the vault has nothing on the topic.
6. **Verify before relying**: notes record what was true when written. If a note names a file, flag or system, check it still exists before recommending it, and fix or archive stale notes (see `engram:conventions`).

This skill is read-only. To save anything new, use `engram:remember`.
