# Guard 2: repair collapsed word runs before any cue is derived from a timing.
#
#   python3 repair.py narration.mp3 raw.json transcript.json
#
# whisper-1 loses word alignment over a stretch of an otherwise fine file,
# collapsing a run of ~10 words into one multi-second token. It is reproducible
# for a given file - re-transcribing it or re-encoding to 16k mono returns the
# same collapse - while transcribing that window alone reads the words back
# correctly. The audio is intact, so the fix is to re-measure that window and
# splice its real timings back in. Still real timing from the single-pass
# narration, just measured twice (ADR-0003: every cue comes from the real audio,
# never from a hand-timed guess).
#
# Every cue derived from inside a collapsed run lands on the wrong beat, and the
# frame looks finished either way. Run this before deriving any cue. It prints
# "no repair needed" and passes the timings through when the file is clean, so it
# is safe - and expected - to run on every module.
# The window is re-measured through `transcribe.py`, not through a second client
# of its own: that keeps ONE path to word timings, so this works on whichever
# engine the module was aligned with (ADR-0008) instead of only on OpenAI.
import json, os, subprocess, sys, tempfile

# A flag takes a value, so skip both - counting the value as a positional is how
# "--engine local" turns into one argument too many and a usage error.
def _parse(argv, takes_value, n, usage):
    args, flags, i = [], {}, 0
    while i < len(argv):
        a = argv[i]
        if a in takes_value:
            if i + 1 >= len(argv):
                sys.exit(f"{a} needs a value")
            flags[a] = argv[i + 1]; i += 2; continue
        if a.startswith("--"):
            sys.exit(f"unknown flag {a}")
        args.append(a); i += 1
    if len(args) != n:
        sys.exit(usage)
    return args, flags

(AUDIO, FULL, OUT), FLAGS = _parse(
    sys.argv[1:], {"--engine"}, 3,
    "usage: repair.py <audio> <raw.json> <out.json> [--engine auto|openai|local]")
ENGINE = FLAGS.get("--engine", "auto")
HERE = os.path.dirname(os.path.abspath(__file__))
PAD = 4.0          # seconds of context either side of the bad span
SUSPECT = 1.5      # a word this long is an alignment collapse, not speech

def transcribe(path):
    """Word rows for one clip, from the studio's single transcription path."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out = f.name
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "transcribe.py"),
                            path, out, "--engine", ENGINE],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("repair could not re-measure the window:\n" + (r.stderr or r.stdout).strip())
        return [{"word": w["text"], "start": w["start"], "end": w["end"]}
                for w in json.load(open(out))]
    finally:
        os.path.exists(out) and os.unlink(out)


words = json.load(open(FULL))
bad = [i for i, w in enumerate(words) if w["end"] - w["start"] > SUSPECT]
if not bad:
    json.dump(words, open(OUT, "w"), indent=1); print("no repair needed"); sys.exit()

for i in reversed(bad):
    lo, hi = max(0.0, words[i]["start"] - PAD), words[i]["end"] + PAD
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        clip = f.name
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(lo), "-t", str(hi - lo),
                    "-i", AUDIO, "-c", "copy", clip], check=True)
    win = [{"text": w["word"], "start": round(w["start"] + lo, 3), "end": round(w["end"] + lo, 3)}
           for w in transcribe(clip)]
    os.unlink(clip)
    keep_before = [w for w in words if w["end"] <= lo]
    keep_after  = [w for w in words if w["start"] >= hi]
    inner = [w for w in win if lo <= w["start"] < hi]
    print(f"  repaired {words[i]['text']!r} @{words[i]['start']:.2f} "
          f"({words[i]['end']-words[i]['start']:.2f}s) -> {len(inner)} words from window [{lo:.1f},{hi:.1f}]")
    words = keep_before + inner + keep_after

for n, w in enumerate(words):
    w["id"] = f"w{n}"
json.dump(words, open(OUT, "w"), indent=1)
print(f"wrote {len(words)} words")
