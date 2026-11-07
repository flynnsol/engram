#!/usr/bin/env python3
"""Engram work commands: move tickets and close epics and projects in one call.

  work.py <vault> ticket "<ticket>" <status> [--force]
  work.py <vault> close-epic "<epic>"
  work.py <vault> close-project "<Project>"

<ticket> / <epic> is a full note name or a unique prefix such as "Engram T12" / "Engram E3".
`ticket` sets the status, bumps `updated`, ticks or unticks the epic's checklist line, moves a
not-yet-started epic to `doing`, and refuses to start a ticket whose blockers are not done
(--force overrides). Every command rebuilds the project's roadmap canvas afterwards.
"""

import datetime
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault as V  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today().isoformat()


class Fail(Exception):
    pass


def find(notes, query, kind):
    hits = [(r, n) for r, n in notes.items() if n["fm"].get("type") == kind
            and (n["name"] == query or n["name"].startswith(query + " "))]
    exact = [h for h in hits if h[1]["name"] == query]
    hits = exact or hits
    if not hits:
        raise Fail("no %s matches '%s'" % (kind, query))
    if len(hits) > 1:
        raise Fail("'%s' is ambiguous: %s" % (query, ", ".join(h[1]["name"] for h in hits)))
    return hits[0]


def set_key(text, key, value):
    """Set a frontmatter key, adding it before the closing --- if absent."""
    end = text.find("\n---", 4)
    head, rest = text[:end], text[end:]
    pat = re.compile(r"^%s:.*$" % re.escape(key), re.M)
    if pat.search(head):
        head = pat.sub("%s: %s" % (key, value), head, count=1)
    else:
        head += "\n%s: %s" % (key, value)
    return head + rest


def edit(vault, rel, **keys):
    path = os.path.join(vault, rel)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    for k, v in keys.items():
        text = set_key(text, k, v)
    return write(path, text)


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def project_of(note):
    ls = V.links(note["fm"].get("project", ""))
    if not ls:
        return None
    return re.sub(r" Overview$", "", V.target(ls[0]))


def roadmap(vault, project):
    if project and os.path.isdir(os.path.join(vault, "01-Projects", project)):
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "roadmap.py"), vault, project],
                           capture_output=True, text=True)
        print("Roadmap: " + (r.stdout.strip().split("\n")[-1] if r.returncode == 0 else "failed: " + r.stderr.strip()))


def tickets_of(notes, epic_name):
    return [n for n in notes.values() if n["fm"].get("type") == "ticket"
            and any(V.target(l) == epic_name for l in V.links(n["fm"].get("epic", "")))]


def cmd_ticket(vault, query, status, force):
    if status not in V.STATUSES:
        raise Fail("status must be one of: " + ", ".join(sorted(V.STATUSES)))
    notes = V.load(vault)
    rel, t = find(notes, query, "ticket")
    names = {n["name"]: n for n in notes.values()}
    if status in ("doing", "review", "done") and not force:
        open_ = [b for b in (V.target(x.strip("[]")) for x in (t["fm"].get("blocked_by") or []) if isinstance(t["fm"].get("blocked_by"), list))
                 if b in names and names[b]["fm"].get("status") != "done"]
        if open_:
            raise Fail("blocked by unfinished: " + ", ".join(open_) + " (use --force to override)")
    edit(vault, rel, status=status, updated=TODAY)
    print("%s: %s -> %s" % (t["name"], t["fm"].get("status", "?"), status))
    eps = V.links(t["fm"].get("epic", ""))
    if eps and V.target(eps[0]) in names:
        en = V.target(eps[0])
        erel = next(r for r, n in notes.items() if n["name"] == en)
        path = os.path.join(vault, erel)
        with open(path, encoding="utf-8") as fh:
            etext = fh.read()
        box = "x" if status == "done" else " "
        etext = re.sub(r"(- \[)[ x](\] \[\[%s(?:\|[^\]]*)?\]\])" % re.escape(t["name"]), r"\g<1>%s\2" % box, etext)
        estatus = notes[erel]["fm"].get("status")
        if status in ("doing", "review") and estatus in ("backlog", "todo"):
            etext = set_key(etext, "status", "doing")
        etext = set_key(etext, "updated", TODAY)
        write(path, etext)
        sibs = tickets_of(notes, en)
        done = sum(1 for s in sibs if (status if s["name"] == t["name"] else s["fm"].get("status")) == "done")
        print("%s: %d of %d tickets done" % (en, done, len(sibs)))
        if done == len(sibs):
            print("All tickets are done: ask whether to close the epic (close-epic).")
    roadmap(vault, project_of(t))


def replace_line(path, needle, fn):
    """Apply fn to the first line containing needle; return True if one was found."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    for i, l in enumerate(lines):
        if needle in l:
            lines[i] = fn(l)
            write(path, "\n".join(lines))
            return True
    return False


def cmd_close_epic(vault, query):
    notes = V.load(vault)
    rel, e = find(notes, query, "epic")
    open_ = [t["name"] for t in tickets_of(notes, e["name"]) if t["fm"].get("status") != "done"]
    if open_:
        raise Fail("open tickets: " + ", ".join(open_))
    edit(vault, rel, status="done", updated=TODAY)
    unmet = len(re.findall(r"^- \[ \]", e["body"].split("## Done when", 1)[-1].split("## ", 1)[0], re.M)) if "## Done when" in e["body"] else 0
    print("%s closed" % e["name"])
    if unmet:
        print("Note: %d 'Done when' item(s) are unticked; check them and tick the ones met." % unmet)
    proj = project_of(e)
    if proj:
        ov = os.path.join(vault, "01-Projects", proj, proj + " Overview.md")
        if os.path.exists(ov):
            replace_line(ov, "[[%s]]" % e["name"], lambda l: l if "done" in l.lower() else l + " (done %s)" % TODAY)
            edit(vault, os.path.relpath(ov, vault), updated=TODAY)
    left = [n["name"] for n in notes.values() if n["fm"].get("type") == "epic" and project_of(n) == proj
            and n["name"] != e["name"] and n["fm"].get("status") != "done"]
    print("Epics left in %s: %s" % (proj, ", ".join(left) if left else "none (ask whether to close the project)"))
    roadmap(vault, proj)


def cmd_close_project(vault, name):
    notes = V.load(vault)
    ov_rel = os.path.join("01-Projects", name, name + " Overview.md")
    if not os.path.exists(os.path.join(vault, ov_rel)):
        raise Fail("no project '%s' under 01-Projects" % name)
    open_ = [n["name"] for n in notes.values() if n["fm"].get("type") == "epic" and project_of(n) == name
             and n["fm"].get("status") != "done"]
    if open_:
        raise Fail("open epics: " + ", ".join(open_))
    edit(vault, ov_rel, status="done", updated=TODAY)
    link = "[[%s Overview" % name

    def move(path, active_marker, archive_marker):
        p = os.path.join(vault, path)
        if not os.path.exists(p):
            return
        with open(p, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        idx = [i for i, l in enumerate(lines) if l.startswith("- ") and link in l]
        if not idx:
            return
        entry = lines.pop(idx[0])
        entry = re.sub(r"^(- \[\[[^\]]*\]\]) — ", r"\1 — done %s: " % TODAY, entry, count=1)
        if archive_marker:
            at = next((i for i, l in enumerate(lines) if archive_marker in l), None)
            if at is not None:
                lines.insert(at + 1, entry)
        write(p, "\n".join(lines))

    move("01-Projects/Projects Overview.md", "engram:projects-active", "engram:projects-archived")
    move("INDEX.md", "engram:active-projects", None)
    print("%s closed and moved to the done list" % name)
    roadmap(vault, name)


def main(argv):
    if len(argv) < 4:
        print(__doc__, file=sys.stderr)
        return 2
    vault, cmd, args = argv[1], argv[2], argv[3:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    try:
        if cmd == "ticket" and len(args) == 2:
            cmd_ticket(vault, args[0], args[1], force)
        elif cmd == "close-epic" and len(args) == 1:
            cmd_close_epic(vault, args[0])
        elif cmd == "close-project" and len(args) == 1:
            cmd_close_project(vault, args[0])
        else:
            print(__doc__, file=sys.stderr)
            return 2
    except Fail as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
