# Guard 3: prove every cue phrase names one moment in the narration.
#
#   python3 cue_check.py transcript.json gen.py
#
# A composition cues its reveals by quoting the narration - t("Leave it where it
# is") - and the lookup returns the FIRST match. Quote something the narrator says
# twice and the reveal silently lands on the wrong one, which usually means it
# fires in an earlier scene and is already on screen when its own scene fades in.
# Nothing fails and nothing warns, and the frame looks finished either way, so it
# is only caught by sampling exactly that frame. Run this before rendering.
#
# Every phrase cued without naming an occurrence must match exactly once. Where a
# phrase genuinely repeats, name the one you mean - t("...", 2) - and this passes
# it, because you have said which. Reports the time of every match so you can tell
# them apart.
#
# What it reports is ambiguity, not a defect. Confirm against the render before
# changing a timing: repeats cluster because a module says its key phrase once in
# the scene that defines it and again in the scene that builds on it, and the
# defining scene comes first, so the first match is usually the occurrence the
# scene was written around. Then name what you found - t("...", 1) as readily as
# t("...", 2). Naming an occurrence records the answer rather than changing it, so
# a cue that was already right keeps the time it had.
#
# Keep no hand-written list of cue phrases. This reads the generator, because every
# module in this series cues through t()/te() and a hand-kept list goes stale.
import json, re, sys, unicodedata

TRANSCRIPT, GEN = sys.argv[1], sys.argv[2]

def norm(s):
    # The same folding cues.py and verify.py use, so this asks the question the
    # lookup will actually answer, not a stricter one.
    w = re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).lower())
    return w[:-1] if len(w) > 3 and w.endswith("s") else w

words = json.load(open(TRANSCRIPT))
TOK = [norm(w["text"]) for w in words]

def matches(phrase):
    want = [norm(t) for t in phrase.split() if norm(t)]
    if not want:
        return None
    return [i for i in range(len(TOK) - len(want) + 1) if TOK[i:i + len(want)] == want]

CALL = re.compile(r'\b(?:t|te|cues\.cue|cues\.endcue)\(\s*"((?:[^"\\]|\\.)*)"\s*(,\s*\d+\s*)?\)')
src = open(GEN, encoding="utf8").read()

seen, bad, missing = {}, [], []
for line_no, line in enumerate(src.splitlines(), 1):
    for m in CALL.finditer(line):
        phrase, nth = m.group(1), m.group(2)
        if nth:                       # an occurrence was named: the author has said which
            continue
        seen.setdefault(phrase, line_no)

for phrase, line_no in seen.items():
    at = matches(phrase)
    if at is None:
        continue
    if not at:
        missing.append((line_no, phrase))
    elif len(at) > 1:
        bad.append((line_no, phrase, [round(words[i]["start"], 2) for i in at]))

print(f"{len(seen)} cue phrase(s) checked against {len(TOK)} words")
for line_no, phrase in missing:
    print(f"  gen.py:{line_no}  NOT IN THE NARRATION  {phrase!r}")
for line_no, phrase, at in bad:
    print(f"  gen.py:{line_no}  {len(at)} matches at {at}  {phrase!r}")
if bad or missing:
    print(f"{len(bad) + len(missing)} ambiguous or unfindable cue(s) - name the occurrence, "
          f"t(\"...\", n), or quote more of the sentence")
    sys.exit(1)
print("every cue phrase names one moment")
