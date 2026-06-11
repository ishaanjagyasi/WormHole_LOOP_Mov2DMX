#!/usr/bin/env bash
# Snapshot the LATEST Claude Code chat transcript(s) for this project back into
# the repo, so you can commit & push an up-to-date copy.
#
# Usage:  cd into the repo, then:  bash claude-session/backup.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$HERE/.." && pwd)"

ENCODED="$(printf '%s' "$PROJECT_DIR" | sed 's/[^A-Za-z0-9]/-/g')"
SRC="$HOME/.claude/projects/$ENCODED"

if ! ls "$SRC"/*.jsonl >/dev/null 2>&1; then
  echo "No transcripts found in $SRC" >&2
  exit 1
fi

cp "$SRC"/*.jsonl "$HERE"/
echo "Updated transcript(s) in $HERE"
echo
echo "Commit & push to save them:"
echo "    git add claude-session && git commit -m 'sync chat history' && git push"
