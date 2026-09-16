# Captions say the script, are timed by the transcript, and live in the video

Every module already holds both halves of a caption, in two different files, and which
half comes from which file is the whole decision.

**The words come from `narration.txt`.** It is the script that was approved, `verify.py`
has already proved every word of it reached the audio, and it spells the product's names
the way the product spells them.

**The times come from `transcript.json`.** Per-word timings against the real audio - the
same file every reveal is cued from ([ADR-0003](0003-pace-visuals-to-the-voice.md)).

The tempting shortcut is to caption from the transcript, which already has both. It is
wrong, and measured rather than feared: an aligner mishears, and a caption is READ rather
than matched, so the mishearing is printed on the screen. In this repo's own corpus a
module whose first spoken word is `Screen` has `Scream` as transcript word zero; `Tier A`
came back as "Tierra"; an em dash glued the words either side of it into one token. A
course whose value is precision about names cannot print any of those.

The two sides do not line up one to one - one measured module is 725 script words against
722 aligned - so the script is ALIGNED to the transcript rather than indexed by it, and a
pairing too poor to trust refuses rather than timing every line against the wrong audio.

**The captions live in the video, as a soft track, and nowhere else.** A subtitle file
stored beside the video is a second thing to keep in step with the first; the track
travels inside the one file that gets handed around, and the viewer can turn it off.
Burned-in is the other wrong answer: it cannot be turned off, and it would sit on top of
whatever a figure has drawn ([ADR-0010](0010-a-highlight-is-measured-from-the-element.md)).
A standalone subtitle file is still a legitimate thing to want, so exporting one is a
command somebody runs - derived from the same script and the same timings, so it cannot
drift - and never a build artifact.

## Consequences

**Nothing about caption STYLE lives here.** soundstage is a generic studio, so line
length, cue length, reading rate, the phrases that must never be split: all of them are
the production's, passed in explicitly, and a missing one refuses by name rather than
falling back to a number nobody chose ([ADR-0004](0004-the-repo-owns-every-path.md) is
the same instinct applied to paths). How to CHOOSE those values is taught in the README,
because it is judgement, not a default.

**A track nobody verified is a video that ships uncaptioned.** A subtitle track is off by
default in most players, so a failed mux is invisible to everyone who reviews the file.
`caption_check.py --in <video.mp4>` reads the track back out of the finished file and
proves it says the script; run it on the thing that ships, not on an intermediate.

**Re-encoding or trimming drops the track, silently.** Any ffmpeg pass without `-map 0`
loses the subtitle stream and the result plays perfectly. Whoever re-encodes re-runs the
caption pass; `join.py` re-assembles the parts' tracks onto the join for the same reason,
because the concat demuxer drops them too.
