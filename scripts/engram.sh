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
  # -n: never overwrite files that already exist in the vault.
  cp -rn "$TEMPLATE_DIR"/. "$v"/
  # Fill date placeholders only in files that still contain them.
  grep -rlF '{{init_date}}' "$v" --include='*.md' 2>/dev/null | while read -r f; do
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
Read $v/INDEX.md first when you need stored context, then follow wikilinks down through the section overviews. Use the engram:remember and engram:recall skills to write and search. Inbox has $inbox unsorted note(s)$( [ "$inbox" -gt 0 ] && echo " (offer engram:triage-inbox)" ).
EOF
}

case "${1:-}" in
  set) shift; cmd_set "$@" ;;
  get) cmd_get ;;
  init) cmd_init ;;
  status) cmd_status ;;
  session-start) cmd_session_start ;;
  *) echo "usage: engram.sh {set <path>|get|init|status|session-start}" >&2; exit 2 ;;
esac
