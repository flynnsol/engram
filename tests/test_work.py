import glob, json, os, unittest
from helpers import VaultCase
from test_vault import n

E = "01-Projects/P/Epics/P E1 A"


class WorkTest(VaultCase):
    def setUp(self):
        super().setUp()
        self.init_vault()
        self.write("01-Projects/P/P Overview.md", n("project-overview", "Projects Overview", "- [[P E1 A]] — first", status="active"))
        self.write("01-Projects/Projects Overview.md",
                   n("overview", "INDEX", "<!-- engram:projects-active -->\n- [[P Overview|P]] — a project\n\n"
                     "<!-- engram:projects-archived -->\n- [[Old Overview|Old]] — done 2026-01-01: old\n"))
        self.write("INDEX.md", "---\ntype: overview\n---\n# E\n\n<!-- engram:active-projects -->\n- [[P Overview|P]] — a project\n- [[Q Overview|Q]] — other\n")
        self.write(f"{E}/P E1 A.md", n("epic", "P Overview", "## Done when\n\n- [ ] works\n\n## Tickets\n\n- [ ] [[P T1 One]]\n- [ ] [[P T2 Two]]",
                                    extra='project: "[[P Overview]]"\n', status="backlog"))
        ex = 'epic: "[[P E1 A]]"\nproject: "[[P Overview]]"\n'
        self.write(f"{E}/Tickets/P T1 One.md", n("ticket", "P E1 A", extra=ex, status="backlog"))
        self.write(f"{E}/Tickets/P T2 Two.md", n("ticket", "P E1 A", extra=ex + 'blocked_by: ["[[P T1 One]]"]\n', status="backlog"))

    def read(self, rel):
        with open(os.path.join(self.vault, rel), encoding="utf-8") as fh:
            return fh.read()

    def test_ticket_flow(self):
        r = self.sh("ticket", "P T2", "doing")
        self.assertEqual(r.returncode, 1)
        self.assertIn("blocked by unfinished: P T1 One", r.stderr)
        r = self.sh("ticket", "P T1", "doing")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("status: doing", self.read(f"{E}/Tickets/P T1 One.md"))
        self.assertIn("status: doing", self.read(f"{E}/P E1 A.md"))  # epic started
        r = self.sh("ticket", "P T1", "done")
        self.assertIn("1 of 2 tickets done", r.stdout)
        self.assertIn("- [x] [[P T1 One]]", self.read(f"{E}/P E1 A.md"))
        self.sh("ticket", "P T2", "done")
        r = self.sh("ticket", "P T1", "review", "--force")
        self.assertIn("- [ ] [[P T1 One]]", self.read(f"{E}/P E1 A.md"))
        self.assertNotIn("checklist", self.sh("lint").stdout)
        self.assertTrue(os.path.exists(os.path.join(self.vault, "01-Projects/P/P Roadmap.canvas")))

    def test_suggested_branch(self):
        import vault as V
        self.assertEqual(V.branch_name("ENG-25 Add Branch Names"), "eng-25/add-branch-names")
        self.assertEqual(V.branch_name("DAU2-7 Fix: the `Kbd` bug!"), "dau2-7/fix-the-kbd-bug")
        self.assertEqual(V.branch_name("Engram T12 Old Name"), "engram-t12/old-name")
        r = self.sh("ticket", "P T1", "doing")
        self.assertIn("Suggested branch: p-t1/one", r.stdout)
        self.assertNotIn("Suggested branch", self.sh("ticket", "P T1", "done").stdout)

    def test_bad_input(self):
        self.assertEqual(self.sh("ticket", "P T1", "finished").returncode, 1)
        self.assertEqual(self.sh("ticket", "P T9", "done").returncode, 1)
        self.assertEqual(self.sh("ticket", "P", "done").returncode, 1)  # ambiguous

    def test_close_epic_and_project(self):
        self.assertEqual(self.sh("close-epic", "P E1").returncode, 1)  # open tickets
        self.sh("ticket", "P T1", "done"); self.sh("ticket", "P T2", "done")
        r = self.sh("close-epic", "P E1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 'Done when'", r.stdout)
        self.assertIn("status: done", self.read(f"{E}/P E1 A.md"))
        self.assertIn("(done ", self.read("01-Projects/P/P Overview.md"))
        r = self.sh("close-project", "P")
        self.assertEqual(r.returncode, 0, r.stderr)
        po = self.read("01-Projects/Projects Overview.md")
        self.assertLess(po.index("projects-archived"), po.index("[[P Overview|P]]"))
        self.assertNotIn("[[P Overview", self.read("INDEX.md"))
        self.assertIn("[[Q Overview", self.read("INDEX.md"))
        self.assertIn("status: done", self.read("01-Projects/P/P Overview.md"))

    def test_prefixed_and_old_names_resolve_and_order(self):
        ex = 'epic: "[[P E1 A]]"\nproject: "[[P Overview]]"\n'
        self.write(f"{E}/Tickets/PPP-3 Three.md", n("ticket", "P E1 A", extra=ex, status="backlog"))
        self.write(f"{E}/Tickets/PPP-10 Ten.md", n("ticket", "P E1 A", extra=ex, status="backlog"))
        for q in ("PPP-3", "PPP-3 Three"):
            self.assertEqual(self.sh("ticket", q, "doing").returncode, 0)
        r = self.sh("ticket", "PPP-1", "doing")  # PPP-1 must not match PPP-10
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.sh("ticket", "P T1", "doing").returncode, 0)  # old name still works
        canvas = json.loads(self.read("01-Projects/P/P Roadmap.canvas"))
        files = [n["file"].split("/")[-1] for n in canvas["nodes"] if n.get("file", "").endswith(".md") and "/Tickets/" in n["file"]]
        self.assertEqual(files, ["P T1 One.md", "P T2 Two.md", "PPP-3 Three.md", "PPP-10 Ten.md"])

    def test_prefix_command(self):
        self.write("01-Projects/Engram/Engram Overview.md", n("project-overview", "Projects Overview", extra="prefix: ENG\n"))
        self.assertEqual(self.sh("prefix", "Engram").stdout.strip(), "ENG")  # existing one is kept
        self.assertEqual(self.sh("prefix", "Engine Room").stdout.strip(), "EN2")  # ENG taken, only 2 initials: numbered
        self.assertEqual(self.sh("prefix", "Zeta").stdout.strip(), "ZET")

    def test_archived_ticket(self):
        r = self.sh("ticket", "P T1", "archived")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("status: archived", self.read(f"{E}/Tickets/P T1 One.md"))
        self.assertIn("updated: ", self.read(f"{E}/Tickets/P T1 One.md"))
        self.assertIn("- [ ] [[P T1 One]]", self.read(f"{E}/P E1 A.md"))
        self.assertIn("0 of 1 tickets done", r.stdout)  # archived tickets leave the count
        self.assertNotIn("checklist", self.sh("lint").stdout)
        self.sh("ticket", "P T2", "done")
        self.assertEqual(self.sh("close-epic", "P E1").returncode, 0)  # archived does not block closing
        self.assertNotIn("epic is done but has open tickets", self.sh("lint").stdout)
        canvas = json.loads(self.read("01-Projects/P/P Roadmap.canvas"))
        colors = {n.get("file", "").split("/")[-1]: n.get("color") for n in canvas["nodes"]}
        self.assertEqual(colors["P T1 One.md"], "#808080")


if __name__ == "__main__":
    unittest.main()


class ReadyTest(VaultCase):
    def setUp(self):
        super().setUp()
        self.init_vault()
        self.write("01-Projects/P/P Overview.md", n("project-overview", "Projects Overview", "- [[P E1 A]]", status="active"))
        self.write(f"{E}/P E1 A.md", n("epic", "P Overview", "- [ ] [[P T1 A]]\n- [ ] [[P T2 B]]\n- [ ] [[P T3 C]]\n- [ ] [[P T4 D]]",
                                    extra='project: "[[P Overview]]"\n', status="doing"))

    def ticket(self, num, status="todo", touches=None, blocked=None):
        ex = 'epic: "[[P E1 A]]"\nproject: "[[P Overview]]"\n'
        if touches is not None:
            ex += "touches: [%s]\n" % ", ".join('"%s"' % t for t in touches)
        if blocked:
            ex += 'blocked_by: ["[[%s]]"]\n' % blocked
        name = "P T%d X" % num
        self.write(f"{E}/Tickets/{name}.md", n("ticket", "P E1 A", extra=ex, status=status))
        return name

    def test_disjoint_tickets_run_together_and_collisions_are_held(self):
        self.ticket(1, touches=["src/a.py"])
        self.ticket(2, touches=["src/b.py", "tests/"])
        self.ticket(3, touches=["src"])            # overlaps T1 and T2 by directory
        self.ticket(4, touches=["docs/x.md"], blocked="P T1 X")  # blocked: not ready
        r = self.sh("ready", "P")
        self.assertIn("Ready now (2", r.stdout)
        self.assertIn("- P T1 X | role=engineer | touches=src/a.py | branch=p-t1/x", r.stdout)
        self.assertIn("Held: P T3 X collides with P T1 X on src ~ src/a.py", r.stdout)
        self.assertNotIn("- P T4 X", r.stdout)

    def test_missing_touches_runs_alone_and_in_flight_reserves_paths(self):
        self.ticket(1, status="doing", touches=["src/a.py"])
        self.ticket(2, touches=["src/a.py"])
        self.ticket(3)  # no touches
        r = self.sh("ready", "P")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Held: P T2 X collides with P T1 X on src/a.py", r.stdout)
        self.assertIn("(no touches)", r.stdout)

    def test_waves_and_unknown_project(self):
        self.ticket(1, touches=["a"])
        self.ticket(2, touches=["b"], blocked="P T1 X")
        r = self.sh("ready", "P", "--waves")
        self.assertIn("wave 1: P T1 X", r.stdout)
        self.assertIn("wave 2: P T2 X", r.stdout)
        self.assertEqual(self.sh("ready", "Nope").returncode, 1)

    def test_archived_tickets_are_ignored_by_ready_and_lint(self):
        self.ticket(1, status="archived", touches=["src/a.py"])
        self.ticket(2, touches=["src/a.py"], blocked="P T1 X")  # archived blocker is resolved
        r = self.sh("ready", "P")
        self.assertIn("- P T2 X", r.stdout)
        self.assertNotIn("P T1 X", r.stdout.replace("blocked", ""))
        self.ticket(3, status="archived")  # no touches: would warn if it were open
        out = self.sh("lint").stdout
        self.assertNotIn("no touches", out)
        self.assertNotIn("touches overlap", out)
        self.assertNotIn("unknown role", out)


class MigrateTest(VaultCase):
    def setUp(self):
        super().setUp()
        self.init_vault()
        self.write("01-Projects/P/P Overview.md", n("project-overview", "Projects Overview", "- [[P E1 A]]", status="active"))
        self.write(f"{E}/P E1 A.md", n("epic", "P Overview", "- [ ] [[P T1 Old]]\n- [x] [[P T2 Done]]\n- [ ] [[P T3 New]]",
                                    extra='project: "[[P Overview]]"\n', status="doing"))
        ex = 'epic: "[[P E1 A]]"\nproject: "[[P Overview]]"\n'
        self.write(f"{E}/Tickets/P T1 Old.md", n("ticket", "P E1 A", extra=ex, status="todo"))
        self.write(f"{E}/Tickets/P T2 Done.md", n("ticket", "P E1 A", extra=ex, status="done"))
        self.write(f"{E}/Tickets/P T3 New.md", n("ticket", "P E1 A", extra=ex + "touches: []\nrole: tester\n", status="todo"))
        self.tpl = os.path.join(self.vault, "99-Meta/Templates/Ticket Template.md")
        with open(self.tpl, "w") as fh:
            fh.write("old template\n")

    def read(self, rel):
        with open(os.path.join(self.vault, rel), encoding="utf-8") as fh:
            return fh.read()

    def test_dry_run_writes_nothing_and_status_reports(self):
        before = self.read(f"{E}/Tickets/P T1 Old.md")
        r = self.sh("migrate")
        self.assertIn("Would update ticket: " + f"{E}/Tickets/P T1 Old.md", r.stdout)
        self.assertNotIn("Would update ticket: " + f"{E}/Tickets/P T2 Done.md", r.stdout)  # no old-format change
        self.assertNotIn("Would update ticket: " + f"{E}/Tickets/P T3 New.md", r.stdout)
        self.assertIn("Would rename ticket: P T1 Old -> PXX-1 Old", r.stdout)
        self.assertIn("Would set prefix PXX", r.stdout)
        self.assertIn("Would set kind feature", r.stdout)
        self.assertFalse(glob.glob(self.vault + ".backup-*"))
        self.assertTrue(os.path.exists(os.path.join(self.vault, E, "Tickets", "P T2 Done.md")))
        self.assertIn("Would update template: Ticket Template.md", r.stdout)
        self.assertEqual(self.read(f"{E}/Tickets/P T1 Old.md"), before)
        self.assertIn("Old format: 1 open ticket", self.sh("status").stdout)

    def test_apply_is_idempotent_and_keeps_backup(self):
        r = self.sh("migrate", "--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        t = self.read(f"{E}/Tickets/PXX-1 Old.md")
        self.assertIn("touches: []", t)
        self.assertIn("role: engineer", t)
        self.assertEqual(self.read(f"{E}/Tickets/PXX-3 New.md").count("role:"), 1)  # kept as is
        self.assertIn("touches:", self.read("99-Meta/Templates/Ticket Template.md"))
        self.assertEqual(self.read("99-Meta/Templates/Ticket Template.md.bak"), "old template\n")
        self.assertIn("Nothing to migrate", self.sh("migrate").stdout)
        self.assertNotIn("Old format", self.sh("status").stdout)
        self.assertEqual(self.sh("migrate", "--bogus").returncode, 2)

    def test_rename_rewrites_links_and_canvas_and_sets_kinds(self):
        self.write(f"{E}/Tickets/P T4 Fix crash.md", n("ticket", "P E1 A", extra='epic: "[[P E1 A]]"\nproject: "[[P Overview]]"\nblocked_by: ["[[P T1 Old]]"]\n', status="todo", body="See [[P T1 Old|the first]] and [[P T1 Old#Notes]]."))
        self.write(f"{E}/Tickets/P T5 Remove cruft.md", n("ticket", "P E1 A", extra='epic: "[[P E1 A]]"\nproject: "[[P Overview]]"\nkind: bug\n', status="done"))
        self.write("01-Projects/P/P Notes.md", n("knowledge", "P Overview", "Link [[P T2 Done]]"))
        canvas = {"nodes": [{"id": "a", "type": "file", "file": f"{E}/Tickets/P T1 Old.md"}, {"id": "b", "type": "text", "text": "[[P T3 New]]"}], "edges": []}
        self.write("01-Projects/P/Other.canvas", json.dumps(canvas))
        before = self.sh("lint").stdout.count("broken link")
        r = self.sh("migrate", "--apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.vault, E, "Tickets", "PXX-4 Fix crash.md")))
        self.assertFalse(os.path.exists(os.path.join(self.vault, E, "Tickets", "P T4 Fix crash.md")))
        t4 = self.read(f"{E}/Tickets/PXX-4 Fix crash.md")
        self.assertIn('blocked_by: ["[[PXX-1 Old]]"]', t4)
        self.assertIn("[[PXX-1 Old|the first]]", t4)
        self.assertIn("[[PXX-1 Old#Notes]]", t4)
        self.assertIn("kind: bug", t4)                                   # "Fix" -> bug
        self.assertIn("kind: bug", self.read(f"{E}/Tickets/PXX-5 Remove cruft.md"))  # existing kind kept
        self.assertIn("kind: feature", self.read(f"{E}/Tickets/PXX-1 Old.md"))
        self.assertIn("[[PXX-1 Old]]", self.read(f"{E}/P E1 A.md"))
        self.assertIn("[[PXX-2 Done]]", self.read("01-Projects/P/P Notes.md"))
        self.assertIn("up: \"[[P E1 A]]\"", t4)                          # epic links untouched
        self.assertIn("prefix: PXX", self.read("01-Projects/P/P Overview.md"))
        c = self.read("01-Projects/P/Other.canvas")
        self.assertIn("Tickets/PXX-1 Old.md", c)
        self.assertIn("[[PXX-3 New]]", c)
        self.assertEqual(self.sh("lint").stdout.count("broken link"), before)
        backups = glob.glob(self.vault + ".backup-*")
        self.assertEqual(len(backups), 1)
        self.assertTrue(os.path.exists(os.path.join(backups[0], E, "Tickets", "P T1 Old.md")))
        self.assertIn("Nothing to migrate", self.sh("migrate").stdout)   # idempotent
        self.sh("migrate", "--apply")
        self.assertEqual(len(glob.glob(self.vault + ".backup-*")), 1)    # no second backup

    def test_chore_kinds_and_prefix_collision(self):
        ex = 'epic: "[[P E1 A]]"\nproject: "[[P Overview]]"\n'
        self.write(f"{E}/Tickets/P T6 Refactor parser.md", n("ticket", "P E1 A", extra=ex, status="todo"))
        self.write("01-Projects/PXX/PXX Overview.md", n("project-overview", "Projects Overview", status="active"))
        self.sh("migrate", "--apply")
        self.assertIn("kind: chore", self.read(f"{E}/Tickets/PXX-6 Refactor parser.md"))
        self.assertIn("prefix: PXX", self.read("01-Projects/P/P Overview.md"))   # first in name order
        self.assertIn("prefix: PX2", self.read("01-Projects/PXX/PXX Overview.md"))  # PXX taken: numbered
