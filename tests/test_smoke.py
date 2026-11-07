import json, os, subprocess, sys, unittest
from helpers import SCRIPTS, VaultCase


def note(kind, status, up, extra=""):
    return f'---\ntype: {kind}\nstatus: {status}\nup: "[[{up}]]"\n{extra}---\n\n# x\n'


class InitTest(VaultCase):
    def test_init_scaffolds_and_never_overwrites(self):
        self.init_vault()
        for rel in ("INDEX.md", "00-Inbox/Inbox Overview.md", "99-Meta/Templates/Ticket Template.md"):
            self.assertTrue(os.path.isfile(os.path.join(self.vault, rel)), rel)
        with open(os.path.join(self.vault, "INDEX.md")) as fh:
            self.assertNotIn("{{init_date}}", fh.read())
        self.write("INDEX.md", "mine\n")
        self.assertEqual(self.sh("init").returncode, 0)
        with open(os.path.join(self.vault, "INDEX.md")) as fh:
            self.assertEqual(fh.read(), "mine\n")

    def test_status_and_session_start(self):
        self.assertIn("not set", self.sh("status").stdout)
        self.init_vault()
        self.write("00-Inbox/scratch.md", "hi\n")
        self.assertIn("1 unsorted", self.sh("status").stdout)
        out = self.sh("session-start").stdout
        self.assertIn(self.vault, out)
        self.assertIn("1 unsorted", out)

    def test_set_requires_path(self):
        self.assertEqual(self.sh("set").returncode, 2)


class RoadmapTest(VaultCase):
    def test_canvas_from_epics_and_tickets(self):
        self.init_vault()
        p = "01-Projects/Demo/Epics/Demo E1 First"
        self.write("01-Projects/Demo/Demo Overview.md", "# Demo\n")
        self.write(f"{p}/Demo E1 First.md", note("epic", "doing", "Demo Overview"))
        self.write(f"{p}/Tickets/Demo T1 One.md", note("ticket", "done", "Demo E1 First", 'epic: "[[Demo E1 First]]"\n'))
        self.write(f"{p}/Tickets/Demo T2 Two.md",
                   note("ticket", "todo", "Demo E1 First", 'epic: "[[Demo E1 First]]"\nblocked_by: ["[[Demo T1 One]]"]\n'))
        r = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "roadmap.py"), self.vault, "Demo"],
                           capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 epics, 2 tickets, 1 dependency arrows", r.stdout)
        with open(os.path.join(self.vault, "01-Projects/Demo/Demo Roadmap.canvas")) as fh:
            canvas = json.load(fh)
        files = {n["file"]: n for n in canvas["nodes"] if n["type"] == "file"}
        self.assertEqual(len(files), 3)
        self.assertEqual(files[f"{p}/Tickets/Demo T1 One.md"]["color"], "4")  # done = green
        self.assertEqual(files[f"{p}/Tickets/Demo T2 Two.md"]["color"], "5")  # todo = cyan
        self.assertEqual(len(canvas["edges"]), 1)
        ids = {n["id"] for n in canvas["nodes"]}
        self.assertTrue(all(e["fromNode"] in ids and e["toNode"] in ids for e in canvas["edges"]))

    def test_ids_are_stable_between_runs(self):
        self.init_vault()
        self.write("01-Projects/Demo/Demo Overview.md", "# Demo\n")
        self.write("01-Projects/Demo/Epics/Demo E1 A/Demo E1 A.md", note("epic", "todo", "Demo Overview"))
        out = os.path.join(self.vault, "01-Projects/Demo/Demo Roadmap.canvas")
        run = lambda: subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "roadmap.py"), self.vault, "Demo"],
                                     capture_output=True, text=True, env=self.env)
        run()
        with open(out) as fh: a = fh.read()
        run()
        with open(out) as fh: b = fh.read()
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
