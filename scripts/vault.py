#!/usr/bin/env python3
"""Engram vault tools: `search` and `lint`.

  vault.py <vault> search <term...> [--limit N]
  vault.py <vault> lint [--summary]

search ranks notes by title, tags, description and body matches and prints one line per hit.
lint checks the link chain and ticket/epic consistency; exit status 1 when it finds errors.
Read-only: it never writes to the vault.
"""

import os
import re
import sys

STATUSES = {"backlog", "todo", "doing", "review", "done", "blocked"}
SKIP_DIRS = {".obsidian", ".git", ".trash"}
LINK = re.compile(r"\[\[([^\]|#\n]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def parse(text):
    """Return (frontmatter dict, body). Values are strings; [a, b] lists become lists."""
    fm, body = {}, text
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            body = text[end + 4:]
            for line in text[4:end].split("\n"):
                m = re.match(r"([A-Za-z_][\w-]*):\s*(.*)$", line)
                if not m:
                    continue
                k, v = m.group(1), m.group(2).strip()
                if v.startswith("[") and v.endswith("]"):
                    v = [x.strip().strip("\"'") for x in re.split(r",(?![^\[]*\]\])", v[1:-1]) if x.strip()]
                else:
                    v = v.strip("\"'")
                fm[k] = v
    return fm, body


def links(text):
    return [m.group(1).strip() for m in LINK.finditer(CODE.sub("", text))]


def load(vault):
    """Every markdown note in the vault: {rel path: dict}. Templates are skipped."""
    notes = {}
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, vault)
            if rel.startswith(os.path.join("99-Meta", "Templates")):
                continue
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            fm, body = parse(text)
            notes[rel] = {"name": f[:-3], "fm": fm, "body": body, "text": text}
    return notes


def target(link):
    """Link text to a note name; strips a leading path and an extension like .canvas."""
    return os.path.basename(link)


def summary(note):
    d = note["fm"].get("description")
    if d:
        return d
    for line in note["body"].split("\n"):
        s = line.strip()
        if s and not s.startswith(("#", "Up:", "<!--", "```")):
            return s[:100]
    return ""


def search(vault, terms, limit=20):
    words = [t.lower() for t in terms if t]
    hits = []
    for rel, n in load(vault).items():
        title = n["name"].lower()
        meta = " ".join(str(v) for k, v in n["fm"].items() if k in ("tags", "description", "type", "memory_type", "status")).lower()
        body = n["body"].lower()
        score = 0
        for w in words:
            s = (3 if w in title else 0) + (2 if w in meta else 0) + (1 if w in body else 0)
            if not s:
                score = 0
                break
            score += s
        if score:
            hits.append((-score, rel, n))
    for _, rel, n in sorted(hits, key=lambda h: (h[0], h[1]))[:limit]:
        kind = n["fm"].get("type", "")
        print("%s [%s] — %s" % (rel[:-3], kind, summary(n)))
    return len(hits)


def lint(vault):
    """Return a list of (level, rel path, message)."""
    notes = load(vault)
    names = {}
    for rel, n in notes.items():
        names.setdefault(n["name"], []).append(rel)
    extra = set()  # non-markdown targets such as canvases and images
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        extra.update(files)
        extra.update(os.path.splitext(f)[0] for f in files)
    out = []
    inbound = {}
    for rel, n in notes.items():
        for l in links(n["text"]):
            t = target(l)
            inbound.setdefault(t, set()).add(rel)
            if t not in names and t not in extra:
                out.append(("error", rel, "broken link [[%s]]" % l))
    for name, rels in names.items():
        if len(rels) > 1:
            out.append(("error", rels[0], "duplicate note name '%s' also in %s" % (name, ", ".join(rels[1:]))))

    for rel, n in notes.items():
        name, fm = n["name"], n["fm"]
        if name == "INDEX" or rel.startswith("00-Inbox"):
            continue
        up = target(links(fm.get("up", ""))[0]) if links(fm.get("up", "")) else None
        if not up:
            out.append(("error", rel, "missing up: property"))
        elif up not in names:
            out.append(("error", rel, "up points at missing note [[%s]]" % up))
        else:
            seen, cur = set(), up
            while cur != "INDEX" and cur not in seen and cur in names:
                seen.add(cur)
                nxt = links(notes[names[cur][0]]["fm"].get("up", ""))
                cur = target(nxt[0]) if nxt else None
                if cur is None:
                    break
            if cur != "INDEX":
                out.append(("error", rel, "up chain does not reach INDEX"))
            else:
                parent = notes[names[up][0]]
                if parent["name"].endswith("Overview") or fm.get("type") == "ticket":
                    if name not in {target(l) for l in links(parent["text"])}:
                        out.append(("warn", rel, "not listed in its parent [[%s]]" % up))
        if not inbound.get(name) and fm.get("type") not in ("overview",):
            out.append(("warn", rel, "orphan: nothing links to it"))
        if fm.get("type") in ("ticket", "epic"):
            st = fm.get("status", "")
            if st not in STATUSES:
                out.append(("error", rel, "bad status '%s'" % st))
            for b in fm.get("blocked_by", []) if isinstance(fm.get("blocked_by"), list) else []:
                if target(b.strip("[]")) not in names:
                    out.append(("error", rel, "blocked_by points at missing note %s" % b))
    # tickets vs their epic's checklist; epics vs their tickets
    tickets_by_epic = {}
    for rel, n in notes.items():
        if n["fm"].get("type") == "ticket":
            ep = links(n["fm"].get("epic", ""))
            if ep:
                tickets_by_epic.setdefault(target(ep[0]), []).append(n)
    for epic, ts in tickets_by_epic.items():
        if epic not in names:
            continue
        erel = names[epic][0]
        etext = notes[erel]["text"]
        for t in ts:
            m = re.search(r"- \[( |x)\] \[\[%s(?:\|[^\]]*)?\]\]" % re.escape(t["name"]), etext)
            if not m:
                continue  # missing entry is reported by the "not listed" warning
            done = t["fm"].get("status") == "done"
            if done != (m.group(1) == "x"):
                out.append(("error", erel, "checklist for [[%s]] is %s but the ticket is %s" % (
                    t["name"], "ticked" if m.group(1) == "x" else "unticked", t["fm"].get("status"))))
        if notes[erel]["fm"].get("status") == "done" and any(t["fm"].get("status") != "done" for t in ts):
            out.append(("error", erel, "epic is done but has open tickets"))
    return sorted(out, key=lambda o: (o[0] != "error", o[1], o[2]))


def main(argv):
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    vault, cmd, rest = argv[1], argv[2], argv[3:]
    if cmd == "search":
        limit = 20
        if "--limit" in rest:
            i = rest.index("--limit")
            limit = int(rest[i + 1])
            rest = rest[:i] + rest[i + 2:]
        if not rest:
            print("usage: search <term...>", file=sys.stderr)
            return 2
        return 0 if search(vault, rest, limit) else 1
    if cmd == "lint":
        res = lint(vault)
        errors = sum(1 for r in res if r[0] == "error")
        warns = len(res) - errors
        if "--summary" in rest:
            print("Lint: %d error(s), %d warning(s)" % (errors, warns))
        else:
            for level, rel, msg in res:
                print("%s %s: %s" % (level.upper(), rel, msg))
            print("%d error(s), %d warning(s)" % (errors, warns))
        return 1 if errors else 0
    print("unknown command: " + cmd, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
