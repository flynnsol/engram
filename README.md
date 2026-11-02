<img alt="Engram" src="res/engram-lockup-card.png" width="360">

A persistent memory vault for Claude Code, stored as an [Obsidian](https://obsidian.md) vault so a human and an AI can both read, search and edit it.

![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-D97757)
![Obsidian](https://img.shields.io/badge/Obsidian-vault-7C3AED?logo=obsidian&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

Memories, ideas, project plans and notes live in one folder you choose. Every section has an overview, every overview links up to a root `INDEX`, and notes link to each other with `[[wikilinks]]`, so you can jump around in Obsidian and Claude can navigate top-down.

## Skills

| Skill | Use it to |
|---|---|
| `/engram vaultpath <path>` | Set where the vault lives (stored in `~/.config/engram/vault`) |
| `/engram init` | Scaffold the vault (never overwrites existing files) |
| `/engram status` | Show the path, note count and inbox size |
| `engram:remember` | Save a memory, idea, plan, decision, knowledge note or journal entry |
| `engram:recall` | Look things up by navigating overviews and links |
| `engram:triage` | File your hand-made scratch notes into the right sections |
| `engram:plan` | Plan a project, epic or ticket through a short interview and create the notes |
| `engram:work` | Show the board, pick up the next ticket, and close tickets, epics and projects |
| `engram:roadmap` | Draw a project's epics, tickets and dependencies as an Obsidian canvas |
| `engram:principles` | Small tickets (under 200 lines, 5 files), small epics (2 weeks or less), short notes |
| `engram:conventions` | The rules for writing and linking notes |

A SessionStart hook tells Claude where the vault is and to read `INDEX.md` when it needs context. It also makes Engram the first choice for memory, project information and documentation, ahead of Claude's built-in memory and the Claude Docs skills. A UserPromptSubmit hook adds a reminder whenever a prompt looks like planning or executing work ("plan", "roadmap", "ticket", "what's next", "it's done"...), so `engram:plan` and `engram:work` are used first.

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

## Planning and executing work

Projects are planned in the vault, not in an issue tracker. `engram:plan` interviews you and creates `<Name> Overview` and `<Name> Plan`, epics (`<Name> E1 Title`) and tickets (`<Name> T1 Title`). Each ticket is a note with a `status` (`backlog`, `todo`, `doing`, `review`, `done`, `blocked`) that links up to its epic, so the `up` chain still reaches `INDEX`. `engram:work` moves tickets along, ticks them off in the epic, and closes epics and projects when everything is done. A Dataview block in the project Overview gives a live board.

## Getting started

```bash
claude plugin marketplace add https://github.com/flynnsol/engram.git
claude plugin install engram@engram
```

Then in Claude Code:

```
/engram vaultpath ~/Vaults/Engram
/engram init
```

Open that folder as a vault in Obsidian. The scaffold points new notes at `00-Inbox`, the Templates plugin at `99-Meta/Templates`, and daily notes at `05-Journal`. Install the Dataview community plugin if you want the live query blocks.

To try a local checkout: `claude --plugin-dir /path/to/engram`.

## License

MIT, see [LICENSE](LICENSE).
