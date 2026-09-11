# Project agent memory

Record here only project-intrinsic agent knowledge - build, test, release, architecture and sharp-edge notes that must travel with the code.

- **Read [`CONTEXT.md`](CONTEXT.md) first.** It is the vocabulary, and it names the words this
  project rejects. `engine` is HyperFrames (adopted whole, never modified);
  `studio` is this repo; a `composition` is the HTML for one video.
- **No content is committable here, and the repo is public.** `/inputs/` and `/outputs/` are
  gitignored whole - source documents, scripts, audio and rendered video all live there and
  none of it enters git. See [ADR-0002](docs/adr/0002-the-repo-is-public-and-holds-no-content.md)
  and read `.gitignore`'s own comments before loosening anything.
- **Narration first, visuals cued from it.** Generate the narration in one pass, transcribe it
  for per-word timings, and derive every reveal from those timings - never hand-time an
  animation ([ADR-0003](docs/adr/0003-pace-visuals-to-the-voice.md)). The chain and the two
  mandatory guards are in the README under "Making narration". Skip a guard and a module ships
  with a fact missing from its audio, or with its cues on the wrong beat, and nothing about
  the render looks wrong ([ADR-0007](docs/adr/0007-the-narration-guards-live-in-the-studio.md)).
  A deletion `verify.py` reports is not yet a proven drop - a lone function word lost at an
  elision can be the full-file transcript mishearing, not the audio. `verify.py` says how to
  tell, and it is the same window transcription `repair.py` already does.
- **A cue phrase must name one moment.** Run `cue_check.py` (README, "Cueing a reveal") before
  rendering: it proves every phrase a composition cues on occurs exactly once in the narration.
  The lookup takes the first match, so a repeated phrase silently fires a reveal a scene early -
  and the frame looks finished either way. What it flags is ambiguity, not a proven defect:
  confirm against the render before touching a timing, then name the occurrence you
  found - the first match is usually the intended one.
- **A module ends a measured two seconds after the last word.** Take the measurement with
  `speech_end.py` (README, "Ending a module") and compose the ending on it - never pad or
  trim a rendered file. It refuses to answer when the audio ends mid-speech, because the
  obvious `silencedetect` reading is wrong there and wrong silently.
- **A look change is reviewed from frames, not from a render.** Pick the seconds with
  `review_frames.py` (README, "Reviewing a module without rendering it") and capture them
  with `hyperframes snapshot --at`. Never type the seconds by hand: a scene clip opens
  before its own first word, so a frame taken inside the handover carries two scenes at
  once and reads as a broken render rather than a badly chosen moment.
- **Re-voicing a finished video runs the other way round.** ADR-0003 governs what the
  studio makes; a video it is *given* cannot be cued, so the old track is the score
  ([ADR-0008](docs/adr/0008-a-re-voice-is-fitted-to-the-old-track.md), README under
  "Re-voicing a video that already exists"). Each line is fitted to its old line's
  duration exactly, not merely inside it - starting on time says nothing about the inside
  of a line, and a long line read a few per cent quick is seconds ahead of the picture by
  its end while still ending in its slot. Read `dub.py --report` before building: the
  median tempo is the pace the take is missing, and `dub_speak.py --speed` is where that
  belongs, because the model changes its delivery for it where `dub.py` stretches audio
  afterwards. Timing, length and wording are all measured; **pronunciation is not and
  cannot be** - a re-voice gets a human ear before it ships.
- **A transcript that will be read back out is not a transcript.** Whisper heard "Aras" as
  AERIS, ERIS and ARIS across one track. Elsewhere that is a harmless spelling; in a
  re-voice it is the finished video saying the wrong product name. Pass the proper nouns
  and part numbers as `--vocab`, taken off the screen, and check the identifiers: the
  speech model reads every zero of `PRT-0000061` where the narrator said the whole thing
  in about a second, which shows up as that line running long in `dub.py --report`.
- **Speech is OpenAI via `tts.mjs`**, which the engine does not support natively
  ([ADR-0005](docs/adr/0005-openai-for-speech.md)). Route every voice track through it. The
  key lives in `.env` beside it and nowhere else.
- **Render on a Linux-native path, never on `/mnt/c`** (README, "Where to render"). The engine
  writes its frame sequence inside the project directory, and on the Windows DrvFs mount those
  tens of thousands of small writes starve the workers: measured on one composition, 3.2 fps
  against 43 fps on ext4. Copy the composition to a Linux path, render there, copy the mp4 back.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
