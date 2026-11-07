#!/usr/bin/env bash
# Engram helper: vault path config, scaffolding, and session-start context.
# The vault path lives in ${XDG_CONFIG_HOME:-~/.config}/engram/vault (one line).
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="$PLUGIN_ROOT/vault-template"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/engram"
CONFIG_FILE="$CONFIG_DIR/vault"

get_vault() {
  [ -f "$CONFIG_FILE" ] && cat "$CONFIG_FILE" || true
}

require_vault() {
  local v
  v="$(get_vault)"
  if [ -z "$v" ]; then
    echo "No vault configured. Run: /engram vaultpath <path>" >&2
    exit 1
  fi
  printf '%s' "$v"
}

cmd_set() {
  [ $# -ge 1 ] || { echo "usage: engram.sh set <vault-path>" >&2; exit 2; }
  local raw="$1" path
  case "$raw" in
    "~") raw="$HOME" ;;
    "~/"*) raw="$HOME/${raw#"~/"}" ;;
  esac
  mkdir -p "$raw"
  path="$(cd "$raw" && pwd)"
  mkdir -p "$CONFIG_DIR"
  printf '%s\n' "$path" > "$CONFIG_FILE"
  echo "Vault path set to: $path"
  if [ ! -f "$path/INDEX.md" ]; then
    echo "Vault has no INDEX.md yet. Run: /engram init"
  fi
}

cmd_get() {
  local v
  v="$(get_vault)"
  [ -n "$v" ] || { echo "No vault configured." >&2; exit 1; }
  echo "$v"
}

cmd_init() {
  local v today
  v="$(require_vault)"
  today="$(date +%F)"
  mkdir -p "$v"
  # Copy only what is missing; never overwrite files that already exist in the vault.
  # (cp -n exits 1 when it skips a file on newer coreutils, so it is not used here.)
  (cd "$TEMPLATE_DIR" && find . -type d -print0) | while IFS= read -r -d '' d; do mkdir -p "$v/$d"; done
  (cd "$TEMPLATE_DIR" && find . -type f -print0) | while IFS= read -r -d '' f; do
    [ -e "$v/$f" ] || cp "$TEMPLATE_DIR/$f" "$v/$f"
  done
  # Fill date placeholders only in files that still contain them.
  { grep -rlF '{{init_date}}' "$v" --include='*.md' 2>/dev/null || true; } | while read -r f; do
    sed -i "s/{{init_date}}/$today/g" "$f"
  done
  echo "Vault initialized at: $v"
}

cmd_status() {
  local v
  v="$(get_vault)"
  if [ -z "$v" ]; then echo "Vault: (not set)"; return; fi
  echo "Vault: $v"
  if [ -d "$v" ]; then
    echo "Notes: $(find "$v" -name '*.md' -not -path '*/.obsidian/*' | wc -l)"
    echo "Inbox: $(find "$v/00-Inbox" -name '*.md' ! -name 'Inbox Overview.md' 2>/dev/null | wc -l) unsorted"
  else
    echo "Directory does not exist."
  fi
}

# Emits context for the SessionStart hook (stdout is added to the session).
cmd_session_start() {
  local v
  v="$(get_vault)"
  if [ -z "$v" ]; then
    echo "Engram is installed but no vault is configured. If the user wants persistent notes, suggest: /engram vaultpath <path>"
    return
  fi
  [ -f "$v/INDEX.md" ] || { echo "Engram vault at $v is not initialized. Suggest: /engram init"; return; }
  local inbox
  inbox="$(find "$v/00-Inbox" -name '*.md' ! -name 'Inbox Overview.md' 2>/dev/null | wc -l)"
  cat <<EOF
Engram vault: $v
PRIORITY: Engram is the first-choice system for memory, project information and documentation. This overrides Claude's built-in memory (the auto-memory directory and its MEMORY.md) and the Claude Docs / docs skills unless the user explicitly asks for one of those formats.
- Reading (memories, project info, past decisions, notes, "what do you know about..."): use the engram:recall skill FIRST. Read $v/INDEX.md, then follow wikilinks down through the section overviews.
- Writing (saving a memory, preference, feedback, project context, idea, plan, decision, or documentation): use engram:conventions and engram:remember FIRST, and write to the vault. Do not write to the built-in memory directory and do not create a Claude Doc instead.
- Planning and executing work (a project, epic, feature, ticket, bug, "what's next", "X is done"): use engram:plan to plan, engram:work to execute and engram:roadmap for the canvas, FIRST, before brainstorming a plan or creating tasks elsewhere. Plans, epics and tickets live in the vault under 01-Projects.
HARD RULE: before creating, scaffolding or building ANY new project, repo, app, tool, site, plugin or feature, you MUST run engram:recall and then engram:plan, and get the user's confirmation, BEFORE writing code or running a scaffold command. This is not optional and is not satisfied by planning in chat. A go-ahead like "let's do it" or "sounds good" approves the idea, it does not skip planning. A PreToolUse gate denies new-project scaffolding until the project has a folder under 01-Projects in the vault.
Inbox has $inbox unsorted note(s)$( [ "$inbox" -gt 0 ] && echo " (offer engram:triage)" ).
EOF
}

# UserPromptSubmit hook: reads the hook JSON on stdin; when the prompt looks like
# planning, creating or executing work, reminds Claude to use the Engram skills first.
cmd_prompt_submit() {
  local v prompt
  v="$(get_vault)"
  if [ -z "$v" ] || [ ! -f "$v/INDEX.md" ]; then return 0; fi
  prompt="$(python3 -I -c 'import json,sys; print(json.load(sys.stdin).get("prompt",""))' 2>/dev/null || true)"
  local plan_re work_re create_re go_re
  plan_re='\b(plan|planning|roadmap|epic|ticket|milestone|scope|break (it|this|that)? ?down|backlog|what.?s next|next (task|ticket|step)|pick up|(is|are|got|was) (done|finished|merged|shipped)|new (project|feature)|build (a|an|the|out)|should we (add|build))\b'
  create_re='\b(create|make|start|set ?up|scaffold|bootstrap|spin up|kick ?off|initiali[sz]e|generate|design|implement|develop|write)\b[^.?!]{0,80}\b(project|repo|repository|app|application|tool|website|site|service|plugin|library|crate|package|feature|folder|cli|bot|game|dashboard|api|extension|generator)\b|\bnew (folder|repo|repository|app|tool|site|website|crate|package|plugin|service|project)\b|\bfrom scratch\b'
  go_re="\\b(let.?s do it|lets do it|go ahead|sounds good|looks good|do it|ship it|make it so|yes,? (please|do|go))\\b"
  if printf '%s' "$prompt" | grep -qiE "$plan_re|$create_re"; then
    cat <<EOF
Engram REQUIRED: this prompt is about planning, creating or executing work. Before writing code, scaffolding or creating files outside the vault, you MUST run engram:recall and then engram:plan (interview, confirm, create the notes), or engram:work for existing tickets. Plans, epics and tickets live in the vault ($v) under 01-Projects; engram:roadmap draws them as a canvas. This takes priority over other planning skills and over replying "let's go" straight into building. Only skip if this is a small edit inside an already-planned project; if unsure, ask once. A PreToolUse gate will deny new-project scaffolding until the project is planned.
EOF
  elif printf '%s' "$prompt" | grep -qiE "$go_re"; then
    cat <<EOF
Engram reminder: a go-ahead approves the idea, it does not skip planning. If the work you are about to start is a new project or feature that has no plan in the vault ($v/01-Projects), run engram:recall then engram:plan and get the user's confirmation BEFORE writing code or scaffolding.
EOF
  fi
}

# PreToolUse hook: denies creating a brand-new project that has not been planned in the vault.
cmd_pretool_gate() {
  local v
  v="$(get_vault)"
  if [ -z "$v" ] || [ ! -f "$v/INDEX.md" ]; then return 0; fi
  ENGRAM_VAULT="$v" python3 -I "$PLUGIN_ROOT/scripts/gate.py" || true
}

case "${1:-}" in
  set) shift; cmd_set "$@" ;;
  get) cmd_get ;;
  init) cmd_init ;;
  status) cmd_status ;;
  session-start) cmd_session_start ;;
  prompt-submit) cmd_prompt_submit ;;
  pretool-gate) cmd_pretool_gate ;;
  *) echo "usage: engram.sh {set <path>|get|init|status|session-start|prompt-submit|pretool-gate}" >&2; exit 2 ;;
esac
