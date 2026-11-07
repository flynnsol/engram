#!/usr/bin/env python3
"""Engram PreToolUse gate.

Refuses to create a brand-new project (scaffold command, or a fresh manifest such as
Cargo.toml / package.json) unless the project already has a folder under
<vault>/01-Projects, i.e. engram:plan has been run for it.

Reads the PreToolUse hook JSON on stdin; prints a deny decision on stdout to block.
Fails open on any internal error: a broken gate must never wedge the session.

Env: ENGRAM_VAULT (required), ENGRAM_GATE=off to disable.
"""

import json
import os
import re
import shlex
import sys
import tempfile

MANIFESTS = {
    "Cargo.toml", "package.json", "pyproject.toml", "go.mod", "Gemfile", "mix.exs",
    "composer.json", "pom.xml", "build.gradle", "build.gradle.kts", "Package.swift",
    "deno.json", "pubspec.yaml", "setup.py",
}

# `cargo new x`, `dx new x`, `npm create ...`, `uv init`, `rails new`, `npx create-*`, `go mod init`.
SCAFFOLD = re.compile(
    r"\b(?:(?:cargo|dx|npm|pnpm|yarn|bun|uv|poetry|rails|mix|dotnet|flutter|django-admin)"
    r"\s+(?:new|init|create|startproject)\b|npx\s+create-\S+|go\s+mod\s+init\b)"
)
# Shell redirect that writes a manifest: `cat > Cargo.toml`, `echo x >> pkg/package.json`.
MANIFEST_REDIRECT = re.compile(
    r">>?\s*(['\"]?)(\S*?(?:%s))\1(?=\s|$|;|&|\|)" % "|".join(re.escape(m) for m in sorted(MANIFESTS))
)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def planned_names(vault: str) -> set[str]:
    """Normalized names of every project that has been planned in the vault."""
    root = os.path.join(vault, "01-Projects")
    names: set[str] = set()
    try:
        entries = os.listdir(root)
    except OSError:
        return names
    for entry in entries:
        folder = os.path.join(root, entry)
        if not os.path.isdir(folder):
            continue
        names.add(norm(entry))
        # Also accept the project's recorded local checkout: "local: `~/Projects/x/name`".
        try:
            for f in os.listdir(folder):
                if not f.endswith("Overview.md"):
                    continue
                with open(os.path.join(folder, f), encoding="utf-8") as fh:
                    for m in re.finditer(r"local:\s*`([^`]+)`", fh.read()):
                        names.add(norm(os.path.basename(m.group(1).rstrip("/"))))
        except OSError:
            pass
    names.discard("")
    return names


def in_tmp(path: str) -> bool:
    p = os.path.realpath(path)
    return any(p == t or p.startswith(t + os.sep) for t in {"/tmp", os.path.realpath(tempfile.gettempdir())})


def ancestor_has_project(path: str) -> bool:
    """True if a parent directory is already a project (manifest or .git), so this is a sub-package."""
    d = os.path.dirname(os.path.abspath(path))
    parent = os.path.dirname(d)
    while parent and parent != d:
        if os.path.exists(os.path.join(parent, ".git")) or any(
            os.path.exists(os.path.join(parent, m)) for m in MANIFESTS
        ):
            return True
        d, parent = parent, os.path.dirname(parent)
    return False


def deny(name: str, what: str) -> None:
    reason = (
        f"Engram gate: {what} looks like a NEW project ('{name}'), but there is no matching folder under "
        "01-Projects in the Engram vault, so it has not been planned. Run the engram:plan skill now "
        "(recall, short interview, confirm, then create the project notes), then retry. "
        "A go-ahead such as \"let's do it\" approves the idea; it does not skip planning. "
        "If the user explicitly says to skip detailed planning, create the minimal project notes "
        "(<Name> Overview and <Name> Plan) via engram:plan first; the gate opens as soon as the folder exists."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def main() -> None:
    if os.environ.get("ENGRAM_GATE", "").lower() == "off":
        return
    vault = os.environ.get("ENGRAM_VAULT", "")
    if not vault or not os.path.isfile(os.path.join(vault, "INDEX.md")):
        return
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    planned = planned_names(vault)

    if tool == "Write":
        path = inp.get("file_path", "")
        if not path or os.path.basename(path) not in MANIFESTS:
            return
        path = os.path.join(cwd, path) if not os.path.isabs(path) else path
        if os.path.exists(path) or in_tmp(path) or ancestor_has_project(path):
            return
        name = os.path.basename(os.path.dirname(path))
        if norm(name) not in planned:
            deny(name, f"writing a new {os.path.basename(path)}")
        return

    if tool == "Bash":
        cmd = inp.get("command", "")
        if in_tmp(cwd):
            return
        scaffold = SCAFFOLD.search(cmd)
        redirect = MANIFEST_REDIRECT.search(cmd)
        target = None
        if redirect:
            target = redirect.group(2)
            full = target if os.path.isabs(target) else os.path.join(cwd, target)
            if os.path.exists(full) or in_tmp(full):
                redirect = None
            else:
                target = os.path.basename(os.path.dirname(os.path.abspath(full)))
        if not scaffold and not redirect:
            return
        try:
            tokens = shlex.split(cmd, comments=False, posix=True)
        except ValueError:
            tokens = cmd.split()
        # A scaffold target under /tmp is scratch work, wherever the command runs from.
        if scaffold and any(in_tmp(os.path.join(cwd, t)) for t in tokens if t.startswith(("/", "./", "../", "~"))):
            return
        # Any word in the command, or the working directory, naming a planned project is enough.
        candidates = {norm(os.path.basename(t.rstrip("/"))) for t in tokens if not t.startswith("-")}
        candidates.add(norm(os.path.basename(cwd)))
        if target:
            candidates.add(norm(target))
        candidates.discard("")
        if candidates & planned:
            return
        name = next((os.path.basename(t.rstrip("/")) for t in reversed(tokens) if not t.startswith("-")), "?")
        deny(target or name, "this scaffold command" if scaffold else "writing a new manifest")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # fail open
        pass
