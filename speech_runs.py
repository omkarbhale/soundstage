# The lines of a finished track, measured - the grid a re-voice is fitted to.
#
#   python3 speech_runs.py voice.mp3            # the table
#   python3 speech_runs.py voice.mp3 --json     # for dub.py
#
# Re-voicing an existing video inverts the usual order. Normally the narration is
# made first and the visuals are cued from it (ADR-0003); here the picture is
# already cut and the voice has to land where the old one did, so the old track
# is the timing and this is what reads it out.
#
# A track assembled from one clip per line has digital silence between the lines,
# and the runs of sound in it are the lines. Two things about inverting
# silencedetect are wrong in ways that survive to a finished file:
#
# 1. silencedetect reports where each silence STARTS and where it ENDS, and it is
#    the END that is a line's start. Read the starts alone and every line is
#    placed at the end of the pause before it, early by most of a second, which
#    sounds like the narrator talking over the previous beat.
#
# 2. A speaker pauses INSIDE a sentence. Those pauses are short and the gaps
#    between lines are long, but both are silence and nothing distinguishes them
#    except length. Split on a pause inside a sentence and that sentence is handed
#    to the speech model as two fragments, which it reads with the falling
#    intonation of two finished sentences - and the assembled track is in sync,
#    on the right words, and still sounds wrong. So runs closer together than
#    MERGE are one line.
#
# Prints each line's start, end and the silence after it. The silence after is
# the room a re-voiced line may run into without moving the next one (dub.py
# spends it), so it is measured here rather than assumed to be the same gap
# everywhere.
#
# Holds no content and takes an explicit path (ADR-0004).
import json
import re
import subprocess
import sys

NOISE = "-50dB"   # below any speech, above the noise floor of a real recording
MIN = 0.20        # a silence shorter than this is inside a word, not around it
MERGE = 0.50      # runs closer than this are one line with a pause in it


def duration(path):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout)


def silences(path, noise=NOISE, mindur=MIN):
    """Every silence in the file, as (start, end). EOF closes a trailing one."""
    err = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path,
         "-af", f"silencedetect=noise={noise}:d={mindur}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    out, start = [], None
    # Parsed in order of appearance: a start is only closed by the end that
    # follows it, and the last silence is closed at EOF rather than left open.
    for kind, value in re.findall(r"silence_(start|end):\s*([\d.]+)", err):
        if kind == "start":
            start = float(value)
        elif start is not None:
            out.append((start, float(value)))
            start = None
    return out


def runs(path, noise=NOISE, mindur=MIN, merge=MERGE):
    """The lines of the track: sound between the silences, short pauses folded in."""
    total = duration(path)
    spans, at = [], 0.0
    for s, e in silences(path, noise, mindur):
        if s > at:
            spans.append([at, s])
        at = e
    if total - at > 0.01:
        spans.append([at, total])
    if not spans:
        raise SystemExit(f"{path}: no sound above {noise} - nothing to re-voice")

    lines = [spans[0]]
    for s, e in spans[1:]:
        if s - lines[-1][1] < merge:   # a pause inside a sentence, not a line break
            lines[-1][1] = e
        else:
            lines.append([s, e])

    return [{"i": n, "start": round(s, 3), "end": round(e, 3),
             "dur": round(e - s, 3),
             "gap_after": round((lines[n + 1][0] if n + 1 < len(lines) else total) - e, 3)}
            for n, (s, e) in enumerate(lines)], total


def main(argv):
    paths = [a for a in argv[1:] if not a.startswith("--")]
    if len(paths) != 1:
        raise SystemExit(__doc__)
    lines, total = runs(paths[0])

    if "--json" in argv:
        print(json.dumps(lines, indent=1))
        return

    print(f"  {'line':>4}  {'start':>8}  {'end':>8}  {'spoken':>7}  {'silence after':>13}")
    for r in lines:
        print(f"  {r['i']:>4}  {r['start']:>8.3f}  {r['end']:>8.3f}  "
              f"{r['dur']:>7.3f}  {r['gap_after']:>13.3f}")
    spoken = sum(r["dur"] for r in lines)
    print(f"\n{len(lines)} lines, {spoken:.1f}s spoken of {total:.1f}s "
          f"({100 * spoken / total:.0f}%)")


if __name__ == "__main__":
    main(sys.argv)
