# Changelog

All notable changes to the Engram plugin. Versions match `.claude-plugin/plugin.json`.
Newest first; `tests/test_release.py` checks that the top entry matches the plugin version.

## 0.5.0 - 2026-11-07

- Added: SessionStart digest ("Where things stand"): tickets in flight, the next unblocked ticket when the session starts inside a planned project, and the last journal entry.
- Changed: the prompt-submit reminder is one short line inside a planned project (matched by the Overview's `local:` path) and silent for a bare go-ahead.
- Added: opt-in Stop hook. With `ENGRAM_STOP_LINT=on`, if vault notes changed in the last hour and lint finds errors, Claude is asked once to fix them before stopping.

## 0.4.0 - 2026-11-07

- Added: `engram.sh ticket <ticket> <status>`, `close-epic` and `close-project`. One call sets the status, bumps `updated`, ticks the epic checklist, starts the epic, enforces `blocked_by`, moves finished projects to the done lists and rebuilds the roadmap canvas.
- Changed: the `work`, `plan` and `roadmap` skills use these commands instead of hand edits.

## 0.3.0 - 2026-11-07

- Added: `engram.sh search <terms>`, ranked by title, tags, description and body, one line per hit.
- Added: `engram.sh lint` (broken links, missing or dead `up` chains, notes missing from their parent overview, orphans, bad ticket status, epic checklists out of sync with tickets). `/engram status` prints the lint counts.
- Added: a `description:` property in the templates and conventions so search can show a note without opening it.

## 0.2.4 - 2026-11-07

- Fixed: `/engram init` no longer fails on an existing vault (`cp -n` exits 1 when it skips files on newer coreutils); it now copies only what is missing.
- Fixed: the PreToolUse gate now allows scaffolding into `/tmp` from any working directory, as the README says.
- Added: unit and smoke tests for the gate, prompt-submit hook, `init`, `status`, `session-start` and `roadmap.py` (`python3 -m unittest discover -s tests -t tests`).
- Added: this changelog and a version-sync check across `plugin.json`, `marketplace.json` and the changelog.

## 0.2.3 - 2026-11-07

- Changed: roomier roadmap canvas layout (wider columns, taller cards, label band) so embedded notes fit.

## 0.2.2 - 2026-11-01

- Changed: each epic's tickets live in a `Tickets/` folder inside the epic.

## 0.2.1 - 2026-11-01

- Added: epics and tickets in sub-folders; the planning gate (PreToolUse hook).

## 0.2.0 - 2026-11-01

- Added: vault-native planning skills `plan`, `work`, `roadmap` and `principles`.

## 0.1.0 - 2026-10-21

- Initial release: vault scaffold, `remember`, `recall`, `triage`, `conventions`, session hooks.
