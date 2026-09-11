# A re-voice is fitted to the old track, line by line

ADR-0003 makes the narration first and paces the picture to it. A video that already
exists cannot be paced to anything - the cut is finished - so re-voicing one runs the
opposite way, and this records where that boundary is. ADR-0003 still governs everything
the studio *makes*; this governs only a video it is *given*.

The old track is the score. It is read for its lines (`speech_runs.py`), each line is
transcribed from its own audio (`dub_script.py`), spoken again in one take
(`dub_speak.py`), and fitted back into the bar the old line occupied (`dub.py`). The
picture is never touched: the video stream is stream-copied, and the new track is built to
the old one's length so there is nothing to touch.

**A line is fitted to its old line's duration exactly, not merely inside it.** Starting
each line on time bounds the error at the line boundaries and says nothing about the
inside of a line, which is where the picture is moving. A nineteen-second line read eight
per cent quick is a second and a half ahead of what it describes by the end - pointing at
a panel that has not opened - and it still ends inside its slot, so no duration check sees
it.

**The pace belongs to the speech request, not to the time-stretch.** The model changes its
own delivery for `--speed`; `dub.py` stretches audio afterwards. Measured on one track,
`sage` ran 29-50% long against a 167 wpm narrator, and instructions telling it to hurry
barely moved that while `--speed` moved it exactly. So `dub.py --report` prints the fit
before any audio is written, and its median is the speed factor the take is missing.

## Consequences

**A take is one take.** The speech model is asked per line and has no memory between
requests, so nothing but identical settings holds a take together, and nothing downstream
can see when one line was read differently. `dub_speak.py` records the settings beside the
clips and re-reads a line from that record rather than from what is typed later.

**Sync is proved against the old grid, not against a grid re-derived from the new track.**
A new reader breathes where the old one did not, so the new track measures as more lines
than there are, and from there every line is compared to its neighbour.

**Proved below the level a lossy encode moves, too.** A threshold answers "where does this
cross -50dB", not "where does the word start". AAC attenuates a soft first phoneme just
enough to cross later: one line read 105ms late in the mp4 that read 4ms late in the wav
it was made from, from identical samples. A guard that reports that is worse than none,
because the fix it invites is shifting audio that was already right.

**The transcript is read back out, so its spellings are the video's words.** Elsewhere a
transcript may spell a name however it likes, because a reader never sees it. Here whisper
heard "Aras" as AERIS, ERIS and ARIS across one track, and a dub built on that says the
wrong product name in a confident voice. Take proper nouns off the screen and pass them as
vocabulary.

**What no measurement here covers is pronunciation.** Timing, length and wording are all
checked; how a word sounds is not, and cannot be. A re-voice gets a human ear before it
ships.
