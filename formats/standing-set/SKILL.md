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

---

# What a piece looks like

A room that was built, dressed and then filmed.

**The frame is mostly still.** When the camera moves it moves once, for a reason, and
stops somewhere worth stopping - and while it is moving, nothing in the room moves. The
eye is given one thing at a time: the camera crossing the floor, or one object doing one
thing while the camera watches it. Two at once is noise, and noise reads as cheap however
well either half is made. A crowded frame is not effort. A still frame with one thing
happening in it, held long enough to land, is.

**Depth carries what a deck carries with layout.** Something stands close to the lens and
slides past fast. The subject sits at the middle distance, sharp. A wall recedes behind
it, soft, because the lens is focused forward. Every frame is three distances at once,
and travelling through them is what makes the space real rather than drawn.

**Colour belongs to places.** The room a piece begins in is not the colour of the room it
ends in, and the change arrives underneath the camera while it travels instead of cutting
between palettes. Crossing from one region into the next should feel like walking through
a door, not like a slide turning.

**Type is an object with a size and a position.** Some of it is enormous - a word built
at the scale of a wall, which the camera backs off to read whole. Some of it is small
enough that the camera has to go and get it. How big a thing is, is an argument about how
much it matters, and a piece where everything is one size is an argument about nothing.

**A move is spent, not used.** There are five, each means something, and each answers the
question the words just raised. Where the words raise none, the camera holds. A piece
that runs out of reasons and keeps moving is a screensaver; a piece that moves only when
it must reads as directed. The move is the transition - there is no other kind here, and
none is decorative.

**The frame never says what the voice is saying.** A screen whose words are the words
being spoken is the single clearest tell of a machine-made video, and no amount of camera
work rescues it. The picture shows what the words cannot - where a thing is, how big, what
it sits next to, what it turned into. The words say what the picture cannot - why it is
there, what it costs, what happens if it is wrong. A word landing on the frame exactly as
it is spoken is a real beat, which is why it is declared and rationed rather than banned.

**This format is not illustration-led.** The set is built out of the real material: a
screen captured off the product, a block of the actual code, a figure that was measured, a
document that exists. Architecture - walls, floors, plans, panels - is what fills the space
between them. Icons are seasoning, never the meal; an icon stands for a thing, and this
format has room to show the thing.

**Care shows up in particular places, and they are where to spend it.** Every object in
the room is its own drawing rather than one drawing twelve times. The ground a prop
stands on is built rather than filled. The camera lands on compositions instead of on
subjects centred in empty frames. The set is in a different state at the end than at the
start, and a viewer can see which parts of it moved.

Everything measured below is the floor under this. It exists to stop a piece falling
through, not to describe what a good one is.

# What a piece sounds like

Someone standing in the room, talking about what is in front of them.

**The voice never says where you are in it.** No section being introduced, no "first,
second, finally", no summary of what was just covered. Those are a contents page read
aloud, and a set narrated from a contents page is a deck with better lighting. The voice
names things and says what they do.

**The words and the camera are bound at the moment of the move.** The line that sends the
camera somewhere is the line that names what is there. That bond is what makes the piece
feel filmed rather than assembled: the picture goes where the sentence goes, because the
sentence is the reason.

**Lines vary the way speech varies.** Some land in four words. Some run long enough to
carry a whole thought. A script of even fifteen-word declaratives is bullet prose with
the bullets taken out, and it sounds like one whatever is on screen.

**It is spoken, not read.** A clause that survives on a page can be unsayable out loud,
and a listener catches a pattern far faster than a reader does. Say every line aloud once.
The ones that come out flat are the ones written by habit rather than by someone who knows
the subject.

**It opens on a thing and ends on what changed.** The first line names what the camera is
already looking at. The last names something that is not how it was at the start. Nothing
is introduced and nothing is recapped, because there is no list to open or close.

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
S.open(on=["handler"], pad=0.20)
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
- Grounds, inks and accents are written as hex, and **a colour painted inside a prop is
  a house variable or a hex clearing 4.5:1 against its own region's ground.** A declared
  ink is a promise the props keep. [COLOUR, UNREADABLE]
- In the order the camera first enters them, the grounds **lighten steadily, darken
  steadily, or turn one way round the wheel** - 0.04 of luminance a step, or 25 degrees
  a step and 70 in total. Three unrelated palettes are three decks in three colours.
  [NO PROGRESSION]
- **At least one travel crosses a region boundary.** [NO CROSSING]

## The house palette

`standing_set.HOUSE` ships it. Three dark grounds turning one way round the wheel, each
owning an accent the others do not. Use it, or derive a palette that holds the same
relationships and passes the same refusals.

| Region    | Ground    | Ink       | Accent    | It is        |
| --------- | --------- | --------- | --------- | ------------ |
| `ingress` | `#0B1522` | `#E8F1FF` | `#5FE0C0` | blue-black, mint  |
| `work`    | `#241019` | `#FFEDF3` | `#FF9A5C` | plum-black, amber |
| `proof`   | `#0F1B12` | `#ECFAF0` | `#7AB8FF` | green-black, blue |

**Two text colours in the set and no more**: the region's ink, and its accent for the one
thing the narration is naming at that moment. A third colour is a decision nobody made.
The accent is spent the way a reserved vector is spent - on meaning, not on variety.

State the progression in one line before building: what the first region is, what the last
one is, and what the journey between them is. A palette that arrives somewhere is the
difference between a film and a colour scheme.

# 3. Planes, and what depth is for

A plane carries a depth. 1.0 is what the camera focuses to; above 1 is further away,
below 1 is nearer than the subject. Depth is not decoration - it is what makes a move
read as a move.

- **At least 3 planes carry props**, no plane holds more than **55%** of them, and the
  populated planes span **2.5x in depth**. [FLAT, SHALLOW]
- **Every framing carries another distance.** Props standing on planes other than the
  subject's cover at least 8% of the frame, counted together. One object on a background
  is a slide, whatever brought the camera there. [FLAT FRAME]
- The near plane magnifies distance from the camera's centre. A near prop stands where
  the camera goes, or it is never seen. [UNSEEN]
- Focus is a framing's property and blur is computed from it. A **rack** is the only way
  to change focus without moving.

# 4. Props

A prop is a thing that exists in the space. Eight roles, and the frame is built out of
several of them at once.

| Role       | What it is                                    | How it stands                                                              | Refused as        |
| ---------- | --------------------------------------------- | --------------------------------------------------------------------------- | ----------------- |
| `surface`  | architecture: a wall, a floor, a grid, a plan | deepest populated plane, 1.5 frames across, one per region                  | [NO ARCHITECTURE] |
| `screen`   | a product screen                              | built with `components/figure.py`, measured highlight unchanged             | [figure_check.py] |
| `code`     | a block of source                             | stands whole; the camera pushes in to read the lines the words name         | [NEVER READ]      |
| `diagram`  | nodes and edges                               | laid out across the world and travelled along, never revealed piece by piece | [ARRIVES]         |
| `chart`    | measured data                                 | one figure big enough to be a destination on its own                        | [UNSEEN, NO SCALE]|
| `artifact` | an object: a document, a card, a device       | sized so a push can read its face                                           | [UNSEEN]          |
| `glyph`    | a mark or an icon                             | near plane, standing close to a framing the camera visits                   | [UNSEEN]          |
| `specimen` | type as an object                             | at most 12 words                                                            | [WALL OF TEXT]    |

- **At least 12 props, in at least 4 roles**, and at most **40%** of them specimens.
  [THIN SET, ONE NOTE, ALL WORDS]
- **Show the thing, not a picture of the idea of it.** At least 30% of props are a
  `screen`, `code`, a `chart` or a `diagram` - material that was captured, written or
  measured. At most 15% are `glyph`. [DRAWN NOT SHOWN]
- **Every prop has a name**, one to four words and its own, walls included, because the
  narration is held to it. `standing_set.py` refuses an unnamed prop at build.
- **Every prop is its own drawing.** Two props whose markup matches once the words and
  their sizes are stripped are one prop placed twice; at most three may be cut from one
  stencil. A room furnished by calling one helper twelve times is a stock photograph of a
  room. [TWINS]
- **A role is what a prop is made of, not a word typed beside it.** A `screen` carries a
  frame from `components/figure.py`; a `glyph` an `<svg>` or an `<img>`; a `chart` or a
  `diagram` an `<svg>` or three drawn parts; a `surface` something drawn on it; a `code`
  prop a monospace family; an `artifact` a drawn face. A text block labelled `chart` is a
  text block. [ROLE]
- **Furnish the route, not just the stops.** A prop that is not a framing target reaches
  8% of the frame **during a move**. One that only ever appears where the camera stopped
  is a destination that forgot to be named. [ALL STOPS]
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

`standing_set.TYPE` ships the scale, in world units, and `standing_set.FAMILY` the two
families:

| Step     | Size  | What it is                                        |
| -------- | ----- | ------------------------------------------------- |
| `wall`   | 240px | a word built at the scale of the room             |
| `figure` | 190px | a number that is the point of its prop            |
| `head`   | 96px  | what a prop is                                    |
| `label`  | 56px  | what a part of it is                              |
| `body`   | 44px  | a line to be read at the middle distance          |
| `code`   | 34px  | source, read on a push                            |
| `fine`   | 22px  | the detail the camera has to go and get           |

Text is `Inter`; source is `JetBrains Mono`. Nothing else.

- **At least 6 distinct sizes, spanning 6x**, counted where they are set on props. Six
  sizes declared in the page and used on nothing is two sizes. [ONE SIZE, NO SCALE]
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

| Move     | What it does           | What proves it                                                         | Refused as     |
| -------- | ---------------------- | ----------------------------------------------------------------------- | -------------- |
| `travel` | goes somewhere         | crosses at least 0.9 frames, scale within 15%                           | [NOT A TRAVEL] |
| `push`   | gets closer            | scale at least 1.25x, crosses at most 1.0 frames                        | [NOT A PUSH]   |
| `pull`   | backs off              | scale at most 0.8x, crosses at most 1.0 frames                          | [NOT A PULL]   |
| `arc`    | turns around something | crosses 0.15-0.6 frames at constant scale, shearing its planes by 0.25  | [NOT AN ARC]   |
| `rack`   | changes what is sharp  | the framing does not move and the focus plane does                      | [NOT A RACK]   |

- **At least 4 of the 5 appear, and none is more than 40% of the moves.** A camera that
  does one thing is a transition. [ONE MOVE]
- **Every move runs 0.6s to 3.5s.** Split a long travel into legs with a beat between.
  [PACE]
- **Every move starts on a word.** Quote the narration, never a number (ADR-0003), and
  quote it in transcript spelling (README, "Write the cue in transcript spelling").
  [NOT SPOKEN, AMBIGUOUS]
- **The camera never overshoots.** No `back`, `elastic` or `bounce` ease: a camera that
  overshoots is a whip, and a whip is a cut. `standing_set.py` refuses one at build.
- **The camera lands every second move.** Three moves running with under 0.8s between
  them is a tour bus. [NO LANDING]
- **At least two props are framed again later from somewhere else** - a different scale
  or a different position. A set nobody returns to is a corridor, and nothing in a
  corridor persists. [NO RETURN]
- **The camera is never over empty ground.** At a quarter, a half and three quarters of
  every move, props that are not `surface` cover at least 12% of the frame. Cluster the
  props at the destinations and the flights between them are transitions, and this format
  has no transitions. [EMPTY TRAVEL]
- **At most two moves of one kind run consecutively.** A move is spent on the change of
  view the words asked for; three pushes in a row is a habit. [ONE MOVE]
- **At most 40% of framings put their subject dead centre**, within 6% of the frame
  centre on both axes. Offset the rest with `off=`, which moves the camera and leaves the
  props where they stand. A subject centred, level and still is the deck's own atom: one
  is a payoff, every one is a gallery. [CENTRED]

## Rest

- **The camera is still for at least 40% of the piece**, in at least 3 holds of 2s, one
  of them 3.5s or longer. Meaning is made where the camera lands. [NO REST]
- **Every hold carries an event or a change.** A hold with nothing happening in it is the
  frame waiting. After the last spoken word the film is allowed to be still, and it ends
  a measured two seconds later (README, "Ending a module"). [DEAD HOLD]

# 7. The set performs

- **Props do not arrive.** Everything is there from the first frame; the camera finds it.
  A prop that fades in when the camera reaches it is a bullet, and so is one held at zero
  scale or parked a full box off its own position. [ARRIVES]
- **A prop stands where it was placed.** The timeline moves a prop only where that prop
  is a declared change or event. The camera goes to things; things do not slide over to
  meet the camera. [RESTAGED]
- An **event** is a prop that arrives anyway. It is rationed to **25% of the props**, and
  each one is caused by a prop already on screen when it fires. [ARRIVALS, UNCAUSED]
- A **change** is a prop in a different state at the end than at the start: a screen
  advanced, a diagram completed, a count moved, a door open. **At least 3, one per prop,
  and never on a `surface`** - a wall does not do anything, and a change on the backdrop
  is a change nobody sees. Each is written as a `fromTo`, so both states are on the page
  to be measured, and moves its prop **1.5% of the frame, half its own box, 0.15 of
  scale, 6 degrees, 0.5 of opacity, or to another colour**, within a second of the word
  that announces it (ADR-0003). Anything smaller is a line written for the guard.
  A change that animates a part its prop does not contain moves nothing, and
  `id_check.py` cannot see it because the head of the selector exists.
  [STATIC, OFF ITS BEAT, NO SUCH PART]
- **One thing moves at a time.** The camera crosses the room, or one prop does one
  thing; never both, and never two props together. Restraint is the format's whole look:
  a frame with three things animating reads as cheap, and `motion-doctrine`'s ban on idle
  motion is the other half of the same rule. [TWO AT ONCE]
- **The changes are not one gesture repeated.** At most half of them move on the same
  channel. A lamp lifting, a count climbing and a contract being signed are three
  different things happening. [STATIC]
- **At most 60% of props may be framing targets.** The rest is space the camera passes
  through on the way, and it is what makes the piece feel like a place rather than a
  route. A set where every prop is a destination is slides laid side by side. [ALL STOPS]

# 8. How it opens and how it ends

- **The opening framing shows at most 40% of the props.** The set is discovered, not
  presented. [OPENS WIDE]
- **The closing framing shows at least 66% of them, including 3 that changed**, and is
  not the opening framing. The last thing the viewer gets is the whole space they have
  been through, different from how they found it. [NO PAYOFF]

# 9. The narration

Half the deck feeling lives in the words. The studio owns how narration is made - README,
"Making narration", and ADR-0003 for what is cued from what; this owns how it sounds and
what binds it to the set. `script_check.py` reads the script, and the transcript
only to place lines against framings, so all of it is refused before a take is spent - run
it in the dry run, where the synthetic transcript already exists.

## The register

- **Nothing announces itself.** No section introduced, no "as you can see", no "in this
  module", no summary at the end. A set has no sections, so there is nothing to introduce
  and nothing to recap. [SIGNPOST]
- **No line opens on a counter** - "first", "second", "next", "finally", "also". A list
  read out loud is the thing this format replaces. [SIGNPOST]

## The shapes of writing that has nothing to say

Every pattern below is a substitute for having something to say, and each one is
recognisable at a distance - in a piece that is spoken, more recognisable than in one that
is read. Write the way a person who knows this subject talks about it.

- **Negative parallelism is refused outright.** "Not only X but also Y." "It's not X, it's
  Y." "Not a mirror but a portal." It is the most recognisable tell there is and a listener
  hears it land. Say the thing it is. [NEGATIVE PARALLELISM]
- **Three is a rhythm once and a machine every time.** At most 15% of lines are three-item
  lists, and never two in a row. [RULE OF THREE]
- **Significance is shown, not asserted.** "Serves as", "stands as", "is a testament to",
  "plays a crucial role", "marks a pivotal moment". Each one is usually a plain `is` that
  lost its nerve. [PUFFERY]
- **Nothing hangs a vague claim off a plain fact.** A line ending ", highlighting its role
  as ..." or ", underscoring the importance of ..." has added a clause instead of a thought.
  [ADDED SIGNIFICANCE]
- **Nobody is cited who cannot be named.** "Experts argue", "industry reports", "observers
  have noted". Name who, or drop the claim. [VAGUE SOURCE]
- **Watch the density, not the word.** There is a vocabulary that clusters in machine-made
  prose - delve, intricate, interplay, tapestry, pivotal, robust, seamless, leverage, foster,
  align, showcase, and whatever has joined them since. Any one of them is a choice. Five in
  a short script is a pattern. At most three, or one per 150 words. [CLUSTER]

**That vocabulary drifts, and the guard's copy of it rots.** The tells move with each
generation of model and each round of public awareness; what reads as machine-made this
year was ordinary two years ago. Read a current catalogue - Wikipedia's "Signs of AI
writing" is the maintained one - before trusting the list in `script_check.py`, and update
it there rather than working around it.

## The shape of a line

- **A line is one thought**, at most 30 words. [LONG LINE]
- **The rhythm varies**: one line in five lands in 8 words or fewer, one runs past 22, and
  the spread of line lengths is at least 5 words. Even declaratives are bullet prose with
  the bullets taken out. [FLAT VOICE]
- **A punch is worth something because its neighbours are not punches**: at most 15% of
  lines are three words or fewer. [STACCATO]
- **No three lines in a row open on the same word**, and no opening word carries more than
  20% of them. [PARALLEL]
- **Nothing is said twice in the same words.** Six words repeated verbatim is filler.
  [PADDING]

## The bond to the set

This is what makes a piece sound filmed rather than assembled, and it is exact.

- **The line that launches the camera names where it lands.** A move's cue phrase sits in
  a line that names a prop that move frames; a `rack`'s line names something on the plane
  it pulls focus to, because that is what it moves attention to. The same holds for a
  change and for an event: the cue sits in a line that names the thing that changes or
  arrives. [UNMOTIVATED]
- **A name is not a line.** The line carrying a cue runs at least 8 words, and prop names
  are at most 15% of the script. A script that is mostly labels is a caption track.
  [NAME DROP]
- **Every prop the camera stops on is named** somewhere in the script. [UNNAMED]
- **The voice stays in the room**: never more than 25 words without naming something in
  the set. [ABSTRACT RUN]
- **The frame does not read the line back.** Of the words in a line, discounting the names
  of what is on screen, at most 35% may also be written on a prop covering the frame while
  that line is spoken. Where a word is meant to land on the frame as it is said, declare it
  - `S.echo(prop, cue=..., note=...)` - and spend at most two in a piece. An unmarked
  mirror is the tell of machine-made video; a declared one is a beat. [ECHO]

## How it opens and how it ends

- **It opens on the thing the camera is already looking at** - the opening framing's
  subject, named in the first line or the second. Not on what is coming. [AGENDA]
- **It ends on what the set is now**: the last two lines name a prop that changed.
  [RECAP]

Write the script first, build the set against it, then run this with the picture guards in
the dry run. A cue quoted from the script is matched against the audio by `cue_check.py`
and spelled the way the README's "Write the cue in transcript spelling" says; this guard
never looks at the audio and does not replace it.

# 10. Build it in this order

1. Write the script, then the world: size, regions and their palette progression, planes.
2. Place and name every prop. Say out loud what each one is and which region it stands in.
3. Write the framings and the moves, cued from the narration. `--why` prints where every
   prop is seen and how much ground each move crosses; a prop's reach depends on its
   plane and no framing shows what a move passes, so place props against that rather than
   by eye.
4. Declare the events and the changes, and write their tweens.
5. `python3 dry_run.py narration.txt <composition>` then build, so every fault below
   surfaces before the narration is paid for.
6. Run the guards. All five, every time:

```
python3 cue_check.py <composition>/transcript.json <composition>/gen.py
python3 id_check.py <composition>/index.html
python3 figure_check.py <composition>/index.html
python3 set_check.py <composition>/index.html <composition>/transcript.json [--why]
python3 script_check.py <composition>/index.html narration.txt <composition>/transcript.json
```

7. **Look at it.** Capture frames and judge them by eye - the guards measure, they do not
   see. `review_frames.py` picks the seconds and `hyperframes snapshot --at` captures them
   (README, "Reviewing a module without rendering it"). Take at minimum: the opening
   framing; the midpoint of the longest travel; the first framing inside each region; and
   the closing wide. Render from a Linux-native path (README, "Where to render").

   At each one, answer out loud: is the near plane doing anything, or is the frame flat in
   practice however the numbers read? Does the accent land on the thing being named, or on
   whatever was convenient? Is the type at this distance actually readable? Does the frame
   have a subject, or three things competing? Is there anything in it that was put there to
   fill space? A piece nobody has looked at has not been finished, and none of the above is
   measurable.

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
| Props clustered at the stops, bare ground in between              | a transition [EMPTY TRAVEL] |
| A change that moves half a pixel, or one declared on a wall       | a line written for the guard [STATIC] |
| A text block labelled `chart`                                     | a text block [ROLE]   |
| Every framing a subject centred, level and still                  | a gallery [CENTRED]   |
| A prop slid into place to suit the camera                         | staging [RESTAGED]    |
| Twelve props from one drawing helper                              | a stock photograph [TWINS] |
| Nine changes that are all the same slide                          | one animation repeated [STATIC] |
| The camera moving while three props animate                       | noise [TWO AT ONCE]   |
| "In this section we will look at three things"                    | a contents page read aloud [SIGNPOST] |
| Fifteen-word declaratives, each opening the same way              | bullet prose [FLAT VOICE, PARALLEL] |
| A line that sends the camera somewhere it does not name           | assembled, not filmed [UNMOTIVATED] |
| A script that ends by recapping what it covered                   | a deck [RECAP]        |
| "Not only a tray, but a pivotal moment in the process"            | the loudest tell there is [NEGATIVE PARALLELISM, PUFFERY] |
| Every list a triplet                                              | a machine [RULE OF THREE] |
| A line ending ", underscoring its enduring significance"          | a clause instead of a thought [ADDED SIGNIFICANCE] |

## The tells of machine-made video, in this medium

| The tell                                                          | What to do instead    |
| ----------------------------------------------------------------- | --------------------- |
| The frame writes out the sentence being spoken                    | show what the words cannot say [ECHO] |
| An evenly-spaced row of generic shapes                            | one prop containing the row, or real material [TWINS, DRAWN NOT SHOWN] |
| A gradient, a glow or a blur that carries no information          | depth carries it: planes, focus, scale |
| An icon chosen because it exists rather than because it says something | show the thing the icon stands for [DRAWN NOT SHOWN] |
| Decoration in the space where the information should be           | the prop IS the information |
| A third and fourth colour arriving by accident                    | ink and accent, and the accent means "this one" |
| Every prop the same drawing at different sizes                    | every object its own [TWINS] |
| A change declared, and a tween that moves nothing answering it    | a line written for the guard [STATIC] |
| A big empty world with everything standing in one frame of it     | a poster [SMALL WORLD] |
| The set ends exactly as it started                                | nothing was learned by going [NO PAYOFF] |
