import os, unittest
from helpers import VaultCase


def n(kind, up, body="", extra="", status=None):
    st = "status: %s\n" % status if status else ""
    return f'---\ntype: {kind}\n{st}up: "[[{up}]]"\n{extra}---\n\n# t\n\nUp: [[{up}]]\n\n{body}\n'


class VaultToolsTest(VaultCase):
    def setUp(self):
        super().setUp()
        self.init_vault()

    def lint(self):
        r = self.sh("lint")
        return r.returncode, r.stdout

    def test_fresh_vault_has_no_errors(self):
        rc, out = self.lint()
        self.assertEqual(rc, 0, out)

    def test_search_ranks_title_and_shows_description(self):
        self.write("03-Knowledge/Rust Lifetimes.md", n("knowledge", "Knowledge Overview", extra="description: borrow checker notes\n"))
        self.write("03-Knowledge/Other.md", n("knowledge", "Knowledge Overview", body="mentions lifetimes once"))
        r = self.sh("search", "lifetimes")
        lines = r.stdout.strip().split("\n")
        self.assertTrue(lines[0].startswith("03-Knowledge/Rust Lifetimes"), r.stdout)
        self.assertIn("borrow checker notes", lines[0])
        self.assertEqual(len(lines), 2)
        self.assertEqual(self.sh("search", "nonexistentword").returncode, 1)
        self.assertEqual(self.sh("search", "lifetimes", "borrow", "zzz").returncode, 1)  # every word must match

    def test_lint_finds_link_problems(self):
        self.write("03-Knowledge/Broken.md", n("knowledge", "Knowledge Overview", body="see [[Nowhere]] and `[[in code]]`"))
        self.write("03-Knowledge/NoUp.md", "---\ntype: knowledge\n---\n\n# x\n")
        rc, out = self.lint()
        self.assertEqual(rc, 1)
        self.assertIn("broken link [[Nowhere]]", out)
        self.assertNotIn("in code", out)
        self.assertIn("NoUp.md: missing up", out)
        self.assertIn("Broken.md: not listed in its parent", out)
        self.assertIn("Broken.md: orphan", out)

    def test_lint_ticket_checklist_and_epic(self):
        e = "01-Projects/P/Epics/P E1 A"
        self.write("01-Projects/P/P Overview.md", n("project-overview", "Projects Overview", "- [[P E1 A]]"))
        self.write(f"{e}/P E1 A.md", n("epic", "P Overview", "- [x] [[P T1 One]]\n- [ ] [[P T2 Two]]", status="done"))
        ex = 'epic: "[[P E1 A]]"\n'
        self.write(f"{e}/Tickets/P T1 One.md", n("ticket", "P E1 A", extra=ex, status="todo"))
        self.write(f"{e}/Tickets/P T2 Two.md", n("ticket", "P E1 A", extra=ex + 'blocked_by: ["[[Ghost]]"]\n', status="nope"))
        rc, out = self.lint()
        self.assertEqual(rc, 1)
        self.assertIn("checklist for [[P T1 One]] is ticked but the ticket is todo", out)
        self.assertIn("epic is done but has open tickets", out)
        self.assertIn("bad status 'nope'", out)
        self.assertIn("blocked_by points at missing note", out)

    def test_prefix_for(self):
        import os, sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        import vault
        self.assertEqual(vault.prefix_for("Engram"), "ENG")
        self.assertEqual(vault.prefix_for("Dioxus Atelier UI", {"DIO"}), "DAU")
        self.assertEqual(vault.prefix_for("Dioxus Atelier", {"DIO", "DAU"}), "DI2")
        self.assertEqual(vault.prefix_for("Dioxus", {"DIO"}), "DI2")  # one word: no initials
        self.assertEqual(vault.prefix_for("Go"), "GOX")
        self.assertEqual(vault.prefix_for("Dioxus Atelier", {"dio", "DAU", "DI2"}), "DI3")

    def test_lint_prefix_and_kind(self):
        e = "01-Projects/P/Epics/P E1 A"
        self.write("01-Projects/P/P Overview.md", n("project-overview", "Projects Overview", "- [[P E1 A]]", extra="prefix: PPP\n"))
        self.write("01-Projects/Q/Q Overview.md", n("project-overview", "Projects Overview", extra="prefix: PPP\n"))
        self.write("01-Projects/R/R Overview.md", n("project-overview", "Projects Overview"))
        self.write(f"{e}/P E1 A.md", n("epic", "P Overview", "- [ ] [[P T1 One]]\n- [ ] [[P T2 Two]]\n- [ ] [[P T3 Three]]", status="doing"))
        ex = 'epic: "[[P E1 A]]"\n'
        self.write(f"{e}/Tickets/P T1 One.md", n("ticket", "P E1 A", extra=ex + "kind: bug\n", status="todo"))
        self.write(f"{e}/Tickets/P T2 Two.md", n("ticket", "P E1 A", extra=ex + "kind: epic\n", status="todo"))
        self.write(f"{e}/Tickets/P T3 Three.md", n("ticket", "P E1 A", extra=ex, status="todo"))
        rc, out = self.lint()
        self.assertEqual(rc, 1)
        self.assertIn("duplicate prefix 'PPP'", out)
        self.assertIn("R Overview.md: missing prefix", out)
        self.assertIn("P T2 Two.md: bad kind 'epic'", out)
        self.assertIn("P T3 Three.md: missing kind", out)
        self.assertNotIn("P T1 One.md: bad kind", out)
        self.assertNotIn("P T1 One.md: missing kind", out)

    def test_templates_have_prefix_and_kind(self):
        t = os.path.join(self.vault, "99-Meta", "Templates")
        with open(os.path.join(t, "Ticket Template.md")) as fh:
            self.assertIn("kind: feature", fh.read())
        with open(os.path.join(t, "Project Overview Template.md")) as fh:
            self.assertIn("prefix:", fh.read())

    def test_status_reports_lint(self):
        self.assertIn("Lint: 0 error(s)", self.sh("status").stdout)


if __name__ == "__main__":
    unittest.main()


class OrchestrationLintTest(VaultCase):
    E = "01-Projects/P/Epics/P E1 A"

    def setUp(self):
        super().setUp()
        self.init_vault()
        self.write("01-Projects/P/P Overview.md", n("project-overview", "Projects Overview", "- [[P E1 A]]", status="active"))
        self.write(f"{self.E}/P E1 A.md", n("epic", "P Overview", "- [ ] [[P T1 X]]\n- [ ] [[P T2 X]]\n- [ ] [[P T3 X]]",
                                           extra='project: "[[P Overview]]"\n', status="doing"))

    def tk(self, num, status, extra=""):
        ex = 'epic: "[[P E1 A]]"\nproject: "[[P Overview]]"\n' + extra
        self.write(f"{self.E}/Tickets/P T{num} X.md", n("ticket", "P E1 A", extra=ex, status=status))

    def test_warnings(self):
        self.tk(1, "todo")                                            # no touches, about to be worked
        self.tk(2, "backlog")                                         # no touches, but only backlog: quiet
        self.tk(3, "backlog", 'role: wizard\ntouches: ["a"]\n')
        out = self.sh("lint").stdout
        self.assertIn("P T1 X.md: no touches", out)
        self.assertNotIn("P T2 X.md: no touches", out)
        self.assertIn("unknown role 'wizard'", out)

    def test_same_wave_overlap_warns_but_blocked_pair_does_not(self):
        self.tk(1, "todo", 'touches: ["src/a.py"]\n')
        self.tk(2, "todo", 'touches: ["src"]\n')
        self.assertIn("wave 1: touches overlap with [[P T2 X]]", self.sh("lint").stdout)
        self.tk(2, "todo", 'touches: ["src"]\nblocked_by: ["[[P T1 X]]"]\n')
        self.assertNotIn("touches overlap", self.sh("lint").stdout)
