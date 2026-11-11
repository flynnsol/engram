import json, os, unittest
from helpers import VaultCase
from test_vault import n


class HookTest(VaultCase):
    def setUp(self):
        super().setUp()
        self.init_vault()
        self.proj = os.path.join(self.tmp, "checkout")
        os.makedirs(self.proj)
        self.write("01-Projects/P/P Overview.md",
                   n("project-overview", "Projects Overview", "local: `%s`" % self.proj, status="active"))
        ex = 'epic: "[[P E1 A]]"\nproject: "[[P Overview]]"\n'
        self.write("01-Projects/P/Epics/P E1 A/P E1 A.md", n("epic", "P Overview", "- [ ] [[P T1 One]]", status="doing"))
        self.write("01-Projects/P/Epics/P E1 A/Tickets/P T1 One.md", n("ticket", "P E1 A", extra=ex, status="doing"))
        self.write("01-Projects/P/Epics/P E1 A/Tickets/P T2 Two.md",
                   n("ticket", "P E1 A", extra=ex + 'blocked_by: ["[[P T1 One]]"]\n', status="todo"))
        self.write("01-Projects/P/Epics/P E1 A/Tickets/P T3 Three.md", n("ticket", "P E1 A", extra=ex, status="todo"))
        self.write("05-Journal/2026-11-06.md", n("journal", "Journal Overview"))

    def test_session_digest(self):
        out = self.sh("session-start", stdin=json.dumps({"cwd": self.proj})).stdout
        self.assertIn("working in planned project P; next unblocked: [[P T3 Three]]", out)
        self.assertIn("doing: [[P T1 One]]", out)
        self.assertIn("last journal entry: [[2026-11-06]]", out)
        elsewhere = self.sh("session-start", stdin=json.dumps({"cwd": "/work/other"})).stdout
        self.assertNotIn("working in planned project", elsewhere)
        self.assertIn("doing: [[P T1 One]]", elsewhere)
        self.write("01-Projects/P/Epics/P E1 A/Tickets/P T3 Three.md",
                   n("ticket", "P E1 A", extra='epic: "[[P E1 A]]"\nproject: "[[P Overview]]"\n', status="archived"))
        self.assertNotIn("P T3 Three", self.sh("session-start", stdin=json.dumps({"cwd": self.proj})).stdout)

    def test_prompt_is_quiet_inside_planned_project(self):
        inside = self.sh("prompt-submit", stdin=json.dumps({"prompt": "plan the next epic", "cwd": self.proj + "/src"})).stdout
        self.assertTrue(inside.startswith("Engram: this repo is the planned project 'P'"), inside)
        self.assertLess(len(inside), 300)
        self.assertEqual(self.sh("prompt-submit", stdin=json.dumps({"prompt": "go ahead", "cwd": self.proj})).stdout, "")
        outside = self.sh("prompt-submit", stdin=json.dumps({"prompt": "plan the next epic", "cwd": "/work/other"})).stdout
        self.assertTrue(outside.startswith("Engram REQUIRED"))

    def test_stop_check_is_opt_in_and_blocks_once(self):
        self.write("03-Knowledge/Bad.md", n("knowledge", "Knowledge Overview", "see [[Nowhere]]"))
        self.assertEqual(self.sh("stop-check", stdin="{}").stdout, "")  # off by default
        self.env["ENGRAM_STOP_LINT"] = "on"
        out = json.loads(self.sh("stop-check", stdin="{}").stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("broken link [[Nowhere]]", out["reason"])
        self.assertEqual(self.sh("stop-check", stdin=json.dumps({"stop_hook_active": True})).stdout, "")


if __name__ == "__main__":
    unittest.main()
