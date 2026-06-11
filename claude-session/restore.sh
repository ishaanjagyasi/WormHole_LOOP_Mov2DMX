#!/usr/bin/env bash
# Restore this project's Claude Code chat history on a new machine so you can
# `claude --resume` exactly where you left off.
#
# Usage:  cd into the repo, then:  bash claude-session/restore.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$HERE/.." && pwd)"

# Claude Code stores transcripts at
#   ~/.claude/projects/<encoded-project-path>/<session-id>.jsonl
# where <encoded-project-path> is the project's absolute path with every
# non-alphanumeric character replaced by a dash.
ENCODED="$(printf '%s' "$PROJECT_DIR" | sed 's/[^A-Za-z0-9]/-/g')"
DEST="$HOME/.claude/projects/$ENCODED"

mkdir -p "$DEST"
cp "$HERE"/*.jsonl "$DEST"/
chmod 600 "$DEST"/*.jsonl 2>/dev/null || true

echo "Restored chat history into:"
echo "    $DEST"
echo
echo "Now, from  $PROJECT_DIR  run one of:"
echo "    claude --resume                 # pick from a list"
for f in "$HERE"/*.jsonl; do
  id="$(basename "$f" .jsonl)"
  echo "    claude --resume $id   # jump straight back into this chat"
done
