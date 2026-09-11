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

What it reports is ambiguity, not a defect, and the two are worth telling apart before you
touch a timing. Repeats cluster because a module says its key phrase once in the scene that
defines it and again in the scene that builds on it - and the defining scene comes first, so
the first match is usually the occurrence the scene was written around. Read the scene, sample
the finished render either side of both candidates, then name what you found: `t("...", 1)` as
readily as `t("...", 2)`. Naming the occurrence records the answer rather than changing it - a
cue that was already right keeps the time it had.

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

Both fail the way the narration faults do. Nothing errors, nothing warns, `cue_check.py`
still passes because every cue phrase still resolves, and the scene's **settled** frame is
identical either way. The only frame that shows it is one sampled between the two cues -
which is not a frame anyone picks by hand, and not one `review_frames.py` promises either,
because it samples a scene's reveals rather than the gaps between them. Run it after
building and before rendering, beside `cue_check.py`.

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
