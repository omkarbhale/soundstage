# One space, and a camera that travels through it.
#
#   import standing_set
#   S = standing_set.Set(frame=(1920, 1080), world=(7600, 3600))
#   S.plane("far", 2.1); S.plane("mid", 1.0); S.plane("near", 0.64)
#   S.region("intake", (0, 0, 2500, 3600), ground="#10151f", ink="#f2f5fb", accent="#7fe3c4")
#   S.prop("wall", "surface", "far", at=(120, 300), size=(2200, 2600), html=...)
#   S.open(on=["title"], pad=0.22)
#   S.move("travel", on=["queue"], cue="where the request lands", dur=1.6)
#   css, html, js = S.render(t, end=speech_end + 2.0)
#
# WHAT THIS IS FOR. The format `formats/standing-set/` is the language; this is its
# geometry. Props are placed once, at world coordinates, and stay placed. The camera
# is a framing computed from the props it is aimed at - name the props, get the
# centre and the scale. Nobody types a transform, and every number in the timeline is
# re-derivable from the manifest this stamps into the document, which is what
# `set_check.py` does after the build.
#
# THE PROJECTION. A plane carries a depth: 1.0 is the plane the camera focuses to,
# above 1 is further away, below 1 is nearer than it. A point P on a plane of depth d,
# under a camera centred on C showing `frame_w / s` of world width, lands at
# `(P - C) * s/d + frame/2` and is drawn at `s/d` of its authored size. So a far prop
# is smaller and lags, which is the parallax, and it is the same arithmetic that
# computes a framing: aim at props on one plane, fit their union, read off C and s.
#
# GROUNDS STAND ON THE SUBJECT PLANE. A region's ground is the floor its props stand
# on, so it is drawn at depth 1 in plain world coordinates and its boundary arrives
# under the camera exactly when the camera enters the region. Depth would buy drift at
# the price of that alignment, and the parallax the eye reads comes from the props in
# front of it. The ground runs one world past every outer edge, which is more than the
# widest framing can reach.
#
# DEPTH OF FIELD IS COMPUTED. Blur per plane comes from its distance to the framing's
# focus plane, scaled by how close the camera is. A rack is a framing that holds still
# and moves the focus; nothing about it is hand-drawn either.
#
# This refuses everything geometrically impossible - a prop on no plane, a prop in no
# region, a framing spanning two planes, a move that runs past the next cue. What
# makes a piece CHEAP rather than impossible is `set_check.py`'s to refuse.
import hashlib
import html as _html
import json
import re

# Eases that overshoot. A camera that overshoots is a whip, and a whip is a cut
# (motion-doctrine's territory), not a camera move.
BANNED_EASE = ("back", "elastic", "bounce")

MOVES = ("travel", "push", "pull", "arc", "rack")

# The house palette. Three places, dark, turning one way round the wheel, with accents
# far enough apart that each region owns one. Real values because a format ships its
# colours; a format that asks for them is a questionnaire.
HOUSE = (
    {"name": "ingress", "ground": "#0B1522", "ink": "#E8F1FF", "accent": "#5FE0C0"},
    {"name": "work",    "ground": "#241019", "ink": "#FFEDF3", "accent": "#FF9A5C"},
    {"name": "proof",   "ground": "#0F1B12", "ink": "#ECFAF0", "accent": "#7AB8FF"},
)

# The type scale, in world units. Seven steps over eleven times, so the camera has to
# move to read the ends of it.
TYPE = {"wall": 240, "figure": 190, "head": 96, "label": 56,
        "body": 44, "code": 34, "fine": 22}
FAMILY = {"text": "Inter", "code": "JetBrains Mono"}

# Depth of field. `blur = K * |d - focus| / focus * min(CAP_S, s)`, capped: a plane
# two depths off the focus at a close framing is unreadable, which is the point, and
# the cap keeps it from smearing into a grey field.
DOF_K = 7.0
DOF_CAP_S = 1.7
DOF_MAX = 15.0

# Both spellings, because SVG sizes type with an ATTRIBUTE and HTML with a CSS
# declaration, and a `chart` or `diagram` prop is an <svg> with <text> in it.
# Reading only `font-size:Npx` made the component refuse such a prop for
# "carries words and declares no font-size" while its type was sized in front
# of it, and hid those sizes from set_check.py's [ONE SIZE] and [NO SCALE].
FONT_SIZE = re.compile(r"""font-size\s*[:=]\s*["']?\s*([\d.]+)\s*(?:px)?""")
WORDS = re.compile(r"[A-Za-z]{2,}")
# What a prop is MADE of, so a role is a claim about markup rather than a label.
GEOM = re.compile(r"(?:width|height|left|top|background|transform|border|stroke|d)\s*[:=]")
INK = re.compile(r"(?:^|[;\"\s])(?:color|fill|stroke)\s*:\s*([^;\"]+)")
GROUND = re.compile(r"(?:^|[;\"\s])(?:background|background-color)\s*:\s*([^;\"]+)")


def _tags_off(markup):
    return re.sub(r"<[^>]*>", " ", markup)


def _shape(markup):
    """What a prop is a drawing OF, with its words and their sizes taken out.

    Two props that hash the same are one prop drawn twice, whatever they are
    labelled and whatever size they are placed at."""
    m = re.sub(r">[^<]*<", "><", markup)
    # Mirrors FONT_SIZE, and has to: that pattern now READS the attribute
    # spelling, so if this stripped only the style one, two copies of a drawing
    # that differ by a font-size attribute would hash apart and walk past [TWINS].
    m = re.sub(r"""font-size\s*[:=]\s*["']?\s*[\d.]+\s*(?:px)?["']?;?""", "", m)
    return hashlib.sha1(re.sub(r"\s+", " ", m).strip().encode()).hexdigest()[:12]


def _stencil(markup):
    """The same, with every number taken out too: the stencil a drawing was cut
    from. A family of related marks shares one; a set furnished from one helper
    shares nothing else."""
    m = re.sub(r">[^<]*<", "><", markup)
    m = re.sub(r"[-\d.]+", "#", m)
    return hashlib.sha1(re.sub(r"\s+", " ", m).strip().encode()).hexdigest()[:12]


class Set:
    """One set and the camera that travels it.

    `frame` is the rendered frame in pixels. `world` is the space, in the same units:
    the camera never sees all of it at once and the format requires it to be several
    frames across."""

    def __init__(self, *, frame, world):
        self.frame = tuple(frame)
        self.world = tuple(world)
        self.planes = {}
        self.regions = []
        self.props = {}
        self.order = []
        self.plate_html = None
        self.events = []
        self.changes = []
        self.echoes = []
        self.shots = []          # every framing, in order; the first is `open`

    # ------------------------------------------------------------- declaring
    def plane(self, name, depth):
        """A depth plane. 1.0 is the plane a framing focuses to."""
        if name in self.planes:
            raise SystemExit(f"plane {name!r} is declared twice")
        if depth <= 0:
            raise SystemExit(f"plane {name!r} has depth {depth} - depth is a distance")
        self.planes[name] = float(depth)

    def region(self, name, box, *, ground, ink, accent):
        """A place in the set with its own palette. Regions tile the world; the ground
        is the wall behind everything in them."""
        x, y, w, h = (float(v) for v in box)
        for r in self.regions:
            rx, ry, rw, rh = r["box"]
            if x < rx + rw and rx < x + w and y < ry + rh and ry < y + h:
                raise SystemExit(f"region {name!r} overlaps {r['name']!r} - regions tile, "
                                 f"they do not stack")
        self.regions.append({"name": name, "box": [x, y, w, h],
                             "ground": ground, "ink": ink, "accent": accent})

    def prop(self, pid, role, plane, *, at, size, html, name=None, cls=""):
        """A thing that exists in the space, from the moment the module starts.

        `role` is what it is - screen, code, diagram, glyph, specimen, surface,
        artifact, chart. `at` is its top-left in world coordinates, `size` its size in
        world units; both are read by the camera when it frames this prop, so they are
        the prop's real extent and not a guess at one. `name` is what the narrator
        calls it, which is how the script is held to the picture."""
        if pid in self.props:
            raise SystemExit(f"prop {pid!r} is declared twice - every prop is one thing")
        if not name or not (1 <= len(name.split()) <= 4):
            raise SystemExit(f"prop {pid!r} needs a name of one to four words - the narrator "
                             f"has to be able to call it something, walls included")
        taken = {p["name"]: i for i, p in self.props.items() if p.get("name")}
        if name in taken:
            raise SystemExit(f"prop {pid!r} is named {name!r}, which is already {taken[name]!r} "
                             f"- two things with one name cannot be told apart by the words")
        if plane not in self.planes:
            raise SystemExit(f"prop {pid!r} sits on plane {plane!r}, which is not declared")
        x, y = (float(v) for v in at)
        w, h = (float(v) for v in size)
        if w <= 0 or h <= 0:
            raise SystemExit(f"prop {pid!r} has no size - the camera cannot frame it")
        if x < 0 or y < 0 or x + w > self.world[0] or y + h > self.world[1]:
            raise SystemExit(f"prop {pid!r} at ({x:.0f},{y:.0f}) {w:.0f}x{h:.0f} is outside "
                             f"the world {self.world[0]:.0f}x{self.world[1]:.0f}")
        where = self._region_of(x + w / 2, y + h / 2)
        if where is None:
            raise SystemExit(f"prop {pid!r} stands in no region - every part of the world "
                             f"the camera visits has a palette")
        sizes = sorted({float(v) for v in FONT_SIZE.findall(html)})
        markup = {
            "svg": "<svg" in html.lower(),
            "img": "<img" in html.lower(),
            "fig": "fig-frame" in html,
            "geom": sum(1 for tag in re.findall(r"<[^>]*>", html) if GEOM.search(tag)),
            "mono": any("mono" in f.lower()
                        for f in re.findall(r"font-family:\s*([^;\"]+)", html)),
            # Does this prop wear the accent at all - as a house variable or as the
            # literal colour. The accent means "this one", so who wears it is counted.
            "accent": ("var(--accent)" in html
                       or any(r["accent"].lower() in html.lower() for r in self.regions)),
            "tags": sorted({t.lower() for t in re.findall(r"<([a-zA-Z][\w-]*)", html)}),
            "classes": sorted({c for a in re.findall(r'class="([^"]+)"', html)
                               for c in a.split()}),
            "colours": ([("ground", c.strip()) for c in GROUND.findall(html)]
                        + [("ink", c.strip()) for c in INK.findall(html)]),
        }
        if WORDS.search(_tags_off(html)) and not sizes:
            raise SystemExit(f"prop {pid!r} carries words and declares no font-size - "
                             f"type in this set is measured, so it is sized where it is written")
        self.props[pid] = {"id": pid, "role": role, "plane": plane, "at": [x, y],
                           "size": [w, h], "region": where, "html": html, "cls": cls,
                           "px": sizes, "words": len(WORDS.findall(_tags_off(html))),
                           "markup": markup, "name": name,
                           "text": _tags_off(html).split()[:80],
                           "shape": _shape(html), "stencil": _stencil(html)}
        self.order.append(pid)

    def plate(self, html):
        """The one element fixed to the frame rather than standing in the world."""
        if self.plate_html is not None:
            raise SystemExit("a set carries one plate - everything else is in the world")
        self.plate_html = html

    def event(self, pid, *, cause, cue, note):
        """A prop that arrives instead of already being there, and the prop that
        causes it. Rationed: `set_check.py` refuses a set that is mostly arrivals."""
        self._known(pid, "event")
        self._known(cause, "event cause")
        self.events.append({"prop": pid, "cause": cause, "cue": cue, "note": note})

    def echo(self, pid, *, cue, note):
        """A word on the frame landing on the same word in the mouth, on purpose.

        Unmarked, that is the signature of a machine-made video. Declared, it is a beat,
        and `script_check.py` caps how many a piece may spend."""
        self._known(pid, "echo")
        self.echoes.append({"prop": pid, "cue": cue, "note": note})

    def change(self, pid, *, cue, note):
        """A prop that is in a different state at the end of the module than at the
        start. The tween is the author's; this is the declaration the guard reads."""
        self._known(pid, "change")
        self.changes.append({"prop": pid, "cue": cue, "note": note})

    # ---------------------------------------------------------------- camera
    def open(self, *, on, pad=0.2, focus=None, off=(0.0, 0.0)):
        """The framing the module starts on."""
        if self.shots:
            raise SystemExit("open() is the first framing and there is one of them")
        self.shots.append(self._shot("open", on, pad, focus, None, 0.0, "", off=off))

    def move(self, kind, *, on=None, cue, dur, pad=0.2, focus=None, ease="power2.inOut",
             note="", off=(0.0, 0.0)):
        """A camera move, starting on the word it quotes.

        `on` names the props it arrives on, and the framing is computed from them - a
        move never carries a typed position. A `rack` holds the framing and changes
        `focus` instead, so it names no props."""
        if not self.shots:
            raise SystemExit("open() before the first move - the camera starts somewhere")
        if kind not in MOVES:
            raise SystemExit(f"{kind!r} is not a camera move; the moves are {', '.join(MOVES)}")
        if any(b in ease for b in BANNED_EASE):
            raise SystemExit(f"move on {cue!r} uses {ease!r} - a camera does not overshoot")
        if dur <= 0:
            raise SystemExit(f"move on {cue!r} has no duration")
        if kind == "rack":
            if on:
                raise SystemExit("a rack holds the framing and moves the focus; it names no props")
            if focus is None:
                raise SystemExit("a rack needs the plane it racks to")
            prev = self.shots[-1]
            shot = dict(prev, kind="rack", on=[], focus=focus, cue=cue, dur=float(dur),
                        ease=ease, note=note)
            self.shots.append(shot)
            return
        if not on:
            raise SystemExit(f"a {kind} names the props it arrives on")
        self.shots.append(self._shot(kind, on, pad, focus, cue, dur, ease, note, off=off))

    # ----------------------------------------------------------------- build
    def render(self, t, *, end):
        """Resolve every cue, compute the camera, and return (css, html, js).

        `t` is the generator's own cue resolver - the same one every other reveal in
        the composition is placed with (ADR-0003). `end` is where the module stops."""
        if len(self.shots) < 2:
            raise SystemExit("a set with one framing is a picture, not a film")
        if not self.regions:
            raise SystemExit("a set with no region has no palette")
        times = [0.0]
        for s in self.shots[1:]:
            times.append(self._resolve(t, s["cue"]))
        for i in range(1, len(times)):
            if times[i] <= times[i - 1]:
                raise SystemExit(f"the move on {self.shots[i]['cue']!r} is cued at "
                                 f"{times[i]:.2f}s, at or before the one before it "
                                 f"({times[i-1]:.2f}s) - the camera cannot go back in time")
            run = times[i - 1] + (self.shots[i - 1].get("dur") or 0.0)
            if times[i] < run - 1e-6:
                raise SystemExit(f"the move on {self.shots[i]['cue']!r} is cued at "
                                 f"{times[i]:.2f}s but the move before it is still running at "
                                 f"{run:.2f}s - shorten it or cue this one later")
        last = times[-1] + (self.shots[-1].get("dur") or 0.0)
        if last > end + 1e-6:
            raise SystemExit(f"the last move ends at {last:.2f}s, past the module's "
                             f"{end:.2f}s - the camera stops before the film does")
        for s, when in zip(self.shots, times):
            s["at"] = when
        for e in self.events + self.changes + self.echoes:
            e["at"] = self._resolve(t, e["cue"])
        self.end = float(end)
        return self._css(), self._html(), self._js()

    # ------------------------------------------------------------- internals
    def _known(self, pid, what):
        if pid not in self.props:
            raise SystemExit(f"{what} names {pid!r}, which is not a prop in this set")

    def _region_of(self, x, y):
        for r in self.regions:
            rx, ry, rw, rh = r["box"]
            if rx <= x < rx + rw and ry <= y < ry + rh:
                return r["name"]
        return None

    def _resolve(self, t, cue):
        return float(t(*cue) if isinstance(cue, (tuple, list)) else t(cue))

    def _shot(self, kind, on, pad, focus, cue, dur, ease, note="", off=(0.0, 0.0)):
        """A framing computed from the props it names.

        The camera is placed so every named prop's PROJECTED box sits inside the frame
        with `pad` of it to spare, at the largest scale that still holds. Props on
        different planes project by different amounts, so the centre that buys the
        most scale is found per axis rather than assumed to be the middle of a box -
        which is what lets one framing hold the whole set at the end."""
        for pid in on:
            self._known(pid, "framing")
        fw, fh = self.frame
        room = max(0.02, 1 - 2 * float(pad))
        cx, sx = self._fit([(self.props[p]["at"][0], self.props[p]["size"][0],
                             self.planes[self.props[p]["plane"]]) for p in on], fw * room)
        cy, sy = self._fit([(self.props[p]["at"][1], self.props[p]["size"][1],
                             self.planes[self.props[p]["plane"]]) for p in on], fh * room)
        # Rounded here and nowhere else, so the manifest a guard re-derives from and
        # the timeline it re-derives are the same numbers to the last digit.
        # The offset moves the camera, not the props: the subject slides off centre by
        # that fraction of the frame. Answered at the SUBJECT's distance, so `off=0.1`
        # is a tenth of the frame whether the thing framed is near or far. It still has
        # to fit, which is what refuses an offset large enough to push it out of shot.
        s = min(sx, sy)
        d0 = self.planes[self.props[on[0]]["plane"]]
        cx -= float(off[0]) * fw * d0 / s
        cy -= float(off[1]) * fh * d0 / s
        for pid in on:
            p = self.props[pid]
            d = self.planes[p["plane"]]
            x0 = (p["at"][0] - cx) * s / d + fw / 2
            y0 = (p["at"][1] - cy) * s / d + fh / 2
            if (x0 < 0 or y0 < 0 or x0 + p["size"][0] * s / d > fw
                    or y0 + p["size"][1] * s / d > fh):
                raise SystemExit(f"framing on {sorted(on)} offset by {tuple(off)} pushes "
                                 f"{pid!r} off the frame - widen `pad` or offset less")
        return {"kind": kind, "on": list(on), "cx": round(cx, 3), "cy": round(cy, 3),
                "s": round(s, 6), "off": [float(off[0]), float(off[1])],
                "focus": focus or self.props[on[0]]["plane"], "cue": cue, "dur": dur,
                "ease": ease, "note": note}

    @staticmethod
    def _fit(boxes, room):
        """The camera centre on one axis, and the scale it buys.

        Half the frame holds `reach(c) = max over props of max((c - near)/d,
        (far - c)/d)` world units, so the scale is `room/2 / reach(c)`. `reach` is the
        maximum of straight lines in c, so it is convex and its minimum is found by
        halving the interval it cannot be outside."""
        def reach(c):
            return max(max((c - a) / d, (a + w - c) / d) for a, w, d in boxes)

        lo = min(a for a, _w, _d in boxes)
        hi = max(a + w for a, w, _d in boxes)
        for _ in range(80):
            m1 = lo + (hi - lo) / 3
            m2 = hi - (hi - lo) / 3
            if reach(m1) < reach(m2):
                hi = m2
            else:
                lo = m1
        c = (lo + hi) / 2
        return c, (room / 2) / max(reach(c), 1e-6)

    def _layer(self, depth, shot):
        """Where a plane sits, and how blurred, under one framing."""
        fw, fh = self.frame
        s = shot["s"] / depth
        x = fw / 2 - shot["cx"] * s
        y = fh / 2 - shot["cy"] * s
        f = self.planes[shot["focus"]]
        blur = min(DOF_MAX, DOF_K * abs(depth - f) / f * min(DOF_CAP_S, shot["s"]))
        return round(x, 3), round(y, 3), round(s, 5), round(blur, 2)

    def _layers(self):
        """Back to front: the ground, then the planes furthest away first."""
        out = [("ground", 1.0)]
        for name, d in sorted(self.planes.items(), key=lambda kv: -kv[1]):
            out.append((name, d))
        return out

    # --------------------------------------------------------------- writing
    def _css(self):
        fw, fh = self.frame
        rules = [f"""
      /* ============================================ the set: one space, one camera
         components/standing_set.py writes every number below the plane classes.
         The view is the frame; the planes are the space, drawn at world coordinates
         and moved by the camera. Nothing here positions anything: the camera's
         transforms are in the timeline, computed from the framings. */
      .set-view {{ position: absolute; inset: 0; overflow: hidden; }}
      .set-plane {{ position: absolute; left: 0; top: 0; width: 0; height: 0;
                   transform-origin: 0 0; will-change: transform, filter; }}
      .set-prop {{ position: absolute; }}
      .set-ground {{ position: absolute; }}
      .set-plate {{ position: absolute; }}"""]
        for i, (name, _d) in enumerate(self._layers()):
            rules.append(f"      #sp-{name} {{ z-index: {i + 1}; }}")
        for r in self.regions:
            rules.append(f"""      .rg-{r['name']} {{ --ground: {r['ground']}; --ink: {r['ink']};
                       --accent: {r['accent']}; color: var(--ink); }}""")
        return "\n".join(rules) + "\n"

    def _html(self):
        fw, fh = self.frame
        grounds = []
        ww, wh = self.world
        # A region touching an outer edge runs one world past it. No framing can be
        # wider than the props it fits, so nothing reaches beyond that.
        for r in self.regions:
            x, y, w, h = r["box"]
            if x <= 0:
                x, w = x - ww, w + ww
            if y <= 0:
                y, h = y - wh, h + wh
            if r["box"][0] + r["box"][2] >= ww:
                w += ww
            if r["box"][1] + r["box"][3] >= wh:
                h += wh
            grounds.append(
                f'<div class="set-ground rg-{r["name"]}" data-region="{r["name"]}" '
                f'style="left:{x:.1f}px;top:{y:.1f}px;width:{w:.1f}px;'
                f'height:{h:.1f}px;background:{r["ground"]}"></div>')
        layers = [f'<div class="set-plane" id="sp-ground">{"".join(grounds)}</div>']
        for name, _d in self._layers()[1:]:
            inner = []
            for pid in self.order:
                p = self.props[pid]
                if p["plane"] != name:
                    continue
                inner.append(
                    f'<div class="set-prop rg-{p["region"]} {p["cls"]}" id="pr-{pid}" '
                    f'data-role="{p["role"]}" data-plane="{name}" '
                    f'style="left:{p["at"][0]:.1f}px;top:{p["at"][1]:.1f}px;'
                    f'width:{p["size"][0]:.1f}px;height:{p["size"][1]:.1f}px">'
                    f'{p["html"]}</div>')
            layers.append(f'<div class="set-plane" id="sp-{name}">{"".join(inner)}</div>')
        plate = (f'<div class="set-plate" id="set-plate">{self.plate_html}</div>'
                 if self.plate_html else "")
        man = _html.escape(json.dumps(self._manifest(), separators=(",", ":")), quote=False)
        return (f'<div class="set-view" id="set-view">{"".join(layers)}</div>{plate}'
                f'<script type="application/json" id="set-manifest">{man}</script>')

    def _js(self):
        out = ["      // The camera. Every number is computed from the set by",
               "      // components/standing_set.py; set_check.py re-derives them."]
        first = self.shots[0]
        for name, depth in self._layers():
            x, y, s, b = self._layer(depth, first)
            out.append(f'      tl.set("#sp-{name}", {{transformOrigin:"0 0",x:{x},y:{y},'
                       f'scale:{s},filter:"blur({b}px)"}}, 0);')
        for i in range(1, len(self.shots)):
            a, z = self.shots[i - 1], self.shots[i]
            out.append(f'      // {z["kind"]}: {z["note"] or ", ".join(z["on"]) or z["focus"]}')
            for name, depth in self._layers():
                x0, y0, s0, b0 = self._layer(depth, a)
                x1, y1, s1, b1 = self._layer(depth, z)
                out.append(
                    f'      tl.fromTo("#sp-{name}", {{x:{x0},y:{y0},scale:{s0},'
                    f'filter:"blur({b0}px)"}}, {{x:{x1},y:{y1},scale:{s1},'
                    f'filter:"blur({b1}px)",duration:{round(z["dur"], 3)},'
                    f'ease:"{z["ease"]}"}}, {round(z["at"], 3)});')
        return "\n".join(out) + "\n"

    def _manifest(self):
        return {
            "frame": list(self.frame), "world": list(self.world),
            "end": self.end,
            "planes": self.planes,
            "regions": self.regions,
            "props": [{k: v for k, v in self.props[p].items() if k != "html"}
                      for p in self.order],
            "plate": (len(WORDS.findall(_tags_off(self.plate_html)))
                      if self.plate_html is not None else None),
            "events": self.events, "changes": self.changes, "echoes": self.echoes,
            "shots": [{"kind": s["kind"], "on": s["on"], "cx": s["cx"], "cy": s["cy"],
                       "s": s["s"], "off": s.get("off", [0.0, 0.0]),
                       "focus": s["focus"], "cue": s["cue"],
                       "at": round(s["at"], 3), "dur": s["dur"], "ease": s["ease"],
                       "note": s["note"]}
                      for s in self.shots],
        }
