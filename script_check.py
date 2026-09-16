# Guard 7: prove a script sounds like someone in the room, not a deck read aloud.
#
#   python3 script_check.py <composition>/index.html narration.txt
#
# The format is `formats/standing-set/SKILL.md`, which owns how a piece in it sounds
# as well as how it looks. This refuses the half of the deck feeling that lives in the
# words, and it needs no audio: run it before a take is spent.
#
#   THE SCRIPT ANNOUNCES ITS OWN STRUCTURE. "In this module we will look at three
#   things. First... Second... Finally... To summarise..." That is a contents page
#   read aloud, and no amount of camera work rescues it.
#
#   THE SCRIPT IS NOT ABOUT WHAT IS ON SCREEN. A set is built and furnished and the
#   voice talks about something else. The bond this guard insists on is exact: the
#   words that launch the camera name the thing it arrives at.
#
#   EVERY LINE IS THE SAME LINE. Fifteen-word declaratives, one after another, each
#   opening the same way. Bullet prose with the bullets taken out.
#
# It reads the SCRIPT rather than the transcript, because the script is what a person
# wrote and what a re-record will say again. Cue resolution against the audio is
# `cue_check.py`'s job and stays there; ADR-0003 is unchanged and unrestated.
#
# Run it in the dry run, beside the others, and again after any edit to the script.
import json
import re
import sys
import unicodedata
from html import unescape
from html.parser import HTMLParser

R = {
    "long_line": 30, "short_line": 8, "long_enough": 22, "spread": 5.0,
    "short_share": 0.15, "short_run": 5, "same_open": 0.20, "open_run": 3,
    "gap_words": 25, "name_share": 0.15, "first_sentence": 8, "echo": 6,
    "mirror": 0.35, "on_screen": 0.06, "echoes": 2,
    "triplet_share": 0.15, "triplets_free": 2, "cluster_per": 150, "cluster_max": 3,
    "breath": 14, "landing_share": 0.25, "front_share": 0.15, "front_words": 18,
    "questions": 1,
}

# Words too common to mean anything when the frame and the voice share them.
STOP = set("""a an and are as at be been but by can could do does for from had has have he
her him his how i if in into is it its me my no nor not of off on once one only or other
our out over own same she should so some such than that the their them then there these
they this those through to too under until up was we were what when where which while who
why will with would you your""".split())

# A deck read aloud, wherever it appears.
DECK = [
    "as you can see", "as we can see", "here we see", "on this slide", "on the slide",
    "on screen", "in this section", "in this module", "in this video", "in this piece",
    "in this presentation", "this video", "this module", "this presentation",
    "this section", "in summary", "to summarise", "to summarize", "to recap",
    "in conclusion", "let us look", "let's look", "let us take a look", "let's take a look",
    "we will look", "we'll look", "we will cover", "we'll cover", "we have covered",
    "we covered", "key takeaway", "key takeaways", "the agenda", "an overview of",
    "learning objectives", "moving on", "next up", "the first thing", "the second thing",
    "the third thing", "by the end of this",
]
# The enumerating openings. These words are ordinary mid-sentence; at the head of a
# sentence they are a list being read out.
COUNTERS = ("first", "firstly", "second", "secondly", "third", "thirdly", "fourth",
            "next", "finally", "lastly", "also", "additionally", "furthermore")

# The shapes a machine falls into when it has nothing to say. These DRIFT - the list
# below is a seed, not a law, and the rule that matters is density rather than any one
# word. Re-read a current catalogue before trusting it; what reads as a tell this year
# was ordinary writing two years ago and will be again.
NEGATIVE = [
    (r"\bnot only\b[^.!?]{0,80}?\bbut\b", "not only X but also Y"),
    (r"\bnot just\b[^.!?]{0,80}?\b(?:but|it'?s)\b", "not just X but Y"),
    (r"\bit'?s not\b[^.!?]{0,60}?,\s*it'?s\b", "it's not X, it's Y"),
    (r"\bis not\b[^.!?]{0,60}?,\s*it is\b", "it is not X, it is Y"),
    (r"\bnot a\b[^.!?]{0,60}?\bbut a\b", "not a X but a Y"),
    (r"\bdoesn'?t just\b[^.!?]{0,60}?,\s*it\b", "X doesn't just Y, it Z"),
]
PUFFERY = ["serves as", "stands as", "functions as", "is a testament", "a testament to",
           "plays a crucial role", "plays a vital role", "marks a pivotal", "pivotal moment",
           "reflects broader", "broader trends", "indelible mark", "deeply rooted",
           "in the heart of", "a diverse array", "rich tapestry"]
# Attribution to nobody is ONE move however it is dressed. These are seeds.
VAGUE = ["experts argue", "experts say", "experts believe", "industry reports",
         "observers have noted", "observers note", "many believe", "it is widely believed",
         "studies show", "research suggests", "critics argue", "some would call",
         "some would say", "some say", "some call it", "many would", "people say",
         "it is said", "one could argue", "you could say", "it is often"]
# Dismissing a first answer to introduce a second is one move however it is worded.
DISMISS = ["undersells", "oversells", "misses the point", "misreads", "the truth of it",
           "what it really is", "is less about", "does it a disservice", "sells it short"]
SUBORD = ("because", "although", "though", "while", "whilst", "since", "whereas", "if",
          "unless", "when", "after", "before", "as")
SIGNIFY = ("highlighting", "underscoring", "emphasizing", "reflecting", "contributing",
           "fostering", "cultivating", "encompassing", "showcasing", "demonstrating",
           "solidifying", "cementing", "ensuring")
CLUSTER = ("delve", "intricate", "interplay", "tapestry", "testament", "pivotal", "crucial",
           "vital", "underscore", "underscores", "landscape", "meticulous", "vibrant",
           "garner", "boasts", "bolster", "bolstered", "enduring", "robust", "seamless",
           "leverage", "harness", "realm", "myriad", "plethora", "profound", "groundbreaking",
           "renowned", "nestled", "align", "aligns", "enhance", "enhances", "foster",
           "showcase", "showcases", "navigate", "unlock", "empower", "transformative")

FAULTS = []


def fault(rule, msg):
    FAULTS.append(f"  {rule:<14} {msg}")


def norm(w):
    w = re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", w).lower())
    return w[:-1] if len(w) > 3 and w.endswith("s") else w


class Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.manifest = None
        self._grab = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and a.get("id") == "set-manifest":
            self._grab = True

    def handle_endtag(self, tag):
        self._grab = False

    def handle_data(self, data):
        if self._grab:
            self.manifest = json.loads(unescape(data))


def sentences(text):
    """The script's lines, in order, each as (raw, [normalised words])."""
    out = []
    for raw in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip()):
        if not raw:
            continue
        words = [norm(w) for w in raw.split() if norm(w)]
        if words:
            out.append((raw, words))
    return out


def seen_frac(prop, shot, planes, frame):
    """How much of the frame a prop covers under one framing."""
    fw, fh = frame
    s = shot["s"] / planes[prop["plane"]]
    x = (prop["at"][0] - shot["cx"]) * s + fw / 2
    y = (prop["at"][1] - shot["cy"]) * s + fh / 2
    w, h = prop["size"][0] * s, prop["size"][1] * s
    ix = max(0.0, min(fw, x + w) - max(0.0, x))
    iy = max(0.0, min(fh, y + h) - max(0.0, y))
    return ix * iy / (fw * fh)


def text_of(cue):
    """The words of a cue, whether or not it also names which occurrence it means."""
    return cue[0] if isinstance(cue, (list, tuple)) and cue else str(cue)


def shown(cue):
    """A cue as it reads back to the author who wrote it."""
    if isinstance(cue, (list, tuple)) and len(cue) > 1:
        return f"{cue[0]!r} (occurrence {cue[1]})"
    return repr(text_of(cue))


def find(seq, want):
    """Every index where `want` starts in `seq`."""
    if not want:
        return []
    return [i for i in range(len(seq) - len(want) + 1) if seq[i:i + len(want)] == want]


def main(argv):
    if len(argv) not in (2, 3):
        sys.exit("usage: script_check.py <composition>/index.html narration.txt "
                 "[<composition>/transcript.json]")
    path, spath = argv[0], argv[1]
    tpath = argv[2] if len(argv) > 2 else None
    doc = Doc()
    doc.feed(open(path, encoding="utf8").read())
    if doc.manifest is None:
        sys.exit(f"{path} carries no set manifest - a script in this format is held to a set, "
                 f"and there is none here")
    m = doc.manifest
    text = open(spath, encoding="utf8").read()
    lines = sentences(text)
    if not lines:
        sys.exit(f"{spath} is empty")
    words = [w for _r, ws in lines for w in ws]
    named = {p["id"]: [norm(w) for w in (p["name"] or "").split() if norm(w)]
             for p in m["props"] if p.get("name")}
    by_id = {p["id"]: p for p in m["props"]}
    shots, changes, events = m["shots"], m["changes"], m["events"]
    targets = {pid for s in shots for pid in s["on"]}

    # --- the register --------------------------------------------------------
    flat = " ".join(words)
    plain = re.sub(r"\s+", " ", text.lower())
    for phrase in DECK:
        if phrase in plain:
            fault("SIGNPOST", f"the script says {phrase!r} - that is a deck announcing itself, "
                              f"and a set has no sections to introduce")
    for raw, ws in lines:
        if ws and ws[0] in (norm(c) for c in COUNTERS):
            fault("SIGNPOST", f"a line opens {raw.split()[0]!r} - an enumerated list read out "
                              f"loud is the thing this format replaces: {raw[:60]!r}")

    # --- the shapes of writing that has nothing to say ------------------------
    for pat, shape in NEGATIVE:
        hit = re.search(pat, plain)
        if hit:
            fault("NEGATIVE PARALLELISM",
                  f"{hit.group(0)[:48]!r} is {shape} - the most recognisable tell there is, and "
                  f"a listener hears it far more sharply than a reader. Say the thing it is")
    for phrase in PUFFERY:
        if phrase in plain:
            fault("PUFFERY", f"the script says {phrase!r} - that is significance asserted "
                             f"instead of shown, and usually a plain 'is' that lost its nerve")
    for phrase in DISMISS:
        if phrase in plain:
            fault("NEGATIVE PARALLELISM",
                  f"the script says {phrase!r} - dismissing a first answer to introduce a "
                  f"second is negative parallelism wearing different words. Write the second "
                  f"half and delete the first")
    for phrase in VAGUE:
        if phrase in plain:
            fault("VAGUE SOURCE", f"the script says {phrase!r} with nobody behind it - name who, "
                                  f"or drop the claim")
    for raw, _ws in lines:
        tail = re.search(r",\s+(\w+ing)\b[^.!?]*[.!?]?\s*$", raw)
        if tail and tail.group(1).lower() in SIGNIFY:
            fault("ADDED SIGNIFICANCE",
                  f"a line ends {', ' + tail.group(1)!r} and hangs a vague claim off a plain "
                  f"fact: {raw[-56:]!r}. Either the claim is the line or it is not in it")
    # X, Y and Z - with or without the serial comma.
    trips = [raw for raw, _ws in lines
             if re.search(r"[^.!?,]{2,40},\s*(?:[^.!?,]{2,40},\s*)?[^.!?,]{2,40}\s+"
                          r"(?:and|or)\s+\w+", raw)]
    if len(trips) > max(R["triplets_free"], R["triplet_share"] * len(lines)):
        fault("RULE OF THREE", f"{len(trips)} of {len(lines)} lines are three-item lists - three "
                               f"is a rhythm once and a machine every time: {trips[0][:48]!r}")
    found = [w for w in words if w in CLUSTER]
    if len(found) > max(R["cluster_max"], len(words) / R["cluster_per"]):
        fault("CLUSTER", f"{len(found)} words from the tell vocabulary ("
                         f"{', '.join(sorted(set(found))[:6])}) in {len(words)} words. Any one "
                         f"of them is a choice; this many is a pattern, and the pattern is "
                         f"writing that has nothing to say")

    # --- the shape of a line -------------------------------------------------
    lens = [len(ws) for _r, ws in lines]
    for raw, ws in lines:
        if len(ws) > R["long_line"]:
            fault("LONG LINE", f"a line runs {len(ws)} words - a line is one thought, at most "
                               f"{R['long_line']}: {raw[:60]!r}")
    mean = sum(lens) / len(lens)
    spread = (sum((x - mean) ** 2 for x in lens) / len(lens)) ** 0.5
    shorts = sum(1 for x in lens if x <= R["short_line"])
    if shorts < len(lens) / R["short_run"] or max(lens) < R["long_enough"] \
            or spread < R["spread"]:
        fault("FLAT VOICE", f"{len(lens)} lines averaging {mean:.0f} words, longest {max(lens)}, "
                            f"{shorts} of them {R['short_line']} words or under, spread "
                            f"{spread:.1f}. A voice varies: one line in {R['short_run']} lands "
                            f"in {R['short_line']} words or fewer, one runs past "
                            f"{R['long_enough']}, and the spread is at least {R['spread']:.0f}")
    tiny = sum(1 for x in lens if x <= 3)
    if tiny > R["short_share"] * len(lens):
        fault("STACCATO", f"{tiny} of {len(lens)} lines are three words or fewer - a punch is "
                          f"worth something because the lines around it are not punches")
    opens = [ws[0] for _r, ws in lines if ws]
    for i in range(len(opens) - R["open_run"] + 1):
        if len(set(opens[i:i + R["open_run"]])) == 1:
            fault("PARALLEL", f"{R['open_run']} lines in a row open on {opens[i]!r} - parallel "
                              f"openings are a bulleted list with the bullets taken out")
            break
    if opens:
        top = max(set(opens), key=opens.count)
        if opens.count(top) > R["same_open"] * len(opens):
            fault("PARALLEL", f"{opens.count(top)} of {len(opens)} lines open on {top!r} - at "
                              f"most {int(R['same_open'] * 100)}% may")
    for i in range(len(words) - R["echo"]):
        chunk = words[i:i + R["echo"]]
        if find(words, chunk)[1:] and find(words, chunk)[0] == i:
            fault("PADDING", f"the script says {' '.join(chunk)!r} more than once - a phrase "
                             f"repeated word for word is filler, not emphasis")
            break

    # --- what a flat synthetic voice can land ---------------------------------
    # The local engine takes a voice, a speed and a lexicon. There is no style prompt,
    # so nothing will act for us: every one of these is an expressive control that has
    # to live in the writing instead.
    for raw, _ws in lines:
        for run in re.split(r"[,;:.!?\u2014-]+", raw):
            n = len(run.split())
            if n > R["breath"]:
                fault("BREATH", f"{n} words run without a break in {run.strip()[:52]!r} - a flat "
                                f"voice cannot phrase what the punctuation does not mark, and "
                                f"there is no style prompt to rescue it")
                break
    ends = [ws[-1] for _r, ws in lines if ws]
    flat_end = [e for e in ends if e in STOP]
    if len(flat_end) > R["landing_share"] * len(ends):
        fault("LANDING", f"{len(flat_end)} of {len(ends)} lines end on a function word "
                         f"({', '.join(sorted(set(flat_end))[:5])}) - a flat reading drops pitch "
                         f"at the full stop, so whatever is last gets the landing. Spend it")
    for raw, ws in lines:
        if ws and ws[0] in (norm(c) for c in SUBORD) and len(ws) > R["front_words"]:
            fault("FRONT LOADED", f"a {len(ws)}-word line opens on {raw.split()[0]!r} and buries "
                                  f"its point behind a subordinate clause: {raw[:52]!r}. Say the "
                                  f"thing, then qualify it")
    hard = re.findall(r"\b(?=\w*\d)(?:\w*\d\w*)\b", text)
    for tok in hard:
        if len(re.findall(r"\d", tok)) >= 4 or (re.search(r"[A-Za-z]", tok)
                                                 and re.search(r"\d", tok)):
            fault("UNSAYABLE", f"the script says {tok!r} - a local voice reads every character "
                               f"of an identifier or a long number. Put it on the frame and say "
                               f"it in words")
            break
    shouty = [w for w in text.split() if len(w) > 3 and w.isupper()]
    if shouty:
        fault("UNSAYABLE", f"the script shouts {shouty[0]!r} - capitals are an instruction to a "
                           f"performer, and there is no performer. Put the weight in the words")
    if text.count("?") > R["questions"]:
        fault("UNSAYABLE", f"{text.count('?')} questions - read flat, a question is a statement. "
                           f"At most {R['questions']} in a piece")

    # --- the bond to the set -------------------------------------------------
    hits = []                       # (word index, prop id) for every naming
    for pid, want in named.items():
        for i in find(words, want):
            hits.append((i, pid))
    hits.sort()
    for pid in sorted(targets):
        if pid in named and not any(h[1] == pid for h in hits):
            fault("UNNAMED", f"the camera stops on {pid!r} and the script never calls it "
                             f"{by_id[pid]['name']!r} - the voice names what the camera goes to")
    # A label line: strip the stop words and nothing is left but the name of a thing.
    # Counting total name WORDS instead would fight [ABSTRACT RUN], which demands the
    # naming this would punish - what matters is whether a naming earns its line.
    name_words = {w for ws2 in named.values() for w in ws2}
    labels = [raw for raw, ws in lines
              if ws and all(w in STOP or w in name_words for w in ws)]
    if len(labels) > R["name_share"] * len(lines):
        fault("NAME DROP", f"{len(labels)} of {len(lines)} lines say nothing but the name of a "
                           f"thing ({labels[0][:40]!r}) - at most "
                           f"{int(R['name_share'] * 100)}%. Naming what the camera finds is the "
                           f"job; a line that only names it is a caption")
    prev = 0
    for i, _pid in hits + [(len(words), None)]:
        if i - prev > R["gap_words"]:
            fault("ABSTRACT RUN", f"{i - prev} words pass without naming anything in the set, "
                                  f"around {' '.join(words[prev:prev + 8])!r} - the voice stays "
                                  f"in the room")
            break
        prev = i

    def line_of(cue):
        """The line carrying the occurrence this cue names.

        A cue is a phrase, or a phrase AND the occurrence meant - which is exactly what
        `set_check.py`'s AMBIGUOUS fault tells an author to write when a phrase repeats
        (README, "Cueing a reveal"). Reading only the phrase would check the bond
        against the wrong sentence; reading only the first would make the two guards
        disagree about a move the format itself prescribes."""
        want = [norm(w) for w in text_of(cue).split() if norm(w)]
        nth = cue[1] if isinstance(cue, (list, tuple)) and len(cue) > 1 else 1
        passed = 0
        for raw, ws in lines:
            hits = find(ws, want)
            if hits:
                if passed + len(hits) >= nth:
                    return raw, ws
                passed += len(hits)
        return None

    def bond(cue, who, what):
        said = shown(cue)
        got = line_of(cue)
        if got is None:
            fault("NOT SPOKEN", f"{what} is cued on {said}, which is not in the script")
            return
        raw, ws = got
        if not any(find(ws, named[p]) for p in who if p in named):
            names = ", ".join(repr(by_id[p]["name"]) for p in who if p in named)
            fault("UNMOTIVATED", f"{what} is cued on {said}, in a line that never names "
                                 f"{names or 'what it is about'} - the words that launch the "
                                 f"camera name where it lands: {raw[:60]!r}")
        elif len(ws) < R["first_sentence"]:
            fault("NAME DROP", f"{what} lands in a {len(ws)}-word line, {raw[:40]!r} - a name "
                               f"on its own is a caption; the line says something about it")

    carried = []
    for sh in shots:
        carried.append(sh["on"] or (carried[-1] if carried else []))
    for sh, on in list(zip(shots, carried))[1:]:
        if sh["kind"] == "rack":
            on = [p["id"] for p in m["props"] if p["plane"] == sh["focus"]
                  and seen_frac(p, sh, m["planes"], m["frame"]) >= R["on_screen"]]
        bond(sh["cue"], on, f"the {sh['kind']} move")
    for c in changes:
        bond(c["cue"], [c["prop"]], f"the change {c['note']!r}")
    for e in events:
        bond(e["cue"], [e["prop"]], f"the event {e['note']!r}")

    # --- the frame does not say what the voice is saying ----------------------
    # The signature of a machine-made video: the screen restating the sentence. The
    # picture shows what the words cannot, the words say what the picture cannot, and
    # the overlap between them is measured rather than trusted. A prop's NAME is
    # discounted, because naming what the camera is on is required elsewhere; what is
    # refused is the rest of the line appearing on the wall.
    if tpath:
        spoken = json.load(open(tpath, encoding="utf8"))
        tok = [norm(w["text"]) for w in spoken]
        if len(m.get("echoes", [])) > R["echoes"]:
            fault("ECHO", f"{len(m['echoes'])} declared echoes - at most {R['echoes']}. A word "
                          f"landing on the frame as it is spoken is a beat because it is rare")
        marked = {e["prop"] for e in m.get("echoes", [])}
        i = 0
        worst = None
        for raw, ws in lines:
            j = min(i + len(ws), len(tok))
            if i >= len(tok):
                break
            t0 = spoken[i]["start"]
            sh = [x for x in shots if x["at"] <= t0 + 1e-6]
            sh = sh[-1] if sh else shots[0]
            here = [p for p in m["props"]
                    if seen_frac(p, sh, m["planes"], m["frame"]) >= R["on_screen"]]
            on_frame = set()
            for p in here:
                if p["id"] in marked:
                    continue
                on_frame |= {norm(w) for w in p.get("text", [])}
            on_frame -= {""}
            said = [w for w in ws if w not in STOP]
            for p in here:
                for nm in [named.get(p["id"], [])]:
                    if nm and find(ws, nm):
                        said = [w for w in said if w not in nm]
            if said:
                hit = [w for w in said if w in on_frame]
                share = len(hit) / len(said)
                if share > R["mirror"] and (worst is None or share > worst[0]):
                    worst = (share, raw, hit)
            i = j
        if worst:
            fault("ECHO", f"{worst[0] * 100:.0f}% of a line is also written on the frame while "
                          f"it is spoken - {', '.join(sorted(set(worst[2]))[:6])} - in "
                          f"{worst[1][:50]!r}. The frame shows what the words cannot say; a "
                          f"frame that reads the line back is the thing that looks machine-made. "
                          f"Declare it with S.echo() if it is a beat you meant")

    # --- how it opens and how it ends ----------------------------------------
    head = lines[0][1] + (lines[1][1] if len(lines) > 1 else [])
    if not any(find(head, named[p]) for p in shots[0]["on"] if p in named):
        want = ", ".join(repr(by_id[p]["name"]) for p in shots[0]["on"] if p in named)
        fault("AGENDA", f"the script opens without naming {want} - a piece opens on the thing "
                        f"the camera is already looking at, not on what is coming")
    tail = lines[-1][1] + (lines[-2][1] if len(lines) > 1 else [])
    moved_props = {c["prop"] for c in changes}
    if not any(find(tail, named[p]) for p in moved_props if p in named):
        fault("RECAP", "the script ends without naming anything that changed - a piece ends on "
                       "what the set is now, not on what was covered")

    print(f"{spath} against {path}")
    print(f"  {len(lines)} lines, {len(words)} words, {len(named)} named props, "
          f"{len(hits)} namings")
    for f in FAULTS:
        print(f)
    if FAULTS:
        sys.exit(f"{len(FAULTS)} fault(s) - this reads as a deck however it is filmed")
    print("  a voice in the room: it names what the camera finds, and announces nothing")


if __name__ == "__main__":
    main(sys.argv[1:])
