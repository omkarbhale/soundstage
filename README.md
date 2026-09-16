# soundstage

An agent-operated video studio: the tools for making a video, and the instructions an
agent reads instead of being briefed.

## Engine and studio

[HyperFrames](https://github.com/heygen-com/hyperframes) (Apache 2.0) is the
**engine**. It renders a composition to video, generates narration and returns
per-word timing. Adopt it whole - never modify it and never wrap it.

This repo is the **studio**. It holds house style, reusable components, voice
configuration, conventions, and the instructions an agent reads so it needs no
briefing. Add no rendering logic here.

## Content never lives here

This repository is public, and no source document, script, generated audio or
finished video enters it. `/inputs/` and `/outputs/` are gitignored whole, because
the material the toolkit is pointed at is not ours to publish - read
[ADR-0002](docs/adr/0002-the-repo-is-public-and-holds-no-content.md) and
`.gitignore`'s own comments before loosening either.

## Where to start

Read [`CONTEXT.md`](CONTEXT.md) first: it is the vocabulary, and it names the words
this project rejects.

[`docs/adr/`](docs/adr/) records the decisions and why they were made:

- [0001](docs/adr/0001-hyperframes-is-the-engine-this-repo-is-the-studio.md) - HyperFrames is the engine, this repo is the studio
- [0002](docs/adr/0002-the-repo-is-public-and-holds-no-content.md) - The repo is public and holds no content
- [0003](docs/adr/0003-pace-visuals-to-the-voice.md) - Pace visuals to the voice, never voice to visuals
- [0004](docs/adr/0004-the-repo-owns-every-path.md) - The repo owns every path, the agent invents none
- [0005](docs/adr/0005-openai-for-speech.md) - OpenAI for speech, though the engine does not support it
- [0006](docs/adr/0006-the-project-is-called-soundstage.md) - The project is called soundstage
- [0007](docs/adr/0007-the-narration-guards-live-in-the-studio.md) - The narration guards live in the studio
- [0008](docs/adr/0008-a-re-voice-is-fitted-to-the-old-track.md) - A re-voice is fitted to the old track, line by line
- [0009](docs/adr/0009-a-local-voice-and-a-local-aligner.md) - A local voice and a local aligner, behind the same two paths
- [0010](docs/adr/0010-a-highlight-is-measured-from-the-element.md) - A highlight is measured from the element, never drawn by hand
- [0011](docs/adr/0011-captions-say-the-script-and-live-in-the-video.md) - Captions say the script, are timed by the transcript, and live in the video

## Making narration

Narration is generated once, in a single pass, and every on-screen reveal is cued from the
per-word timings of that real audio ([ADR-0003](docs/adr/0003-pace-visuals-to-the-voice.md)).
Four scripts, each taking explicit paths:

```
node tts.mjs        narration.txt narration.mp3 --voice sage --instructions "..."
python3 transcribe.py  narration.mp3 raw.json
python3 verify.py      narration.txt raw.json          # every script word reached the audio
python3 repair.py      narration.mp3 raw.json transcript.json   # fix collapsed word runs
```

`verify.py` and `repair.py` are not optional. Both catch faults that fail silently and leave
a module looking finished - a dropped clause, and cues landing on the wrong beat. The drop is
non-deterministic, so `verify.py` certifies the audio in hand and never the script: run it
again on every regeneration. Read
[ADR-0007](docs/adr/0007-the-narration-guards-live-in-the-studio.md) before skipping either.

One pass has a ceiling, and it is on **tokens rather than characters**, so counting
characters will not find it. `gpt-4o-mini-tts` refuses an input over **2000 tokens** - about
1,700 words, or a little over ten minutes of speech. `tts-1` and `tts-1-hd` cap at 4096
*characters*, which is smaller, so neither is an escape hatch. ADR-0003 requires one pass for
one video, so that ceiling is the length of a soundstage video: a topic that will not fit is
**more than one module**, not one module generated twice.

Measure the script before writing to it rather than after. The endpoint reports the token
count inside its own refusal, so sending the script twice over (`input: script + script`)
costs nothing, fails, and hands back twice the number you wanted.

### The clause drop is length-driven, and 2000 tokens is not the working ceiling

The hard limit refuses loudly. The fault that matters arrives long before it and says nothing:
**the longer the pass, the more clauses the model silently drops**, and `verify.py` is the only
thing that sees it. Measured on one script, same voice, same instructions, one variable:

| words in the pass | what `verify.py` found |
|---|---|
| 280 | clean, first take |
| **1,398** | **clean, first take** |
| 1,663 | 1 to 8 dropped words or clauses **on every one of ten takes** — never clean |

At 1,663 words the drops were scattered singletons in different places each time, so they cannot
be written out: hardening the sentence that dropped only moves the loss somewhere else. Among them
were a whole gate ("then calibration, then validation"), the adjective in "resolves the **wrong**
element" — which inverts the sentence — and, once, the script's central principle entire.

So **write to about 1,200 words a pass and treat that as the ceiling**, not the 2000-token limit.
A topic that will not fit is more modules, not a longer pass: **add a module rather than cut
content**, and join them (below). Run `verify.py` on every pass and every regeneration — the drop
is non-deterministic, so a clean pass certifies the audio in hand and nothing else.

## Joining modules into one video

A course is several modules, and the deliverable is often one file. Render each module normally,
then join the finished files:

```
python3 join.py course.mp4 module-01.mp4 module-02.mp4 module-03.mp4
```

Each module keeps its own narration pass and cues its own reveals from its own per-word timings,
so nothing is paced to a guess and [ADR-0003](docs/adr/0003-pace-visuals-to-the-voice.md) is
satisfied — what that ADR forbids is pacing the voice to the visuals, not a deliverable having
more than one pass.

`join.py` copies the streams rather than re-encoding, so the joined file is bit-for-bit the
modules that went into it and joining costs seconds instead of minutes. That only works when every
part shares a codec, resolution, frame rate and audio layout, so it **checks that first and refuses
to join mismatched parts** rather than producing a file that plays for one viewer and not another.
It also checks the finished duration against the sum of the parts, because a concat that silently
drops a part still produces a playable file.

**The concat demuxer drops caption tracks**, measured rather than feared, and the joined file plays
perfectly without them. So `join.py` re-assembles the parts' subtitle tracks onto the join, shifted
by the same cumulative durations it already measures, and refuses a set of parts where only some
carry captions rather than joining to a track that stops partway through.

## Speaking without an account

`tts.mjs` and `transcribe.py` each speak two engines behind one path (ADR-0009). OpenAI is
the default while a key works; the local pair needs no key, no network and no account, and
runs on CPU.

```
node tts.mjs narration.txt narration.mp3 --engine kokoro --voice af_heart --speed 0.9
python3 transcribe.py narration.mp3 raw.json --engine local
```

`--engine auto` (the default on both) prefers OpenAI and falls back to local when the key is
refused or out of credit. It says so loudly and always prints which engine actually spoke,
because a voice that changes without anyone noticing is worse than one that fails.

**Setting the local pair up.** Both need a Python that is not the system one - `kokoro-onnx`
refuses Python 3.14, and the system interpreter here is 3.14. Build one venv, put all three
packages in it, and point the engine's own variable at it:

```
uv venv --python 3.12 ~/.cache/soundstage/voice-venv
uv pip install --python ~/.cache/soundstage/voice-venv/bin/python kokoro-onnx soundfile faster-whisper
echo "HYPERFRAMES_PYTHON=$HOME/.cache/soundstage/voice-venv/bin/python" >> .env
```

`hyperframes doctor` then reports `TTS (Kokoro)` as installed, which is the check that the
speech half is wired. The model downloads itself on first use (~310 MB) into
`~/.cache/hyperframes/tts/`; faster-whisper downloads its own on first use.

**What changes when the voice is local.** Kokoro is deterministic - the same text gives the
same audio every time - so *taking a module repeatedly until `verify.py` is clean is
meaningless*. There is one take. Run `verify.py` anyway: a drop it reports is now a fact
about the script rather than a dice roll, and no number of retakes will move it. Measured
over six voices on a sample built from the hardest tokens in one corpus, Kokoro produced
**zero deletions and zero insertions** in every one.

**It mispronounces proper nouns, and has no `instructions` control to fix it with.** Measured:
`Aras` read as ARR-as, `tas-playwright` as "task playwright", and a capitalised `TAS` spelled
out letter by letter - 0.62s against 0.34s for the single syllable, which is how you tell
without listening. So pass a respelling table:

```
node tts.mjs narration.txt out.mp3 --engine kokoro --lexicon pronunciation.json
#   { "Aras": "Airus", "tas-playwright": "tahs playwright" }
```

It rewrites what is **spoken**, never the script, so `verify.py` still diffs the real
narration against the real audio. Match it against a reference: synthesise the name, align
it, and compare the spelling the aligner returns with the one it returns for audio you know
is right.

## Re-voicing a video that already exists

Replacing the reader on a finished video runs the opposite way to everything above: the
cut cannot be paced to a new voice, so the old track is the score
([ADR-0008](docs/adr/0008-a-re-voice-is-fitted-to-the-old-track.md)). The picture is never
touched - the video stream is stream-copied and the new track is built to the old one's
length.

```
python3 speech_runs.py old-voice.wav                      # the lines of the old track
python3 dub_script.py  old-voice.wav script/ --vocab v.txt  # each line, from its own audio
python3 dub_speak.py   script/ clips/ --instructions voice.txt --speed 1.27
python3 dub.py         old-voice.wav clips/ new-voice.wav --report   # the fit, first
python3 dub.py         old-voice.wav clips/ new-voice.wav
```

Read `--report` before building. Every line's tempo is the difference between two speaking
rates on the same words, so corrections clustering off 1.0 mean the take is paced wrong as
a whole - and the fix for that is `dub_speak.py --speed`, which changes the model's own
delivery, not a harder time-stretch afterwards. A line past the limit is refused rather
than squeezed audibly; shorten it instead. The three worst-fitting lines of one track were
the three naming a part number, because the speech model read every zero of an identifier
the narrator had said in about a second.

`--vocab` is a file of the proper nouns and part numbers **taken off the screen**. A
transcript is normally allowed its own spelling of a name, because a reader never sees it;
this one is read back out by a speech model, so a name heard wrong becomes the finished
video saying the wrong word.

To mend one line later, edit its text and re-read only it:

```
python3 dub_speak.py script/ clips/ --only 7
```

It takes the voice, model, speed and instructions from `clips/take.json` and refuses to be
given them again. The rest of the take was read at one setting, and a line read at another
sounds like a different person in a different room - one sentence in four minutes.

The last step is not one of these scripts. The new track is the old one's length, so the
picture needs nothing done to it and is copied across rather than encoded again:

```
ffmpeg -i old.mp4 -i new-voice.wav -map 0:v -map 1:a -c:v copy revoiced.mp4
```

`dub.py` proves the finished track lands on the old grid before it is worth muxing, but
nothing here can check pronunciation. Give a re-voice a human ear before it ships.

## Cueing a reveal

A composition cues each reveal by quoting the narration - `t("Leave it where it is")` - and
the lookup returns the **first** match. Quote something the narrator says twice and the
reveal lands on the wrong one, usually a scene early and already drawn when its own scene
fades in. Nothing fails and nothing warns, and the frame looks finished either way, so it is
only caught by sampling exactly that frame. Run this before rendering:

```
python3 cue_check.py transcript.json gen.py     # every cue phrase names one moment
```

Where a phrase genuinely repeats, name the occurrence - `t("...", 2)` - and it passes, because
you have said which. Keep no hand-written list of cue phrases: it reads the generator, and a
hand-kept list goes stale.

**It reads `t("literal")` calls, so a cue built from a variable is invisible to it.** A scene
that cues a row of pills from a list - `for c in [...]: M.rise(..., t(c))` - passes this check
with every one of those cues unverified, and they are exactly the cues a repeated row uses. The
reliable check is to RUN the generator rather than scan it: build the composition against its
own transcript in a copy and let the generator's own cue resolution refuse. Do that before a
render is started, not after - a cue fault found afterwards has already cost the render slot.

What it reports is ambiguity, not a defect, and the two are worth telling apart before you
touch a timing. Repeats cluster because a module says its key phrase once in the scene that
defines it and again in the scene that builds on it - and the defining scene comes first, so
the first match is usually the occurrence the scene was written around. Read the scene, sample
the finished render either side of both candidates, then name what you found: `t("...", 1)` as
readily as `t("...", 2)`. Naming the occurrence records the answer rather than changing it - a
cue that was already right keeps the time it had.

### Write the cue in transcript spelling

A cue is matched against the **transcript**, and the transcript does not spell everything the
way your script does. Four differences, each one measured rather than guessed:

- **No hyphens, ever.** Across a 1,334-word module not one hyphenated word came back
  hyphenated, and `multi-step wizards` came back as `step wizards`.
- **Numbers come back as digits, inconsistently.** In one module `Screen one` was transcribed
  `Screen 1` while `Screen two` and `Screen three` stayed words - so the hazard does not even
  announce itself by breaking every sibling cue.
- **Spelling is Americanised.** `recognise` comes back `recognize`, `centred` comes back
  `centered`.
- **Compounds separate.** `preflight` comes back `pre flight`, `cannot` as `can not`,
  `lifecycle` as `life cycle`.
- **And a local aligner glues words together across a dash.** faster-whisper renders some
  punctuation as an em dash with no spaces and emits both sides as ONE token: a script
  reading `the provenance thread: occurrence one` aligned as `thread—occurrence`, so a cue
  ending on `thread` or starting on the next word matched nothing. Three tokens in a
  969-word module, and four broken cues between them. Cue away from the punctuation, not
  just away from the spelling.

So a cue quoting any of those resolves against the script you wrote and against nothing in the
audio. Move the cue onto a neighbouring phrase that contains none of them - that survives a
re-record, where transcript spelling does not, because the next take may spell it the other
way. Do not quote a number, a hyphenated word, a compound or a word whose two spellings differ.

A function word can also simply be absent: a take that says `Drive to the exact screen` can
transcribe as `Drive to the screen`, with the audio intact. Another reason to cue on the part
of the sentence that carries the meaning rather than on its opening words.

This is not a style preference: on one course it was eight broken cues across six modules
before a take was spent, and five more that only the real transcript could reveal.

## Proving a reveal lands

A composition animates by selector, and two ways of writing one stop the reveal landing
where it was meant to. A **duplicate id** - a scene that writes literal ids and also
generates numbered ones in a loop - resolves to the first match in document order, so one
element is tweened twice and the other has no reveal at all: it is simply on screen from the
moment its scene fades in. A **selector that matches nothing** - an element renamed, a tween
left behind - animates an empty set, with the same result.

```
python3 id_check.py <composition>/index.html    # every reveal has one element to land on
```

It refuses a third thing for the same reason: **a clip that is never on screen**. Measured in this
repo's own corpus - a scene table listed out of spoken order gave one clip `data-duration="-63.59"`
and let another overlay ninety-seven seconds of its module. Each scene's end is taken from the NEXT
table entry's start, so a table out of order is the way that happens. Every reveal inside the
negative clip had exactly one element to land on, and none of them were ever seen.

Both fail the way the narration faults do. Nothing errors, nothing warns, `cue_check.py`
still passes because every cue phrase still resolves, and the scene's **settled** frame is
identical either way. The only frame that shows it is one sampled between the two cues -
which is not a frame anyone picks by hand, and not one `review_frames.py` promises either,
because it samples a scene's reveals rather than the gaps between them. Run it after
building and before rendering, beside `cue_check.py`.

## Proving a composition before you spend the narration on it

Every reveal is placed from the module's transcript, so a composition cannot be run at all
until its audio exists - and the audio is the expensive, non-deterministic half. That ordering
hides a whole class of fault until the worst possible moment. A generator that raises, a cue
that names no moment or two of them, a duplicate id: none of them are about the recording, and
all of them are found only after it has been paid for.

```
python3 dry_run.py narration.txt <composition>   # synthetic transcript, then build it
( cd <composition> && python3 gen.py )
python3 cue_check.py <composition>/transcript.json <composition>/gen.py
python3 id_check.py <composition>/index.html
```

`dry_run.py` writes the script's own words at a steady rate, spelled the way transcription
really spells them, plus the two tail files the generator reads. Every fault that is a property
of the composition rather than of the recording surfaces now, for no API calls and no takes.

It proves no timing. Every time it writes is invented, so a clean dry run says the composition
is well-formed and says nothing about whether a reveal lands on its word - that is what the
real chain and `review_frames.py` are for. Run it before the first take of a module, and again
after any edit to a generator, and keep the real guards where they are.


## Showing a screen, so someone can find it again

A video that names a control should show it where it lives. The question a viewer
actually has is **where is that**, and a tight crop of a button answers a different one -
it shows what the button looks like and says nothing about its position. So a figure
carries enough of the screen to learn the position from (the page it is on, the panel it
sits in), and the highlight does the pointing. A magnified inset, for when the label has
to be read as well as found, goes BESIDE the wide shot and never instead of it.

`components/figure.py` is the component. A composition imports it, is told where the
measured shots live, and asks for a figure:

```python
import figure
F = figure.Figures(f"{D}/assets/shots")        # the path is owned here (ADR-0004)
F.fig("screen-one", "f1",
      mark=("name", "Name"),                   # ringed, named, spotlit
      also=[("tenant", "Tenant")],             # ringed; pass None to ring without naming
      zoom="name",                             # magnified beside the frame
      caption="the card is the whole page")
```

Every id derives from the second argument - `#f1-frame`, `#f1-m-name`, `#f1-t-name`,
`#f1-z`, `#f1-cap` - so each piece is cued on its own word like any other reveal, and
`id_check.py` still finds exactly one element for each.

**Never type a highlight's numbers.** The capture reads each element's own bounding box
off the page and writes it beside the picture; the component places the ring from that
file and stamps the shot and mark name on it.

```
python3 figure_check.py <composition>/index.html   # every ring is still the measured box
```

A hand-typed or stale box is the quietest fault in the set: the ring lands on the control
NEXT to the one the narration named, and the frame looks exactly as finished either way -
`cue_check.py` passes, `id_check.py` passes, and nobody reviewing a render spots it
because there is nothing to spot. Run it after building and before rendering, beside the
other two. [ADR-0010](docs/adr/0010-a-highlight-is-measured-from-the-element.md) has the
argument.

**When the narration is out of date, correct the picture, not the words.** The audio is
locked (ADR-0003), so `note=("since this was recorded", "…")` puts a short factual line
under the frame saying what the product does today. Two rules go with it. It must not go
into the **captions** — a subtitle has to say what the voice says, and a corrected caption
disagrees with the audio the viewer is hearing, which is a second wrong thing rather than
a fix (`caption_check.py` refuses it anyway). And it is not drawn in `--warm`: in this
house terracotta is a claim that something is *refused*, and a screen that has moved on
since the recording is not a refusal. Write down, with the note, the exact sentence a
re-record would change, so a later pass does not have to find it again.

**A figure changes the layout around it, so re-check the frame.** A stack of cards that
fits comfortably across 1580px does not fit in the 620px column beside a screenshot: it
gets taller, and the last card renders off the bottom of the picture. The frame then
reads as a design with a lot of air at the top, and the card that fell off was the one
carrying the point. Measured twice in one afternoon's work, both times by eye. Whatever
the production uses to check it - the engine's own `snapshot`, or a browser measuring the
laid-out page - check it after adding a figure to a scene that had none, and look at
every scene rather than a sample.

Capturing is the production's job, not the studio's - it drives whatever product the
video is about - but two rules travel with the component. **Measure, do not type**, and
**refuse rather than guess**: a mark selector that matches nothing, or matches more than
one element, must fail the capture. The first match of an ambiguous selector is exactly
the kind of answer that renders beautifully and points at the wrong control.

## Captioning a module

Captions are a soft subtitle track inside the video, and nowhere else. The viewer can
turn them off, there is no sidecar file to keep in step, and nothing is burned into the
picture where it would sit on top of a figure's callouts.

```
# the normal path: caption a finished module, leaving no sidecar behind
python3 captions.py --style captions.json --into module.mp4 module-cc.mp4 \
                    narration.txt <composition>/transcript.json --offset 2.0

# prove the track that actually shipped
python3 caption_check.py --style captions.json narration.txt --in module-cc.mp4

# on demand, for a platform that strips or ignores a muxed track
python3 captions.py --style captions.json narration.txt \
                    <composition>/transcript.json out.srt --offset 2.0 --report
```

`--offset` is where the narration starts inside the video - the composition's opening
card - and a caption timed without it is wrong by exactly that much.

**The words come from the script, the times from the transcript.** Never caption from the
transcript's own text: the aligner mishears, and a caption is read rather than matched, so
the mishearing is printed on the screen. Measured here: a module whose first spoken word
is `Screen` has `Scream` as transcript word zero. `caption_check.py` refuses a track that
does not say the script word for word, which is what makes that rule enforceable.

**Verify the track in the finished file, not an intermediate.** A subtitle track is off by
default in most players, so a failed mux ships an uncaptioned video and nobody reviewing
it notices. `--in` reads the stream back out and checks it. Re-encoding or trimming drops
the track silently - any ffmpeg pass without `-map 0` - so re-run the caption pass after
one. `join.py` re-assembles the parts' tracks onto a join for the same reason, and refuses
a set of parts where only some carry captions.

### Choosing the caption style

soundstage holds no house style, so every value arrives in `--style` and a missing one
refuses by name. Choosing them is judgement, and this is how to do it.

**Start from the narration's pace, because it governs everything else.** Divide the
script's words by the audio's length. At 160-171 words a minute - about 16 characters of
speech a second - a caption is already at the top of comfortable adult reading, so cues
must be SHORT AND FREQUENT rather than long and dense. A slower narration can carry longer
cues; a faster one cannot, and no setting downstream can fix it without going out of sync.

- `line_chars` / `lines` - 42 and 2 is what broadcast subtitling settled on and what a
  viewer reads without tracking back. Go narrower if the frame is busy under the caption.
- `cue_seconds` - the ceiling stops a cue outstaying its sentence and is enforced. The
  floor is what a cue is held to *where the cue after it leaves room*: a two-word sentence
  tail whose next cue follows immediately is merged back or brought on earlier, and where
  neither is possible it stays short rather than overlapping. Readability there is
  `hard_cps`'s job, not the floor's - three characters in under a second is not a flash.
- `hold_seconds` / `gap_seconds` - a cue that vanishes on the last syllable reads as a
  flicker, and two cues with no gap between them read as one.
- `min_break_chars` - the shortest cue worth breaking a clause for. A boundary two words
  in leaves a caption on screen long enough to read with nothing on it to read.
- `fast_cps` / `hard_cps` - reading rate is partly the narrator's, so the first is
  reported and only the second refuses.
- `min_alignment` - below this the script and the transcript are not a pair, and every
  line would be timed against the wrong audio.
- `keep_together` - **the production's own vocabulary**, and the rule that matters most in
  a course that teaches names. A named UI element or technical term must never be split
  across two cues: "the session chip" must not arrive as "the session" and then "chip".
  List the terms; the generator will not break inside one and the guard refuses a track
  that does. Articles and numbers are held to their nouns and units by grammar rather than
  by the list.

**Break at the top of the ladder that fits**: end of sentence first, then strong
punctuation - colon, semicolon, dash - then a clause boundary or conjunction, and only as
a last resort a plain phrase break. The structure comes from the script, because that is
where the punctuation already is; the clock comes from the aligned words.

**A cue that names something on screen should be on screen with it.** Captions and figures
are answering the same question, so cue a figure's ring on the same phrase the caption
carries and they arrive together.

## Ending a module

A composition ends a measured couple of seconds after the last word, never a guessed one.
`speech_end.py` takes that measurement:

```
python3 speech_end.py voice.mp3        # -> the second the last word ends
```

The obvious measurement is wrong in a way that fails silently. `silencedetect` reports where
each silence *starts*, so the last one is the end of speech only if the audio actually ends in
silence. When narration runs on to the last word of the file, the last hit is a pause seconds
earlier, mid-script, and a closing card built on that number sits there in silence.
`speech_end.py` refuses to answer rather than return it, so give the voice track a tail
(`ffmpeg -af apad`) before measuring; the last word wants room to decay anyway.

## Reviewing a module without rendering it

A change to the look does not need a render to be judged. `hyperframes snapshot
--at` captures any second you name, and `review_frames.py` names them:

```
python3 review_frames.py <composition>/index.html            # what it will capture
hyperframes snapshot --no-end --at "$(python3 review_frames.py <composition>/index.html --times)"
```

One frame per scene at its settled state, plus one per distinct reveal inside
it, so the reviewer sees the module build rather than fifteen end-states.

Do not type the seconds yourself. A scene clip opens before its own first word
so the cross-fade has room, and a frame captured inside that handover carries
two scenes at once - one heading printed through another. It reads as a broken
render rather than a badly chosen moment, and it costs the reviewer a bug report
about a fault that is not there. `review_frames.py` reads both fades out of the
generated timeline and stays past them.

## Where to render

Render from a Linux-native path. The engine writes its frame sequence inside the project
directory, and a composition living on the Windows mount (`/mnt/c/...`) makes every one of
those tens of thousands of small writes cross DrvFs, which starves the render workers.
Measured on one composition: **3.2 fps on `/mnt/c` against 43 fps on ext4**. Copy the
composition to a path under `~`, render there, and copy the finished mp4 back.

The engine downloads `chrome-headless-shell` on first render and cannot unpack it on a box
with no `unzip` and no `yauzl` - it fails with "no zip archiver is available". Fetch the zip
from `storage.googleapis.com/chrome-for-testing-public/<version>/linux64/` and extract it with
Python's `zipfile`, keeping the exec bit. It is cached in `~/.cache/hyperframes/chrome/`
afterwards, so this is once per machine.

## Building a module

There is no build step: a module is a directory of its own with a composition in it, and the
engine renders it. Every artifact has a declared place in the repo and the agent invents none
([ADR-0004](docs/adr/0004-the-repo-owns-every-path.md)).
