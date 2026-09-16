# Captions for a module, written from the SCRIPT and timed by the TRANSCRIPT.
#
#   # the normal path: caption a finished module, leaving no sidecar behind
#   python3 captions.py --style <style.json> --into <video.mp4> <out.mp4> \
#                       <narration.txt> <transcript.json> --offset 2.0
#
#   # on demand, for a platform that strips or ignores a muxed track
#   python3 captions.py --style <style.json> <narration.txt> <transcript.json> <out.srt> \
#                       --offset 2.0 [--report]
#
# THE CAPTIONS LIVE IN THE VIDEO, AS A SOFT TRACK, AND NOWHERE ELSE. A subtitle file
# stored beside the video is a second thing to keep in step with the first, and it is
# not needed: the track travels inside the one file that gets handed around, and the
# viewer can turn it off. Burned-in is the other wrong answer - it cannot be turned
# off, and it would sit on top of the callouts a screenshot figure carries.
#
# A standalone file is still a legitimate thing to want, so the export above exists and
# is a command somebody runs, never a build artifact: it derives from the same script
# and the same timings, so there is one source of truth and nothing that can drift.
#
# A MUXED TRACK IS LOST SILENTLY BY RE-ENCODING OR TRIMMING. Anything that rewrites the
# file without `-map 0` drops the subtitle stream and the result plays perfectly.
# Whoever re-encodes runs `--into` again; `caption_check.py --in <video.mp4>` proves
# the track is really there.
#
# Both halves of a caption already exist by the time a module is finished, and they
# come from different files. That split is the design, not an implementation detail:
#
#   THE WORDS COME FROM `narration.txt`. It is the script that was approved, and
#   `verify.py` has already proved every word of it reached the audio. It spells the
#   product's names the way the product spells them.
#
#   THE TIMES COME FROM `transcript.json`. Per-word timings against the real audio -
#   the same file every reveal is cued from (ADR-0003). Nothing here is hand-timed.
#
# NEVER CAPTION FROM THE TRANSCRIPT'S OWN TEXT. An aligner mishears, and a caption is
# read rather than matched, so the mishearing is printed on the screen. Measured in
# this repo's own corpus: a module whose first word is `Screen` in the script is
# `Scream` in the transcript; `Tier A` came back as "Tierra"; an em dash glued the
# words either side of it into one token. See ADR-0011.
#
# THE TWO SIDES DO NOT LINE UP ONE TO ONE, so nothing here indexes one by the other -
# one measured module is 725 script words against 722 aligned. The script is aligned to
# the transcript with a sequence matcher; words inside a matched run take that word's
# times, and words in a gap are interpolated across the gap. A pairing too poor to
# trust refuses rather than producing plausible captions for the wrong audio.
#
# EVERY NUMBER IS THE CALLER'S. soundstage is a generic studio and holds no house
# style, so there is no built-in line length, cue length or reading rate to discover
# and override: they arrive in `--style` and a missing one refuses by name. What to put
# in that file, and how to choose it for a given narration, is in the README under
# "Captioning a module" - that is judgement to be taught, not a default to be buried.
import json
import os
import re
import subprocess
import sys
import unicodedata
from difflib import SequenceMatcher

# The style keys, and what each one is. Required, every one of them: a caption that
# quietly used a number nobody chose is worse than one that refused.
STYLE_KEYS = {
    "line_chars": "characters a line",
    "lines": "lines a cue",
    "cue_seconds": "[shortest, longest] a cue may be on screen",
    "hold_seconds": "how long a cue may run past its last word into the pause after it",
    "gap_seconds": "the visible gap between one cue going and the next arriving",
    "min_break_chars": "the shortest cue worth breaking a clause for",
    "min_alignment": "the fraction of the script that must align before the pairing is trusted",
    "keep_together": "phrases that must never be split across two cues",
}


def load_style(path):
    style = json.load(open(path, encoding="utf8"))
    missing = [k for k in STYLE_KEYS if k not in style]
    if missing:
        sys.exit(f"{path} is missing " + ", ".join(f"{k!r} ({STYLE_KEYS[k]})" for k in missing))
    style["chars"] = style["line_chars"] * style["lines"]
    return style


def norm(s):
    """The matcher's key. Same folding as a cue's, for the same reason: the written
    script and what the aligner heard differ on possessives and plurals."""
    w = re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).lower())
    return w[:-1] if len(w) > 3 and w.endswith("s") else w


def script_words(text):
    """The script as words that keep their own spelling, punctuation and paragraph
    breaks - because those are what a caption is broken on.

    A token with nothing to match on - a standing em dash, a lone bracket - is JOINED
    to its neighbour rather than dropped. Dropping it would lose the script's own
    punctuation from the caption and break the property `caption_check.py` proves:
    that the captions say the script and nothing else."""
    out, held = [], []
    for para_i, para in enumerate(p for p in text.split("\n\n") if p.strip()):
        for tok in para.split():
            key = norm(tok)
            if not key:
                if out and out[-1]["para"] == para_i:
                    out[-1]["text"] += " " + tok
                else:
                    held.append(tok)
                continue
            if held:
                tok = " ".join(held + [tok])
                held = []
            out.append({"text": tok, "para": para_i, "key": key})
        if out:
            out[-1]["para_end"] = True
    return out


def align(script, words):
    """Give every script word a start and an end.

    Matched runs take the aligned word's times. A gap - a mishearing, a word the
    aligner dropped, two words it glued - is spread evenly across whatever span the
    transcript gives that region, so the times stay monotonic and stay inside the
    surrounding words rather than jumping."""
    sm = SequenceMatcher(None, [w["key"] for w in script], [norm(w["text"]) for w in words],
                         autojunk=False)
    matched = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                script[i1 + k]["start"] = float(words[j1 + k]["start"])
                script[i1 + k]["end"] = float(words[j1 + k]["end"])
            matched += i2 - i1
        else:
            # The span the transcript gives this region. When the aligner inserted or
            # dropped nothing here (j1 == j2) the region is a zero-width point between
            # its neighbours, which is still the right place to put it.
            lo = float(words[j1]["start"]) if j1 < len(words) else float(words[-1]["end"])
            hi = float(words[j2 - 1]["end"]) if j2 > j1 else lo
            n = max(1, i2 - i1)
            step = (hi - lo) / n
            for k in range(i2 - i1):
                script[i1 + k]["start"] = lo + step * k
                script[i1 + k]["end"] = lo + step * (k + 1)
    ratio = matched / len(script) if script else 0.0

    # Monotonic, and no zero-length word: the aligner emits `start == end` on a word it
    # clipped, and a cue built on two of those has no duration at all.
    t = 0.0
    for w in script:
        w["start"] = max(w.get("start", t), t)
        w["end"] = max(w.get("end", w["start"]), w["start"])
        t = w["start"]
    return ratio


# THE BOUNDARY LADDER. English, not house style, so it lives here: a sentence end is
# the best place to break, strong punctuation next, then a clause boundary, and a plain
# phrase break only when the sentence offers none of those.
HARD = re.compile(r'[.!?]["”’)]?$')
STRONG = re.compile(r'[;:—–]["”’]?$')
CLAUSE = re.compile(r'[,)]["”’]?$')

# Words that usually START a phrase rather than continue one, in the form `norm`
# produces. Used only for that last resort.
HEADS = {norm(w) for line in (
    "the a an and or but so that which who when where while because if then than as",
    "is are was were has have had will would can could may might must does do did",
    "to of in on at for with from by into onto about after before under over",
    "you it they we he this these those there here not no its their our your",
) for w in line.split()}

# Never break between these and what follows: an article from its noun, a number from
# its unit. Same rule as `keep_together`, but grammar rather than vocabulary, so it is
# here and not in a style file.
GLUE = {norm(w) for w in ("a", "an", "the")}
NUMBER = re.compile(r"^\d")


def forbidden(script, keep):
    """Break positions that would split something that must not be split.

    A named UI element cut in half - "the session" then "chip" - is worse than a badly
    balanced line, because the whole value of a course like this is that it says the
    names exactly. The LIST of terms is the production's, and arrives in the style."""
    keys = [w["key"] for w in script]
    bad = set()
    for phrase in keep:
        want = [norm(t) for t in phrase.split() if norm(t)]
        if len(want) < 2:
            continue
        for i in range(len(keys) - len(want) + 1):
            if keys[i:i + len(want)] == want:
                bad.update(range(i + 1, i + len(want)))
    for i, w in enumerate(script[:-1]):
        # An article, or a number and its unit.
        if w["key"] in GLUE or (NUMBER.match(w["text"]) and not HARD.search(w["text"])):
            bad.add(i + 1)
    return bad


def cues(script, style):
    """Group script words into cues, broken as high up the boundary ladder as the
    reading budget allows.

    The break is CHOSEN, not taken: the cue runs until it would exceed the budget, and
    is then cut back to the best boundary inside it. Cutting at the character limit is
    what makes a caption hard to read, and it is what a plain chunker does."""
    lo, hi = style["cue_seconds"]
    keep = forbidden(script, style["keep_together"])
    out, i = [], 0
    while i < len(script):
        j, chars, cut, cand = i, 0, None, []
        while j < len(script):
            w = script[j]
            add = len(w["text"]) + (1 if j > i else 0)
            if j > i and (chars + add > style["chars"] or w["end"] - script[i]["start"] > hi):
                break
            chars += add
            j += 1
            if j in keep:
                continue
            if HARD.search(w["text"]) or w.get("para_end"):
                cut = j
                break
            rank = (3 if STRONG.search(w["text"]) else
                    2 if CLAUSE.search(w["text"]) else
                    1 if j < len(script) and script[j]["key"] in HEADS else 0)
            if rank:
                cand.append((rank, j, chars))
        if cut is None:
            worth = [(r, k) for r, k, c in cand if c >= style["min_break_chars"]]
            cut = max(worth)[1] if worth else j
        cut = max(cut, i + 1)
        # The character budget is the arithmetic ceiling, and a cue can sit under it
        # and still be unlayable - a long word straddling the last line break leaves
        # one line over the limit with nowhere else to break. So the cue is shortened
        # until it lays out, rather than shipped with an over-long line.
        while cut > i + 1 and lay(script[i:cut], style) is None:
            cut -= 1
        # A run with no legal break at all - one unsplittable term - still has to end
        # somewhere.
        out.append(script[i:cut])
        i = cut

    # A group whose own words span less than the shortest cue is a FLASH - it is on
    # screen and gone before it is read. It comes from a sentence tail of two or three
    # words, so the answer is to put it back with its neighbour whenever the two
    # together still lay out; the alternative, holding it longer, would overlap the cue
    # after it.
    merged, k = [], 0
    while k < len(out):
        g = out[k]
        while (g[-1]["end"] - g[0]["start"] < lo and k + 1 < len(out)
               and lay(g + out[k + 1], style) is not None):
            g = g + out[k + 1]
            k += 1
        if (g[-1]["end"] - g[0]["start"] < lo and merged
                and lay(merged[-1] + g, style) is not None):
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)
        k += 1
    return merged


def srt_time(t):
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def lay(words, style):
    """Fill the cue's words into lines, first-fit. Returns the lines, or None when the
    words cannot be made to fit - a word longer than a line, or more lines than the
    production allows. `cues()` uses it to know when a group is too long to show."""
    limit, maxlines = style["line_chars"], style["lines"]
    lines, cur = [], ""
    for w in words:
        t = w["text"]
        if len(t) > limit:
            return None
        nxt = f"{cur} {t}" if cur else t
        if len(nxt) <= limit:
            cur = nxt
        else:
            lines.append(cur)
            cur = t
    if cur:
        lines.append(cur)
    return lines if len(lines) <= maxlines else None


def wrap(words, style):
    """One line if it fits, otherwise `lines` lines, split at the boundary nearest the
    middle - and at the balanced space when there is none to use.

    A clause break is worth a lot of imbalance: "Across the top: a breadcrumb, / the
    step name as an editable field" reads, and the same words cut at their midpoint do
    not."""
    limit = style["line_chars"]
    text = " ".join(w["text"] for w in words)
    if len(text) <= limit:
        return text
    best, bestcost = None, None
    for k in range(1, len(words)):
        a = " ".join(w["text"] for w in words[:k])
        b = " ".join(w["text"] for w in words[k:])
        if len(a) > limit or len(b) > limit:
            continue
        boundary = STRONG.search(words[k - 1]["text"]) or CLAUSE.search(words[k - 1]["text"])
        cost = abs(len(a) - len(b)) - (limit // 2 if boundary else 0)
        if bestcost is None or cost < bestcost:
            best, bestcost = (a, b), cost
    if best:
        return f"{best[0]}\n{best[1]}"
    lines = lay(words, style)
    return "\n".join(lines) if lines else text


def render(groups, style, offset):
    """Cue text and timing. A cue starts at its first word and ends at its last, held a
    little into the pause after it - a caption that vanishes on the last syllable reads
    as a flicker - and always with a visible gap before the next one arrives."""
    lo, hi = style["cue_seconds"]
    hold, gap = style["hold_seconds"], style["gap_seconds"]
    rows = []
    for n, g in enumerate(groups):
        start = g[0]["start"] + offset
        # The hold is room for the last syllable to land, not licence to outstay the
        # longest cue the production allows: it is clamped to that ceiling.
        end = min(max(g[-1]["end"] + offset + hold, start + lo), start + hi)
        nxt = groups[n + 1][0]["start"] + offset if n + 1 < len(groups) else None
        if nxt is not None:
            end = min(end, nxt - gap)
        rows.append({"n": n + 1, "start": start, "end": max(end, start + gap),
                     "text": wrap(g, style)})
    return rows


def write_srt(rows, path):
    with open(path, "w", encoding="utf8") as f:
        for r in rows:
            f.write(f"{r['n']}\n{srt_time(r['start'])} --> {srt_time(r['end'])}\n{r['text']}\n\n")


def mux(video, srt, out):
    """Attach the captions as a SOFT track the player can turn off.

    `mov_text` is the mp4 container's own subtitle codec, and `-map 0` carries every
    stream the video already had, so the picture and the sound are still stream-copied
    and nothing is re-encoded. `-map 0` is also the line to keep in mind for any later
    ffmpeg pass over this file: without it the subtitle stream is dropped, silently."""
    if os.path.abspath(video) == os.path.abspath(out):
        sys.exit("this writes a new file; give it an output path of its own")
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", video, "-i", srt,
         "-map", "0", "-map", "1", "-c", "copy", "-c:s", "mov_text",
         "-metadata:s:s:0", "language=eng", "-metadata:s:s:0", "handler_name=Captions",
         "-movflags", "+faststart", out],
        capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg refused:\n{r.stderr.strip()}")


def build(script_path, transcript_path, style, offset):
    script = script_words(open(script_path, encoding="utf8").read())
    words = json.load(open(transcript_path, encoding="utf8"))
    if not script or not words:
        sys.exit("nothing to caption")
    ratio = align(script, words)
    if ratio < style["min_alignment"]:
        sys.exit(f"{ratio:.0%} of the script aligned to {transcript_path} - below "
                 f"{style['min_alignment']:.0%}. That is not this script's own transcript; "
                 f"captioning it would time every line against the wrong audio.")
    return render(cues(script, style), style, offset), script, words, ratio


def summarise(rows, script, words, ratio, where, offset):
    spoken = sum(len(w["text"].split()) for w in script)
    secs = [r["end"] - r["start"] for r in rows]
    print(where)
    print(f"  {spoken} script words, {len(words)} aligned  ({ratio:.1%} matched)")
    print(f"  {len(rows)} cues, {min(secs):.2f}-{max(secs):.2f}s each "
          f"(median {sorted(secs)[len(secs) // 2]:.2f}s), last out {rows[-1]['end']:.2f}s")


def take(argv, flag, cast=str):
    if flag not in argv:
        return None
    i = argv.index(flag)
    v = argv[i + 1]
    del argv[i:i + 2]
    return cast(v)


def main(argv):
    report = "--report" in argv
    argv = [a for a in argv if a != "--report"]
    style_path = take(argv, "--style")
    if not style_path:
        sys.exit("--style <style.json> is required: soundstage holds no house caption style, "
                 "so line length, cue length and the rest come from the production. "
                 "The README, under \"Captioning a module\", says how to choose them.")
    style = load_style(style_path)
    offset = take(argv, "--offset", float)
    if offset is None:
        sys.exit("--offset <seconds> is required: it is where the narration starts inside "
                 "the video, and a caption timed without it is wrong by that much.")

    if argv[:1] == ["--into"]:
        rest = argv[1:]
        if len(rest) != 4:
            sys.exit("usage: captions.py --style <style.json> --into <video.mp4> <out.mp4> "
                     "<narration.txt> <transcript.json> --offset S")
        video, out, script_path, transcript_path = rest
        rows, script, words, ratio = build(script_path, transcript_path, style, offset)
        # The subtitle file is a step, not a product: ffmpeg needs a file to read, and
        # leaving one beside the video is the second copy this design refuses.
        tmp = out + ".captions.srt"
        try:
            write_srt(rows, tmp)
            mux(video, tmp, out)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        summarise(rows, script, words, ratio,
                  f"{video} -> {out}  (soft track, stream-copied)", offset)
        print(f"  prove it with: python3 caption_check.py --style {style_path} "
              f"{script_path} --in {out}")
        return

    if len(argv) != 3:
        sys.exit("usage: captions.py --style <style.json> --into <video.mp4> <out.mp4> "
                 "<narration.txt> <transcript.json> --offset S\n"
                 "       captions.py --style <style.json> <narration.txt> <transcript.json> "
                 "<out.srt> --offset S [--report]")
    script_path, transcript_path, out = argv
    rows, script, words, ratio = build(script_path, transcript_path, style, offset)
    write_srt(rows, out)
    summarise(rows, script, words, ratio, out, offset)
    if report:
        for r in rows:
            cps = len(r["text"].replace("\n", " ")) / (r["end"] - r["start"])
            print(f"  {r['n']:4d}  {srt_time(r['start'])} {r['end'] - r['start']:5.2f}s "
                  f"{cps:5.1f}cps  {r['text'].replace(chr(10), ' / ')}")


if __name__ == "__main__":
    main(sys.argv[1:])
