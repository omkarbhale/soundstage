# soundstage

An agent-operated video studio: the captain's own toolkit for making videos with an
LLM agent, built so the agent opens the repo already knowing how to use the tools
rather than being taught them each time.

## Engine and studio

[HyperFrames](https://github.com/heygen-com/hyperframes) (Apache 2.0) is the
**engine**. It renders a composition to video, generates narration and returns
per-word timing. It is adopted whole, never modified and never wrapped.

This repo is the **studio**. It holds house style, reusable components, voice
configuration, conventions, and the instructions an agent reads so it needs no
briefing. There is almost no code here and no rendering logic at all.

## Content never lives here

This repository is public, and no source document, script, generated audio or
finished video enters it. The material the toolkit is pointed at is not ours to
publish, so it is gitignored from the first commit - see
[ADR-0002](docs/adr/0002-the-repo-is-public-and-holds-no-content.md) and read it
before loosening anything in `.gitignore`.

## Where to start

[`CONTEXT.md`](CONTEXT.md) is the glossary: the words this project uses for formats,
topics, sources, modules, scripts, compositions, and the engine/studio split - with
the words it deliberately avoids.

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
a module looking finished - a dropped clause, and cues landing on the wrong beat. Because the
drop is non-deterministic, `verify.py` certifies the audio in hand and not the script: run it
again on every regeneration. Read
[ADR-0007](docs/adr/0007-the-narration-guards-live-in-the-studio.md) before skipping either.

## Status

The design record, the speech adapter and the narration guards. There is no build step:
a module is a directory of its own with a composition in it, and the engine renders it.
