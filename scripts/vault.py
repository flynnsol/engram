#!/usr/bin/env python3
"""Engram vault tools: `search` and `lint`.

  vault.py <vault> search <term...> [--limit N]
  vault.py <vault> lint [--summary]
  vault.py <vault> digest [cwd]        tickets in flight, next ticket here, last journal
  vault.py <vault> old-format          count of open tickets missing touches or role
  vault.py <vault> project-of <cwd>    name of the planned project that owns cwd
  vault.py <vault> ready <Project> [--epic "<epic>"] [--waves]
                                       tickets that can start now without colliding

search ranks notes by title, tags, description and body matches and prints one line per hit.
lint checks the link chain and ticket/epic consistency; exit status 1 when it finds errors.
Read-only: it never writes to the vault.
"""

import fnmatch
import os
import re
import sys

STATUSES = {"backlog", "todo", "doing", "review", "done", "blocked"}
ROLES = {"engineer", "reviewer", "tester"}
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
    # orchestration fields: only open tickets, and only the ones about to be worked for `touches`
    by_project = {}
    for rel, n in notes.items():
        fm = n["fm"]
        if fm.get("type") != "ticket" or fm.get("status") == "done":
            continue
        role = fm.get("role")
        if role and role not in ROLES:
            out.append(("warn", rel, "unknown role '%s' (use %s)" % (role, ", ".join(sorted(ROLES)))))
        if fm.get("status") in ("todo", "doing") and not touches_of(n):
            out.append(("warn", rel, "no touches: it cannot run in parallel with other tickets"))
        by_project.setdefault(fm.get("project", ""), []).append(n)
    for ts in by_project.values():
        for w, group in plan_waves(ts).items():
            for i, a in enumerate(group):
                for b in group[i + 1:]:
                    if touches_of(a) and touches_of(b) and collision(a, b):
                        rel = next(r for r, n in notes.items() if n is a)
                        out.append(("warn", rel, "wave %d: touches overlap with [[%s]] (%s); order them with blocked_by" % (w, b["name"], collision(a, b))))
    return sorted(out, key=lambda o: (o[0] != "error", o[1], o[2]))


def old_format_tickets(notes):
    """Open tickets that lack the `touches` or `role` property (planned before orchestration fields)."""
    return sorted(rel for rel, n in notes.items() if n["fm"].get("type") == "ticket"
                  and n["fm"].get("status") != "done" and ("touches" not in n["fm"] or "role" not in n["fm"]))


def paths_overlap(a, b):
    """True if two `touches` entries (files, directories or globs) can name the same file."""
    a, b = a.strip().lstrip("./").rstrip("/"), b.strip().lstrip("./").rstrip("/")
    if not a or not b:
        return True
    if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
        return True
    return fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a)


def touches_of(ticket):
    t = ticket["fm"].get("touches")
    return [x for x in t if x] if isinstance(t, list) else []


def collision(a, b):
    """First pair of overlapping touches between two tickets, or None. No touches collides with all."""
    ta, tb = touches_of(a), touches_of(b)
    if not ta or not tb:
        return "(no touches)"
    for x in ta:
        for y in tb:
            if paths_overlap(x, y):
                return x if x == y else "%s ~ %s" % (x, y)
    return None


def blockers(ticket):
    bb = ticket["fm"].get("blocked_by")
    return [target(b.strip("[]")) for b in bb] if isinstance(bb, list) else []


def plan_waves(tickets):
    """Group open tickets into waves: wave 1 has no open blockers, wave n follows wave n-1."""
    open_ = {t["name"]: t for t in tickets if t["fm"].get("status") != "done"}
    wave = {}

    def depth(name, seen=()):
        if name in wave:
            return wave[name]
        if name in seen:
            return 1
        deps = [b for b in blockers(open_[name]) if b in open_]
        wave[name] = 1 + max((depth(b, seen + (name,)) for b in deps), default=0)
        return wave[name]

    for name in open_:
        depth(name)
    out = {}
    for name, w in wave.items():
        out.setdefault(w, []).append(open_[name])
    return {w: sorted(ts, key=ticket_order) for w, ts in sorted(out.items())}


def ticket_order(t):
    m = re.search(r" T(\d+) ", t["name"])
    return (int(m.group(1)) if m else 9999, t["name"])


def ready(vault, project, epic=None, waves=False):
    """Print the tickets that can start now (unblocked, not colliding with each other or with work in flight)."""
    notes = load(vault)
    scope = [t for t in notes.values() if t["fm"].get("type") == "ticket"
             and "[[%s Overview" % project in t["fm"].get("project", "")]
    if epic:
        scope = [t for t in scope if any(target(l) == epic or target(l).startswith(epic + " ") for l in links(t["fm"].get("epic", "")))]
    if not scope:
        print("no tickets found for %s%s" % (project, " in " + epic if epic else ""), file=sys.stderr)
        return 1
    done = {t["name"] for t in scope if t["fm"].get("status") == "done"}
    all_done = {n["name"] for n in notes.values() if n["fm"].get("status") == "done"}
    flight = [t for t in scope if t["fm"].get("status") in ("doing", "review")]
    cands = sorted((t for t in scope if t["fm"].get("status") in ("todo", "backlog")
                    and all(b in all_done for b in blockers(t))), key=lambda t: (t["fm"].get("status") != "todo", ticket_order(t)))
    batch, held = [], []
    for t in cands:
        clash = next(((o, collision(t, o)) for o in flight + batch if collision(t, o)), None)
        if clash:
            held.append((t, clash))
        else:
            batch.append(t)
    if waves:
        for w, ts in plan_waves(scope).items():
            print("wave %d: %s" % (w, "; ".join("%s [%s]" % (t["name"], t["fm"].get("status")) for t in ts)))
        return 0
    print("In flight: %s" % (", ".join(t["name"] for t in flight) or "none"))
    print("Ready now (%d, safe to run in parallel):" % len(batch))
    for t in batch:
        print("- %s | role=%s | touches=%s" % (t["name"], t["fm"].get("role") or "engineer", ", ".join(touches_of(t)) or "none"))
    for t, (o, why) in held:
        print("Held: %s collides with %s on %s" % (t["name"], o["name"], why))
    return 0 if batch else 1


def project_for_cwd(vault, cwd):
    """Name of the planned project whose `local:` checkout contains cwd, else ''."""
    cwd = os.path.realpath(cwd)
    best, found = "", ""
    root = os.path.join(vault, "01-Projects")
    for name in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        ov = os.path.join(root, name, name + " Overview.md")
        if not os.path.isfile(ov):
            continue
        with open(ov, encoding="utf-8", errors="replace") as fh:
            for m in re.finditer(r"local:\s*`([^`]+)`", fh.read()):
                path = os.path.realpath(os.path.expanduser(m.group(1)))
                if (cwd == path or cwd.startswith(path + os.sep)) and len(path) > len(best):
                    best, found = path, name
    return found


def digest(vault, cwd=""):
    """A few lines for session start: tickets in flight, this project's next ticket, last journal."""
    notes = load(vault)
    tickets = [n for n in notes.values() if n["fm"].get("type") == "ticket"]
    lines = []
    flight = [t for t in tickets if t["fm"].get("status") in ("doing", "blocked", "review")]
    for t in sorted(flight, key=lambda t: t["name"])[:8]:
        lines.append("- %s: [[%s]]" % (t["fm"]["status"], t["name"]))
    here = project_for_cwd(vault, cwd) if cwd else ""
    if here:
        done = {t["name"] for t in tickets if t["fm"].get("status") == "done"}

        def blockers_done(t):
            bb = t["fm"].get("blocked_by")
            return all(target(b.strip("[]")) in done for b in bb) if isinstance(bb, list) else True

        def num(t):
            m = re.search(r" T(\d+) ", t["name"])
            return int(m.group(1)) if m else 9999

        todo = [t for t in tickets if "[[%s Overview" % here in t["fm"].get("project", "")
                and t["fm"].get("status") in ("todo", "backlog") and blockers_done(t)]
        todo.sort(key=lambda t: (t["fm"].get("status") != "todo", num(t), t["name"]))
        nxt = "; next unblocked: [[%s]]" % todo[0]["name"] if todo else ""
        lines.insert(0, "- working in planned project %s%s" % (here, nxt))
    journal = sorted(r for r in notes if r.startswith("05-Journal") and "Overview" not in r)
    if journal:
        lines.append("- last journal entry: [[%s]]" % notes[journal[-1]]["name"])
    return lines


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
    if cmd == "ready":
        epic = None
        if "--epic" in rest:
            i = rest.index("--epic")
            epic = rest[i + 1]
            rest = rest[:i] + rest[i + 2:]
        w = "--waves" in rest
        rest = [r for r in rest if r != "--waves"]
        if len(rest) != 1:
            print('usage: ready <Project> [--epic "<epic>"] [--waves]', file=sys.stderr)
            return 2
        return ready(vault, rest[0], epic, w)
    if cmd == "old-format":
        print(len(old_format_tickets(load(vault))))
        return 0
    if cmd == "project-of":
        print(project_for_cwd(vault, rest[0] if rest else os.getcwd()))
        return 0
    if cmd == "digest":
        for l in digest(vault, rest[0] if rest else ""):
            print(l)
        return 0
    print("unknown command: " + cmd, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
