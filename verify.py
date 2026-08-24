# Guard 1: prove the audio contains every word of the script.
#
# The speech model silently drops short standalone sentences. On module 1 it
# dropped "One note on regulation." entirely - no error, no warning, just absent
# from the audio, and it was caught only by diffing the script against the
# transcript word for word. This is compliance material and a dropped sentence
# is a missing fact, so this runs after every narration generation.
#
#   python3 verify.py narration.txt transcript.json
#
# Reports every difference and whether the diff is clean. Insertions and
# deletions are the fault; 1:1 replacements are whisper spelling a number or a
# proper noun its own way and are not a dropped word. If a fragment does go
# missing, fold it into an adjacent sentence rather than leaving it standalone
# and regenerate - do not ship a module whose audio is missing a fact.
import json, re, sys, unicodedata, difflib
def norm(s):
    w = re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).lower())
    return w[:-1] if len(w) > 3 and w.endswith("s") else w
script = [norm(x) for x in open(sys.argv[1], encoding="utf8").read().split() if norm(x)]
heard  = [norm(w["text"]) for w in json.load(open(sys.argv[2]))]
print(f"script {len(script)} words / heard {len(heard)}")
bad = 0
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, script, heard, autojunk=False).get_opcodes():
    if tag == "equal":
        continue
    bad += 1
    print(f"  {tag:8s} script: {' '.join(script[i1:i2])!r}\n           heard : {' '.join(heard[j1:j2])!r}")
print("clean" if not bad else f"{bad} difference(s)")
