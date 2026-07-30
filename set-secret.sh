#!/usr/bin/env bash
# =============================================================================
#  MUNI-PAL — set one secret into secrets/muni-pal.enc.env
# =============================================================================
#      ./set-secret.sh STRIPE_SECRET_KEY
#
#  Prompts silently, then re-encrypts. The value is never echoed, never passed
#  as a command-line argument (argv is visible to any process listing — the
#  exact flaw noted against the cloudflared tunnel token), and never written to
#  disk in plaintext: the updated file goes to SOPS over stdin.
#
#  Writer-side only. Run this on Stephen's laptop, which holds the sole age
#  identity in .sops.yaml.
# =============================================================================

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECRETS_FILE="$PROJECT_ROOT/secrets/muni-pal.enc.env"
SOPS_CONFIG="$PROJECT_ROOT/.sops.yaml"

: "${SOPS_AGE_KEY_FILE:=C:\\Users\\st3ja\\.config\\sops\\age\\keys.txt}"
export SOPS_AGE_KEY_FILE
SOPS_BIN="$(command -v sops || echo "$HOME/bin/sops.exe")"

NAME="${1:-}"
if [ -z "$NAME" ]; then
  echo "Usage: ./set-secret.sh <SLOT_NAME>" >&2
  echo "Slots: $("$SOPS_BIN" decrypt "$SECRETS_FILE" 2>/dev/null | sed $'1s/^\xEF\xBB\xBF//' | cut -d= -f1 | paste -sd, -)" >&2
  exit 1
fi

printf 'Value for %s (input hidden): ' "$NAME" >&2
IFS= read -rs VALUE
echo >&2
if [ -z "$VALUE" ]; then echo "Empty value, aborting." >&2; exit 1; fi

# Reject a pasted value that still carries a shell prompt or quotes — a common
# copy/paste artifact that silently produces a key that authenticates nowhere.
case "$VALUE" in
  *' '*|*'"'*|*"'"*) echo "Value contains a space or quote. Aborting — check the paste." >&2; exit 1 ;;
esac

CURRENT="$("$SOPS_BIN" decrypt "$SECRETS_FILE" 2>/dev/null | sed $'1s/^\xEF\xBB\xBF//')"
if [ -z "$CURRENT" ]; then echo "Could not decrypt $SECRETS_FILE" >&2; exit 1; fi

UPDATED="$(NAME="$NAME" VALUE="$VALUE" python -c '
import os, sys
name, value = os.environ["NAME"], os.environ["VALUE"]
lines = sys.stdin.read().splitlines()
out, seen = [], False
for line in lines:
    if line.split("=", 1)[0].strip() == name:
        out.append(f"{name}={value}"); seen = True
    else:
        out.append(line)
if not seen:
    out.append(f"{name}={value}")
sys.stdout.write("\n".join(out) + "\n")
' <<< "$CURRENT")"

# Encrypt over stdin with --filename-override so the creation_rules path_regex
# still matches, without ever materialising plaintext on disk.
#
# Pass NO filename argument — that is what makes sops read stdin. Do not write
# `/dev/stdin`: on Windows sops resolves it to the literal path C:\proc\self\fd\0
# and fails with "cannot operate on non-existent file".
NEW_CIPHERTEXT="$(printf '%s' "$UPDATED" | "$SOPS_BIN" --config "$SOPS_CONFIG" encrypt --filename-override "$SECRETS_FILE")"
if [ -z "$NEW_CIPHERTEXT" ]; then echo "Encryption produced nothing; leaving the file untouched." >&2; exit 1; fi

printf '%s' "$NEW_CIPHERTEXT" > "$SECRETS_FILE"

# Prove the round-trip before declaring success — a file that encrypts but does
# not decrypt is worse than no change at all.
if "$SOPS_BIN" decrypt "$SECRETS_FILE" >/dev/null 2>&1; then
  echo "OK: $NAME set. Verify with  ./secrets.sh list" >&2
else
  echo "FAILED: the file no longer decrypts. Restore it with: git checkout -- $SECRETS_FILE" >&2
  exit 1
fi
