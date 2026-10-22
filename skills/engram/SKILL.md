---
name: engram
description: Manage the Engram Obsidian vault. Use for `/engram vaultpath <path>` (set the vault location), `/engram init` (scaffold the vault), `/engram status`, or `/engram` with no arguments to show the current state. Also use when the user asks where their vault is or wants to point Engram at a different folder.
---

# engram

Engram stores memories, ideas, project plans and notes in an Obsidian vault at a user-configured path. This skill handles setup. For day-to-day use see `engram:remember`, `engram:recall` and `engram:triage-inbox`; the vault rules are in `engram:conventions`.

The helper script is `${CLAUDE_PLUGIN_ROOT}/scripts/engram.sh`. Parse the arguments after `/engram`:

| Invocation | Action |
|---|---|
| `vaultpath <path>` | Run `engram.sh set "<path>"`. Then, if it reports the vault has no `INDEX.md`, offer to run init. |
| `vaultpath` (no path) | Run `engram.sh get` and report it. |
| `init` | Run `engram.sh init`. It copies the scaffold without overwriting existing files, so it is safe on an existing vault. Report what it created. |
| `status` or no args | Run `engram.sh status` and summarize: path, note count, inbox count. If no vault is set, explain `/engram vaultpath <path>`. |

Notes:
- Quote the path. `~` is expanded by the script.
- The path is stored in `${XDG_CONFIG_HOME:-~/.config}/engram/vault`, so it survives plugin updates and applies to every project.
- After changing the path, tell the user a new session picks up the new `INDEX.md` automatically; in the current session, read `<vault>/INDEX.md` now.
- Never delete or move an existing vault when the path changes.
