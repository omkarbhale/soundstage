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
  tell, and it is the same window transcription `repair.py` already does. **Write about 1,200 words
  a pass.** The 2000-*token* hard limit refuses loudly; the fault that matters arrives earlier and
  silently, because the clause drop is length-driven - measured clean at 1,398 words and never clean
  in ten takes at 1,663 (README, "Making narration"). A topic that will not fit is more modules:
  **add a module rather than cut content**, and join the finished files with `join.py` (README,
  "Joining modules into one video"), which refuses mismatched parts and a part that did not arrive.
- **A cue phrase must name one moment.** Run `cue_check.py` (README, "Cueing a reveal") before
  rendering: it proves every phrase a composition cues on occurs exactly once in the narration.
  The lookup takes the first match, so a repeated phrase silently fires a reveal a scene early -
  and the frame looks finished either way. What it flags is ambiguity, not a proven defect:
  confirm against the render before touching a timing, then name the occurrence you
  found - the first match is usually the intended one.
- **A reveal must have exactly one element to land on, inside a clip that is on screen.**
  Run `id_check.py` (README, "Proving a reveal lands") after building and before rendering.
  A duplicate `id` resolves to the first match, so one element is tweened twice and the
  other is on screen from its scene's first frame; a tween whose selector matches nothing
  does the same. It also refuses a clip with no duration - **a scene table listed out of
  spoken order** gave one clip `data-duration="-63.59"` and let another overlay ninety-seven
  seconds of its module, because each scene's end comes from the NEXT table entry's start.
  `cue_check.py` passes through all of it and the settled frame is identical either way.
- **A screenshot shows WHERE, and a highlight is measured, never typed.** `components/figure.py`
  is the component (README, "Showing a screen, so someone can find it again"); `figure_check.py`
  proves after building that every ring on the frame is still the box the capture measured off
  the element. A tight crop of a button teaches nothing about position, so the frame carries
  the page and a magnified inset goes BESIDE the wide shot, never instead of it. A hand-typed
  or stale box rings the control next to the one the narration named and the frame looks
  finished either way ([ADR-0010](docs/adr/0010-a-highlight-is-measured-from-the-element.md)).
- **Captions say the SCRIPT and are timed by the TRANSCRIPT, and they live in the video.**
  `captions.py --into` muxes a soft track; there is no sidecar, and burned-in is refused
  because it would sit on a figure's callouts. Never caption from the transcript's own text -
  the aligner misheard `Screen` as `Scream` in this corpus, and a caption is read rather than
  matched. Prove the track in the FINISHED file with `caption_check.py --in`, because a
  subtitle track is off by default and a failed mux ships silently; re-run it after anything
  that re-encodes or trims, which drops the track without a word. `join.py` re-assembles the
  parts' tracks onto a join for that reason. **No caption style lives in this repo**: line
  length, cue length, reading rate and the phrases that must never be split all arrive in
  `--style` and a missing one refuses by name - the README teaches how to choose them
  ([ADR-0011](docs/adr/0011-captions-say-the-script-and-live-in-the-video.md)).
- **Prove a composition before you spend the narration on it.** A composition reads its
  transcript, so nothing about it runs until the audio exists - which hides a generator that
  raises, an ambiguous cue and a duplicate id until the expensive half is already paid for.
  `dry_run.py` (README, "Proving a composition before you spend the narration on it") writes a
  synthetic transcript from the script so the generator and both guards run for free. It proves
  no timing - every time it writes is invented - only that the composition is well-formed.
  Related: **a cue is matched against the transcript, and the transcript has no hyphens in it
  at all.** It also writes numbers as digits (inconsistently - `Screen 1` while `Screen two`
  stayed words), Americanises spelling (`centred` to `centered`) and separates compounds
  (`preflight` to `pre flight`). Cue on a phrase carrying none of those: transcript spelling
  itself is not safe to quote, because the next take may spell it the other way.
  README, "Write the cue in transcript spelling".
- **A module ends a measured two seconds after the last word.** Take the measurement with
  `speech_end.py` (README, "Ending a module") and compose the ending on it - never pad or
  trim a rendered file. It refuses to answer when the audio ends mid-speech, because the
  obvious `silencedetect` reading is wrong there and wrong silently.
- **A look change is reviewed from frames, not from a render.** Pick the seconds with
  `review_frames.py` (README, "Reviewing a module without rendering it") and capture them
  with `hyperframes snapshot --at`. Never type the seconds by hand: a scene clip opens
  before its own first word, so a frame taken inside the handover carries two scenes at
  once and reads as a broken render rather than a badly chosen moment.
- **Two engines, two paths, and no third caller.** `tts.mjs` is the only way to make speech
  and `transcribe.py` the only way to get word timings; each speaks OpenAI or a local model
  behind that one path (`--engine`), and `auto` falls back loudly, always printing which
  engine spoke ([ADR-0009](docs/adr/0009-a-local-voice-and-a-local-aligner.md), README,
  "Speaking without an account"). Anything needing a transcript calls `transcribe.py` -
  `repair.py` does, and so should the next thing. The local pair needs a non-system Python
  (`kokoro-onnx` refuses 3.14) named by `HYPERFRAMES_PYTHON`.
  **The local voice is deterministic, so taking a module repeatedly is meaningless** - one
  take, and a drop `verify.py` reports is a fact about the script, not a dice roll. It also
  mispronounces proper nouns and has no `instructions` control; `--lexicon` respells what is
  spoken without touching the script the guards check. To tell a mispronunciation from an
  ASR quirk, run the local aligner over audio you know is right and compare spellings.
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
- **A format is a soundstage-owned skill and lives in `/formats/`, never in `.agents/skills/`.**
  Those 26 are the engine's, version-locked in `skills-lock.json`, and
  `hyperframes skills update` overwrites anything put there
  ([ADR-0012](docs/adr/0012-a-format-is-a-soundstage-owned-skill.md), README under
  "Formats"). Each format is linked into `.claude/skills/<name>`; re-create the link if an
  update removes it, and check a new format's name is absent from the lock file first.
  [`formats/standing-set/`](formats/standing-set/SKILL.md) is the not-a-deck format - one
  space and a camera that travels it - with `components/standing_set.py` for its geometry
  and `set_check.py` for its guard. That guard is a fifth one to run beside the others,
  and it refuses by name what renders perfectly and is still a deck: a world that fits the
  frame, props that fade in as the camera reaches them, a camera that never lands, one
  palette everywhere, every prop a destination.
- **Render on a Linux-native path, never on `/mnt/c`** (README, "Where to render"). The engine
  writes its frame sequence inside the project directory, and on the Windows DrvFs mount those
  tens of thousands of small writes starve the workers: measured on one composition, 3.2 fps
  against 43 fps on ext4. Copy the composition to a Linux path, render there, copy the mp4 back.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
