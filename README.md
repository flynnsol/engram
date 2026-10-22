# Engram

A persistent memory vault for Claude Code, stored as an [Obsidian](https://obsidian.md) vault so a human and an AI can both read, search and edit it.

Memories, ideas, project plans and notes live in one folder you choose. Every section has an overview, every overview links up to a root `INDEX`, and notes link to each other with `[[wikilinks]]`, so you can jump around in Obsidian and Claude can navigate top-down.

## Skills

| Skill | Use it to |
|---|---|
| `/engram vaultpath <path>` | Set where the vault lives (stored in `~/.config/engram/vault`) |
| `/engram init` | Scaffold the vault (never overwrites existing files) |
| `/engram status` | Show the path, note count and inbox size |
| `engram:remember` | Save a memory, idea, plan, decision, knowledge note or journal entry |
| `engram:recall` | Look things up by navigating overviews and links |
| `engram:triage-inbox` | File your hand-made scratch notes into the right sections |
| `engram:conventions` | The rules for writing and linking notes |

A SessionStart hook tells Claude where the vault is and to read `INDEX.md` when it needs context.

## Vault layout

```
INDEX.md            root overview, links to every section
00-Inbox/           drop scratch notes here by hand
01-Projects/<Name>/ <Name> Overview, plan, decisions
02-Ideas/
03-Knowledge/
04-Memory/          user/ feedback/ project/ reference/
05-Journal/         YYYY-MM-DD daily notes
99-Meta/            Conventions, Templates/
```

Each section has `<Section> Overview.md` with `Up: [[INDEX]]`, and every note carries an `up:` property so the chain always leads back to the root. Static lists in overviews are maintained by Claude; optional Dataview blocks give live views.

## Getting started

```bash
claude plugin marketplace add /path/to/engram   # or the git URL once published
claude plugin install engram@engram
```

Then in Claude Code:

```
/engram vaultpath ~/Vaults/Engram
/engram init
```

Open that folder as a vault in Obsidian. The scaffold points new notes at `00-Inbox`, the Templates plugin at `99-Meta/Templates`, and daily notes at `05-Journal`. Install the Dataview community plugin if you want the live query blocks.

To try a local checkout: `claude --plugin-dir /path/to/engram`.
