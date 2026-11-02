---
name: principles
description: Core Engram planning rules - small tickets (one commit or PR, under 200 lines and 5 files), small epics (2 weeks or less), short notes, one epic per milestone-sized slice. Use during any project planning, ticket splitting, commit or PR writing, or documentation work, alongside engram:plan and engram:work.
---

# principles

## 1. Small changes

- A ticket is **one commit or PR, under 200 changed lines and 5 files**.
- If a ticket would exceed that, split it before starting. Do not plan a big ticket and hope it fits.
- Keep refactors, renames and formatting separate from behavior changes.

## 2. Small epics

- An epic is **2 weeks or less for one engineer** (about 10 working days), including review.
- Bigger ideas become several epics, each a thin, shippable slice.

## 3. Short notes

- Lead with the point. The first lines say what this is and what to do.
- Cut background and hedging. Prefer lists and tables to paragraphs.
- Link to a note instead of repeating it; long explanations go in a `Details` section or their own note.

## Applying

- Before creating tickets, check each against the size limit and propose a split for any that exceed it.
- Before saving a plan or status note, shorten it once more.
