# A local voice and a local aligner, behind the same two paths

ADR-0005 chose OpenAI for speech on the reasoning that the key already existed. That
reasoning holds only while the key works. It stopped working mid-course - the account ran
out of credit - and the failure was larger than losing a voice, because **both halves of the
narration path were OpenAI**: `tts.mjs` for speech and `transcribe.py` for the per-word
timings ADR-0003 requires. A local voice with no local alignment is audio you cannot cue, so
either both halves work offline or neither does.

The captain's own framing, which is the decision:

> Use some (moderate level quality, i guess) local model. I do not have any GPU. Scope to
> soundstage if it aligns, which it might since soundstage was never about just openai.

It does align. ADR-0005 recorded that the engine speaks HeyGen, ElevenLabs and **Kokoro**,
and that Kokoro was the recommendation then and was declined for convenience rather than on
merit. This ADR takes the recommendation.

## The decision

**Speech: Kokoro-82M, through the engine's own `tts` command.** It is the one option the
engine already speaks, so the Kokoro path in `tts.mjs` shells out to `hyperframes tts` and
loads no model itself (ADR-0001: adopt the engine, never reimplement it). It runs on CPU,
which is what matters here - there is no GPU.

**Alignment: faster-whisper, in-process in a local venv.** The engine's own `transcribe`
command would have been the matching choice and was not available: it needs a `whisper-cpp`
binary, and building one needs cmake and a C compiler, neither of which is installed here
and neither of which we can install. faster-whisper ships wheels, runs on CPU and returns
word timestamps, which is the whole requirement. If `whisper-cpp` ever becomes buildable
here, moving to the engine's command is the better answer and this is the reason to revisit.

**Both live behind the existing single paths, not beside them.** `tts.mjs` takes
`--engine auto|openai|kokoro` and `transcribe.py` takes `--engine auto|openai|local`. There
is still one way to make speech and one way to get timings. `auto` prefers OpenAI and falls
back to local **loudly** - the engine that actually spoke is printed on every run, because a
voice that changes without anyone noticing is worse than one that fails.

## Consequences

**A deterministic voice changes what a take means.** The OpenAI model silently drops
detachable clauses, non-deterministically, which is why the course takes a module repeatedly
until `verify.py` is clean (README, "Making narration"). Kokoro reads what it is given:
measured over six voices on a sample built from the hardest tokens in the corpus, **zero
deletions and zero insertions in every one**. So there is exactly one take, and a drop that
`verify.py` does report cannot be retaken away - the script is what has to change. Keep the
guard. It is now a proof about the text rather than a dice roll.

**A local model has no `instructions` control and mispronounces proper nouns.** Measured
here: it read `Aras` as ARR-as and `tas-playwright` as "task playwright", and spelled out
`TAS` letter by letter when the word was capitalised. So `tts.mjs` takes a `--lexicon` of
respellings applied to the **input** of the local engine only. Respelling what is spoken
leaves the script the guards check untouched, so `verify.py` still diffs the real narration
against the real audio. The table is content and lives with the course, not here.

**Local costs time instead of money.** Synthesis runs about 0.55x realtime and alignment
about 0.5x, so a seven-minute module is roughly eight minutes of CPU rather than a few
seconds of API. It is free, offline, and needs no account.

**A cue still matches the transcript, and this is a different transcript.** The
transcript-spelling rules in the README were measured against `whisper-1`; the local model
respells differently in places and adds homophones of its own - it wrote "right once" for
"write once". Re-check cues against the transcript the module was actually aligned with
(`cue_check.py` already does exactly this).

**Setup is not automatic.** Kokoro and faster-whisper need a Python that is not the system
one: `HYPERFRAMES_PYTHON` points at it, which is the engine's own convention. The README
says how to build it.
