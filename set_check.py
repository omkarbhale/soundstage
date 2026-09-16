# Guard 6: prove a standing set is a space the camera travels, and not slides.
#
#   python3 set_check.py <composition>/index.html <composition>/transcript.json
#
# The format is `formats/standing-set/SKILL.md`; components/standing_set.py is its
# geometry. This is the part that refuses. Every fault below renders: the frame is
# composed, the timeline runs, `cue_check.py`, `id_check.py` and `figure_check.py`
# all pass, and what ships is a deck with a camera move on it.
#
#   THE SET FITS THE FRAME. A world the camera can see all of at once is a slide,
#   whatever it is called, and travelling across it is a pan over a poster.
#
#   THE PROPS ARRIVE. A prop that fades in when the camera reaches it is a bullet.
#   In a standing set everything is already there and the camera finds it; an
#   arrival is rationed and has to be caused by something already on screen.
#
#   THE CAMERA NEVER LANDS. Continuous motion with no rest reads as a screensaver.
#   Meaning is made by arriving and holding, and a hold has to carry something.
#
#   ONE ACCENT ON GREY. A single palette repeated across the whole world is the
#   deck reflex wearing a camera. Regions differ, and the camera crosses between
#   them.
#
#   EVERY STOP IS A DESTINATION. A set where every prop is a framing target is a
#   deck with the slides laid side by side. Some of the space is passed through.
#
# The numbers in the timeline are re-derived here from the manifest the component
# stamped into the document, the way figure_check.py re-derives a highlight from its
# measurement: a camera position typed by hand is refused (ADR-0010's rule in the
# third medium).
#
# Run it after building and before rendering, beside cue_check.py, id_check.py and
# figure_check.py.
import collections
import json
import math
import re
import sys
import unicodedata
from html import unescape
from html.parser import HTMLParser

# Matches components/standing_set.py. A change to either is a change to both.
DOF_K, DOF_CAP_S, DOF_MAX = 7.0, 1.7, 15.0

R = {                              # every threshold the format states, in one place
    "world_long": 3.0, "world_short": 1.5,
    "props": 12, "roles": 4, "specimen_share": 0.40, "target_share": 0.60,
    "prop_seen": 0.04, "twin_size": 0.05,
    "planes": 3, "plane_share": 0.55, "depth_ratio": 2.5,
    "regions": 3, "region_props": 2, "contrast": 7.0,
    "hue_gap": 25.0, "lum_gap": 0.12, "accent_hue_gap": 40.0, "grey_sat": 0.06,
    "wall": 1.5, "layer_seen": 0.08, "specimen_words": 12,
    "travel_full": 0.12, "passed_seen": 0.08, "samples": (0.25, 0.5, 0.75),
    "centred": 0.40, "centre_slack": 0.06,
    "move_px": 0.015, "move_pct": 50.0, "move_scale": 0.15, "move_rot": 6.0,
    "move_alpha": 0.5, "move_lum": 0.10, "move_hue": 25.0, "move_size_pct": 25.0,
    "prop_ink": 4.5, "channel_share": 0.5, "same_kind_run": 2, "stencil_share": 3,
    "glyph_share": 0.15, "material_share": 0.30,
    "prop_words": 60, "plate_words": 4, "lum_step": 0.04, "hue_step": 25.0,
    "hue_turn": 70.0,
    "sizes": 6, "size_ratio": 6.0, "big_px": 200.0, "small_px": 28.0,
    "small_apparent": 30.0, "families": (2, 3),
    "kinds": 4, "kind_share": 0.40, "dur": (0.6, 3.5),
    "push": 1.25, "pull": 0.80, "close_move": 1.0,
    "travel_move": 0.9, "travel_scale": 0.15,
    "arc_move": (0.15, 0.60), "arc_scale": 0.20, "arc_shear": 0.25, "scale_range": 4.0,
    "rest_share": 0.40, "long_holds": 3, "long_hold": 2.0, "longest_hold": 3.5,
    "run_gap": 0.8, "run": 3,
    "revisits": 2, "revisit_scale": 1.35, "revisit_move": 0.5,
    "open_share": 0.40, "close_share": 0.66, "close_changes": 3,
    "changes": 3, "event_share": 0.25,
}

FAULTS = []


def fault(rule, msg):
    FAULTS.append(f"  {rule:<14} {msg}")


# ------------------------------------------------------------------- colour
def rgb(c):
    c = c.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", c):
        return None
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lum(c):
    def lin(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def hue_sat(c):
    mx, mn = max(c), min(c)
    d = mx - mn
    if d == 0:
        return 0.0, 0.0
    r, g, b = c
    h = (60 * (((g - b) / d) % 6) if mx == r else
         60 * ((b - r) / d + 2) if mx == g else
         60 * ((r - g) / d + 4))
    return h % 360, d / mx


def hue_gap(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


# --------------------------------------------------------------- the markup
class Doc(HTMLParser):
    """Enough of a tree to answer two questions: what is inside the set view but
    outside every plane, and how many clips carry a picture."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []
        self.loose = []
        self.clips = []
        self.manifest = None
        self._grab = False
        self.sizes = []
        self.families = []
        self.plate = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        eid = a.get("id") or ""
        style = a.get("style") or ""
        self.sizes += [float(v) for v in re.findall(r"font-size:\s*([\d.]+)px", style)]
        self.families += re.findall(r"font-family:\s*([^;\"]+)", style)
        if "clip" in cls:
            self.clips.append((tag, eid))
        if "set-plate" in cls:
            self.plate += 1
        inview = any("set-view" in c for _t, c, _i in self.stack)
        inplane = any("set-plane" in c for _t, c, _i in self.stack)
        if inview and not inplane and "set-plane" not in cls:
            self.loose.append(eid or tag)
        if tag == "script" and a.get("type") == "application/json" and eid == "set-manifest":
            self._grab = True
        if tag not in ("br", "img", "input", "hr", "meta", "link", "source", "use", "path"):
            self.stack.append((tag, cls, eid))

    def handle_endtag(self, tag):
        self._grab = False
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._grab:
            self.manifest = json.loads(unescape(data))


# ------------------------------------------------------------------ camera
def layer(depth, shot, planes, frame):
    fw, fh = frame
    s = shot["s"] / depth
    f = planes[shot["focus"]]
    blur = min(DOF_MAX, DOF_K * abs(depth - f) / f * min(DOF_CAP_S, shot["s"]))
    return (round(fw / 2 - shot["cx"] * s, 3), round(fh / 2 - shot["cy"] * s, 3),
            round(s, 5), round(blur, 2))


def box_of(prop, shot, planes, frame):
    """A prop's projected box under one framing."""
    fw, fh = frame
    s = shot["s"] / planes[prop["plane"]]
    return ((prop["at"][0] - shot["cx"]) * s + fw / 2,
            (prop["at"][1] - shot["cy"]) * s + fh / 2,
            prop["size"][0] * s, prop["size"][1] * s)


def during(a, b, p):
    """The camera the renderer really shows at path fraction `p` of a move.

    Each plane's x, y and scale are tweened straight, so the scale runs linearly and
    the centre is the scale-weighted mix - the same camera for every plane, which is
    what makes this the frame the viewer sees rather than a guess at it."""
    s = (1 - p) * a["s"] + p * b["s"]
    return {"cx": ((1 - p) * a["cx"] * a["s"] + p * b["cx"] * b["s"]) / s,
            "cy": ((1 - p) * a["cy"] * a["s"] + p * b["cy"] * b["s"]) / s,
            "s": s, "focus": b["focus"], "on": b["on"]}


def covered(shot, props, planes, frame, skip=("surface",), keep=None):
    """How much of the frame carries something that is not the backdrop.

    Counted over a grid rather than summed, so stacking three props in one place
    does not read as three times the frame. `keep` narrows it to a set of props."""
    fw, fh = frame
    gx, gy = 64, 36
    cells = set()
    for p in props:
        if p["role"] in skip or (keep is not None and p["id"] not in keep):
            continue
        x, y, w, h = box_of(p, shot, planes, frame)
        for i in range(max(0, int(x / fw * gx)), min(gx, math.ceil((x + w) / fw * gx))):
            for j in range(max(0, int(y / fh * gy)), min(gy, math.ceil((y + h) / fh * gy))):
                cells.add((i, j))
    return len(cells) / (gx * gy)


def seen(prop, shot, planes, frame):
    """How much of the frame a prop covers under one framing, as a fraction."""
    fw, fh = frame
    x, y, w, h = box_of(prop, shot, planes, frame)
    ix = max(0.0, min(fw, x + w) - max(0.0, x))
    iy = max(0.0, min(fh, y + h) - max(0.0, y))
    return ix * iy / (fw * fh)


# ------------------------------------------------------------------ the timeline
STMT = re.compile(r'tl\.(fromTo|from|to|set)\(\s*"([^"]+)"\s*,(.*?)\)\s*;', re.S)
PAIR = re.compile(r'([A-Za-z]\w*)\s*:\s*("[^"]*"|[-+\d.eE]+|[^,}]+)')


def tweens(raw):
    out = []
    for m in STMT.finditer(raw):
        tail = m.group(3)
        objs = [dict((k, v.strip().strip('"')) for k, v in PAIR.findall(o))
                for o in re.findall(r"\{([^{}]*)\}", tail)]
        pos = re.search(r",\s*([\d.]+)\s*$", tail.strip())
        out.append({"how": m.group(1), "sel": m.group(2), "objs": objs,
                    "at": float(pos.group(1)) if pos else None})
    return out


def num(o, k):
    try:
        return float(o[k])
    except (KeyError, TypeError, ValueError):
        return None


def span(tw):
    """When a tween runs, as (start, end)."""
    if tw["at"] is None:
        return None
    d = num(tw["objs"][-1], "duration") if tw["objs"] else None
    return tw["at"], tw["at"] + (d or 0.0)


def moved(tw, k, frame):
    """Which channel a tween moves on and by how much, or None.

    Only a `fromTo` says. A `to` leaves its start off the page, so there is nothing
    to measure and nothing to prove - which is also why the engine prefers it that
    way for a deterministic render."""
    if tw["how"] != "fromTo" or len(tw["objs"]) < 2:
        return None
    a, b = tw["objs"][0], tw["objs"][1]
    fw, fh = frame
    for key, span in (("x", fw), ("y", fh), ("width", fw), ("height", fh)):
        p, q = num(a, key), num(b, key)
        if p is not None and q is not None and abs(q - p) * k / span >= R["move_px"]:
            return "shift", f"{key} by {abs(q - p) * k / span * 100:.1f}% of the frame"
    for key in ("xPercent", "yPercent"):
        p, q = num(a, key), num(b, key)
        if p is not None and q is not None and abs(q - p) >= R["move_pct"]:
            return "slide", f"{key} by {abs(q - p):.0f}"
    for key in ("scale", "scaleX", "scaleY"):
        p, q = num(a, key), num(b, key)
        if p is not None and q is not None and abs(q - p) >= R["move_scale"]:
            return "grow", f"{key} by {abs(q - p):.2f}"
    p, q = num(a, "rotation"), num(b, "rotation")
    if p is not None and q is not None and abs(q - p) >= R["move_rot"]:
        return "turn", f"rotation by {abs(q - p):.0f} degrees"
    for key in ("opacity", "autoAlpha"):
        p, q = num(a, key), num(b, key)
        if p is not None and q is not None and abs(q - p) >= R["move_alpha"]:
            return "fade", f"{key} by {abs(q - p):.2f}"
    for key in ("color", "backgroundColor", "borderColor", "fill", "stroke"):
        p, q = rgb(a.get(key, "")), rgb(b.get(key, ""))
        if p and q and (abs(lum(p) - lum(q)) >= R["move_lum"]
                        or hue_gap(hue_sat(p)[0], hue_sat(q)[0]) >= R["move_hue"]):
            return "light", f"{key} to another colour"
    return None


# ------------------------------------------------------------------- cueing
def norm(s):
    w = re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).lower())
    return w[:-1] if len(w) > 3 and w.endswith("s") else w


def cue_matches(tok, phrase):
    want = [norm(t) for t in phrase.split() if norm(t)]
    if not want:
        return []
    return [i for i in range(len(tok) - len(want) + 1) if tok[i:i + len(want)] == want]


def off_of(sh, on, by_id, planes, frame):
    """Where a framing puts its subject, measured off the frame rather than asked for -
    which is the number [CENTRED] reads."""
    if not on:
        return "-"
    bs = [box_of(by_id[pid], sh, planes, frame) for pid in on]
    cx = (min(b[0] for b in bs) + max(b[0] + b[2] for b in bs)) / 2
    cy = (min(b[1] for b in bs) + max(b[1] + b[3] for b in bs)) / 2
    return f"{max(abs(cx - frame[0] / 2) / frame[0], abs(cy - frame[1] / 2) / frame[1]) * 100:.0f}%"


def why(props, shots, legs, planes, frame, targets, by_id, subject):
    """Where every prop is seen and how much ground each move crosses.

    Placing props is the part of this format that cannot be done by eye: a prop's
    reach depends on its plane, and the ground a move crosses is not visible in any
    framing. Printed on demand with `--why`, beside whatever it refuses."""
    mid = [c for _b, cams in legs for c in cams]
    print(f"  {'prop':12s} {'role':9s} {'plane':5s} {'at a stop':>9s} {'in a move':>9s}  target")
    for p in props:
        a = max(seen(p, s, planes, frame) for s in shots)
        b = max([seen(p, c, planes, frame) for c in mid] or [0.0])
        print(f"  {p['id']:12s} {p['role']:9s} {p['plane']:5s} {a * 100:8.1f}% "
              f"{b * 100:8.1f}%  {'yes' if p['id'] in targets else '-'}")
    print(f"\n  {'move':24s} {'scale':>13s} {'frames':>7s}  "
          f"{'ground .25/.5/.75':14s} {'off':>6s}")
    for i, ((b, cams), a) in enumerate(zip(legs, shots)):
        mv = max(abs(b["cx"] - a["cx"]) * b["s"] / frame[0],
                 abs(b["cy"] - a["cy"]) * b["s"] / frame[1])
        g = "/".join(f"{covered(c, props, planes, frame) * 100:.0f}" for c in cams)
        print(f"  {b['kind'] + ' ' + str(b['cue'])[:18]:24s} "
              f"{a['s']:6.3f}->{b['s']:6.3f} {mv:7.2f}  {g:14s} "
              f"{off_of(b, subject[i + 1], by_id, planes, frame):>6s}")
    print()


def main(argv):
    show = "--why" in argv
    argv = [a for a in argv if a != "--why"]
    if len(argv) != 2:
        sys.exit("usage: set_check.py <composition>/index.html <composition>/transcript.json "
                 "[--why]")
    path, tpath = argv
    raw = open(path, encoding="utf8").read()
    doc = Doc()
    doc.feed(raw)
    if doc.manifest is None:
        sys.exit(f"{path} carries no set manifest - this is not a standing set, or it was "
                 f"not built through components/standing_set.py")
    m = doc.manifest
    frame = m["frame"]
    world = m["world"]
    planes = m["planes"]
    props = m["props"]
    shots = m["shots"]
    regions = m["regions"]
    fw, fh = frame
    n = len(props)
    by_id = {p["id"]: p for p in props}
    moves = shots[1:]
    # The frames BETWEEN the framings. Everything the format claims about travelling
    # through a space is a claim about these, and nothing else in this file could see
    # them.
    legs = [(b, [during(a, b, q) for q in R["samples"]]) for a, b in zip(shots, moves)]
    mid = [c for _b, cams in legs for c in cams]
    tl_all = tweens(raw)
    roots = {}
    for tw in tl_all:
        m2 = re.fullmatch(r"#pr-([\w-]+)", tw["sel"].strip())
        if m2:
            roots.setdefault(m2.group(1), []).append(tw)

    # --- A. the composition is a set, not a stack ---------------------------
    picture = [c for c in doc.clips if c[0] not in ("audio", "video")]
    if len(picture) != 1:
        fault("ONE CLIP", f"{len(picture)} picture clips ({', '.join(i or t for t, i in picture)}) "
                          f"- a standing set is one clip for the whole module, because a second "
                          f"clip is a second slide")
    for loose in doc.loose:
        fault("LOOSE", f"{loose!r} is inside the view but on no plane - everything the "
                       f"viewer sees stands in the world, except the one plate")
    if doc.plate > 1:
        fault("PLATES", f"{doc.plate} plates - a set fixes one thing to the frame")

    declared = {e["prop"] for e in m["events"]}
    staged = declared | {c["prop"] for c in m["changes"]}
    for pid, tws in roots.items():
        for tw in tws:
            a = tw["objs"][0] if tw["objs"] else {}
            # Every way of starting a prop off the frame, not only a fade. A prop held
            # at scale 0 or shoved a full box sideways is the same bullet.
            hidden = (any(num(a, k) == 0 for k in ("opacity", "autoAlpha", "scale",
                                                   "scaleX", "scaleY"))
                      or any(abs(num(a, k) or 0) >= 100 for k in ("xPercent", "yPercent")))
            if hidden and pid not in declared:
                fault("ARRIVES", f"prop {pid!r} starts off the frame and is not a declared "
                                 f"event - a prop that appears when the camera reaches it is "
                                 f"a bullet")
            if pid not in staged and any(
                    num(a, k) != num(tw["objs"][-1], k)
                    for k in ("x", "y", "xPercent", "yPercent")
                    if num(a, k) is not None or num(tw["objs"][-1], k) is not None):
                fault("RESTAGED", f"prop {pid!r} is moved by the timeline and is neither a "
                                  f"declared change nor an event - a prop stands where it was "
                                  f"placed; the camera goes to it")
    if len(m["events"]) > R["event_share"] * n:
        fault("ARRIVALS", f"{len(m['events'])} of {n} props arrive - at most "
                          f"{int(R['event_share'] * 100)}% of a set may be built in front of "
                          f"the viewer")

    # --- B. the space -------------------------------------------------------
    # Measured across the props, not across the declared world: a big empty world with
    # everything standing in one frame of it is still a poster.
    spread = (max(p["at"][0] + p["size"][0] for p in props) - min(p["at"][0] for p in props),
              max(p["at"][1] + p["size"][1] for p in props) - min(p["at"][1] for p in props))
    long_r = max(spread[0] / fw, spread[1] / fh)
    short_r = min(spread[0] / fw, spread[1] / fh)
    if long_r < R["world_long"] or short_r < R["world_short"]:
        fault("SMALL WORLD", f"the props stand across {long_r:.2f} frames on the long axis and "
                             f"{short_r:.2f} on the short - a standing set is at least "
                             f"{R['world_long']}x{R['world_short']} of OCCUPIED space, or the "
                             f"camera is panning over a poster")
    if n < R["props"]:
        fault("THIN SET", f"{n} props - a set carries at least {R['props']}, or the camera "
                          f"travels through nothing")
    roles = {p["role"] for p in props}
    if len(roles) < R["roles"]:
        fault("ONE NOTE", f"{len(roles)} role(s) ({', '.join(sorted(roles))}) - a set holds at "
                          f"least {R['roles']} different things")
    # This format is not illustration-led. The set is built out of the real material -
    # screens, code, measured figures, documents - and icons are the seasoning.
    glyphs = sum(1 for p in props if p["role"] == "glyph")
    if glyphs > R["glyph_share"] * n:
        fault("DRAWN NOT SHOWN", f"{glyphs} of {n} props are glyphs - at most "
                                 f"{int(R['glyph_share'] * 100)}%. An icon stands for a thing; "
                                 f"this format shows the thing")
    material = sum(1 for p in props if p["role"] in ("screen", "code", "chart", "diagram"))
    if material < R["material_share"] * n:
        fault("DRAWN NOT SHOWN", f"{material} of {n} props carry real material (a screen, code, "
                                 f"a measured figure, a diagram) - at least "
                                 f"{int(R['material_share'] * 100)}%, or the set is decoration "
                                 f"with labels on it")
    spec = sum(1 for p in props if p["role"] == "specimen")
    if spec > R["specimen_share"] * n:
        fault("ALL WORDS", f"{spec} of {n} props are specimens - a set made of type is a deck "
                           f"laid on its side")
    targets = {pid for s in shots for pid in s["on"]}
    if len(targets) > R["target_share"] * n:
        fault("ALL STOPS", f"{len(targets)} of {n} props are framing targets - at most "
                           f"{int(R['target_share'] * 100)}% may be destinations, or the set is "
                           f"slides laid side by side")
    for p in props:
        best = max(seen(p, s, planes, frame) for s in shots + mid)
        if best < R["prop_seen"]:
            fault("UNSEEN", f"prop {p['id']!r} never covers {R['prop_seen'] * 100:.0f}% of the "
                            f"frame (best {best * 100:.1f}%) - it is in the file and not in the "
                            f"film")
    # The other half of the same rule: a prop that is not a destination has to be
    # something the camera PASSES. One that only ever shows up where the camera
    # stopped is a destination that was not named.
    for p in props:
        if p["id"] in targets or p["role"] == "surface":
            continue
        best = max([seen(p, c, planes, frame) for c in mid] or [0.0])
        if best < R["passed_seen"]:
            fault("ALL STOPS", f"prop {p['id']!r} is not a framing target and never reaches "
                               f"{R['passed_seen'] * 100:.0f}% of the frame during a move "
                               f"(best {best * 100:.1f}%) - it stands where the camera stopped, "
                               f"so it is a destination that forgot to be named")
    for i in range(n):
        for j in range(i + 1, n):
            a, b = props[i], props[j]
            if a["role"] != b["role"]:
                continue
            if all(abs(a["size"][k] - b["size"][k]) <= R["twin_size"] * b["size"][k]
                   for k in (0, 1)):
                fault("TWINS", f"props {a['id']!r} and {b['id']!r} are the same role at the same "
                               f"size - repeated identical objects belong inside one prop, not "
                               f"beside each other like cards on a slide")
    # The same rule, looking at the drawing instead of the numbers. A set furnished by
    # calling one helper twelve times is one prop twelve times.
    drawn = collections.defaultdict(list)
    cut = collections.defaultdict(list)
    for p in props:
        if p.get("shape"):
            drawn[p["shape"]].append(p["id"])
            cut[p["stencil"]].append(p["id"])
    for ids in drawn.values():
        if len(ids) > 1:
            fault("TWINS", f"props {', '.join(repr(i) for i in ids)} are the same drawing with "
                           f"different words on it - a set furnished from one helper is one prop "
                           f"repeated, and a room of identical objects is a stock photograph")
    for ids in cut.values():
        if len(ids) > R["stencil_share"]:
            fault("TWINS", f"{len(ids)} props ({', '.join(repr(i) for i in ids)}) are cut from "
                           f"one stencil with the numbers changed - at most "
                           f"{R['stencil_share']} may share a construction")
    NEEDS = {
        "screen":   (lambda k: k["fig"],
                     "a frame from components/figure.py; a product screen is measured, "
                     "never typed out (ADR-0010)"),
        "glyph":    (lambda k: k["svg"] or k["img"], "an <svg> or an <img>"),
        "chart":    (lambda k: k["svg"] or k["geom"] >= 3, "an <svg> or 3 drawn parts"),
        "diagram":  (lambda k: k["svg"] or k["geom"] >= 3, "an <svg> or 3 drawn parts"),
        "surface":  (lambda k: k["svg"] or k["img"] or k["geom"] >= 2,
                     "anything drawn on it; a wall is built, not an empty div"),
        "code":     (lambda k: k["mono"], "a monospace family"),
        "artifact": (lambda k: k["svg"] or k["img"] or k["geom"] >= 1,
                     "a drawn face; an object is looked at, not captioned"),
    }
    for p in props:
        want = NEEDS.get(p["role"])
        k = p.get("markup")
        if want and k and not want[0](k):
            fault("ROLE", f"prop {p['id']!r} claims the role {p['role']!r} and carries no "
                          f"{want[1]}. A role is what a prop is made of, not a word typed "
                          f"beside it")
    used = {p["plane"] for p in props}
    if len(used) < R["planes"]:
        fault("FLAT", f"{len(used)} plane(s) carry props - a set has at least {R['planes']}, or "
                      f"it has no depth to travel through")
    for pl in used:
        c = sum(1 for p in props if p["plane"] == pl)
        if c > R["plane_share"] * n:
            fault("FLAT", f"{c} of {n} props are on plane {pl!r} - no plane carries more than "
                          f"{int(R['plane_share'] * 100)}%")
    if used:
        ds = [planes[p] for p in used]
        if max(ds) / min(ds) < R["depth_ratio"]:
            fault("SHALLOW", f"the populated planes span {max(ds) / min(ds):.2f}x in depth - "
                             f"at least {R['depth_ratio']}x, or the parallax is invisible")

    # --- C. palette ---------------------------------------------------------
    if len(regions) < R["regions"]:
        fault("ONE PALETTE", f"{len(regions)} region(s) - a set changes palette as the camera "
                             f"travels, and that needs at least {R['regions']} places")
    greys = 0
    for r in regions:
        g, ink, acc = rgb(r["ground"]), rgb(r["ink"]), rgb(r["accent"])
        if g is None or ink is None or acc is None:
            fault("COLOUR", f"region {r['name']!r} has a colour this cannot read - write "
                            f"grounds, inks and accents as hex")
            continue
        c = contrast(ink, g)
        if c < R["contrast"]:
            fault("UNREADABLE", f"region {r['name']!r} sets ink on ground at {c:.1f}:1 - "
                                f"{R['contrast']}:1 or better, because type in this format is "
                                f"read at depth and through blur")
        if hue_sat(g)[1] < R["grey_sat"]:
            greys += 1
        held = sum(1 for p in props if p["region"] == r["name"])
        if held < R["region_props"]:
            fault("EMPTY REGION", f"region {r['name']!r} holds {held} prop(s) - a region with "
                                  f"nothing in it is paint, not a place")
    if greys > 1:
        fault("GREY", f"{greys} regions have a near-neutral ground - one may be neutral, the "
                      f"rest are colours")

    grounds = {r["name"]: rgb(r["ground"]) for r in regions}
    for p in props:
        g = grounds.get(p["region"])
        for raw_c in (p.get("markup") or {}).get("colours", []):
            v = raw_c.strip()
            if v.startswith("var(") or v in ("none", "transparent", "currentColor"):
                continue
            c = rgb(v)
            if c is None:
                fault("COLOUR", f"prop {p['id']!r} paints {v!r}, which this cannot read - a "
                                f"colour inside a prop is a house variable or a hex, so it "
                                f"can be held to its own ground")
            elif g and contrast(c, g) < R["prop_ink"]:
                fault("UNREADABLE", f"prop {p['id']!r} paints {v} on region "
                                    f"{p['region']!r}'s ground at {contrast(c, g):.1f}:1 - "
                                    f"{R['prop_ink']}:1 or better, or the region's declared ink "
                                    f"is a promise the props do not keep")

    def adjacent(a, b):
        ax, ay, aw, ah = a["box"]
        bx, by, bw, bh = b["box"]
        touch_x = abs(ax + aw - bx) < 1 or abs(bx + bw - ax) < 1
        touch_y = abs(ay + ah - by) < 1 or abs(by + bh - ay) < 1
        over_x = ax < bx + bw and bx < ax + aw
        over_y = ay < by + bh and by < ay + ah
        return (touch_x and over_y) or (touch_y and over_x)

    for i, a in enumerate(regions):
        for b in regions[i + 1:]:
            if not adjacent(a, b):
                continue
            ga, gb = rgb(a["ground"]), rgb(b["ground"])
            aa, ab = rgb(a["accent"]), rgb(b["accent"])
            if not all((ga, gb, aa, ab)):
                continue
            dh, dl = hue_gap(hue_sat(ga)[0], hue_sat(gb)[0]), abs(lum(ga) - lum(gb))
            if dh < R["hue_gap"] and dl < R["lum_gap"]:
                fault("SAME ROOM", f"regions {a['name']!r} and {b['name']!r} meet and differ by "
                                   f"{dh:.0f}deg of hue and {dl:.3f} of luminance - crossing the "
                                   f"boundary shows nothing")
            da = hue_gap(hue_sat(aa)[0], hue_sat(ab)[0])
            if da < R["accent_hue_gap"]:
                fault("SAME ACCENT", f"regions {a['name']!r} and {b['name']!r} meet and their "
                                     f"accents are {da:.0f}deg apart - each place has its own")

    deep = max((planes[p] for p in used), default=1.0)
    for r in regions:
        if not any(p["region"] == r["name"] and p["role"] == "surface"
                   and planes[p["plane"]] == deep
                   and (p["size"][0] >= R["wall"] * fw or p["size"][1] >= R["wall"] * fh)
                   for p in props):
            fault("NO ARCHITECTURE", f"region {r['name']!r} has no surface on the deepest plane "
                                     f"at least {R['wall']} frames across - props stand in a "
                                     f"built space, not in a void with a colour behind it")

    # The palette goes somewhere. In the order the camera first enters the regions,
    # the grounds either get steadily lighter or steadily darker, or their hue turns
    # one way. Three unrelated palettes are three decks.
    entered, order_r = [], []
    for sh in shots:
        for pid in sh["on"]:
            rn = by_id[pid]["region"]
            if rn not in entered:
                entered.append(rn)
    order_r = [next((r for r in regions if r["name"] == nm), None) for nm in entered]
    order_r = [r for r in order_r if r and rgb(r["ground"])]
    if len(order_r) >= 3:
        ls = [lum(rgb(r["ground"])) for r in order_r]
        hs = [hue_sat(rgb(r["ground"]))[0] for r in order_r]
        mono = (all(b - a >= R["lum_step"] for a, b in zip(ls, ls[1:])) or
                all(a - b >= R["lum_step"] for a, b in zip(ls, ls[1:])))
        def turn(sign):
            total = 0.0
            for a, b in zip(hs, hs[1:]):
                step = ((b - a) * sign) % 360
                if not (R["hue_step"] <= step <= 180):
                    return False
                total += step
            return total >= R["hue_turn"]
        if not (mono or turn(1) or turn(-1)):
            fault("NO PROGRESSION", f"the grounds in the order the camera meets them "
                                    f"({' -> '.join(r['name'] for r in order_r)}) neither "
                                    f"lighten nor darken by {R['lum_step']} a step, nor turn "
                                    f"{R['hue_step']:.0f}deg a step one way - a palette that "
                                    f"goes nowhere is three decks in three colours")

    bounds_x = sorted({r["box"][0] for r in regions} | {r["box"][0] + r["box"][2]
                                                        for r in regions})[1:-1]
    bounds_y = sorted({r["box"][1] for r in regions} | {r["box"][1] + r["box"][3]
                                                        for r in regions})[1:-1]
    crossed = False
    for a, b in zip(shots, shots[1:]):
        if any(min(a["cx"], b["cx"]) < v < max(a["cx"], b["cx"]) for v in bounds_x):
            crossed = True
        if any(min(a["cy"], b["cy"]) < v < max(a["cy"], b["cy"]) for v in bounds_y):
            crossed = True
    if regions and not crossed:
        fault("NO CROSSING", "no move carries the camera over a region boundary - the palette "
                             "changes because the camera goes somewhere, not because a slide "
                             "turned")

    # --- D. type ------------------------------------------------------------
    # Counted off the props, so six declared sizes that nothing is set in do not pass.
    sizes = sorted({round(v, 1) for p in props for v in p["px"]})
    if len(sizes) < R["sizes"]:
        fault("ONE SIZE", f"{len(sizes)} type size(s) in the document - a set needs at least "
                          f"{R['sizes']}, because a headline and a body size is a slide")
    elif max(sizes) / min(sizes) < R["size_ratio"]:
        fault("NO SCALE", f"the type runs {min(sizes):.0f}px to {max(sizes):.0f}px "
                          f"({max(sizes) / min(sizes):.1f}x) - at least {R['size_ratio']}x, or "
                          f"nothing is worth travelling to read")
    if re.search(r"<ul\b|<ol\b|&bull;|•|‣|▪", raw, re.I):
        fault("BULLETS", "the set contains a list - a bulleted list is the thing this format "
                         "exists instead of")
    fams = {f.strip().strip("'\"").split(",")[0].strip().strip("'\"").lower()
            for f in doc.families + re.findall(r"font-family:\s*([^;}\"]+)", raw)}
    fams = {f for f in fams if f and f not in
            ("inherit", "initial", "unset", "sans-serif", "serif", "monospace", "system-ui")}
    lo, hi = R["families"]
    if not (lo <= len(fams) <= hi):
        fault("FAMILIES", f"{len(fams)} type families ({', '.join(sorted(fams)) or 'none'}) - a "
                          f"set uses {lo} to {hi}, so the voice changes where the material does")
    if not any(p["px"] and max(p["px"]) >= R["big_px"] for p in props):
        fault("NO SCALE", f"no prop sets type at {R['big_px']:.0f}px or more - a set holds type "
                          f"as an object, at a size the camera has to back off to read")
    small = [p for p in props if p["px"] and min(p["px"]) <= R["small_px"]]
    if not small:
        fault("NO DETAIL", f"no prop sets type at {R['small_px']:.0f}px or less - a set holds "
                           f"something the wide shot cannot read, or the camera never earns a "
                           f"push")
    else:
        ok = False
        for p in small:
            for s in shots:
                if p["id"] in s["on"] and min(p["px"]) * s["s"] / planes[p["plane"]] >= \
                        R["small_apparent"]:
                    ok = True
        if not ok:
            fault("NEVER READ", f"the smallest type in the set is never framed close enough to "
                                f"read ({R['small_apparent']:.0f}px on the frame) - detail "
                                f"nobody can reach is not detail")

    words = json.load(open(tpath, encoding="utf8"))
    tok = [norm(w["text"]) for w in words]
    spoken = words[-1]["end"] if words else m["end"]

    for p in props:
        cap = R["specimen_words"] if p["role"] == "specimen" else R["prop_words"]
        if p["words"] > cap:
            fault("WALL OF TEXT", f"prop {p['id']!r} carries {p['words']} words against a cap of "
                                  f"{cap} - a specimen is type as an object and every other prop "
                                  f"is a thing, not a paragraph nobody can read at depth")
    if m["plate"] is not None and m["plate"] > R["plate_words"]:
        fault("PLATE", f"the plate carries {m['plate']} words - it is a mark on the frame, not a "
                       f"place to say something; say it in the world")
    if re.search(r'tl\.\w+\(\s*"#set-plate', raw):
        fault("PLATE", "the timeline animates the plate - the one thing fixed to the frame holds "
                       "still, or it is a slide element in disguise")

    subject, last_on = [], []
    for sh in shots:
        last_on = sh["on"] or last_on
        subject.append(last_on)
    for sh, on in zip(shots, subject):
        home = {by_id[pid]["plane"] for pid in on} or {sh["focus"]}
        # Everything standing at another distance, taken together: a wide shot is
        # layered by its whole depth rather than by one big prop in it.
        others = {p["id"] for p in props if p["plane"] not in home}
        if covered(sh, props, planes, frame, skip=(), keep=others) < R["layer_seen"]:
            fault("FLAT FRAME", f"the framing on {sh['cue'] or 'the opening'!r} carries nothing "
                                f"from another plane at {R['layer_seen'] * 100:.0f}% of the "
                                f"frame - one object against a background is a slide, whatever "
                                f"brought the camera there")
    # A centred, level, still subject is the deck's own atom. One is a payoff; every
    # one is a gallery.
    dead = []
    for sh, on in zip(shots, subject):
        if not on:
            continue
        bs = [box_of(by_id[pid], sh, planes, frame) for pid in on]
        cx = (min(b[0] for b in bs) + max(b[0] + b[2] for b in bs)) / 2
        cy = (min(b[1] for b in bs) + max(b[1] + b[3] for b in bs)) / 2
        if abs(cx - fw / 2) / fw <= R["centre_slack"] and \
                abs(cy - fh / 2) / fh <= R["centre_slack"]:
            dead.append(sh["cue"] or "the opening")
    if len(dead) > R["centred"] * len(shots):
        fault("CENTRED", f"{len(dead)} of {len(shots)} framings put their subject dead centre "
                         f"within {R['centre_slack'] * 100:.0f}% of the frame - at most "
                         f"{int(R['centred'] * 100)}% may; offset the rest with `off=`")

    # --- E. the camera ------------------------------------------------------
    # The frames between the framings. A film that clusters its props at the stops and
    # flies over bare ground between them passes every other rule in this file.
    for b, cams in legs:
        thin = [(q, covered(c, props, planes, frame)) for q, c in zip(R["samples"], cams)]
        worst = min(thin, key=lambda t: t[1])
        if worst[1] < R["travel_full"]:
            fault("EMPTY TRAVEL", f"the {b['kind']} on {b['cue']!r} crosses ground carrying "
                                  f"{worst[1] * 100:.1f}% of the frame at "
                                  f"{worst[0]:.0%} through (backdrop not counted) - at least "
                                  f"{R['travel_full'] * 100:.0f}% the whole way, or the camera "
                                  f"is over a blank wall and this is a transition")
    kinds = [s["kind"] for s in moves]
    if len(set(kinds)) < R["kinds"]:
        fault("ONE MOVE", f"{len(set(kinds))} move kind(s) ({', '.join(sorted(set(kinds)))}) - "
                          f"a camera that only does one thing is a transition")
    for k in set(kinds):
        if kinds.count(k) > R["kind_share"] * len(moves):
            fault("ONE MOVE", f"{kinds.count(k)} of {len(moves)} moves are {k!r} - no kind is "
                              f"more than {int(R['kind_share'] * 100)}%")
    dlo, dhi = R["dur"]
    for s in moves:
        if not (dlo <= s["dur"] <= dhi):
            fault("PACE", f"the {s['kind']} on {s['cue']!r} runs {s['dur']}s - a move is "
                          f"{dlo}s to {dhi}s; split a long travel into legs with a beat between")
    for a, b in zip(shots, moves):
        ratio = b["s"] / a["s"]
        # How far the camera went, in frames, at the scale it arrived at - the larger
        # axis, because a move that crosses the frame vertically crossed the frame.
        move = max(abs(b["cx"] - a["cx"]) * b["s"] / fw,
                   abs(b["cy"] - a["cy"]) * b["s"] / fh)
        if b["kind"] in ("push", "pull"):
            want = R["push"] if b["kind"] == "push" else R["pull"]
            if (ratio < want) if b["kind"] == "push" else (ratio > want):
                fault(f"NOT A {b['kind'].upper()}",
                      f"the {b['kind']} on {b['cue']!r} changes scale {ratio:.2f}x - a push is "
                      f"at least {R['push']}x closer and a pull at most {R['pull']}x")
            if move > R["close_move"]:
                fault(f"NOT A {b['kind'].upper()}",
                      f"the {b['kind']} on {b['cue']!r} also crosses {move:.2f} frames - past "
                      f"{R['close_move']} it has gone somewhere else, which is a travel")
        if b["kind"] == "travel":
            if move < R["travel_move"]:
                fault("NOT A TRAVEL", f"the travel on {b['cue']!r} moves {move:.2f} frames - a "
                                      f"travel crosses at least {R['travel_move']}; anything "
                                      f"shorter is a nudge")
            if abs(ratio - 1) > R["travel_scale"]:
                fault("NOT A TRAVEL", f"the travel on {b['cue']!r} also changes scale "
                                      f"{ratio:.2f}x - travel goes somewhere, push and pull "
                                      f"change how close you are, and one move does one of them")
        if b["kind"] == "arc":
            lo_m, hi_m = R["arc_move"]
            here = {p["plane"] for p in props if seen(p, b, planes, frame) > 0.01}
            depths = sorted(planes[pl] for pl in here)
            shear = (max(abs(b["cx"] - a["cx"]) / fw, abs(b["cy"] - a["cy"]) / fh) * b["s"] *
                     (1 / depths[0] - 1 / depths[-1])) if len(depths) > 1 else 0.0
            if not (lo_m <= move <= hi_m):
                fault("NOT AN ARC", f"the arc on {b['cue']!r} crosses {move:.2f} frames - an arc "
                                    f"is a close move of {lo_m} to {hi_m}; further than that it "
                                    f"is a travel and nothing turns")
            if abs(ratio - 1) > R["arc_scale"]:
                fault("NOT AN ARC", f"the arc on {b['cue']!r} changes scale {ratio:.2f}x - an "
                                    f"arc goes around something, it does not approach it")
            if shear < R["arc_shear"]:
                fault("NOT AN ARC", f"the arc on {b['cue']!r} shears its planes {shear:.2f} "
                                    f"frames - at least {R['arc_shear']}, and that needs near "
                                    f"AND far in the same frame; an arc is parallax or it is a "
                                    f"nudge")
        if b["kind"] == "rack":
            if abs(b["cx"] - a["cx"]) > 1 or abs(b["cy"] - a["cy"]) > 1 or \
                    abs(ratio - 1) > 0.02:
                fault("NOT A RACK", f"the rack on {b['cue']!r} also moves the camera - a rack "
                                    f"holds still and moves the focus")
            if b["focus"] == a["focus"]:
                fault("NOT A RACK", f"the rack on {b['cue']!r} focuses where it already was")
    run = 1
    for a, b in zip(kinds, kinds[1:]):
        run = run + 1 if a == b else 1
        if run > R["same_kind_run"]:
            fault("ONE MOVE", f"{run} {b} moves in a row - a move is spent on the change of "
                              f"view the words just asked for, and leaning on one is a habit "
                              f"rather than a choice")
    ss = [s["s"] for s in shots]
    if max(ss) / min(ss) < R["scale_range"]:
        fault("ONE DISTANCE", f"the camera works over {max(ss) / min(ss):.2f}x of scale - at "
                              f"least {R['scale_range']}x, or it never goes anywhere near or far")

    # rest
    gaps = []
    for a, b in zip(shots, moves):
        gaps.append((a["at"] + (a["dur"] or 0.0), b["at"] - (a["at"] + (a["dur"] or 0.0))))
    tail = m["end"] - (shots[-1]["at"] + (shots[-1]["dur"] or 0.0))
    gaps.append((shots[-1]["at"] + (shots[-1]["dur"] or 0.0), tail))
    rest = sum(max(0.0, g) for _t, g in gaps)
    if rest < R["rest_share"] * m["end"]:
        fault("NO REST", f"the camera is still for {rest:.1f}s of {m['end']:.1f}s "
                         f"({rest / m['end'] * 100:.0f}%) - at least "
                         f"{int(R['rest_share'] * 100)}%, because meaning is made where it lands")
    longs = [(t0, g) for t0, g in gaps if g >= R["long_hold"]]
    if len(longs) < R["long_holds"]:
        fault("NO REST", f"{len(longs)} hold(s) of {R['long_hold']}s or more - at least "
                         f"{R['long_holds']}")
    if gaps and max(g for _t, g in gaps) < R["longest_hold"]:
        fault("NO REST", f"the longest hold is {max(g for _t, g in gaps):.1f}s - one hold of at "
                         f"least {R['longest_hold']}s, or nothing in the film is allowed to land")
    acts = [e["at"] for e in m["events"]] + [c["at"] for c in m["changes"]]
    for t0, g in longs:
        if min(t0 + g, spoken) - t0 < R["long_hold"]:
            continue               # after the last word the film is allowed to be still
        if not any(t0 - 0.2 <= a <= t0 + g + 0.2 for a in acts):
            fault("DEAD HOLD", f"the hold at {t0:.1f}s runs {g:.1f}s with nothing happening in "
                               f"it - a hold carries an event or a change, or the frame is "
                               f"waiting")
    run = 1
    for a, b in zip(moves, moves[1:]):
        gap = b["at"] - (a["at"] + a["dur"])
        run = run + 1 if gap < R["run_gap"] else 1
        if run >= R["run"]:
            fault("NO LANDING", f"the moves around {b['cue']!r} run {run} deep without landing "
                                f"- the camera arrives somewhere every second move")

    # revisits
    revisits = 0
    for pid in sorted(targets):
        at = [i for i, s in enumerate(shots) if pid in s["on"]]
        for i, j in zip(at, at[1:]):
            if j - i < 2:
                continue
            a, b = shots[i], shots[j]
            if max(b["s"] / a["s"], a["s"] / b["s"]) >= R["revisit_scale"] or \
                    max(abs(b["cx"] - a["cx"]) * b["s"] / fw,
                        abs(b["cy"] - a["cy"]) * b["s"] / fh) >= R["revisit_move"]:
                revisits += 1
                break
    if revisits < R["revisits"]:
        fault("NO RETURN", f"{revisits} prop(s) are framed again later from somewhere else - at "
                           f"least {R['revisits']}, or the set is a corridor and nothing in it "
                           f"persists")

    # the ends
    first, last = shots[0], shots[-1]
    o_seen = sum(1 for p in props if seen(p, first, planes, frame) > 0)
    c_seen = sum(1 for p in props if seen(p, last, planes, frame) > 0)
    if o_seen > R["open_share"] * n:
        fault("OPENS WIDE", f"the opening framing shows {o_seen} of {n} props - it shows at most "
                            f"{int(R['open_share'] * 100)}%, because the set is discovered, not "
                            f"presented")
    if c_seen < R["close_share"] * n:
        fault("NO PAYOFF", f"the closing framing shows {c_seen} of {n} props - it shows at least "
                           f"{int(R['close_share'] * 100)}%, because the last thing the viewer "
                           f"gets is the whole space they have been through")
    changed = {c["prop"] for c in m["changes"]}
    in_close = sum(1 for p in props if p["id"] in changed and seen(p, last, planes, frame) > 0)
    if in_close < R["close_changes"]:
        fault("NO PAYOFF", f"the closing framing shows {in_close} changed prop(s) - at least "
                           f"{R['close_changes']}, or the set ends exactly as it started")
    if abs(first["cx"] - last["cx"]) * last["s"] / fw < 0.3 and \
            abs(first["s"] / last["s"] - 1) < 0.05:
        fault("NO PAYOFF", "the closing framing is the opening framing - the film ends where it "
                           "began and nothing was learned by going")

    # --- F. change and cue --------------------------------------------------
    if len(m["changes"]) < R["changes"]:
        fault("STATIC", f"{len(m['changes'])} declared change(s) - at least {R['changes']}: the "
                        f"set is in a different state at the end than at the start")
    # A declared change has to BE one: written as a fromTo so both states are on the
    # page, moving something a viewer can see, on the beat that announces it, and not
    # on the wall - a backdrop does not do anything.
    per_prop = collections.Counter(c["prop"] for c in m["changes"])
    for pid, cnt in per_prop.items():
        if cnt > 1:
            fault("STATIC", f"prop {pid!r} carries {cnt} declared changes - one prop, one "
                            f"change, or three changes is three lines about one thing")
    channels = []
    acts = []                      # (what it is, when it runs) for every declared act
    for c in m["changes"]:
        prop = by_id[c["prop"]]
        if prop["role"] == "surface":
            fault("STATIC", f"change {c['note']!r} is declared on {c['prop']!r}, which is a "
                            f"surface - a wall does not do anything, and a change on the "
                            f"backdrop is a change nobody sees")
            continue
        sh = [x for x in shots if x["at"] <= c["at"] + 1e-6][-1]
        k = sh["s"] / planes[prop["plane"]]
        mine = [tw for tw in tl_all
                if re.match(rf"#pr-{re.escape(c['prop'])}(?![\w-])", tw["sel"].strip())]
        if not mine:
            fault("STATIC", f"change {c['note']!r} on {c['prop']!r} is declared and nothing in "
                            f"the timeline touches that prop")
            continue
        big = [(tw, moved(tw, k, frame)) for tw in mine]
        big = [(tw, ch, why) for tw, got in big if got for ch, why in [got]]
        if not big:
            fault("STATIC", f"change {c['note']!r} on {c['prop']!r} moves nothing a viewer can "
                            f"see. A change is written as a fromTo and shifts the prop "
                            f"{R['move_px'] * 100:.1f}% of the frame, half its own box, "
                            f"{R['move_scale']} of scale, {R['move_rot']:.0f} degrees, "
                            f"{R['move_alpha']} of opacity, or to another colour")
            continue
        channels.append(big[0][1])
        runs = [span(tw) for tw, _c, _w in big if span(tw)]
        if runs:
            acts.append((f"the change {c['note']!r}",
                         (min(r[0] for r in runs), max(r[1] for r in runs))))
        if not any(tw["at"] is None or abs(tw["at"] - c["at"]) <= 1.0 for tw, _c, _w in big):
            near = min((tw["at"] for tw, _c, _w in big if tw["at"] is not None),
                       key=lambda a: abs(a - c["at"]), default=None)
            fault("OFF ITS BEAT", f"change {c['note']!r} is cued on {c['cue']!r} at "
                                  f"{c['at']:.1f}s and the nearest tween that moves "
                                  f"{c['prop']!r} is at {near:.1f}s - a change happens on the "
                                  f"word that announces it (ADR-0003)")
    for e in m["events"]:
        runs = [span(tw) for tw in roots.get(e["prop"], []) if span(tw)]
        if runs:
            acts.append((f"the event {e['note']!r}",
                         (min(r[0] for r in runs), max(r[1] for r in runs))))

    # The set performs in more than one way.
    seen_ch = collections.Counter(channels)
    if seen_ch and max(seen_ch.values()) > R["channel_share"] * len(m["changes"]):
        top, cnt = seen_ch.most_common(1)[0]
        fault("STATIC", f"{cnt} of {len(m['changes'])} changes are the same gesture ({top}) - "
                        f"at most {int(R['channel_share'] * 100)}% may be. A lamp lifting, a "
                        f"count climbing and a contract being signed are not one animation "
                        f"three times")

    # RESTRAINT. The eye is given one thing: the camera crossing the room, or one thing
    # in the room doing one thing. Two at once is noise, and noise reads as cheap
    # however well each half is made.
    for what, (t0, t1) in acts:
        for sh in moves:
            if t0 < sh["at"] + sh["dur"] - 0.05 and sh["at"] < t1 - 0.05:
                fault("TWO AT ONCE", f"{what} runs while the camera is in the {sh['kind']} on "
                                     f"{sh['cue']!r} - the camera moves or the set does, never "
                                     f"both at once")
                break
    for i, (w1, (a0, a1)) in enumerate(acts):
        for w2, (b0, b1) in acts[i + 1:]:
            if a0 < b1 - 0.05 and b0 < a1 - 0.05:
                fault("TWO AT ONCE", f"{w1} and {w2} run together - one thing moves at a time, "
                                     f"or the frame is busy rather than alive")

    live = {}
    for e in m["events"]:
        s = [sh for sh in shots if sh["at"] <= e["at"] + 1e-6][-1]
        if seen(by_id[e["cause"]], s, planes, frame) <= 0.005:
            fault("UNCAUSED", f"the event on {e['cue']!r} is caused by {e['cause']!r}, which is "
                              f"not on screen when it fires - an arrival is caused by something "
                              f"the viewer can see")

    cues = ([(s["cue"], f"the {s['kind']} move") for s in moves] +
            [(e["cue"], "an event") for e in m["events"]] +
            [(c["cue"], "a change") for c in m["changes"]])
    for cue, what in cues:
        if isinstance(cue, (list, tuple)):
            continue                   # an occurrence was named: the author has said which
        at = cue_matches(tok, cue)
        if not at:
            fault("NOT SPOKEN", f"{what} is cued on {cue!r}, which is not in the narration")
        elif len(at) > 1:
            fault("AMBIGUOUS", f"{what} is cued on {cue!r}, said {len(at)} times at "
                               f"{[round(words[i]['start'], 2) for i in at]} - name the "
                               f"occurrence")

    # --- G. the numbers are computed ---------------------------------------
    TWEEN = re.compile(r'tl\.fromTo\(\s*"#sp-([\w-]+)"\s*,\s*\{x:(-?[\d.]+),y:(-?[\d.]+),'
                       r'scale:([\d.]+),filter:"blur\(([\d.]+)px\)"\}\s*,\s*\{x:(-?[\d.]+),'
                       r'y:(-?[\d.]+),scale:([\d.]+),filter:"blur\(([\d.]+)px\)",'
                       r'duration:([\d.]+),ease:"[^"]+"\}\s*,\s*([\d.]+)\)')
    got = TWEEN.findall(raw)
    order = [("ground", 1.0)] + sorted(planes.items(), key=lambda kv: -kv[1])
    want = []
    for a, b in zip(shots, moves):
        for name, depth in order:
            want.append((name, layer(depth, a, planes, frame),
                         layer(depth, b, planes, frame), round(b["dur"], 3),
                         round(b["at"], 3)))
    if len(got) != len(want):
        fault("HAND-DRIVEN", f"{len(got)} camera tween(s) in the timeline against {len(want)} "
                             f"the set describes - the camera is written by "
                             f"components/standing_set.py and nowhere else")
    else:
        # Both sides compute from the manifest's own rounded framings, so the only
        # slack needed is the last digit of a blur that landed on a tie.
        TOL = (0, 0.005, 0.005, 0.005, 0.011, 0.005, 0.005, 0.005, 0.011, 0.005, 0.005)
        for g, w in zip(got, want):
            mine = (w[0], w[1][0], w[1][1], w[1][2], w[1][3],
                    w[2][0], w[2][1], w[2][2], w[2][3], w[3], w[4])
            theirs = (g[0],) + tuple(float(v) for v in g[1:])
            if any(a != b if isinstance(a, str) else abs(a - b) > tol
                   for a, b, tol in zip(mine, theirs, TOL)):
                fault("HAND-DRIVEN", f"the camera tween on plane {g[0]!r} at {g[10]}s is not the "
                                     f"framing the set describes - a camera position typed by "
                                     f"hand rings the wrong control (ADR-0010)")
                break

    print(f"{path}")
    print(f"  {n} props on {len(used)} planes, {len(regions)} regions, {len(moves)} moves, "
          f"{rest / m['end'] * 100:.0f}% held")
    if show:
        why(props, shots, legs, planes, frame, targets, by_id, subject)
    for f in FAULTS:
        print(f)
    if FAULTS:
        sys.exit(f"{len(FAULTS)} fault(s) - this would render as a deck with a camera on it")
    print("  one space, travelled: the set is bigger than the frame, the props persist, "
          "the camera lands")


if __name__ == "__main__":
    main(sys.argv[1:])
