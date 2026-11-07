import json, os, re, unittest
from helpers import ROOT


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


class ReleaseTest(unittest.TestCase):
    def test_versions_agree(self):
        plugin = json.loads(load(".claude-plugin/plugin.json"))["version"]
        market = json.loads(load(".claude-plugin/marketplace.json"))["plugins"][0]["version"]
        top = re.search(r"^## (\d+\.\d+\.\d+) - \d{4}-\d{2}-\d{2}$", load("CHANGELOG.md"), re.M).group(1)
        self.assertEqual((plugin, market), (top, top), "plugin.json, marketplace.json and CHANGELOG.md must agree")

    def test_hooks_point_at_existing_commands(self):
        hooks = json.loads(load("hooks/hooks.json"))["hooks"]
        sh = load("scripts/engram.sh")
        for event in hooks.values():
            for group in event:
                for h in group["hooks"]:
                    sub = h["command"].rsplit(" ", 1)[-1]
                    self.assertIn(f"{sub}) ", sh, f"engram.sh has no '{sub}' command")


if __name__ == "__main__":
    unittest.main()
