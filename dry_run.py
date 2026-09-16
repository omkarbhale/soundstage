# Prove a composition builds before you spend the narration on it.
#
#   python3 dry_run.py narration.txt <composition-dir>
#
# A composition reads its module's transcript to place every reveal, so nothing
# about it can be run until the audio exists - and the audio is the expensive,
# non-deterministic part (README, "Making narration"). That ordering hides a
# whole class of fault until the worst moment: a generator that raises, a cue
# that names no moment or two, a duplicate id. None of them are about the audio,
# and all of them are found after it has been paid for.
#
# So this writes a SYNTHETIC transcript from the script - the same words at a
# steady rate, with the tail files the generator expects - and you run the
# generator and both guards against it. Every fault that is a property of the
# composition rather than of the recording surfaces now.
#
# It spells the synthetic transcript the way transcription really does, because
# that is where the cue faults hide. Transcription returns no hyphens at all:
# measured over a 1,334-word module, zero of its hyphenated words came back
# hyphenated, and "multi-step wizards" came back as "step wizards". So a cue
# quoting a hyphenated word matches the script and nothing in the audio. Here
# the hyphen is split the same way, and that cue fails now instead of later.
#
# What it does NOT prove: any real timing. Every time it writes is invented, so
# a clean dry run says the composition is well-formed and says nothing about
# whether a reveal lands on its word. Run the real chain for that.
import io
import json
import os
import re
import sys

WPS = 2.2   # a steady reading rate; only the ORDER of these times is meaningful
HOLD = 2.0  # house style: the video ends a measured two seconds after speech

if len(sys.argv) != 3:
    sys.exit("usage: dry_run.py narration.txt <composition-dir>")
script, out = sys.argv[1], sys.argv[2]
if not os.path.isdir(out):
    sys.exit(f"not a directory: {out}")

raw = io.open(script, encoding="utf8").read()
words = []
for tok in raw.split():
    # transcription splits a hyphenated word and never returns the hyphen, and an
    # em dash is punctuation rather than a word.
    for piece in re.split(r"[-‐-―]", tok):
        if re.sub(r"[^0-9A-Za-z]", "", piece):
            words.append(piece)
if not words:
    sys.exit(f"no words in {script}")

step, t, rows = 1.0 / WPS, 1.0, []
for i, w in enumerate(words):
    rows.append({"id": f"w{i}", "text": w,
                 "start": round(t, 3), "end": round(t + step * 0.9, 3)})
    t += step

json.dump(rows, io.open(os.path.join(out, "transcript.json"), "w", encoding="utf8"), indent=1)
io.open(os.path.join(out, "speech_end.txt"), "w", encoding="utf8").write(f"{t:.3f}\n")
io.open(os.path.join(out, "audio_len.txt"), "w", encoding="utf8").write(f"{t + HOLD:.3f}\n")
print(f"synthetic transcript written: {len(words)} words, {t:.1f}s of invented timing")
print(f"now run the generator in {out} and then cue_check.py and id_check.py")
