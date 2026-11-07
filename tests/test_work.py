import json, os, unittest
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


if __name__ == "__main__":
    unittest.main()
