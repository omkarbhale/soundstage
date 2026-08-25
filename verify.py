# Guard 1: prove the audio contains every word of the script.
#
#   python3 verify.py narration.txt transcript.json
#
# The speech model silently drops detachable clauses - anything liftable without
# breaking the grammar, anywhere in a sentence. A standalone sentence, a leading
# adverbial, a trailing adjunct carrying an instruction, the "dot" in a spoken
# domain. Long sentences are not safe by being long. Nothing errors and nothing
# warns, so the only way a drop is found is diffing the script against the
# transcript word for word, which is what this does. Skip it and a module ships
# missing a fact with nothing about it looking wrong.
#
# Reports every difference and whether the diff is clean. Insertions and
# deletions are the fault; 1:1 replacements are whisper spelling a number or a
# proper noun its own way, or contracting "here is" to "here's", and are not a
# dropped word.
#
# Two things to do with a failure:
#
# 1. Rewrite the fragment so it is structurally undroppable - the words have to
#    sit in a clause the sentence needs, not in an adjunct that can be lifted out
#    and leave the grammar intact. Joining it to its neighbour is not enough: an
#    adjunct stays liftable wherever it is joined.
# 2. Regenerate, and run this again. The drop is non-deterministic - an unchanged
#    sentence can survive one generation and lose its closing clause on the next.
#    A clean pass certifies the audio in hand and says nothing about the script,
#    so never carry a previous pass forward.
#
# Prove a deletion before acting on it. This diffs against the FULL-FILE
# transcript, and whisper elides across a word boundary there in a way it does
# not on a short window: "No attacker is involved anywhere" comes back as "no
# attackers involved anywhere", which lands here as a deleted "is" because norm()
# folds the trailing s - nothing is missing from the audio. So when the whole of
# a failure is one function word at a contraction or an elision, re-transcribe
# that window before regenerating (repair.py already carries the technique). A
# dropped CLAUSE stays missing when the window is read on its own; a mishearing
# does not.
#
# This is compliance material and a dropped clause is a missing fact. Do not ship
# a module whose audio is missing one.
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
