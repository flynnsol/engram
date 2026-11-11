<img alt="Engram" src="res/engram-banner.png" width="100%">

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
| `/engram status` | Show the path, note count, inbox size and lint counts |
| `/engram search <terms>` | Ranked search over titles, tags, descriptions and bodies |
| `/engram lint` | Check links, the `up` chain and ticket/epic consistency |
| `engram:remember` | Save a memory, idea, plan, decision, knowledge note or journal entry |
| `engram:recall` | Look things up by navigating overviews and links |
| `engram:triage` | File your hand-made scratch notes into the right sections |
| `engram:plan` | Plan a project, epic or ticket through a short interview and create the notes |
| `engram:work` | Show the board, pick up the next ticket (or run several in parallel), and close tickets, epics and projects (`engram.sh ticket`, `ready`, `close-epic`, `close-project` do the bookkeeping) |
| `engram:roadmap` | Draw a project's epics, tickets and dependencies as an Obsidian canvas |
| `engram:principles` | Small tickets (under 200 lines, 5 files), small epics (2 weeks or less), short notes |
| `engram:conventions` | The rules for writing and linking notes |

Four hooks keep Claude on the rails (the fourth, Stop, is opt-in):

- **SessionStart** tells Claude where the vault is and to read `INDEX.md` when it needs context. It makes Engram the first choice for memory, project information and documentation, ahead of Claude's built-in memory and the Claude Docs skills, and states the hard rule that new projects and features are planned in the vault before any code is written. It also adds a short "where things stand" digest: tickets in flight, the next unblocked ticket when the session starts in a planned project's checkout, and the last journal entry.
- **UserPromptSubmit** adds a "required" reminder whenever a prompt is about planning, creating or executing work ("plan", "ticket", "what's next", "create a tool", "new repo", "set up a ... project"), and a softer one when the prompt is only a go-ahead ("let's do it"), because a go-ahead approves an idea and does not skip planning. Inside a planned project's checkout (matched by the Overview's `local:` path) the reminder shrinks to one line, and a bare go-ahead is silent.
- **Stop** (opt-in, `ENGRAM_STOP_LINT=on`) runs `engram.sh lint` when vault notes changed in the last hour and asks Claude, once, to fix any errors before it stops.
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

Projects are planned in the vault, not in an issue tracker. `engram:plan` interviews you and creates `<Name> Overview` and `<Name> Plan`, epics (`Epics/<Name> E1 Title/<Name> E1 Title.md`) and tickets (`Epics/<Name> E1 Title/Tickets/<Name> T1 Title.md`). Each ticket is a note with a `status` (`backlog`, `todo`, `doing`, `review`, `done`, `blocked`, `archived`) that links up to its epic, so the `up` chain still reaches `INDEX`. `engram:work` moves tickets along, ticks them off in the epic, and closes epics and projects when everything is done. A Dataview block in the project Overview gives a live board.

The bookkeeping is scripted, so it is one call instead of several hand edits, and each call rebuilds the roadmap canvas:

```bash
engram.sh ticket "Engram T12" doing      # also: review, done, blocked, archived; refuses if blocked_by are open (--force)
engram.sh close-epic "Engram E3"         # refuses while tickets are open
engram.sh close-project "Engram"         # moves the project to the done lists
engram.sh search gate hook               # ranked, one line per hit with its description
engram.sh lint                           # broken links, up chains, orphans, checklist drift
engram.sh ready "Engram" --waves          # tickets that can run in parallel, and the order
engram.sh migrate [--apply]              # bring old tickets and templates up to date
```

### Running tickets in parallel

Tickets carry `touches` (the paths they change) and a `role` (`engineer`, `reviewer`, `tester`), and an *Acceptance* section of checks a command can confirm. `engram.sh ready "<Project>"` lists the tickets that can start now without colliding; `--waves` shows the order for an epic. `engram:work` then runs them as worktree subagents, picking an installed agent whose name matches the `role` (for example from a separate agents plugin) and falling back to `general-purpose`. Only the orchestrating session changes ticket status; a reviewer agent checks each diff before it is marked done. Lint warns about missing or overlapping `touches`. Vaults planned before 0.6.0: run `engram.sh migrate` (dry run) and `engram.sh migrate --apply`.

Every non-overview note carries a one-line `description:` property so search (and Claude) can judge a note without opening it.

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
