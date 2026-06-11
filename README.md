# WormHole LOOP — Movie → DMX (private)

Full working setup for the WormHole LOOP show: a movie-to-DMX player that
streams video out as Art-Net pixel data, a 3D simulator, the TouchDesigner
receiver, and the show media.

| File | Purpose |
|------|---------|
| `cylinder_player.py` | Plays `show.mov` (+ `track.wav`) out as Art-Net to a 16×150 LED cylinder. |
| `cylinder_sim.py`    | 3D simulator — renders the LEDs locally so you can preview with no hardware. |
| `DMX_to_RGB_tox.tox` | TouchDesigner receiver component. |
| `show.mov` / `track.wav` | The show media. |
| `claude-session/`    | Backup of the Claude Code chat so it can be resumed on any machine (see below). |

> The public, generic template version of this player lives in its own repo:
> **[video-to-artnet-dmx](https://github.com/ishaanjagyasi/video-to-artnet-dmx)**.

## Resume the Claude Code chat on another computer

This repo carries the Claude Code conversation transcript, so you can pick the
chat back up from any machine:

```bash
git clone https://github.com/ishaanjagyasi/WormHole_LOOP_Mov2DMX.git
cd WormHole_LOOP_Mov2DMX
bash claude-session/restore.sh
claude --resume 540c064a-7c1a-4c26-a669-4253dc79fbe6
```

`restore.sh` derives the correct `~/.claude/projects/` path from wherever you
clone, so it works even if the folder location differs from the original Mac.

After chatting more, save the newer history back into the repo:

```bash
bash claude-session/backup.sh
git add claude-session && git commit -m "sync chat history" && git push
```

See [`claude-session/README.md`](claude-session/README.md) for details and caveats.

## Run the show

```bash
# 1. (optional) preview locally — in one terminal:
python cylinder_sim.py

# 2. play the show out as Art-Net — in another terminal:
python cylinder_player.py
```

Edit the config block at the top of `cylinder_player.py` (`TARGET_IP`,
`SOURCE_IP`, `NUM_STRIPS`, `PIXELS`, …) to match your network and rig.

> **Note:** the committed `.venv/` is not included — it's a Windows-only,
> 385 MB environment. Recreate it from the public repo's `requirements.txt`.
