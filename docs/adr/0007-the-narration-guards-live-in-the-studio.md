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
- `verify.py` - **the speech model silently drops detachable clauses.** On module 1 it
  dropped "One note on regulation." with no error at all, which read as a fault about short
  standalone sentences. Module 4 then lost three fragments that were not standalone at all,
  each sitting inside a longer sentence: a leading adverbial that opened one ("Before any of
  that, though,"), and two trailing adjuncts that closed one ("about something ordinary", and
  "and send it to IT either way" - a reporting instruction). It also elided "dot" from a
  spoken domain. What goes missing is whatever can be lifted out without breaking the
  grammar, wherever it sits. This diffs the script against the transcript word for word,
  which is the only way any of it is found.
- `repair.py` - **whisper reproducibly collapses a run of words into one impossibly long
  token.** On module 1 about ten words became a single 4.48-second "and". Every cue in that
  stretch would have landed on the wrong beat.

## Consequences

Both faults are silent: nothing fails, nothing warns, and the module looks finished. That
is precisely why the checks cannot live somewhere they can be lost. Run `verify.py` after
generating narration and `repair.py` before deriving any cue, on every module.

Rewriting a dropped fragment means making it structurally undroppable rather than merely
joining it to its neighbour: the words have to sit in a clause the sentence needs, not in an
adjunct that can be lifted out and leave the grammar intact. Long sentences are not safe by
being long - all three of module 4's drops were inside them.

The drop is also non-deterministic. On module 4 the same closing sentence survived one
generation and lost its final clause on the next, unchanged. So a clean `verify.py` pass
certifies the audio in hand and says nothing about the script: regenerate, and diff again.

They stay plain scripts taking explicit paths, so a module directory owns its own files
(ADR-0004) and the studio owns none of them. No content moves here: a script that measures
narration is not narration.
