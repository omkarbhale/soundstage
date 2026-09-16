# Prove every highlight on a built composition is still the box that was measured.
#
#   python3 figure_check.py <composition>/index.html
#
# A figure makes two claims: that this is a picture of the product, and that the ring
# is round the thing just named. Both fail silently.
#
#   THE PICTURE IS NOT THERE. A missing or renamed image renders as an empty frame.
#   Nothing errors, `id_check.py` still finds the element, and a scene that is mostly
#   type reads as a design choice rather than as a broken figure.
#
#   THE RING IS ROUND THE WRONG THING. This is the one worth the guard. A box typed by
#   hand, or a shot re-taken after the product's layout moved, leaves a ring sitting
#   over empty space or over the control NEXT to the one the narration named - and the
#   frame looks every bit as finished. Nobody reviewing a render spots it, because
#   there is nothing to spot: it is a confident, well-drawn answer to the wrong
#   question.
#
# So the rule is ADR-0010's: a highlight is measured from the element, never drawn by
# hand - and this is what makes that rule enforceable rather than a convention. Each
# mark carries `data-shot` and `data-mark`; the numbers on the frame are compared back
# to the measurement the capture wrote, and any difference refuses.
#
# Run it after building and before rendering, beside `cue_check.py` and `id_check.py`.
import json
import os
import re
import sys

# A percentage rounded to three places by the generator is equal to the measurement it
# came from within this. Anything wider is an edit, not rounding.
TOLERANCE = 0.01   # percentage points

MARK = re.compile(r'<div class="fig-mark[^"]*"[^>]*?data-shot="([^"]+)"\s+data-mark="([^"]+)"'
                  r'[^>]*?style="([^"]+)"')
SHOT = re.compile(r'<img class="fig-shot" src="([^"]+)"')
STYLE = re.compile(r'(left|top|width|height):([0-9.]+)%')


def main(argv):
    if len(argv) != 1:
        sys.exit("usage: figure_check.py <composition>/index.html")
    path = argv[0]
    d = os.path.dirname(os.path.abspath(path))
    html = open(path, encoding="utf8").read()

    faults = 0
    srcs = SHOT.findall(html)
    for src in sorted(set(srcs)):
        if not os.path.exists(os.path.join(d, src)):
            print(f"  FAULT the picture is missing: {src}")
            faults += 1

    marks = MARK.findall(html)
    shots = {}
    for shot, mark, style in marks:
        rel = next((s for s in srcs if s.endswith(f"/{shot}.png") or s == f"{shot}.png"), None)
        meta = os.path.join(d, os.path.dirname(rel) if rel else "", f"{shot}.json")
        if meta not in shots:
            if not os.path.exists(meta):
                print(f"  FAULT no measurement for {shot!r} at {meta} - "
                      f"the highlight cannot be proved against anything")
                shots[meta] = None
                faults += 1
            else:
                shots[meta] = json.load(open(meta, encoding="utf8"))
        s = shots[meta]
        if s is None:
            continue
        want = s["marks"].get(mark)
        if want is None:
            print(f"  FAULT {shot}: no mark {mark!r} was measured (it has {sorted(s['marks'])})")
            faults += 1
            continue
        got = {k: float(v) for k, v in STYLE.findall(style)}
        for key, axis in (("left", "x"), ("top", "y"), ("width", "w"), ("height", "h")):
            drawn, measured = got.get(key), want[axis] * 100
            if drawn is None:
                print(f"  FAULT {shot}/{mark}: the highlight has no {key}")
                faults += 1
            elif abs(drawn - measured) > TOLERANCE:
                print(f"  FAULT {shot}/{mark}: {key} drawn at {drawn:.3f}% but measured at "
                      f"{measured:.3f}% - the shot moved, or the number was typed")
                faults += 1

    print(f"{path}")
    print(f"  {len(set(srcs))} picture(s), {len(marks)} highlight(s)")
    if faults:
        sys.exit(f"{faults} figure fault(s)")
    print("  every highlight is the box that was measured, and every picture is there")


if __name__ == "__main__":
    main(sys.argv[1:])
