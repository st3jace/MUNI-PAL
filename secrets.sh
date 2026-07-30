#!/usr/bin/env bash
# =============================================================================
#  MUNI-PAL — secrets helper
# =============================================================================
#  Reads secrets/muni-pal.enc.env (SOPS + age) and injects them as environment
#  variables. Same shape as CHAMPION SOCIAL/secrets.sh and arthur/secrets.sh —
#  house standard, do not reinvent.
#
#      ./secrets.sh doctor                   check this machine can decrypt
#      ./secrets.sh list                     show slots + whether filled
#      ./secrets.sh get RESEND_API_KEY       print one value
#      ./secrets.sh run uvicorn munipal.main:app --reload
#
#  WHY the app still works: munipal.config.Settings orders its sources
#  init > env > dotenv, so a value injected here beats anything left in .env.
#  That is what lets the Resend key live in SOPS while the rest of .env has
#  not migrated yet.
#
#  TO CHANGE A SECRET (laptop is the only writer):
#      sops decrypt secrets/muni-pal.enc.env > /tmp/x.enc.env
#      # edit /tmp/x.enc.env
#      sops --config .sops.yaml encrypt /tmp/x.enc.env > secrets/muni-pal.enc.env
#      rm /tmp/x.enc.env
#  Never byte-edit the encrypted file directly — the MAC covers key names and
#  editing makes it permanently undecryptable.
# =============================================================================

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_FILE="$PROJECT_ROOT/secrets/muni-pal.enc.env"
SOPS_CONFIG="$PROJECT_ROOT/.sops.yaml"
UNSET_SENTINEL="__UNSET__"

# Explicit key path: scheduled tasks run without a logon session and do not
# reliably resolve the same profile defaults an interactive shell does.
: "${SOPS_AGE_KEY_FILE:=C:\\Users\\st3ja\\.config\\sops\\age\\keys.txt}"
export SOPS_AGE_KEY_FILE

SOPS_BIN="$(command -v sops || echo "$HOME/bin/sops.exe")"

ok()   { printf '  [ok]   %s\n' "$1"; }
bad()  { printf '  [FAIL] %s\n' "$1"; }
warn() { printf '  [warn] %s\n' "$1"; }

decrypt_all() {
  # SOPS on Windows emits a UTF-8 BOM that fuses onto the FIRST variable name,
  # so `grep '^RESEND_API_KEY='` silently misses. PowerShell hides this because
  # it strips BOMs when decoding; git-bash does not. Do not remove this sed.
  "$SOPS_BIN" decrypt "$SECRETS_FILE" 2>/dev/null | sed $'1s/^\xEF\xBB\xBF//'
}

mask() {
  local v="$1"
  if [ -z "$v" ]; then echo "(empty)"; return; fi
  if [ "$v" = "$UNSET_SENTINEL" ]; then echo "(not set)"; return; fi
  if [ ${#v} -le 8 ]; then printf '%*s\n' ${#v} '' | tr ' ' '*'; return; fi
  echo "${v:0:4}******${v: -4}"
}

cmd_doctor() {
  echo ""
  echo "MUNI-PAL - secrets health check"
  local fail=0

  if [ -x "$SOPS_BIN" ] || command -v sops >/dev/null 2>&1; then ok "sops found at $SOPS_BIN"
  else bad "sops not found"; fail=$((fail+1)); fi

  local winkey="${SOPS_AGE_KEY_FILE//\\//}"
  winkey="${winkey/C:/\/c}"
  if [ -f "$winkey" ]; then ok "age identity present ($SOPS_AGE_KEY_FILE)"
  else bad "no age identity at $SOPS_AGE_KEY_FILE"; fail=$((fail+1)); fi

  [ -f "$SOPS_CONFIG" ]  && ok ".sops.yaml present"  || { bad ".sops.yaml missing"; fail=$((fail+1)); }
  [ -f "$SECRETS_FILE" ] && ok "secrets file present" || { bad "secrets file missing"; fail=$((fail+1)); }

  if [ $fail -eq 0 ]; then
    local out
    out="$(decrypt_all)"
    if [ -n "$out" ]; then
      ok "decrypt round-trip OK ($(echo "$out" | grep -c '=') values)"
      local missing
      missing="$(echo "$out" | grep "=${UNSET_SENTINEL}$" | cut -d= -f1 | paste -sd, -)"
      [ -n "$missing" ] && warn "still unset: $missing" || ok "all slots filled"
    else
      bad "decrypt FAILED - this machine's key is probably not a recipient."
      bad "Fix: add this machine's public key to .sops.yaml, then"
      bad "     sops updatekeys secrets/muni-pal.enc.env"
      fail=$((fail+1))
    fi
  fi

  echo ""
  if [ $fail -eq 0 ]; then echo "HEALTHY"; else echo "$fail problem(s) found"; return 1; fi
}

cmd_list() {
  echo ""
  printf '  %-38s %-12s %s\n' "SLOT" "STATUS" "PREVIEW"
  printf '  %s\n' "$(printf '%.0s-' {1..70})"
  local line name val status
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac
    name="${line%%=*}"; val="${line#*=}"
    if [ "$val" = "$UNSET_SENTINEL" ]; then status="not set"; else status="SET"; fi
    printf '  %-38s %-12s %s\n' "$name" "$status" "$(mask "$val")"
  done < <(decrypt_all)
  echo ""
}

cmd_get() {
  local name="${1:-}"
  [ -z "$name" ] && { echo "Usage: ./secrets.sh get <SLOT_NAME>" >&2; return 1; }
  local out; out="$(decrypt_all | grep "^${name}=")"
  [ -z "$out" ] && { echo "'$name' not found. Try: ./secrets.sh list" >&2; return 1; }
  echo "$out"
}

cmd_run() {
  [ $# -eq 0 ] && { echo "Usage: ./secrets.sh run <command> [args...]" >&2; return 1; }
  local injected=0 skipped=""
  local line name val
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac
    name="${line%%=*}"; val="${line#*=}"
    if [ "$val" = "$UNSET_SENTINEL" ]; then skipped="$skipped $name"; continue; fi
    export "$name=$val"
    injected=$((injected+1))
  done < <(decrypt_all)

  echo "  Injected $injected secret(s)." >&2
  [ -n "$skipped" ] && echo "  Not set, not injected:$skipped" >&2
  cd "$PROJECT_ROOT" || return 1
  exec "$@"
}

case "${1:-help}" in
  doctor) cmd_doctor ;;
  list|ls) cmd_list ;;
  get)    shift; cmd_get "$@" ;;
  run)    shift; cmd_run "$@" ;;
  *)
    cat <<'EOF'

MUNI-PAL - secrets helper

  ./secrets.sh doctor            Check this machine can decrypt. Start here.
  ./secrets.sh list              Show slots and whether they are filled.
  ./secrets.sh get <SLOT>        Print one value.
  ./secrets.sh run <command...>  Run a command with secrets injected.

Only the Resend credential has migrated so far. Stripe, Anthropic, JWT and
Postgres are still plaintext in .env — see SECRETS-REGISTRY.md waves 1-2.

EOF
    ;;
esac
