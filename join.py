# Join finished modules into one video.
#
#   python3 join.py course.mp4 module-01.mp4 module-02.mp4 ...
#
# A course is several modules and the deliverable is often one file, so this is
# how a video gets made rather than part of any one video - the same reason
# tts.mjs and speech_end.py live here (ADR-0007).
#
# It is assembly, not rendering, and that boundary is worth stating because
# ADR-0001 keeps rendering logic out of the studio: the engine renders a
# composition to video and nothing here reimplements or wraps that. This takes
# files the engine has already finished and concatenates them, which is the same
# shape as speech_end.py measuring a file the adapter already produced.
#
# Two failures it exists to prevent, both of which produce a playable file:
#
#   MISMATCHED PARTS. Stream copy concatenation assumes every part shares a
#   codec, resolution, frame rate and audio layout. Join parts that do not and
#   the result plays correctly for whoever encoded it and breaks somewhere after
#   the first boundary for everyone else. So the parameters are compared first
#   and a mismatch refuses.
#
#   A PART THAT DID NOT ARRIVE. ffmpeg's concat demuxer is happy to skip a part
#   it cannot read, and the output still plays - it is just short by one module,
#   which nobody notices until the module they were looking for is missing. So
#   the finished duration is checked against the sum of the parts.
#
#   THE CAPTIONS FALL OFF. Measured, not feared: the concat demuxer drops a
#   subtitle stream without a word, and the joined file plays perfectly with no
#   captions in it. A course joined from captioned modules would ship uncaptioned
#   and nobody would see it, because a subtitle track is off by default in most
#   players. So the parts' tracks are re-assembled onto the join, shifted by the
#   same cumulative durations the length check already measures, and a set of
#   parts where only some carry captions refuses rather than joining to a track
#   with holes in it.
#
# Streams are COPIED, never re-encoded: the joined file is bit-for-bit the
# modules that went into it, and joining a long course costs seconds rather than
# re-encoding every frame a second time and losing a generation of quality.
import json
import os
import re
import subprocess
import sys
import tempfile

from captions import srt_time

if len(sys.argv) < 4:
    sys.exit("usage: join.py <out.mp4> <part.mp4> <part.mp4> [...]   (two or more parts)")
OUT, PARTS = sys.argv[1], sys.argv[2:]

for p in PARTS:
    if not os.path.isfile(p):
        sys.exit(f"{p}: not a file")


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
        capture_output=True, text=True)
    if r.returncode != 0:
        # Say which file and what ffprobe said, rather than a traceback. This is
        # the likeliest way a part fails to arrive: it was never finished.
        sys.exit(f"{path}: cannot be read - {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'ffprobe failed'}")
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        sys.exit(f"{path}: no video stream")
    return {
        "duration": float(d["format"]["duration"]),
        # Captions are a soft track, so their presence is a property of the part
        # like any other and is compared the same way (see `shape`).
        "captions": sum(1 for s in d["streams"] if s["codec_type"] == "subtitle"),
        # Everything the concat demuxer needs to agree on. An audio stream that
        # is absent from one part and present in another is a mismatch too.
        "shape": (v["codec_name"], v["width"], v["height"], v.get("r_frame_rate"),
                  v.get("pix_fmt"),
                  a["codec_name"] if a else None,
                  a.get("sample_rate") if a else None,
                  a.get("channels") if a else None),
    }


CUE = re.compile(r"(\d\d):(\d\d):(\d\d)[,.](\d\d\d) --> (\d\d):(\d\d):(\d\d)[,.](\d\d\d)")


def track(path, work):
    """One part's caption track, as (start, end, text) in that part's own clock."""
    out = os.path.join(work, os.path.basename(path) + ".srt")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-map", "0:s:0",
                        "-c:s", "srt", "-f", "srt", out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{path}: has a caption track that cannot be read back - {r.stderr.strip()}")
    cues = []
    for b in re.split(r"\n\s*\n", open(out, encoding="utf8").read().strip()):
        lines = [x for x in b.split("\n") if x.strip()]
        if len(lines) < 3:
            continue
        m = CUE.match(lines[1])
        if not m:
            sys.exit(f"{path}: a caption cue has no timing line")
        g = [int(x) for x in m.groups()]
        cues.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000,
                     g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000,
                     "\n".join(lines[2:])))
    return cues


def rejoin_captions(out, parts, info):
    """Put the parts' caption tracks back on the join, shifted onto its clock.

    The offset for a part is the sum of the parts before it - the same cumulative
    duration the length check is built on, so there is one measurement and not two
    that can disagree."""
    work = tempfile.mkdtemp()
    merged, at, n = [], 0.0, 0
    for p, i in zip(parts, info):
        for start, end, text in track(p, work):
            n += 1
            merged.append(f"{n}\n{srt_time(start + at)} --> {srt_time(end + at)}\n{text}\n")
        at += i["duration"]
    srt = os.path.join(work, "joined.srt")
    open(srt, "w", encoding="utf8").write("\n".join(merged) + "\n")
    tmp = out + ".cc.mp4"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-i", srt,
                        "-map", "0", "-map", "1", "-c", "copy", "-c:s", "mov_text",
                        "-metadata:s:s:0", "language=eng",
                        "-metadata:s:s:0", "handler_name=Captions",
                        "-movflags", "+faststart", tmp], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"the captions could not be put back on the join:\n{r.stderr.strip()}")
    os.replace(tmp, out)
    return n


info = [probe(p) for p in PARTS]
first = info[0]["shape"]
bad = [(p, i["shape"]) for p, i in zip(PARTS, info) if i["shape"] != first]
if bad:
    print(f"{PARTS[0]}\n  {first}")
    for p, shape in bad:
        print(f"{p}\n  {shape}")
    sys.exit("parts differ - re-render the odd one with the same settings rather than joining these")

captioned = sum(1 for i in info if i["captions"])
if captioned and captioned != len(PARTS):
    for p, i in zip(PARTS, info):
        if not i["captions"]:
            print(f"{p}\n  no caption track")
    sys.exit(f"{captioned} of {len(PARTS)} parts carry captions - caption the rest before "
             f"joining, or the course ships with captions that stop partway through")

expected = sum(i["duration"] for i in info)

# The concat demuxer wants a list file, and its paths are resolved relative to
# that file unless they are absolute - so make them absolute and the list can
# live anywhere.
listing = OUT + ".concat.txt"
with open(listing, "w", encoding="utf8") as f:
    for p in PARTS:
        f.write("file '" + os.path.abspath(p).replace("'", r"'\''") + "'\n")

try:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", listing, "-c", "copy", "-movflags", "+faststart", OUT], check=True)
finally:
    os.unlink(listing)

cues = rejoin_captions(OUT, PARTS, info) if captioned else 0

got = probe(OUT)["duration"]
print(f"{len(PARTS)} parts -> {OUT}")
for p, i in zip(PARTS, info):
    print(f"  {i['duration']:8.2f}s  {p}")
print(f"  {'-' * 8}")
print(f"  {got:8.2f}s  joined  (parts total {expected:.2f}s)")
# A part that was skipped shows up here and nowhere else: the file still plays,
# it is just short by a module. The test is against HALF THE SHORTEST PART rather
# than a fixed tolerance, because that is the thing being detected - container
# duration rounds by a frame or two at every boundary and an mp4 whose audio is
# a little longer than its video drifts a fraction per join, and neither of those
# is a missing module.
shortest = min(i["duration"] for i in info)
if expected - got > shortest / 2:
    sys.exit(f"joined is {expected - got:.2f}s short against parts totalling {expected:.2f}s - "
             f"a part did not make it in (shortest part is {shortest:.2f}s)")
if captioned:
    print(f"  {cues} caption cues carried across the join")
print(f"{int(got // 60)}:{got % 60:05.2f} total")
