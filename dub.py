#!/usr/bin/env python3
"""Fit a new voice to the timing of an existing track, line by line.

    python3 dub.py old-voice.wav clips/ new-voice.wav          # the track
    python3 dub.py old-voice.wav clips/ new-voice.wav --report # the fit, first

`clips/` holds one file per line, named for its index - `line-00.mp3`,
`line-01.mp3`, one for every line `speech_runs.py` finds in the old track.

ADR-0003 makes the narration first and cues the picture from it. A video that
already exists cannot be cued, so a re-voice runs the other way: the old track
is the score and every new line is fitted to the bar the old one occupied. Two
ways of doing that are wrong in ways that reach a finished file and are hard to
see there.

**A speech clip does not start when its file does.** The model leaves a little
silence before the first word and a little after the last, and the amount varies
per request. Place clips by file start and every line begins late by however much
padding that request happened to carry - the track is in sync by the numbers and
the words are behind the picture all the way through. So each clip is trimmed to
its own speech before it is measured or placed.

**Fitting a line INSIDE its slot is not fitting it to the picture.** Starting
each line at the old line's start bounds the error at the line boundaries and
says nothing about the inside of a line, where the picture is moving: a
nineteen-second line read eight per cent quick is a second and a half ahead of
what it is describing by the end, pointing at a panel that has not opened. And it
still ends inside its slot, so nothing measures as wrong. So each line is fitted
to its old line's duration EXACTLY, which holds the voice on the picture across
the line and not only at its edges.

Fitted that way the lines and the silences between them are the old track's, so
the dubbed track is the same length as the old one and the video is untouched -
mux it in with `-c:v copy`.

Same words in, so a line's tempo correction is only the difference between two
speaking rates. Corrections cluster off 1.0 when the whole take is paced wrong,
and the fix for that is the speech request's own `--speed`, not a harder squeeze
here: `--report` prints the tempo the take would need before any audio is
written, and the median of those is the speed factor the take is missing. A line
past TEMPO_LIMIT is refused, because past there the honest fix is a shorter line
and squeezing sounds it.

Holds no content and takes explicit paths (ADR-0004).
"""
import os
import statistics
import subprocess
import sys

from speech_runs import runs

RATE = 48000
TEMPO_LIMIT = 1.35    # past this a squeeze is audible; reword the line instead
TEMPO_FLOOR = 0.70    # and past this a stretch drags
NUDGE = 0.04          # corrections smaller than this are left alone
SYNC_LIMIT = 0.060    # a line's start may miss the old one by this much and no more


def probe(path):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout)


def speech_span(path):
    """First word to last word of a clip - the padding is not the line."""
    lines, total = runs(path)
    return lines[0]["start"], lines[-1]["end"]


def tempo_chain(ratio):
    """atempo, split into legal steps. One filter cannot do every ratio."""
    steps = []
    while ratio > 2.0:
        steps.append(2.0)
        ratio /= 2.0
    while ratio < 0.5:
        steps.append(0.5)
        ratio /= 0.5
    steps.append(ratio)
    return ",".join(f"atempo={s:.6f}" for s in steps)


def measure(old, clips):
    """What each line would need, before anything is written."""
    lines, total = runs(old)
    out = []
    for r in lines:
        clip = os.path.join(clips, f"line-{r['i']:02d}.mp3")
        if not os.path.exists(clip):
            raise SystemExit(f"{clip}: missing - {len(lines)} lines need "
                             f"line-00.mp3 .. line-{len(lines) - 1:02d}.mp3")
        start, end = speech_span(clip)
        spoken = end - start
        out.append({**r, "clip": clip, "trim": (start, end), "spoken": round(spoken, 3),
                    "tempo": round(spoken / r["dur"], 4)})
    return out, total


def build(fit, total, out):
    """One line per slot, the old silences between them, the old total length."""
    inputs, filters, labels = [], [], []
    silence_at, line_at = 0, 0
    at = 0.0
    for r in fit:
        if r["start"] - at > 0.001:
            filters.append(f"aevalsrc=0:d={r['start'] - at:.6f}:s={RATE}:c=stereo[q{silence_at}]")
            labels.append(f"[q{silence_at}]")
            silence_at += 1
        s, e = r["trim"]
        inputs += ["-i", r["clip"]]
        # trimmed to its own speech, fitted to the old line's length exactly,
        # then padded and cut so the slot is filled to the sample either way
        filters.append(
            f"[{line_at}:a]atrim=start={s:.6f}:end={e:.6f},asetpts=N/SR/TB,"
            f"{tempo_chain(r['tempo'])},aresample={RATE},aformat=channel_layouts=stereo,"
            f"apad,atrim=end={r['dur']:.6f},asetpts=N/SR/TB[l{line_at}]")
        labels.append(f"[l{line_at}]")
        line_at += 1
        at = r["start"] + r["dur"]

    if total - at > 0.001:
        filters.append(f"aevalsrc=0:d={total - at:.6f}:s={RATE}:c=stereo[q{silence_at}]")
        labels.append(f"[q{silence_at}]")

    filters.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1[out]")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
                    "-filter_complex", ";".join(filters), "-map", "[out]",
                    "-ar", str(RATE), "-ac", "2", out], check=True)


def confirm(old, new):
    """Read the finished track back and prove its lines land on the old ones.

    Filling every slot to the right length does not prove the words are in it.
    A clip whose lead-in this missed sits late INSIDE a correct slot, and the
    track is then the right length, with the right silences, and late all the
    way through - which the durations cannot see. So the finished file is
    measured the same way the old one was, and the two grids compared.
    """
    a, _ = runs(old)
    b, _ = runs(new)
    if len(a) != len(b):
        raise SystemExit(f"{new}: reads as {len(b)} lines against the old track's {len(a)} - "
                         "lines have run together or split, do not mux this")
    off = [(abs(x["start"] - y["start"]), x["i"]) for x, y in zip(a, b)]
    worst, where = max(off)
    if worst > SYNC_LIMIT:
        raise SystemExit(f"{new}: line {where} starts {worst * 1000:.0f}ms off the old track "
                         f"(limit {SYNC_LIMIT * 1000:.0f}ms) - do not mux this")
    return worst, where


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 3:
        raise SystemExit(__doc__)
    old, clips, out = args

    fit, total = measure(old, clips)
    tempos = [r["tempo"] for r in fit]

    print(f"  {'line':>4}  {'slot':>7}  {'spoken':>7}  {'tempo':>6}")
    for r in fit:
        mark = "  <-- past the limit" if not TEMPO_FLOOR <= r["tempo"] <= TEMPO_LIMIT else ""
        print(f"  {r['i']:>4}  {r['dur']:>7.3f}  {r['spoken']:>7.3f}  {r['tempo']:>6.3f}{mark}")
    med = statistics.median(tempos)
    print(f"\n{len(fit)} lines, tempo {min(tempos):.3f}..{max(tempos):.3f}, median {med:.3f}")
    if abs(med - 1) > NUDGE:
        print(f"the take is paced {'fast' if med > 1 else 'slow'} as a whole - "
              f"regenerate it at --speed {1 / med:.2f} and the per-line corrections shrink")

    over = [r for r in fit if not TEMPO_FLOOR <= r["tempo"] <= TEMPO_LIMIT]
    if over:
        raise SystemExit(
            f"\n{len(over)} line(s) outside {TEMPO_FLOOR}..{TEMPO_LIMIT}: "
            + ", ".join(f"{r['i']} ({r['tempo']:.2f})" for r in over)
            + "\nA squeeze that hard is audible. Shorten the line, or re-read it, "
              "rather than fitting it here.")

    if "--report" in argv:
        return
    build(fit, total, out)
    made = probe(out)
    if abs(made - total) > 0.05:
        raise SystemExit(f"{out}: {made:.3f}s against the old track's {total:.3f}s - "
                         "the slots did not add up, do not mux this")
    worst, where = confirm(old, out)
    print(f"\nwrote {out} - {made:.3f}s against the old track's {total:.3f}s, "
          f"every line within {worst * 1000:.0f}ms (line {where})")


if __name__ == "__main__":
    main(sys.argv)
