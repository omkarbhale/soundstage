#!/usr/bin/env python3
"""Pick the frames that show a module, for review without rendering it.

    python3 review_frames.py <composition>/index.html            # the table
    python3 review_frames.py <composition>/index.html --times    # for --at
    python3 review_frames.py <composition>/index.html --json

A review round wants one frame per scene at its settled state plus one per
distinct reveal inside it, and `hyperframes snapshot --at` will capture any
second you name. Naming those seconds by hand goes wrong in a way that looks
like a broken module rather than a bad capture:

**A scene clip starts before its own first word and overlaps the outgoing
scene's fade.** Compositions here open each clip half a second early so the
cross-fade has room, so for that half second two scenes are on screen at once.
A frame captured inside the handover shows one scene's heading printed through
another's and reads as a rendering fault - the reviewer reports a bug that is
not in the module. The same overlap makes the outgoing scene's last reveal
land inside the incoming clip's span, so reading tweens by time alone credits
it to the wrong scene and puts the first frame even earlier.

So every time here is past the handover: after this clip's own fade-in has
finished AND after the previous clip's fade-out has, plus a margin. Both
durations are read out of the generated timeline rather than assumed, because
they are the composition's to choose.

Reads only the generated index.html, so it cannot name a moment the
composition does not have. Holds no content and takes an explicit path
(ADR-0004).
"""
import json
import re
import sys

SCENE_RE = re.compile(
    r'id="sc-([A-Za-z0-9_-]+)"[^>]*class="clip scene"[^>]*'
    r'data-start="([\d.]+)"[^>]*data-duration="([\d.]+)"'
)
TWEEN_RE = re.compile(
    r'tl\.(fromTo|to)\("([^"]+)",.*?duration:\s*([\d.]+).*?,\s*([\d.]+)\);'
)

HANDOVER = 0.5   # margin past the last of the two fades
CLUSTER = 1.1    # reveals landing this close read as one stage
MAX_STAGES = 4   # build frames per scene, before the settled one


def plan(html, max_stages=MAX_STAGES):
    scenes = [(m.group(1), float(m.group(2)),
               float(m.group(2)) + float(m.group(3)))
              for m in SCENE_RE.finditer(html)]
    if not scenes:
        raise SystemExit("no scene clips found - is this a generated index.html?")

    reveals, fade_in, fade_out = [], {}, {}
    for kind, sel, dur, at in TWEEN_RE.findall(html):
        dur, at = float(dur), float(at)
        m = re.match(r"#in-([A-Za-z0-9_-]+)$", sel)
        if m:                       # the scene's own in/out, not a reveal
            (fade_in if kind == "fromTo" else fade_out)[m.group(1)] = (at, dur)
        else:
            # round: a reveal can finish exactly on the handover floor, and
            # float error there decides whether the frame exists at all
            reveals.append(round(at + dur, 3))
    reveals.sort()

    out, prev_out_end = [], 0.0
    for name, cs, nxt in scenes:
        in_at, in_dur = fade_in.get(name, (cs, 0.0))
        out_at, out_dur = fade_out.get(name, (nxt, 0.0))
        floor = round(max(in_at + in_dur, prev_out_end) + HANDOVER, 3)
        prev_out_end = round(out_at + out_dur, 3)

        settled = round(min(out_at - 0.1, nxt - 0.9), 2)
        if settled <= floor:                     # a scene too short to build
            out.append((name, [round(max(floor, (cs + nxt) / 2), 2)]))
            continue

        stages, last = [], None
        for e in (e for e in reveals if floor <= e < out_at - 0.35):
            if last is None or e - last > CLUSTER:
                stages.append(e)
            last = e

        times, keep = [round(min(s + 0.25, settled - 0.4), 2) for s in stages], []
        for t in times:
            if t >= floor and (not keep or t - keep[-1] > 0.9):
                keep.append(t)
        keep = [t for t in keep if settled - t > 0.9]
        if len(keep) > max_stages:
            step = (len(keep) - 1) / (max_stages - 1)
            keep = sorted({keep[round(i * step)] for i in range(max_stages)})
        out.append((name, keep + [settled]))
    return out


def main(argv):
    paths = [a for a in argv[1:] if not a.startswith("--")]
    if len(paths) != 1:
        raise SystemExit(__doc__)
    p = plan(open(paths[0], encoding="utf8").read())
    flat = sorted((t, n) for n, ts in p for t in ts)

    if "--times" in argv:
        print(",".join(f"{t:g}" for t, _ in flat))
    elif "--json" in argv:
        print(json.dumps([{"t": t, "scene": n} for t, n in flat]))
    else:
        for name, times in p:
            print(f"  {name:9s} {len(times)} frame(s): "
                  + " ".join(f"{t:.2f}" for t in times))
        print(f"\n{len(flat)} frames across {len(p)} scenes")
        print("hyperframes snapshot --no-end --at "
              f"\"$(python3 review_frames.py {paths[0]} --times)\"")


if __name__ == "__main__":
    main(sys.argv)
