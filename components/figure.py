# A screenshot, in enough of its surroundings to be findable, with the named thing
# pointed at.
#
#   import figure
#   F = figure.Figures(f"{D}/assets/shots")        # ADR-0004: the path is owned here
#   html = F.fig("m03-screen-one", "f1",
#                mark=("name", "Name"), also=[("tenant", "Tenant")],
#                zoom="name", caption="the card is the whole page")
#
# WHAT THIS IS FOR. A viewer who has just heard a control named should be able to sit
# down at the product and put a finger on it. That is a question about POSITION, and a
# tight crop of a button answers a different one: it shows what the button looks like
# and says nothing about where it lives. So the frame carries the screen - the page it
# is on, the panel it sits in - and the highlight does the pointing. `zoom` puts a
# magnified inset BESIDE the wide shot, never instead of it, for when the label has to
# be read as well as found.
#
# THE HIGHLIGHT IS MEASURED, NEVER TYPED. Every box here comes from the shot's `.json`,
# which the capture wrote from the element's own bounding box on the page. A box typed
# by hand is the fault this repo writes guards for: it renders beautifully while
# ringing the wrong control, and the settled frame looks finished either way.
# `figure_check.py` proves, after building, that every box on the frame is still the
# one that was measured. See ADR-0010.
#
# COLOUR IS SEMANTIC, and a highlight inherits that. It is drawn in `--accent`, which
# in this house means "the thing being taught". A mark never uses `--warm`, because
# terracotta is a claim that something is refused.
#
# The sizes below are geometry, not style: they are the arithmetic that keeps a
# measured box over the pixel it was measured from. Every look decision - how big the
# figure is, what a tag says, how dark the veil is - is a caller's argument or a house
# token, so a different series restyles this without touching it.
import json
import os

CSS = """
      /* ================================================== figures: screenshots
         A framed screen, the named element ringed and named, and an optional
         magnified inset beside it. components/figure.py writes the geometry;
         every box on a mark was measured from the element itself and
         figure_check.py proves it still matches. */
      .fig { position: relative; align-self: center; display: flex;
             flex-direction: column; gap: 24px; align-items: center; }
      .fig-row { display: flex; align-items: center; gap: 36px; }
      .fig-frame {
        position: relative; border-radius: 22px; overflow: hidden; flex: none;
        background: var(--card); box-shadow: var(--lift);
      }
      /* The window bar. The product really does run in a browser, and 30px of one
         says "this is a screen" so the frame is not read as a diagram. */
      .fig-bar { height: 30px; background: var(--card-2); display: flex;
                 align-items: center; gap: 8px; padding-left: 16px; }
      .fig-bar i { width: 9px; height: 9px; border-radius: 999px;
                   background: rgba(28, 34, 48, 0.16); display: block; }
      .fig-shot { display: block; width: 100%; height: auto; }
      .fig-hold { position: relative; }

      .fig-mark {
        position: absolute; border: 3px solid var(--accent); border-radius: 9px;
        margin: -5px; padding: 5px;
      }
      /* The spotlight, and it is one element doing two jobs: the ring is the border
         and the veil is a shadow spread far enough to reach every edge, clipped by
         the frame. Only the PRIMARY mark carries it - two veils would stack and the
         page would go dark, and a page nobody can read teaches no position. */
      .fig-mark.lit { box-shadow: 0 0 0 4000px rgba(28, 34, 48, 0.30); }

      .fig-tag {
        position: absolute; background: var(--accent); color: #fff;
        font-size: 26px; font-weight: 650; letter-spacing: -0.005em; line-height: 1.22;
        padding: 8px 18px; border-radius: 11px;
        box-shadow: 0 10px 24px rgba(28, 38, 64, 0.22);
      }
      /* The leader: a short rule from the tag to the ring, so a tag beside a dense
         column still says WHICH row it names. */
      .fig-tag::after { content: ""; position: absolute; background: var(--accent); }
      .fig-tag.east::after  { left: -18px; top: 50%; margin-top: -1.5px; width: 18px; height: 3px; }
      .fig-tag.west::after  { right: -18px; top: 50%; margin-top: -1.5px; width: 18px; height: 3px; }
      .fig-tag.south::after { left: 26px; top: -16px; width: 3px; height: 16px; }
      .fig-tag.north::after { left: 26px; bottom: -16px; width: 3px; height: 16px; }

      /* The inset: the same picture, magnified on the marked region. Beside the wide
         shot and never instead of it - the wide shot is what teaches where the thing
         is, and this is only what it says.
         Two placements, and the choice is arithmetic rather than taste. `beside` puts
         it in its own column, which a figure-led scene has room for. `corner` stands
         it proud of the frame's bottom-right, for a scene that also carries a column
         of type: there a second column would push the whole row off the frame. */
      .fig-zoom {
        flex: none; border-radius: 16px; background-repeat: no-repeat;
        box-shadow: var(--lift); outline: 3px solid var(--accent); outline-offset: -3px;
      }
      .figrow .fig-zoom { display: none; }   /* see above: no room, and it would cover
                                                the very thing it magnifies */
      .fig-cap { font-size: 29px; color: var(--ink-3); line-height: 1.35;
                 text-align: center; max-width: 1320px; }
      .fig-cap b { color: var(--ink); font-weight: 650; }

      /* A CORRECTION NOTE. What the product does TODAY, where the narration was
         written against something else and the audio is locked.
         It is NOT --warm: terracotta in this house is a claim that something is
         refused, and a screen that has moved on since the recording is not a refusal.
         It borrows the card's own kicker-and-body grammar rather than inventing a
         second annotation language, so it reads as part of the frame and not as an
         erratum slip pasted on. */
      .fig-note { background: var(--card-2); border-radius: 18px; padding: 20px 26px;
                  align-self: center; }
      .fig-note .card-k { margin-bottom: 8px; }
      .fig-note-v { font-size: 27px; line-height: 1.32; color: var(--ink-2); }
      .fig-note-v b { color: var(--ink); font-weight: 650; }
      .figrow .fig-note { padding: 16px 20px; }
      .figrow .fig-note-v { font-size: 24px; }

      /* A figure-led scene: the frame is the content, so it gets the margins back.
         Content still clears the brandmark and the module name. */
      .scene-in.figful { padding: 78px 100px; gap: 30px; }
      /* Type on one side, the screen on the other. The type column is held narrow
         so the figure keeps the width: the figure is the thing being taught here,
         and a screenshot squeezed beside a full-width column teaches nothing. A
         figure in this layout carries no caption - the line under it belongs in the
         column, where there is room for it. */
      .figrow { display: flex; align-items: center; gap: 56px; }
      .figrow > .stack { flex: none; width: 620px; max-width: 620px; gap: 26px; }
      .figrow > .fig { flex: none; }
      .figrow .head { font-size: 52px; }
      .figrow .line-said { font-size: 38px; }
      .figrow .note { font-size: 26px; }
      .figrow .card-v { font-size: 30px; }
      .figrow .def-t { font-size: 29px; width: 190px; }
      .figrow .def-d { font-size: 26px; }
      .figrow .pill { font-size: 25px; padding: 13px 26px; }
      /* Anything that assumes the full frame has to be told otherwise in here, or it
         reaches under the figure. These are the house's full-width containers. */
      .figrow .cols, .figrow .versus { flex-direction: column; gap: 16px; }
      /* Three cards that were a row are now a column, so they have to give back the
         height they used to take sideways or the last one falls off the frame. */
      .figrow .cols .card { padding: 22px 26px; }
      .figrow .cols .card-v { font-size: 27px; }
      .figrow .cols .card-k { font-size: 18px; margin-bottom: 10px; }
      .figrow .cols .card-ico { margin-bottom: 10px; }
      .figrow .cols .card-ico .ico { width: 34px; height: 34px; }
      .figrow .ladder { width: auto; gap: 12px; }
      .figrow .rung { padding: 14px 20px; gap: 16px; }
      .figrow .rung-n { width: 58px; font-size: 19px; }
      .figrow .rung-t { font-size: 25px; }
      .figrow .rung-w { width: 200px; font-size: 20px; }
      .figrow .stack.wide { max-width: 620px; }
      .figrow .refusal { font-size: 25px; padding: 18px 24px; gap: 20px; }
      .figrow .refusal .ico { width: 34px; height: 34px; }
      .figrow .refusals, .figrow .gates, .figrow .owns, .figrow .opens { gap: 14px; }
      .figrow .vs-t { font-size: 38px; }
      .figrow .vs-q { font-size: 27px; }
      .figrow .vs-l div { font-size: 23px; }
      .figrow .word { font-size: 38px; }
"""

# Geometry, not taste: how much clear width a tag needs beside a mark before it is
# put there rather than under it, and how far the leader stands off.
SIDE_ROOM = 250
LEADER = 18


class Figures:
    """Every figure in one module. Constructed with the directory the measured shots
    live in, so no call site invents a path (ADR-0004)."""

    def __init__(self, shots_dir, rel="assets/shots"):
        self.dir = shots_dir
        self.rel = rel

    def shot(self, name):
        path = f"{self.dir}/{name}.json"
        if not os.path.exists(path):
            raise SystemExit(f"no measured shot {name!r} at {path} - capture it before building")
        return json.load(open(path, encoding="utf8"))

    def box(self, name, mark):
        s = self.shot(name)
        m = s["marks"].get(mark)
        if m is None:
            raise SystemExit(f"shot {name!r} has no mark {mark!r} - it has {sorted(s['marks'])}")
        return m

    def fig(self, name, el_id, *, mark=None, also=(), zoom=None, caption=None,
            note=None, height=620, zoom_width=500, zoom_ratio=0.66, zoom_pad=1.35,
            chrome=True, cls=""):
        """One figure.

        `mark` is `(mark_name, label)` - the thing the narration just named, ringed,
        named and spotlit. `also` is more of the same, ringed without the spotlight;
        pass `None` for a label to ring something without naming it. `zoom` names a
        mark to magnify beside the frame.

        Every id derives from `el_id`, so a generator can cue each piece on its own
        word and `id_check.py` still finds exactly one element for each:
        `#<id>-frame`, `#<id>-m-<mark>`, `#<id>-t-<mark>`, `#<id>-z`, `#<id>-cap`,
        `#<id>-note`."""
        s = self.shot(name)
        bar = 30 if chrome else 0
        width = round(height * s["w"] / s["h"])
        pic_h = round(width * s["h"] / s["w"])

        rings, tags = [], []
        for mk, label in ([mark] if mark else []) + list(also):
            rings.append(self._mark(name, mk, el_id, lit=(mark is not None and mk == mark[0])))
            if label:
                tags.append(self._tag(name, mk, el_id, label, width, pic_h))

        pic = (f'<div class="fig-hold">'
               f'<img class="fig-shot" src="{self.rel}/{name}.png" alt="" />'
               f'{"".join(rings)}{"".join(tags)}</div>')
        frame = (f'<div class="fig-frame" id="{el_id}-frame" style="width:{width}px">'
                 f'{f"""<div class="fig-bar">{"<i></i>" * 3}</div>""" if chrome else ""}'
                 f'{pic}</div>')
        inset = (self._zoom(name, zoom, el_id, zoom_width, zoom_ratio, zoom_pad)
                 if zoom else "")
        cap = (f'<figcaption class="fig-cap" id="{el_id}-cap">{caption}</figcaption>'
               if caption else "")
        # `note` is (kicker, body): a short, factual statement of what the product does
        # today, for a frame whose narration was written against something else. The
        # audio is locked (ADR-0003), so the correction goes on the picture rather than
        # into the words - and never into the captions, which must say what the voice
        # says or they are a second wrong answer rather than a fix.
        # Capped at the frame's own width, in pixels, because `.fig` is a flex column
        # that takes the width of its widest child - a long note would otherwise make
        # the whole figure wider than the frame and push it off the picture.
        nte = (f'<div class="fig-note" id="{el_id}-note" style="max-width:{width}px">'
               f'<div class="card-k">{note[0]}</div>'
               f'<div class="fig-note-v">{note[1]}</div></div>' if note else "")
        return (f'<figure class="fig {cls}" id="{el_id}">'
                f'<div class="fig-row">{frame}{inset}</div>{cap}{nte}</figure>')

    # ---------------------------------------------------------------- pieces
    def _mark(self, name, mk, el_id, lit):
        b = self.box(name, mk)
        # data-shot / data-mark are what figure_check.py reads the numbers back
        # against. Strip either and the guard reports the mark as unprovable.
        return (f'<div class="fig-mark{" lit" if lit else ""}" id="{el_id}-m-{mk}" '
                f'data-shot="{name}" data-mark="{mk}" '
                f'style="left:{b["x"] * 100:.3f}%;top:{b["y"] * 100:.3f}%;'
                f'width:{b["w"] * 100:.3f}%;height:{b["h"] * 100:.3f}%"></div>')

    def _tag(self, name, mk, el_id, label, width, pic_h):
        """Beside the mark where the page has room, under it where it has not.

        A screenshot of this product is mostly margin, and a tag in the margin covers
        nothing. Stacking tags under their marks is what covers the next control down
        - which is the one the viewer is about to be told to find."""
        b = self.box(name, mk)
        east = (1 - b["x"] - b["w"]) * width
        west = b["x"] * width
        mid = (b["y"] + b["h"] / 2) * 100
        if max(east, west) >= SIDE_ROOM:
            if east >= west:
                side, room = "east", east
                pos = f'left:calc({(b["x"] + b["w"]) * 100:.3f}% + {LEADER}px)'
            else:
                side, room = "west", west
                pos = f'right:calc({(1 - b["x"]) * 100:.3f}% + {LEADER}px)'
            pos += f';top:{mid:.3f}%;transform:translateY(-50%)'
        else:
            below = (b["y"] + b["h"]) * pic_h < pic_h - 90
            side = "south" if below else "north"
            left = min(max(b["x"], 0.006), 0.66)
            room = (1 - left) * width
            pos = (f'top:calc({(b["y"] + b["h"]) * 100:.3f}% + {LEADER}px)' if below
                   else f'bottom:calc({(1 - b["y"]) * 100:.3f}% + {LEADER}px)')
            pos += f';left:{left * 100:.3f}%'
        # The tag wraps rather than running off the picture. The room it has is known
        # exactly - it is the measurement - so this is arithmetic, not a guessed cap
        # on how long a label may be.
        pos += f';max-width:{max(160, round(room - LEADER - 10))}px'
        return f'<div class="fig-tag {side}" id="{el_id}-t-{mk}" style="{pos}">{label}</div>'

    def _zoom(self, name, mk, el_id, w, ratio, pad):
        """A magnified crop of one mark.

        The crop is the mark grown by `pad` so the element keeps some of what is
        around it: a magnified button floating in nothing is the close-up this
        component exists to stop anyone shipping on its own."""
        b = self.box(name, mk)
        h = round(w * ratio)
        # Grow the mark by `pad` in whichever direction binds, then to the inset's
        # aspect. A wide, short mark - a toolbar - is grown mostly sideways; a tall,
        # narrow one mostly downwards; either way the element keeps its neighbours.
        cw = min(1.0, b["w"] * pad)
        ch = min(1.0, b["h"] * pad)
        if cw / ch < w / h:
            cw = min(1.0, ch * w / h)
        else:
            ch = min(1.0, cw * h / w)
        cx = min(max(b["x"] + b["w"] / 2 - cw / 2, 0.0), 1.0 - cw)
        cy = min(max(b["y"] + b["h"] / 2 - ch / 2, 0.0), 1.0 - ch)
        # The background-position identity: a percentage positions that fraction of
        # the OVERFLOW, so the crop's origin is cx/(1-cw) of it.
        px = 0.0 if cw >= 1 else cx / (1 - cw) * 100
        py = 0.0 if ch >= 1 else cy / (1 - ch) * 100
        return (f'<div class="fig-zoom" id="{el_id}-z" '
                f'style="width:{w}px;height:{h}px;'
                f'background-image:url({self.rel}/{name}.png);'
                f'background-size:{100 / cw:.3f}% {100 / ch:.3f}%;'
                f'background-position:{px:.3f}% {py:.3f}%"></div>')
