# The narration guards live in the studio, not beside a module

ADR-0003 requires that every animation land on a cue derived from the real audio, which
means narration must be generated once and transcribed with per-word timestamps. Neither
the transcription step nor the two checks that make its output trustworthy had a home in
this repo: they were written while building module 1 and left in that module's output
directory, which `/outputs/` ignores whole (ADR-0002).

That is content storage, not tooling storage. Clear `/outputs/` and the guards are gone;
every new module has to copy them out of a previous module's working directory and hope it
still exists. Module 5 did exactly that, which is what surfaced this.

Three scripts move into the studio beside `tts.mjs`, which is already here for the same
reason - it is how a video gets made, not part of any one video:

- `transcribe.py` - narration audio to per-word timings. ADR-0003 asks for these and
  nothing here produced them.
- `verify.py` - **the speech model silently drops short standalone sentences.** On module 1
  it dropped "One note on regulation." with no error at all. This diffs the script against
  the transcript word for word.
- `repair.py` - **whisper reproducibly collapses a run of words into one impossibly long
  token.** On module 1 about ten words became a single 4.48-second "and". Every cue in that
  stretch would have landed on the wrong beat.

## Consequences

Both faults are silent: nothing fails, nothing warns, and the module looks finished. That
is precisely why the checks cannot live somewhere they can be lost. Run `verify.py` after
generating narration and `repair.py` before deriving any cue, on every module.

They stay plain scripts taking explicit paths, so a module directory owns its own files
(ADR-0004) and the studio owns none of them. No content moves here: a script that measures
narration is not narration.
