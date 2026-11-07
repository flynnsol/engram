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

Three hooks keep Claude on the rails:

- **SessionStart** tells Claude where the vault is and to read `INDEX.md` when it needs context. It makes Engram the first choice for memory, project information and documentation, ahead of Claude's built-in memory and the Claude Docs skills, and states the hard rule that new projects and features are planned in the vault before any code is written.
- **UserPromptSubmit** adds a "required" reminder whenever a prompt is about planning, creating or executing work ("plan", "ticket", "what's next", "create a tool", "new repo", "set up a ... project"), and a softer one when the prompt is only a go-ahead ("let's do it"), because a go-ahead approves an idea and does not skip planning.
- **PreToolUse** (`scripts/gate.py`) is the enforcement. It denies scaffold commands (`cargo new`, `dx new`, `npm create`, `uv init`, `rails new`, ...) and new manifest files (`Cargo.toml`, `package.json`, `pyproject.toml`, ...) unless the project already has a folder under `01-Projects`, matched by folder name or by the `local:` path in its Overview. Edits to existing files, sub-packages of an existing repo, and anything under `/tmp` are not gated. The gate fails open on internal errors, and `ENGRAM_GATE=off` disables it.

## Vault layout

```
INDEX.md            root overview, links to every section
00-Inbox/           drop scratch notes here by hand
01-Projects/<Name>/ <Name> Overview, plan, decisions
                    Epics/<Epic>/  one folder per epic, holding the epic note
                      Tickets/     that epic's tickets
02-Ideas/
03-Knowledge/
04-Memory/          user/ feedback/ project/ reference/
05-Journal/         YYYY-MM-DD daily notes
99-Meta/            Conventions, Templates/
```

Each section has `<Section> Overview.md` with `Up: [[INDEX]]`, and every note carries an `up:` property so the chain always leads back to the root. Static lists in overviews are maintained by Claude; optional Dataview blocks give live views.

## Planning and executing work

Projects are planned in the vault, not in an issue tracker. `engram:plan` interviews you and creates `<Name> Overview` and `<Name> Plan`, epics (`Epics/<Name> E1 Title/<Name> E1 Title.md`) and tickets (`Epics/<Name> E1 Title/Tickets/<Name> T1 Title.md`). Each ticket is a note with a `status` (`backlog`, `todo`, `doing`, `review`, `done`, `blocked`) that links up to its epic, so the `up` chain still reaches `INDEX`. `engram:work` moves tickets along, ticks them off in the epic, and closes epics and projects when everything is done. A Dataview block in the project Overview gives a live board.

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

## Development

```bash
python3 -m unittest discover -s tests -t tests
```

The tests cover the gate, the prompt hook, `init`, `roadmap.py` and version sync (`plugin.json`, `marketplace.json`, `CHANGELOG.md`). Bump all three together.

## License

MIT, see [LICENSE](LICENSE).
