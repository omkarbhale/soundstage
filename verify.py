# Guard 1: prove the audio contains every word of the script.
#
# The speech model silently drops detachable clauses - whatever can be lifted out
# without breaking the grammar, wherever it sits. Module 1 lost a standalone
# sentence and read the fault as being about short sentences; module 4 then lost
# a leading adverbial and two trailing adjuncts, all three INSIDE longer
# sentences, and elided "dot" from a spoken domain. Long sentences are not safe
# by being long. No error, no warning: the only way any of it is found is diffing
# the script against the transcript word for word, which is what this does.
# ADR-0007 has the full account.
#
#   python3 verify.py narration.txt transcript.json
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
#    and leave the grammar intact. Merely joining it to its neighbour does not
#    work; module 4 proved that.
# 2. Regenerate, and run this again. The drop is non-deterministic - on module 4
#    the same sentence survived one generation and lost its closing clause on the
#    next, unchanged. A clean pass certifies the audio in hand and says nothing
#    about the script, so never carry a previous pass forward.
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
