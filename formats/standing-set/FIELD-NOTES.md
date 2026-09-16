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

## The act budget caps the number of camera holds, and that is what sets prop count

This is the single most useful thing to know before writing a shot list, and no
threshold in `SKILL.md` says it.

Three rules multiply:

- every hold of `long_hold` (2s) or more **before the last spoken word** has to carry a
  declared event or change [DEAD HOLD];
- no two acts may overlap, and none may run while the camera moves [TWO AT ONCE];
- a prop carries **one** change, and events are capped at 25% of the props.

So the number of long holds a piece may have is capped by the number of acts, and the
number of acts is capped by the number of props **the script names** - `script_check.py`
requires a change's cue to sit in a line that names the prop that changes, so a prop the
narration never mentions cannot carry one. Dressing props are free for [ALL STOPS] and
useless for [DEAD HOLD].

The arithmetic, for a piece of length `T` with `M` moves:

    holds = M + 1
    long holds needing an act = holds - (gaps under 2s)
    acts available = (named, non-surface props) + (events)

**A gap between 0.8s and 2.0s is free**: under 2.0s it needs no act, and at or above
0.8s it does not count toward [NO LANDING]'s run of three. So a piece buys camera
movement it cannot afford in acts by **pairing** moves - cueing the second a beat after
the first, usually from the next sentence - and landing once for the pair. That is a
legitimate shape, not a dodge: the camera crosses in two legs.

If a shot list will not fit the act budget, the choices are: fewer moves, more pairs, or
a script that names more of the set. Not "more props" - unnamed props do not help.

## `NEVER READ` forces the smallest-type prop to be a destination

[NO DETAIL] wants a prop setting type at 28px or less, and [NEVER READ] wants that type
framed at 30px **on the frame**, in a framing that names its prop. So the small-type prop
must be a framing target, and a target it is - against a [ALL STOPS] cap of 60%. Put the
small type on a **near-plane** prop: the apparent size is `px * s / depth`, so a near
plane buys 1.6x for free and the framing can be wider.

## An offset can turn a push into a travel

[CENTRED] pushes an author to offset most framings, and `off=` moves the camera. Two
consecutive framings offset in **opposite** directions add their shifts to the distance
the move crosses, which is what [NOT A PUSH] and [NOT A PULL] measure against
`close_move` (1.0 frames). Offsetting the pair the same way costs nothing. Check the pair,
not the framing.

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
