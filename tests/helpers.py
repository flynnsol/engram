"""Shared helpers: build a temp vault and run the plugin scripts against it."""
import json, os, shutil, subprocess, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
ENGRAM_SH = os.path.join(SCRIPTS, "engram.sh")


class VaultCase(unittest.TestCase):
    """Each test gets a fresh config dir and an empty vault path (not yet initialized)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="engram-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.vault = os.path.join(self.tmp, "vault")
        self.env = dict(os.environ, XDG_CONFIG_HOME=os.path.join(self.tmp, "cfg"), HOME=self.tmp)
        self.env.pop("ENGRAM_GATE", None)

    def sh(self, *args, stdin=""):
        return subprocess.run([ENGRAM_SH, *args], input=stdin, capture_output=True, text=True, env=self.env)

    def init_vault(self):
        self.assertEqual(self.sh("set", self.vault).returncode, 0)
        self.assertEqual(self.sh("init").returncode, 0)

    def write(self, rel, text):
        path = os.path.join(self.vault, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def hook(self, **fields):
        return json.dumps(fields)
