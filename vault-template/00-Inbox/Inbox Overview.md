---
type: overview
tags: [overview, inbox]
up: "[[INDEX]]"
created: {{init_date}}
updated: {{init_date}}
---

# Inbox Overview

Up: [[INDEX]]

Drop anything here by hand: scratch pads, half-thoughts, links. No frontmatter or structure required. Claude triages it (`/engram:triage-inbox`) by moving each note to its proper section and linking it from that section's overview.

Create a new note with the **Scratch** template: [[Scratch Template]].

## Currently in the inbox

```dataview
LIST FROM "00-Inbox" WHERE file.name != "Inbox Overview" SORT file.ctime DESC
```
