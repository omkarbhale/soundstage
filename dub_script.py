#!/usr/bin/env python3
"""Read the old track's script back, one line at a time.

    OPENAI_API_KEY=... python3 dub_script.py old-voice.wav script/
    OPENAI_API_KEY=... python3 dub_script.py old-voice.wav script/ --check
    OPENAI_API_KEY=... python3 dub_script.py old-voice.wav script/ --vocab terms.txt

Re-voicing keeps the words and replaces the reader, so the script is the old
track's own transcript - and it has to reach the speech model the way the old
track was assembled, one request per line. Ask for the whole script in one
request and the model decides where the pauses go; the lines come back at
lengths of its choosing and there is nothing left to fit to the old grid.

**Each line is transcribed from its own audio, not cut out of a transcript of
the whole file.** Bucketing one whole-file alignment by timestamp looks
equivalent and is cheaper, and it puts words in the wrong line. Whisper's word
times drift either side of a boundary by a tenth of a second or so as a matter
of course, and a word that opens a sentence drifts back into the silence before
it - measured on one 226s track, nine words of 542 landed in a gap, one of them
353ms deep, closer to the line that had just ended than to the line it opens.
Snapping by distance moves it to the previous line. Nothing about that fails:
both lines still fit their slots, and the video ships with a word spoken over
the end of the wrong picture. Cutting the audio first makes the assignment
structural - a word cannot be in a line whose audio it is not in - so there is
no tolerance to tune and no boundary to get wrong.

The cut is on the silences `speech_runs.py` found, which are real silence here,
so no word is cut in half by it.

`--vocab` is a file of the proper nouns and part numbers on screen, passed to
whisper as its prompt. A transcript is usually allowed its spelling of a name,
because a reader never sees it. This one is read back out by a speech model, so
a product name heard wrong is not a typo - it is the finished video saying the
wrong word, confidently, in a voice that sounds sure of it. Take the spellings
off the screen rather than from the transcript.

Writes UTF-8, one file per line, named as `tts.mjs` reads and `dub.py` expects
the clips back. Holds no content and takes explicit paths (ADR-0004).
"""
import os
import subprocess
import sys
import tempfile

from speech_runs import runs
from transcribe import words

PAD = 0.15   # a little of the silence either side, so no first or last word is clipped


def line_text(audio, start, dur, key, workdir, vocab=None):
    """Transcribe one line from its own audio."""
    clip = os.path.join(workdir, "line.mp3")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", f"{max(0.0, start - PAD):.3f}", "-t", f"{dur + 2 * PAD:.3f}",
                    "-i", audio, "-c:a", "libmp3lame", "-b:a", "64k",
                    "-ar", "16000", "-ac", "1", clip], check=True)
    return " ".join(w["text"] for w in words(clip, key, vocab)).strip()


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if "--vocab" in argv:
        args = [a for a in args if a != argv[argv.index("--vocab") + 1]]
    if len(args) != 2:
        raise SystemExit(__doc__)
    old, out = args
    key = os.environ["OPENAI_API_KEY"]
    vocab = None
    if "--vocab" in argv:
        vocab = open(argv[argv.index("--vocab") + 1], encoding="utf8").read().strip()

    lines, _ = runs(old)
    texts = []
    with tempfile.TemporaryDirectory() as work:
        for r in lines:
            t = line_text(old, r["start"], r["dur"], key, work, vocab)
            if not t:
                raise SystemExit(f"line {r['i']} ({r['start']:.2f}s, {r['dur']:.2f}s long) "
                                 "came back empty - it is not speech, so the grid is reading "
                                 "something else as a line. Do not go on with it.")
            texts.append(t)
            print(f"  {r['i']:>4}  {r['dur']:>7.3f}s  {len(t.split()):>3} words  "
                  f"{len(t.split()) / r['dur'] * 60:>5.0f} wpm  {t[:52]}")

    total = sum(len(t.split()) for t in texts)
    spoken = sum(r["dur"] for r in lines)
    print(f"\n{len(lines)} lines, {total} words, {total / spoken * 60:.0f} wpm overall")

    if "--check" in argv:
        return
    os.makedirs(out, exist_ok=True)
    for r, t in zip(lines, texts):
        with open(os.path.join(out, f"line-{r['i']:02d}.txt"), "w",
                  encoding="utf8", newline="\n") as f:
            f.write(t + "\n")
    print(f"wrote {len(lines)} files to {out}")


if __name__ == "__main__":
    main(sys.argv)
