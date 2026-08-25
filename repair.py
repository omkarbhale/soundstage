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
import json, os, subprocess, sys, tempfile, urllib.request

AUDIO, FULL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
KEY = os.environ["OPENAI_API_KEY"]
PAD = 4.0          # seconds of context either side of the bad span
SUSPECT = 1.5      # a word this long is an alignment collapse, not speech

def transcribe(path):
    import uuid
    b = open(path, "rb").read()
    bnd = uuid.uuid4().hex
    parts = []
    for k, v in (("model", "whisper-1"), ("response_format", "verbose_json"),
                 ("timestamp_granularities[]", "word")):
        parts.append(f'--{bnd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{bnd}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\n'
                 f'Content-Type: audio/mpeg\r\n\r\n'.encode() + b + b"\r\n")
    parts.append(f"--{bnd}--\r\n".encode())
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions", data=b"".join(parts),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": f"multipart/form-data; boundary={bnd}"})
    return json.load(urllib.request.urlopen(req))["words"]

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
