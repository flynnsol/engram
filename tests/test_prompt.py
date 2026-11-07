import json, unittest
from helpers import VaultCase

REQUIRED = [
    "plan the next epic", "what's next?", "create a new tool for syncing", "scaffold an app",
    "start a new project", "the ticket is done", "build a landing page", "break this down",
]
SOFT = ["let's do it", "sounds good", "go ahead", "ship it"]
NONE = ["fix the typo in README", "why does this test fail?", "explain the gate", "rename the variable"]


class PromptTest(VaultCase):
    def classify(self, prompt):
        out = self.sh("prompt-submit", stdin=json.dumps({"prompt": prompt})).stdout
        if out.startswith("Engram REQUIRED"):
            return "required"
        if out.startswith("Engram reminder"):
            return "soft"
        return "none"

    def test_no_vault_is_silent(self):
        self.assertEqual(self.classify("plan the next epic"), "none")

    def test_classes(self):
        self.init_vault()
        for group, want in ((REQUIRED, "required"), (SOFT, "soft"), (NONE, "none")):
            for prompt in group:
                with self.subTest(prompt=prompt):
                    self.assertEqual(self.classify(prompt), want)


if __name__ == "__main__":
    unittest.main()
