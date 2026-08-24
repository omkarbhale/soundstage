# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- **Read [`CONTEXT.md`](CONTEXT.md) first.** It is the glossary, and it names the words this
  project deliberately avoids. `engine` is HyperFrames (adopted whole, never modified);
  `studio` is this repo; a `composition` is the HTML for one video.
- **No content is committable here, and the repo is public.** `/inputs/` and `/outputs/` are
  gitignored whole - source documents, scripts, audio and rendered video all live there and
  none of it enters git. See [ADR-0002](docs/adr/0002-the-repo-is-public-and-holds-no-content.md)
  and read `.gitignore`'s own comments before loosening anything.
- **Narration first, visuals cued from it.** Generate the narration in one pass, transcribe it
  for per-word timings, and derive every reveal from those timings - never hand-time an
  animation ([ADR-0003](docs/adr/0003-pace-visuals-to-the-voice.md)). The chain and the two
  mandatory guards are in the README under "Making narration"; the guards catch faults that
  fail **silently** ([ADR-0007](docs/adr/0007-the-narration-guards-live-in-the-studio.md)).
- **A cue phrase must name one moment.** `cue_check.py` (README, "Cueing a reveal") proves
  every phrase a composition cues on occurs exactly once in the narration. The lookup takes
  the first match, so a repeated phrase silently fires a reveal a scene early - and the
  frame looks finished either way.
- **A module ends a measured two seconds after the last word.** Take the measurement with
  `speech_end.py` (README, "Ending a module") and compose the ending on it - never pad or
  trim a rendered file. It refuses to answer when the audio ends mid-speech, because the
  obvious `silencedetect` reading is wrong there and wrong silently.
- **Speech is OpenAI via `tts.mjs`**, which the engine does not support natively
  ([ADR-0005](docs/adr/0005-openai-for-speech.md)). The key lives in `.env` beside it and
  nowhere else.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
