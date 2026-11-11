---
name: roadmap
description: Build or refresh a project's roadmap as an Obsidian canvas (epics as columns, tickets colored by status, arrows for blockers). Use after engram:plan or engram:work change a plan or a status, or when the user asks for a roadmap, board view, timeline or "draw this as a canvas". Also covers hand-built canvases for data models and explainer diagrams.
---

# roadmap

Follow `engram:conventions`.

## Project roadmap

1. Get the vault (`${CLAUDE_PLUGIN_ROOT}/scripts/engram.sh get`) and the exact project folder name under `01-Projects/`.
2. (`engram.sh ticket`, `close-epic` and `close-project` already do this for you.) Run `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/roadmap.py" "<vault>" "<Project Name>"`. It writes `01-Projects/<Name>/<Name> Roadmap.canvas` from the epic and ticket notes (found anywhere under the project folder, normally `Epics/<epic>/` and `Epics/<epic>/Tickets/`): one group per epic in `E<n>` order, tickets as file cards in `T<n>` order, colored by `status` (cyan todo, yellow doing, purple review, green done, red blocked, grey archived, none backlog), arrows from each `blocked_by` entry to the blocked note.
3. First time only: list `[[<Name> Roadmap]]` in the project Overview under *Notes in this project* (`<Name> Roadmap.canvas` is the file; link it as `[[<Name> Roadmap.canvas]]`).
4. Report the counts it printed. Tell the user to nudge cards if the layout needs it.

The canvas is regenerated from scratch each time, so hand edits to it are lost. For manual diagrams make a separate canvas.

`blocked_by` must be quoted wikilinks (`["[[Name]]"]`); anything else is ignored.

## Hand-built canvases (data models, explainers)

For a data structure or a "how X connects to Y" map, write a `.canvas` JSON file next to the related note, e.g. `03-Knowledge/<Topic>.canvas` or in the project folder. Link it from the parent overview like any note.

- Format: `{"nodes": [...], "edges": [...]}`. Node: `id` (unique), `type` (`text`, `file`, `link`, `group`), `x`, `y`, `width`, `height`, optional `color` (`"1"` red … `"6"` purple). Text nodes take `text` (Markdown); file nodes `file` (vault path); groups `label`.
- Edge: `id`, `fromNode`, `fromSide`, `toNode`, `toSide` (`top|right|bottom|left`), optional `label`, `toEnd`.
- Lay out on a grid (about 320 wide, 80+ apart); one entity or step per node; label edges with the relationship. Embed real notes as `file` nodes instead of copying their text.
- For code-accurate schemas or sequences, a Mermaid block in the note is often cleaner.
- Claude cannot see the rendered canvas; keep layouts simple and tell the user to adjust.
