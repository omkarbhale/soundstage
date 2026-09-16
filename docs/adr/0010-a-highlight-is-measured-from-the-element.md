# A highlight is measured from the element, never drawn by hand

A video that names a control in a product should show that control where it lives, and
point at it. The pointing is a rectangle over a screenshot, and the tempting way to get
one is to look at the picture and type four numbers.

Those numbers are wrong the moment the product's layout moves, and nothing says so. The
composition builds, `cue_check.py` passes because the phrase still resolves,
`id_check.py` passes because the element still exists, and the frame is as beautifully
finished as it ever was - with the ring round the control NEXT to the one the narration
just named. It is a confident, well-drawn answer to the wrong question, which is the
failure this repo cares about more than any other.

So a highlight is never drawn by hand. The capture reads the element's own bounding box
off the page and writes it beside the picture; the composition places the highlight from
that file; `figure_check.py` proves, after building, that the numbers on the frame are
still the numbers that were measured. This is [ADR-0003](0003-pace-visuals-to-the-voice.md)'s
rule in another medium: never hand-time an animation, never hand-place a highlight.

## Consequences

A shot can only be re-taken by re-running the capture, which is the point: a re-take
re-measures, and a mark whose selector no longer matches anything fails the capture
loudly instead of producing a picture with a ring in the old place.

It also settles what a figure is for. The question a viewer has is "where is that?", and
a tight crop of a button does not answer it - it shows what the button looks like and
says nothing about where it lives. So the frame carries enough of the screen to learn
the position from, and a magnified inset, when the label has to be read as well as
found, goes BESIDE the wide shot and never instead of it.
