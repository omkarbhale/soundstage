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

## `cue_check.py` reports zero cues on a set, and that is not a hole

It reads `t("literal")` calls, and a standing set writes its cues in a table that
`S.move()` and `S.change()` resolve - so it prints "0 cue phrases checked" on a piece with
thirty of them. Do not go and hand-write a list: that is the thing the README warns
against, and the cues are covered twice already. `standing_set.render()` resolves every
one and raises on a miss, which is the README's own "run the generator" check; and
`set_check.py` then matches each of them against the real transcript and refuses
[NOT SPOKEN] and [AMBIGUOUS]. Read the zero as "nothing for me here", not "nothing
checked".

## Far props lean in from the next room, and a tall far wall frames very wide

Two consequences of the projection that decide where props go, and neither is obvious
from the numbers:

- A far prop lands at `(P - camera) * s / depth` from the centre, so at depth 2.3 it sits
  **less than half as far off centre** as a mid prop at the same world position. A far
  prop 2,600 units away in the NEXT region is only 1,100 mid-equivalent units away, and it
  will be in shot. That is correct - the format wants props that persist and a camera that
  finds them - but it means anything you want kept for later belongs on the **mid** plane,
  not the far one.
- A framing computed on a tall far surface is set by its HEIGHT, and at that scale the
  frame is enormous horizontally: a 6,650-tall wall at depth 2.3 gives `s` 0.22, and the
  frame is then 8,500 world units wide - wider than a whole region. Those framings are
  establishing shots whether you meant them or not. Compose them as such, or frame the
  surface together with a mid prop to tighten it.

## A pause is not in the transcript, and the delivery check depends on it

The format's whole case for a local voice is that "punctuation does the timing" [BREATH],
so the obvious check on a take is whether the voice actually breaks where the script
does. It cannot be read off `transcript.json`: **the aligner emits contiguous word
boundaries and models no silence at all**, so every gap computed from it is zero and a
take looks like it runs every sentence together. Measure it off the waveform - an
energy gate at about 32 dB below the speech peak, and the quiet runs between - and key it
to the TRANSCRIPT's own punctuation rather than to the script's, because the two drift
apart wherever the aligner merged words (`four hundred` -> `400`) and a word-count walk
then reads the wrong boundary from there on.

Measured on this piece's take, which is what the check is worth: 57 full stops, median
pause 0.64s, one under 0.20s; 45 commas, median 0.24s. That is the difference between a
voice that lands the writing and one that does not, and it is invisible in every other
number.

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

## Type is measured in both spellings of font-size now

`<text font-size="56px">` is valid SVG and `components/standing_set.py` could not see it,
so a correctly sized prop was refused for "carrying words and declaring no font-size" -
twice in one afternoon, and the refusal does not say which spelling it wants. Fixed: the
component reads both, and `_shape()` strips both, since it strips font-size before hashing
a prop so [TWINS] compares the drawing rather than the words. Recorded because the two
halves have to move together - reading the attribute without stripping it would let one
drawing through twice by differing in a number.

## Departures made by the first piece, and why

A departure is a finding, not an apology. Each of these is a place where the format was
wrong for the piece, silent about something it needed to speak about, or fighting what
the piece was for.

| What the format says | What the piece did | Why |
| --- | --- | --- |
| "two or three families, one of them monospace **only where a `code` prop needs it**" | Monospace with no `code` prop at all: the engraved plates, the measured tick labels and the counted units | [FAMILIES] still demands two families. The piece had no code in it and could not have - its listener has never seen a repository. The rule's reason is "the voice changes where the material does", and stamped metal is a different material from spoken type. The format should say **monospace is the machine-cut voice**, of which source is one case. |
| "the set is built out of the real material: a screen captured off the product, a block of the actual code" | No `screen`, no `code`, no `components/figure.py` at all. The material floor is met with `chart` and `diagram` | [DRAWN NOT SHOWN] counts `screen`, `code`, `chart` and `diagram` together, so this is inside the letter of the rule. It is recorded because the spirit - capture, do not draw - is only half served, and a piece with no product to point at has no other option. |

## What the first piece did not have to depart from

Worth recording because it is the strongest thing that can be said about a format: a
four-minute piece with 37 props, 28 moves and 22 acts was built end to end and **no rule
had to be gone around**. Every refusal it hit was one of three things - a real defect in
a guard (two, both fixed here), an interaction the format implies but does not state (one,
now stated), or geometry that was simply wrong and had to be moved. The two departures
above are both forced by what the piece is ABOUT, not by the format being wrong; each one
sits inside the letter of its rule and is recorded for the spirit.

The thresholds that cost the most work, in order, and all of them earned it: [ALL STOPS]
(which is what turned a route into a room - fourteen props exist only to be passed),
[DEAD HOLD] (the act budget), and [CENTRED] (which is what stopped every framing being a
subject in the middle of an empty frame).
