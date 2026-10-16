#!/usr/bin/env bash
# Usage: peer.sh <codex|claude> <state-dir> <message-file>
# Sends one turn to the reviewer session: the first call starts it, later calls resume it.
# Writes the reply to <message-file minus .md>.reply.md and prints it.
set -euo pipefail
peer=$1 dir=$2 msg=$3
sid_file="$dir/$peer.session"
reply="${msg%.md}.reply.md"

case $peer in
  codex)
    model=gpt-6-astra
    if [[ -s $sid_file ]]; then
      codex exec resume "$(cat "$sid_file")" -m "$model" -c sandbox_mode=read-only --json \
        -o "$reply" - <"$msg" >/dev/null
    else
      codex exec -m "$model" -s read-only --json -o "$reply" - <"$msg" \
        | sed -n 's/.*"type":"thread.started","thread_id":"\([^"]*\)".*/\1/p' >"$sid_file"
    fi
    ;;
  claude)
    resume=()
    [[ -s $sid_file ]] && resume=(--resume "$(cat "$sid_file")")
    claude -p --model claude-opus-5-5 --output-format json --permission-mode dontAsk \
      --allowedTools Read Grep Glob "Bash(git diff:*)" "Bash(git log:*)" "Bash(git show:*)" \
      ${resume[@]+"${resume[@]}"} <"$msg" >"$dir/claude.out.json"
    python3 - "$dir/claude.out.json" "$sid_file" "$reply" <<'PY'
import json, sys
out = json.load(open(sys.argv[1]))
open(sys.argv[2], "w").write(out["session_id"])
open(sys.argv[3], "w").write(out["result"])
sys.exit(1 if out.get("is_error") else 0)
PY
    ;;
  *) echo "unknown peer: $peer" >&2; exit 2 ;;
esac

[[ -s $reply ]] || { echo "empty reply from $peer" >&2; exit 1; }
cat "$reply"
