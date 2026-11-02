#!/usr/bin/env python3
"""Generate <Project> Roadmap.canvas from a project's epic and ticket notes.

usage: roadmap.py <vault> <Project Name>

Reads every note under 01-Projects/<Project Name>/ (Epics/<epic>/ and Epics/<epic>/Tickets/) with `type: epic` or `type: ticket`.
One group per epic (ordered by E<n>), tickets stacked inside (ordered by T<n>),
colored by status, with arrows for `blocked_by` (from blocker to blocked).
Rewrites the canvas each run; hand edits to it are lost.
"""
import hashlib, json, os, re, sys

COLORS = {"todo": "5", "doing": "3", "review": "6", "done": "4", "blocked": "1"}
COL_W, GAP, PAD = 320, 90, 30
HEAD_H, TICKET_H, ROW_GAP = 90, 80, 20
TOP = 170  # room for the title/legend row


def front(path):
    """Minimal frontmatter reader: scalars, plus wikilink targets for blocked_by."""
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    data, lines, i = {}, m.group(1).split("\n"), 0
    while i < len(lines):
        k = re.match(r"([A-Za-z_]+):\s*(.*)$", lines[i])
        i += 1
        if not k:
            continue
        key, val = k.groups()
        block = val
        while i < len(lines) and re.match(r"\s+-|\s+\S", lines[i]) and not re.match(r"[A-Za-z_]+:", lines[i]):
            block += " " + lines[i]
            i += 1
        data[key] = block.strip()
    return data


def links(val):
    return [l.split("|")[0].split("#")[0].strip() for l in re.findall(r"\[\[([^\]]+)\]\]", val or "")]


def nid(s):
    return hashlib.sha1(s.encode()).hexdigest()[:16]


def num(name, letter):
    m = re.search(r"\b%s(\d+)\b" % letter, name)
    return int(m.group(1)) if m else 10**6


def main(vault, project):
    pdir = os.path.join(vault, "01-Projects", project)
    if not os.path.isdir(pdir):
        sys.exit("no such project folder: %s" % pdir)
    epics, tickets = {}, {}
    paths = {}
    for dirpath, _, files in os.walk(pdir):
        for f in sorted(files):
            if f.endswith(".md"):
                paths[f[:-3]] = os.path.join(dirpath, f)
    for name in sorted(paths):
        fm = front(paths[name])
        if fm.get("type") == "epic":
            epics[name] = fm
        elif fm.get("type") == "ticket":
            tickets[name] = fm
    if not epics and not tickets:
        sys.exit("no epics or tickets in %s" % pdir)

    rel = lambda n: os.path.relpath(paths[n], vault).replace(os.sep, "/")
    nodes, edges, where = [], [], {}
    order = sorted(epics, key=lambda n: (num(n, "E"), n))
    by_epic = {e: [] for e in order}
    orphans = []
    for t, fm in tickets.items():
        parent = (links(fm.get("epic")) or [None])[0]
        (by_epic[parent] if parent in by_epic else orphans).append(t)
    if orphans:  # tickets with no known epic get a column of their own
        order.append(None)
        by_epic[None] = orphans

    x = 0
    for e in order:
        ts = sorted(by_epic[e], key=lambda n: (num(n, "T"), n))
        h = PAD * 2 + (HEAD_H + ROW_GAP if e else 0) + len(ts) * (TICKET_H + ROW_GAP)
        gx, gy, gw = x, TOP, COL_W + PAD * 2
        label = (re.sub(r"^.*? E\d+ ", "", e) if e else "No epic")
        nodes.append({"id": nid("g" + str(e)), "type": "group", "label": label,
                      "x": gx, "y": gy, "width": gw, "height": h})
        where[e or "_"] = (gx, gy, gw, h)
        y = gy + PAD
        if e:
            node = {"id": nid(rel(e)), "type": "file", "file": rel(e),
                    "x": gx + PAD, "y": y, "width": COL_W, "height": HEAD_H}
            if epics[e].get("status") in COLORS:
                node["color"] = COLORS[epics[e]["status"]]
            nodes.append(node)
            y += HEAD_H + ROW_GAP
        for t in ts:
            node = {"id": nid(rel(t)), "type": "file", "file": rel(t),
                    "x": gx + PAD, "y": y, "width": COL_W, "height": TICKET_H}
            if tickets[t].get("status") in COLORS:
                node["color"] = COLORS[tickets[t]["status"]]
            nodes.append(node)
            where[t] = (gx + PAD, y, COL_W, TICKET_H)
            y += TICKET_H + ROW_GAP
        x += gw + GAP

    ids = {n: nid(rel(n)) for n in list(tickets) + list(epics)}
    for name, fm in list(tickets.items()) + list(epics.items()):
        for b in links(fm.get("blocked_by")):
            if b not in ids:
                continue
            sx, tx = where[b][0], where[name][0]
            if name in epics:  # epic-level dependency: group to group
                s_id, t_id = nid("g" + b), nid("g" + name)
            else:
                s_id, t_id = ids[b], ids[name]
            if sx == tx:
                fs, ts_ = "bottom", "top"
            elif sx < tx:
                fs, ts_ = "right", "left"
            else:
                fs, ts_ = "left", "right"
            edges.append({"id": nid("e%s>%s" % (s_id, t_id)), "fromNode": s_id, "fromSide": fs,
                          "toNode": t_id, "toSide": ts_, "toEnd": "arrow"})

    nodes.insert(0, {"id": nid("title"), "type": "text", "x": 0, "y": 0, "width": 520, "height": 130,
                     "text": "# %s roadmap\n\nColor = status: cyan todo, yellow doing, purple review, green done, red blocked, none backlog. Arrows point from blocker to blocked." % project})
    out = os.path.join(pdir, "%s Roadmap.canvas" % project)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"nodes": nodes, "edges": edges}, fh, indent="\t")
    print(out)
    print("%d epics, %d tickets, %d dependency arrows" % (len(epics), len(tickets), len(edges)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
