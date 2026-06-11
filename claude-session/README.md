# Claude Code session backup

This folder lets you **resume this Claude Code chat on any computer**.

Claude Code keeps each conversation as a `.jsonl` transcript under
`~/.claude/projects/<encoded-project-path>/` on the machine where it ran — *not*
inside the project. This folder carries a copy of that transcript (plus the
project's `.claude/settings.local.json`, tracked at the repo root) so it travels
with the repo.

## Resume on a new machine

```bash
git clone <this-repo-url> WormHole_LOOP_Mov2DMX
cd WormHole_LOOP_Mov2DMX

bash claude-session/restore.sh     # copies the transcript into ~/.claude/projects/
claude --resume                    # then pick this conversation
```

`restore.sh` computes the right `~/.claude/projects/...` location from wherever
you cloned the repo, so it works even if the path differs from the original Mac.

## Save newer progress back into the repo

The committed transcript is a **point-in-time snapshot**. After chatting more,
update it and push:

```bash
bash claude-session/backup.sh
git add claude-session && git commit -m "sync chat history" && git push
```

## Notes & caveats

- **Snapshot lag:** the very last message or two of a live session may not be
  flushed to disk yet when you back up. Re-run `backup.sh` after the session
  fully ends for a complete copy.
- **Same account:** resume works when signed into the same Claude account, with
  a reasonably current Claude Code version.
- **Privacy:** the `.jsonl` is the full conversation (commands, file contents,
  output). Keep this repo **private**.
