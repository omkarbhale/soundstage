---
name: standing-set
description: "The soundstage format for a video that is not a deck. ONE space, built before the composition is written, and a camera that travels through it: props exist from the first frame to the last, and meaning comes from where the camera goes and what it finds, never from one rectangle replacing another. Owns the visual LANGUAGE - the world and its regions, depth planes, palette progression, type as objects, how a screen or a block of code or an icon is staged, the five camera moves and the holds between them, and what makes a piece refuse. Built on motion-doctrine, which it does not repeat. Load before composing any soundstage video that is not a slideshow. [set, camera, space, depth, parallax, world, region, palette, travel, push, pull, arc, rack, hold, persistence, no-slides, format]"
---

# Standing Set

There are no slides here and nothing replaces anything. There is **one space**, built
before a line of the composition is written, and **one camera** that travels through it.
Every prop exists from the first frame to the last. The camera moves to things, past
them, into them, around them; it holds; the set changes state while it holds. That is
the whole language.

A piece in this format is **one clip**. A second picture clip is a second slide, and
`set_check.py` refuses it.

## Read these first, and do not repeat them

| For                                                                    | Go to             |
| ---------------------------------------------------------------------- | ----------------- |
| The vector law, carriers, causal motion, the ban on idle motion, stillness before climax | `motion-doctrine` |
| Ease and parameter catalogue for a cut, a blur-cut, a staggered entry  | `cut-the-curve`   |
| Render mechanics where two wrappers overlap                            | `seam-craft`      |
| A pointer-led action inside a prop                                     | `oversized-cursor`|

Those own the mechanics. This owns the language. Two joins to make and neither is a
contradiction:

- A standing set has no boundaries between separately authored parts, so the Seam Gate
  has nothing to verify inside one. Where a piece genuinely cuts - joining modules,
  entering a sub-composition - that cut belongs to `motion-doctrine` and `cut-the-curve`
  implements it.
- The camera IS the film's current. Every rule about idle motion and about stillness
  before a climax applies here unchanged; this format says what the camera does instead
  of wobbling.

The narration chain, the cue guards and the ending are the studio's and are unchanged
by this format: README, "Making narration", "Cueing a reveal", "Proving a reveal lands",
"Proving a composition before you spend the narration on it", "Showing a screen, so
someone can find it again", "Ending a module".

## The material

| File                          | What it is                                               |
| ----------------------------- | -------------------------------------------------------- |
| `components/standing_set.py`  | the space and the camera; computes every transform        |
| `set_check.py`                | the guard; refuses everything named below                 |
| `components/figure.py`        | a product screen inside the set, ADR-0010 unchanged       |

```python
import standing_set
S = standing_set.Set(frame=(1920, 1080), world=(12600, 2600))
S.plane("far", 2.4); S.plane("mid", 1.0); S.plane("near", 0.62)
S.region("intake", (0, 0, 4200, 2600), ground="#0b1522", ink="#eaf2ff", accent="#5fe0c0")
S.prop("handler", "code", "mid", at=(4650, 1400), size=(2100, 1000), html=...)
S.plate('<svg class="mark">…</svg>')
S.open(on=["intake"], pad=0.20)
S.move("travel", on=["queue"], cue="carried through", dur=2.4, pad=0.14)
S.move("rack", cue="what stands behind", dur=0.9, focus="far")
S.event("lamp", cause="chip", cue="the light comes up", note="the lamp lifts")
S.change("count", cue="the number climbs", note="0 to 41")
css, html, js = S.render(t, end=speech_end + 2.0)
```

`t` is the composition's own cue resolver. Nothing in the camera is typed: name the
props, get the framing.

**A composition not built through `components/standing_set.py` is not in this format.**
The component is what makes every rule below measurable; hand-written markup that looks
like a set carries no manifest, and `set_check.py` refuses to certify it at all.

---

# 1. The world

Build the whole space first. The composition is written against a set that already
exists, the way a crew walks onto a floor that is already built.

- The props **occupy at least 3 frames on their long axis and 1.5 on their short** -
  measured across the props, not across the world declared around them. A space the
  camera can see at once is a poster, and travelling across it is a pan. [SMALL WORLD]
- The camera works over **at least 4x of scale** across the piece. [ONE DISTANCE]
- Props are placed at world coordinates once and never move to accommodate the camera.

# 2. Regions, and the palette that travels

The world is divided into **regions**: places with their own ground, ink and accent. The
palette changes because the camera went somewhere.

- **At least 3 regions**, each holding **at least 2 props**. [ONE PALETTE, EMPTY REGION]
- Ink on ground is **7:1 or better** in every region. Type here is read at depth and
  through the depth-of-field blur. [UNREADABLE]
- Two regions that meet differ by **25 degrees of hue or 0.12 of relative luminance**,
  and their accents differ by **40 degrees**. [SAME ROOM, SAME ACCENT]
- **At most one region is neutral.** The rest are colours. [GREY]
- In the order the camera first enters them, the grounds **lighten steadily, darken
  steadily, or turn one way round the wheel** - 0.04 of luminance a step, or 25 degrees
  a step and 70 in total. Three unrelated palettes are three decks in three colours.
  [NO PROGRESSION]
- **At least one travel crosses a region boundary.** [NO CROSSING]

Choose the progression for the piece and state it in one line before building: what the
first region is, what the last one is, and what the journey between them is. A palette
that arrives somewhere is the difference between a film and a colour scheme.

# 3. Planes, and what depth is for

A plane carries a depth. 1.0 is what the camera focuses to; above 1 is further away,
below 1 is nearer than the subject. Depth is not decoration - it is what makes a move
read as a move.

- **At least 3 planes carry props**, no plane holds more than **55%** of them, and the
  populated planes span **2.5x in depth**. [FLAT, SHALLOW]
- **At least half of all framings carry a prop from another plane at 8% of the frame or
  more.** A frame with one object on a background is a slide photographed at an angle.
  [FLAT FRAME]
- The near plane magnifies distance from the camera's centre. A near prop stands where
  the camera goes, or it is never seen. [UNSEEN]
- Focus is a framing's property and blur is computed from it. A **rack** is the only way
  to change focus without moving.

# 4. Props

A prop is a thing that exists in the space. Eight roles, and the frame is built out of
several of them at once.

| Role       | What it is                              | How it stands                                                                 |
| ---------- | --------------------------------------- | ----------------------------------------------------------------------------- |
| `surface`  | architecture: a wall, a floor, a grid, a plan | deepest populated plane, at least 1.5 frames across, one per region      |
| `screen`   | a product screen                        | built with `components/figure.py`; the measured highlight is unchanged here    |
| `code`     | a block of source                       | shown whole and read in part: the camera pushes to the lines the words name    |
| `diagram`  | nodes and edges                         | laid out in the world, so the camera can travel along it rather than reveal it |
| `chart`    | measured data                           | one figure large enough to be a destination                                    |
| `artifact` | an object: a document, a card, a device | carries the region's accent, never the ink                                     |
| `glyph`    | a mark or an icon                       | near plane, standing close to a framing the camera visits                      |
| `specimen` | type as an object                       | at most 12 words [WALL OF TEXT]                                                |

- **At least 12 props, in at least 4 roles**, and at most **40%** of them specimens.
  [THIN SET, ONE NOTE, ALL WORDS]
- **Every region has a surface on the deepest populated plane.** Props stand in a built
  space, not in a void with a colour behind it. [NO ARCHITECTURE]
- **No two props share a role and a size.** Repeated identical objects belong inside one
  prop; side by side they are cards on a slide. [TWINS]
- **Every prop covers 4% of the frame at some point.** A prop nobody ever sees is in the
  file and not in the film. [UNSEEN]
- **No prop carries more than 60 words.** [WALL OF TEXT]
- **One plate**, fixed to the frame, at most 4 words, never animated. Everything else the
  viewer sees stands in the world. [LOOSE, PLATE, PLATES]

# 5. Type

Type is an object in the space with a position and a distance, not a label on a picture.

- **At least 6 distinct sizes, spanning 6x.** A headline size and a body size is a deck.
  [ONE SIZE, NO SCALE]
- **Two or three families**, one of them monospace only where a `code` prop needs it.
  [FAMILIES]
- **One prop sets type at 200px or more** in world units, and **one at 28px or less**.
  [NO SCALE, NO DETAIL]
- **The smallest type is framed close enough to read** - 30px on the frame - in a framing
  that names its prop. Detail nobody can reach is not detail. [NEVER READ]
- **No lists.** A bulleted list is the thing this format exists instead of. [BULLETS]

# 6. The camera

Five moves and the holds between them. A framing is computed from the props it names:
name them, and the centre and the scale follow. A typed camera position is refused the
way a typed highlight is. [HAND-DRIVEN]

| Move     | What it does                          | What proves it                                                            |
| -------- | ------------------------------------- | -------------------------------------------------------------------------- |
| `travel` | goes somewhere                        | crosses at least 0.9 frames, scale within 15%                              |
| `push`   | gets closer                           | scale at least 1.25x, crosses at most 1.0 frames                           |
| `pull`   | backs off                             | scale at most 0.8x, crosses at most 1.0 frames                             |
| `arc`    | turns around something                | crosses 0.15-0.6 frames at constant scale, shearing its planes by 0.25     |
| `rack`   | changes what is sharp                 | the framing does not move and the focus plane does                          |

- **At least 4 of the 5 appear, and none is more than 40% of the moves.** A camera that
  does one thing is a transition. [ONE MOVE]
- **Every move runs 0.6s to 3.5s.** Split a long travel into legs with a beat between.
  [PACE]
- **Every move starts on a word.** Quote the narration, never a number (ADR-0003), and
  quote it in transcript spelling (README, "Write the cue in transcript spelling").
  [NOT SPOKEN, AMBIGUOUS]
- **The camera never overshoots.** No `back`, `elastic` or `bounce` ease: a camera that
  overshoots is a whip, and a whip is a cut.
- **The camera lands every second move.** Three moves running with under 0.8s between
  them is a tour bus. [NO LANDING]
- **At least two props are framed again later from somewhere else** - a different scale
  or a different position. A set nobody returns to is a corridor, and nothing in a
  corridor persists. [NO RETURN]

## Rest

- **The camera is still for at least 40% of the piece**, in at least 3 holds of 2s, one
  of them 3.5s or longer. Meaning is made where the camera lands. [NO REST]
- **Every hold carries an event or a change.** A hold with nothing happening in it is the
  frame waiting. After the last spoken word the film is allowed to be still, and it ends
  a measured two seconds later (README, "Ending a module"). [DEAD HOLD]

# 7. The set performs

- **Props do not arrive.** Everything is there from the first frame; the camera finds it.
  A prop that fades in when the camera reaches it is a bullet. [ARRIVES]
- An **event** is a prop that arrives anyway. It is rationed to **25% of the props**, and
  each one is caused by a prop already on screen when it fires. [ARRIVALS, UNCAUSED]
- A **change** is a prop in a different state at the end than at the start: a screen
  advanced, a diagram completed, a count moved, a door open. **At least 3.** Each one is
  answered by a tween that moves something on the frame - a prop's opacity nudged between
  0.9 and 1 satisfies nothing - and that tween lands **within a second of the word that
  announces it** (ADR-0003). [STATIC, OFF ITS BEAT]
- Every prop is a destination is the failure this rations from the other side: **at most
  60% of props may be framing targets.** The rest is space the camera passes through, and
  it is what makes the film feel like a place. [ALL STOPS]

# 8. How it opens and how it ends

- **The opening framing shows at most 40% of the props.** The set is discovered, not
  presented. [OPENS WIDE]
- **The closing framing shows at least 66% of them, including 3 that changed**, and is
  not the opening framing. The last thing the viewer gets is the whole space they have
  been through, different from how they found it. [NO PAYOFF]

# 9. Build it in this order

1. Write the world: size, regions and their palette progression, planes.
2. Place every prop. Say out loud what each one is and which region it stands in.
3. Write the framings and the moves, cued from the narration.
4. Declare the events and the changes, and write their tweens.
5. `python3 dry_run.py narration.txt <composition>` then build, so every fault below
   surfaces before the narration is paid for.
6. Run the guards. All five, every time:

```
python3 cue_check.py <composition>/transcript.json <composition>/gen.py
python3 id_check.py <composition>/index.html
python3 figure_check.py <composition>/index.html
python3 set_check.py <composition>/index.html <composition>/transcript.json
```

`review_frames.py` picks the seconds to look at; `hyperframes snapshot --at` captures
them (README, "Reviewing a module without rendering it"). Render from a Linux-native
path (README, "Where to render").

# What makes a piece wrong

Everything above refuses by name. These are the readings that pass a careless eye and
are refused anyway:

| The lazy reading                                                  | What it is            |
| ----------------------------------------------------------------- | --------------------- |
| One clip per beat, with a camera move at each boundary            | slides [ONE CLIP]     |
| A world the size of the frame, panned across                      | a poster [SMALL WORLD]|
| Props that fade in as the camera reaches them                     | bullets [ARRIVES]     |
| Twelve props, twelve stops                                        | slides side by side [ALL STOPS] |
| One accent on one dark ground, everywhere                         | a deck wearing a camera [ONE PALETTE, NO PROGRESSION] |
| A row of identical cards                                          | a slide [TWINS]       |
| A headline size and a body size                                   | a deck [ONE SIZE]     |
| A camera that never stops moving                                  | a screensaver [NO REST] |
| A hold on a frame where nothing happens                           | waiting [DEAD HOLD]   |
| Every move a push                                                 | a transition [ONE MOVE] |
| A framing typed by hand because it looked right                   | a highlight drawn by hand, in the third medium [HAND-DRIVEN] |
| A title fixed to the frame over the top of the world              | an overlay [LOOSE]    |
| A change declared, and a tween that moves nothing answering it    | a line written for the guard [STATIC] |
| A big empty world with everything standing in one frame of it     | a poster [SMALL WORLD] |
| The set ends exactly as it started                                | nothing was learned by going [NO PAYOFF] |
