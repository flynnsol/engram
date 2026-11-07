import json, os, subprocess, sys, unittest
from helpers import SCRIPTS, VaultCase

# cwd outside /tmp (the gate ignores /tmp); the paths need not exist.
CWD = "/work/dev"


class GateTest(VaultCase):
    def setUp(self):
        super().setUp()
        self.init_vault()
        self.write("01-Projects/Planned App/Planned App Overview.md",
                   "# Planned App Overview\n\nlocal: `~/Projects/planned-checkout`\n")

    def gate(self, tool, **inp):
        env = dict(self.env, ENGRAM_VAULT=self.vault)
        data = {"tool_name": tool, "tool_input": inp, "cwd": CWD}
        p = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "gate.py")],
                           input=json.dumps(data), capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stderr)
        if not p.stdout.strip():
            return "allow"
        return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]

    def test_denied_bash(self):
        for cmd in ["cargo new widget", "dx new site", "npm create vite@latest app", "uv init thing",
                    "rails new blog", "npx create-next-app shop", "go mod init example.com/x",
                    "cat > fresh/Cargo.toml", "echo '{}' >> fresh/package.json"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.gate("Bash", command=cmd), "deny")

    def test_allowed_bash(self):
        for cmd in ["ls -la", "cargo build", "git status", "npm install", "cargo new planned-app",
                    "uv init planned-checkout", "cargo new /tmp/scratch-thing"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.gate("Bash", command=cmd), "allow")

    def test_write_manifest(self):
        self.assertEqual(self.gate("Write", file_path="/work/dev/brand-new/Cargo.toml"), "deny")
        self.assertEqual(self.gate("Write", file_path="/work/dev/Planned App/package.json"), "allow")
        self.assertEqual(self.gate("Write", file_path="/work/dev/brand-new/notes.md"), "allow")
        self.assertEqual(self.gate("Write", file_path="/tmp/x/Cargo.toml"), "allow")

    def test_switch_off(self):
        self.env["ENGRAM_GATE"] = "off"
        self.assertEqual(self.gate("Bash", command="cargo new widget"), "allow")

    def test_no_vault_fails_open(self):
        self.env["ENGRAM_VAULT"] = ""
        p = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "gate.py")],
                           input="{}", capture_output=True, text=True, env=dict(self.env, ENGRAM_VAULT=""))
        self.assertEqual(p.stdout.strip(), "")

    def test_bad_input_fails_open(self):
        p = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "gate.py")],
                           input="not json", capture_output=True, text=True,
                           env=dict(self.env, ENGRAM_VAULT=self.vault))
        self.assertEqual((p.returncode, p.stdout.strip()), (0, ""))


if __name__ == "__main__":
    unittest.main()
