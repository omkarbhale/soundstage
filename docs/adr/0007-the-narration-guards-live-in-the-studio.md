# The narration guards live in the studio, not beside a module

ADR-0003 requires that every animation land on a cue derived from the real audio, which
means narration must be generated once and transcribed with per-word timestamps. The
transcription step and the two checks that make its output trustworthy belong in the
studio, not in a module's output directory. `/outputs/` is gitignored whole (ADR-0002), so
anything left there is stored as content rather than as tooling: clear `/outputs/` and the
guards are gone, and every new module has to copy them out of a previous module's working
directory and hope it still exists.

Three scripts live in the studio beside `tts.mjs`, which is here for the same reason - it
is how a video gets made, not part of any one video:

- `transcribe.py` - narration audio to per-word timings. ADR-0003 asks for these and
  nothing else here produces them.
- `verify.py` - **the speech model silently drops detachable clauses.** Whatever can be
  lifted out without breaking the grammar goes missing, wherever it sits: a standalone
  sentence, a leading adverbial, a trailing adjunct carrying an instruction, the "dot" in
  a spoken domain. Long sentences are not safe by being long. Diffing the script against
  the transcript word for word is the only way any of it is found.
- `repair.py` - **whisper reproducibly collapses a run of words into one impossibly long
  token**, and every cue derived from that stretch lands on the wrong beat.

## Consequences

Both faults are silent: nothing fails, nothing warns, and the module looks finished. That
is why the checks cannot live somewhere they can be lost. Run `verify.py` after generating
narration and `repair.py` before deriving any cue, on every module.

Rewrite a dropped fragment so it is structurally undroppable rather than merely joined to
its neighbour: the words have to sit in a clause the sentence needs, not in an adjunct that
can be lifted out and leave the grammar intact.

The drop is also non-deterministic - an unchanged sentence can survive one generation and
lose its final clause on the next - so a clean `verify.py` pass certifies the audio in hand
and says nothing about the script. Regenerate, and diff again.

They stay plain scripts taking explicit paths, so a module directory owns its own files
(ADR-0004) and the studio owns none of them. No content moves here: a script that measures
narration is not narration.
