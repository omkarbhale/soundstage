# Field notes: the first real piece in this format

`SKILL.md` is the format. This file is what a **production** learned by being held to
it - the places where the thresholds interact, the arithmetic they imply that none of
them states, and the departures that piece made and why. The format's numbers were
tuned against demonstration sets; a real piece pushes back in different places, and
that is what this records.

Keep it short and keep it true. A note here is worth writing only if the next author
would otherwise spend an hour rediscovering it. When a note turns into a rule, move it
into `SKILL.md` and delete it from here.

---

## The act budget caps the number of camera holds

This was the first thing the first real piece hit and the most useful thing to know
before writing a shot list. It is now stated in `SKILL.md` under "Rest", with the
arithmetic and the paired-move answer, so it is a rule rather than a note. Recorded here
only as provenance: two productions found it independently, from different pieces, and
both of them found it at shot-list time rather than at planning time.

## `--freeze` was drawing the wrong framing, and every frame looked right

Fixed in `set_check.py`, recorded because of how it hid. `--freeze` stamps a framing's
transforms into the page as CSS; the timeline is still in that page, and **GSAP renders a
`fromTo`'s FROM state the moment the tween is created**, paused timeline or not. An inline
style beats a stylesheet rule whatever its specificity, so every frozen frame drew the
LAST camera tween's start. Measured here: 13 `--freeze` calls, 3 distinct images.

Nothing about the output says so. Each frame is a real framing of the real set, composed,
lit and plausible - it is simply not the one asked for. The fix is `!important` on the
three frozen properties, which is the one thing an inline style does not beat. **If you
are looking at frozen frames and several of them are identical, this is what it was.**

## Two hazards the aligner adds to the README's list

Both hit real cues in one 800-word take, and neither is in README, "Write the cue in
transcript spelling":

- **A two-word function phrase can come back as one different word.** `the empty slots`
  aligned as `those slots`. It is not a drop - the audio says it - so `verify.py` reports
  it as a replacement and moves on, and the cue quoting it simply never resolves.
- **`too` comes back as `two`.** Same shape: a homophone the aligner picks the other way.

The working rule is unchanged and is the README's: quote the part of the sentence that
carries the meaning. Both of these were on function words at the edge of a phrase.

## `NEVER READ` forces the smallest-type prop to be a destination

[NO DETAIL] wants a prop setting type at 28px or less, and [NEVER READ] wants that type
framed at 30px **on the frame**, in a framing that names its prop. So the small-type prop
must be a framing target, and a target it is - against a [ALL STOPS] cap of 60%. Put the
small type on a **near-plane** prop: the apparent size is `px * s / depth`, so a near
plane buys 1.6x for free and the framing can be wider.

## An offset can turn a push into a travel, and on a far wide it is enormous

[CENTRED] pushes an author to offset most framings, and `off=` moves the camera. Two
consecutive framings offset in **opposite** directions add their shifts to the distance
the move crosses, which is what [NOT A PUSH] and [NOT A PULL] measure against
`close_move` (1.0 frames). Offsetting the pair the same way costs nothing. Check the pair,
not the framing.

The size of that shift is not intuitive, because `off` is a fraction of the FRAME at the
subject's distance and the camera lives in WORLD units:

    world units moved = off * frame * depth / scale

On a mid prop framed close (`depth` 1, `s` 1.2) an `off` of 0.09 moves the camera 144
world units. On a far wall framed wide (`depth` 2.3, `s` 0.22) the same 0.09 moves it
**1,800** - twelve times as far, and enough on its own to make the next move fail its
kind. Offsets on far, wide framings are the ones to write small.

## Type is measured off a style declaration, never off an SVG attribute

`<text font-size="56px">` is valid SVG and invisible to the component, which then refuses
the prop for carrying words and declaring no size. Write `style="font-size:56px;..."`.
This bit twice in one afternoon and the refusal does not say which form it wants.

## Departures made by the first piece, and why

A departure is a finding, not an apology. Each of these is a place where the format was
wrong for the piece, silent about something it needed to speak about, or fighting what
the piece was for.

| What the format says | What the piece did | Why |
| --- | --- | --- |
| "two or three families, one of them monospace **only where a `code` prop needs it**" | Monospace with no `code` prop at all: the engraved plates, the measured tick labels and the counted units | [FAMILIES] still demands two families. The piece had no code in it and could not have - its listener has never seen a repository. The rule's reason is "the voice changes where the material does", and stamped metal is a different material from spoken type. The format should say **monospace is the machine-cut voice**, of which source is one case. |
| "the set is built out of the real material: a screen captured off the product, a block of the actual code" | No `screen`, no `code`, no `components/figure.py` at all. The material floor is met with `chart` and `diagram` | [DRAWN NOT SHOWN] counts `screen`, `code`, `chart` and `diagram` together, so this is inside the letter of the rule. It is recorded because the spirit - capture, do not draw - is only half served, and a piece with no product to point at has no other option. |
