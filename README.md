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

## Status

The design record is all that exists so far. There is no build, no usage flow and
nothing to run yet.
