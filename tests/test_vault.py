import unittest
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

    def test_status_reports_lint(self):
        self.assertIn("Lint: 0 error(s)", self.sh("status").stdout)


if __name__ == "__main__":
    unittest.main()
