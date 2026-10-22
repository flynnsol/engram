---
type: overview
tags: [overview, projects]
up: "[[INDEX]]"
created: {{init_date}}
updated: {{init_date}}
---

# Projects Overview

Up: [[INDEX]]

Each project is a folder `01-Projects/<Project Name>/` with its own hub note, `<Project Name> Overview`, that links back to this page. Start new ones from [[Project Overview Template]].

## Active

<!-- engram:projects-active -->
- _none yet_

## On hold / done

<!-- engram:projects-archived -->
- _none yet_

## All projects (live query)

```dataview
TABLE status, updated FROM "01-Projects" WHERE type = "project-overview" SORT updated DESC
```
