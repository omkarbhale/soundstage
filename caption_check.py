# Prove a caption track says its script, and is readable at the pace it plays.
#
#   python3 caption_check.py --style <style.json> <narration.txt> --in <finished.mp4>
#   python3 caption_check.py --style <style.json> <narration.txt> <captions.srt>
#
# The narration guards exist because the faults they catch are silent (ADR-0007), and
# a caption's faults are the quietest of the lot: a subtitle track is off by default in
# most players, so nobody watching the review copy sees it at all. What ships is then
# a file that looks finished and says something the narrator did not - or says nothing,
# because the mux failed and the video is simply uncaptioned.
#
# `--in` IS THE ONE THAT MATTERS, and it exists because captions live in the video and
# nowhere else (see `captions.py`). It reads the subtitle stream back out of the
# finished file and proves the five things below about THAT, not about an intermediate
# that may never have reached it. Anything that re-encodes or trims the file afterwards
# drops the track silently, so this is what to re-run after any such pass.
#
#   THE TRACK IS THERE, AND IT IS ENGLISH. A mux that failed leaves a playable video
#   with no captions in it, which is exactly the confident wrong answer this repo
#   refuses to ship.
#
#   THE CAPTIONS SAY THE SCRIPT. Every word of `narration.txt`, in order, with nothing
#   added and nothing lost. This is what refuses a caption built from the transcript's
#   own text - the aligner's "Scream" for "Screen", "Tierra" for "Tier A" - and it is
#   also what refuses a track left behind by a script that was edited afterwards.
#
#   THE TIMES ARE A TIMELINE. Increasing, non-overlapping, each cue with a duration,
#   and the last cue out before the video ends rather than after it.
#
#   THE LINES FIT, at whatever length the production chose. An extra line covers
#   picture, and a course like this one puts figures under the caption band.
#
#   NOBODY IS READING AT THE PRODUCTION'S `hard_cps`. Above it a cue is gone before it
#   is read, and the words are lost as surely as if they were missing.
#
#   NOTHING THE PRODUCTION NAMED IS CUT IN HALF. "the session chip" must never arrive
#   as "the session" and then "chip", and a course whose value is precision about names
#   cannot ship one that does.
#
# Reading rate is the one measure that is partly the narrator's rather than the
# generator's: a fast delivery produces a fast caption and nothing downstream can slow
# it without going out of sync. So it is reported at `fast_cps` and refused only at
# `hard_cps`, where the caption has stopped being readable at all.
#
# EVERY NUMBER IS THE CALLER'S, in the same `--style` file `captions.py` reads - the
# guard and the generator must not be able to disagree about what the rules are.
# ADR-0011 records why, and why the track is the thing that gets checked.
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

# What this guard needs on top of what `captions.py` needs. Required, every one.
STYLE_KEYS = {
    "line_chars": "characters a line",
    "lines": "lines a cue",
    "fast_cps": "characters a second above which a cue is reported as fast",
    "hard_cps": "characters a second above which a cue is refused as unreadable",
    "language": "the language tag the muxed track must carry",
    "keep_together": "phrases that must never be split across two cues",
}


def load_style(path):
    style = json.load(open(path, encoding="utf8"))
    missing = [k for k in STYLE_KEYS if k not in style]
    if missing:
        sys.exit(f"{path} is missing " + ", ".join(f"{k!r} ({STYLE_KEYS[k]})" for k in missing))
    return style


def norm(s):
    w = re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).lower())
    return w[:-1] if len(w) > 3 and w.endswith("s") else w


def words(s):
    return re.sub(r"\s+", " ", s).strip().split(" ")


def parse(text, where):
    """SRT, strictly enough to reject something that is not one."""
    out = []
    for b in re.split(r"\n\s*\n", text.strip()):
        lines = [x for x in b.strip().split("\n") if x.strip() != ""]
        if len(lines) < 3:
            sys.exit(f"{where}: cue {lines[0] if lines else '?'} has no text")
        m = re.match(r"(\d\d):(\d\d):(\d\d)[,.](\d\d\d) --> (\d\d):(\d\d):(\d\d)[,.](\d\d\d)", lines[1])
        if not m:
            sys.exit(f"{where}: cue {lines[0]} has no timing line")
        g = [int(x) for x in m.groups()]
        out.append({
            "n": lines[0].strip(),
            "start": g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000,
            "end": g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000,
            "lines": lines[2:],
        })
    return out


def probe(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                        "-of", "json", video], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{video}: cannot be read - "
                 f"{r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'ffprobe failed'}")
    return json.loads(r.stdout)


def read_track(video):
    """Pull the muxed subtitle stream out as SRT, so the thing checked is the thing
    that shipped rather than an intermediate that may never have reached the file."""
    d = probe(video)
    dur = float(d["format"]["duration"])
    subs = [s for s in d["streams"] if s["codec_type"] == "subtitle"]
    if not subs:
        sys.exit(f"{video}: carries NO subtitle track. The mux did not happen, or a later "
                 f"pass over this file dropped it - re-run captions.py --into.")
    if len(subs) > 1:
        sys.exit(f"{video}: carries {len(subs)} subtitle tracks; expected one")
    lang = (subs[0].get("tags") or {}).get("language", "")
    tmp = os.path.join(tempfile.mkdtemp(), "track.srt")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-map", "0:s:0",
                        "-c:s", "srt", "-f", "srt", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{video}: the subtitle track is there but cannot be read back:\n{r.stderr.strip()}")
    text = open(tmp, encoding="utf8").read()
    os.unlink(tmp)
    return text, lang, dur


def main(argv):
    style_path = None
    if "--style" in argv:
        i = argv.index("--style")
        style_path = argv[i + 1]
        del argv[i:i + 2]
    if not style_path:
        sys.exit("--style <style.json> is required, and it is the same file captions.py "
                 "was given: the guard and the generator must not be able to disagree "
                 "about what the rules are.")
    style = load_style(style_path)
    video = None
    if "--in" in argv:
        i = argv.index("--in")
        video = argv[i + 1]
        del argv[i:i + 2]

    faults, fast = [], 0
    if video:
        if len(argv) != 1:
            sys.exit("usage: caption_check.py --style <style.json> <narration.txt> "
                     "--in <finished.mp4>")
        script_path, = argv
        text, lang, dur = read_track(video)
        where = f"{video}  (subtitle track)"
        cues = parse(text, where)
        if lang != style["language"]:
            faults.append(f"the track is tagged language {lang!r}, "
                          f"expected {style['language']!r}")
        if cues and cues[-1]["end"] > dur + 0.5:
            faults.append(f"the last cue is out at {cues[-1]['end']:.2f}s, "
                          f"after the video ends at {dur:.2f}s")
    else:
        if len(argv) != 2:
            sys.exit("usage: caption_check.py --style <style.json> <narration.txt> "
                     "--in <finished.mp4>\n"
                     "       caption_check.py --style <style.json> <narration.txt> "
                     "<captions.srt>")
        script_path, where = argv
        cues = parse(open(where, encoding="utf8").read(), where)

    if not cues:
        sys.exit(f"{where}: no cues")

    # 1. the captions say the script
    want = words(open(script_path, encoding="utf8").read())
    got = words(" ".join(" ".join(c["lines"]) for c in cues))
    if want != got:
        n = min(len(want), len(got))
        at = next((k for k in range(n) if want[k] != got[k]), n)
        faults.append(
            f"the captions do not say the script: {len(want)} script words, {len(got)} captioned, "
            f"first difference at word {at + 1}\n"
            f"      script:  ...{' '.join(want[max(0, at - 4):at + 5])}...\n"
            f"      caption: ...{' '.join(got[max(0, at - 4):at + 5])}...")

    # 2. the times are a timeline
    prev = None
    for c in cues:
        if c["end"] <= c["start"]:
            faults.append(f"cue {c['n']}: ends at or before it starts")
        if prev is not None and c["start"] < prev["end"]:
            faults.append(f"cue {c['n']}: starts before cue {prev['n']} has gone")
        prev = c

    # 3. the lines fit
    for c in cues:
        if len(c["lines"]) > style["lines"]:
            faults.append(f"cue {c['n']}: {len(c['lines'])} lines (limit {style['lines']})")
        for ln in c["lines"]:
            if len(ln) > style["line_chars"]:
                faults.append(f"cue {c['n']}: a line is {len(ln)} characters "
                              f"(limit {style['line_chars']}) - {ln!r}")

    # 4. the pace is readable
    for c in cues:
        cps = len(" ".join(c["lines"])) / max(0.001, c["end"] - c["start"])
        if cps > style["hard_cps"]:
            faults.append(f"cue {c['n']}: {cps:.0f} characters a second "
                          f"(unreadable above {style['hard_cps']:.0f})")
        elif cps > style["fast_cps"]:
            fast += 1

    # 5. nothing the production named is cut in half
    edges = set()
    keys, at = [], 0
    for c in cues:
        toks = [norm(t) for t in " ".join(c["lines"]).split() if norm(t)]
        keys += toks
        at += len(toks)
        edges.add(at)
    for phrase in style["keep_together"]:
        want = [norm(t) for t in phrase.split() if norm(t)]
        if len(want) < 2:
            continue
        for i in range(len(keys) - len(want) + 1):
            if keys[i:i + len(want)] == want and edges & set(range(i + 1, i + len(want))):
                faults.append(f"{phrase!r} is split across two cues")

    print(where)
    print(f"  {len(cues)} cues, {len(got)} words, last out {cues[-1]['end']:.2f}s"
          + (f", video {dur:.2f}s, language {lang}" if video else ""))
    if fast:
        print(f"  {fast} cue(s) above {style['fast_cps']:.0f} characters a second "
              f"- the narrator's pace, not a fault")
    for f in faults:
        print(f"  FAULT {f}")
    if faults:
        sys.exit(f"{len(faults)} caption fault(s)")
    print("  the captions say the script, and every cue fits and holds")


if __name__ == "__main__":
    main(sys.argv[1:])
