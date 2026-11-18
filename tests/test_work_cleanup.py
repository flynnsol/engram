import os, re, unittest

SKILL = os.path.join(os.path.dirname(__file__), "..", "skills", "work", "SKILL.md")


def step6():
    with open(SKILL, encoding="utf-8") as fh:
        text = fh.read()
    section = text.split("## Run tickets in parallel", 1)[1].split("\n## ", 1)[0]
    m = re.search(r"^6\. .*$", section, re.M)
    assert m, "step 6 missing from Run tickets in parallel"
    return m.group(0)


class WorkCleanupTest(unittest.TestCase):
    def setUp(self):
        self.step = step6()

    def test_removes_worktree_after_clean_merge(self):
        self.assertIn("git worktree remove <path>", self.step)
        self.assertRegex(self.step, r"clean merge with green tests")

    def test_deletes_branch_safely(self):
        self.assertIn("git branch -d <branch>", self.step)
        self.assertNotRegex(self.step, r"git branch -D")
        # worktree removal comes before the branch delete
        self.assertLess(self.step.index("git worktree remove"), self.step.index("git branch -d"))

    def test_keeps_worktree_on_failure(self):
        self.assertRegex(self.step, r"(?i)merge fails or the tests fail, keep the worktree")
        self.assertIn("report the worktree path", self.step)


if __name__ == "__main__":
    unittest.main()
