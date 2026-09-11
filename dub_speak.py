#!/usr/bin/env python3
"""Speak every line of a script in one take, and record what the take was.

    python3 dub_speak.py script/ clips/ --instructions voice.txt --speed 1.27
    python3 dub_speak.py script/ clips/ --only 7,19          # re-read two lines

Routes every line through `tts.mjs`, which is the one path to speech
(ADR-0005). This is the loop around it, not a second path.

A re-voice is one narration cut into lines, but the speech model is asked for
each line separately and has no memory between requests, so the only thing
holding the take together is that every request was identical apart from its
words. Nothing downstream can see that it was not. Come back a week later to fix
one awkward line, generate it at a different speed or with the instructions
reworded, and that line lands in the finished video sounding like a different
person in a different room - one sentence in four minutes, which is exactly the
kind of thing a reviewer hears and cannot name.

So the settings are written beside the clips as `take.json`, and re-reading part
of a take (`--only`) uses that file rather than whatever is typed at the time.
A full run rewrites it. `--speed` is the honest place to match the old
narrator's pace: the model changes its own delivery for it, where `dub.py`'s
per-line correction is a time-stretch applied afterwards, so leave that the
small residual and put the pace here (`dub.py --report` prints the factor).

Holds no content and takes explicit paths (ADR-0004).
"""
import concurrent.futures
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORKERS = 4


def opt(argv, name, fallback=None):
    return argv[argv.index(f"--{name}") + 1] if f"--{name}" in argv else fallback


def speak(text_file, out_file, take):
    cmd = ["node", os.path.join(HERE, "tts.mjs"), text_file, out_file,
           "--voice", take["voice"], "--model", take["model"],
           "--speed", str(take["speed"])]
    if take["instructions"]:
        cmd += ["--instructions", take["instructions"]]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{os.path.basename(text_file)}: {r.stderr.strip()}")
    return out_file


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    for flag in ("instructions", "speed", "voice", "model", "only"):
        if f"--{flag}" in argv:
            args = [a for a in args if a != argv[argv.index(f"--{flag}") + 1]]
    if len(args) != 2:
        raise SystemExit(__doc__)
    script, clips = args
    os.makedirs(clips, exist_ok=True)
    record = os.path.join(clips, "take.json")

    texts = sorted(glob.glob(os.path.join(script, "line-*.txt")))
    if not texts:
        raise SystemExit(f"{script}: no line-*.txt - run dub_script.py first")

    only = opt(argv, "only")
    if only:
        # Re-reading part of a take must not change the take. The settings come
        # off the record, not off this command line, or the mended line is the
        # one that stands out.
        if not os.path.exists(record):
            raise SystemExit(f"{record}: missing - --only mends an existing take, "
                             "and there is no record of what that take was. "
                             "Generate the whole take first.")
        take = json.load(open(record, encoding="utf8"))
        for flag in ("instructions", "speed", "voice", "model"):
            if f"--{flag}" in argv:
                raise SystemExit(f"--{flag} cannot be given with --only: the rest of the "
                                 f"take was read at {take['voice']}/{take['model']} "
                                 f"speed {take['speed']}, and a line read at anything else "
                                 "sounds like a different person in the finished video.")
        wanted = {int(n) for n in re.split(r"[,\s]+", only) if n != ""}
        texts = [t for t in texts
                 if int(re.search(r"line-(\d+)", os.path.basename(t)).group(1)) in wanted]
        if len(texts) != len(wanted):
            raise SystemExit(f"{script}: asked for lines {sorted(wanted)}, found {len(texts)}")
    else:
        instructions_file = opt(argv, "instructions")
        take = {
            "voice": opt(argv, "voice", "sage"),
            "model": opt(argv, "model", "gpt-4o-mini-tts"),
            "speed": float(opt(argv, "speed", 1.0)),
            "instructions": (open(instructions_file, encoding="utf8").read().strip()
                             if instructions_file else ""),
            "instructions_from": instructions_file or "",
            "lines": len(texts),
        }

    print(f"{take['voice']} / {take['model']} / speed {take['speed']} "
          f"-> {len(texts)} line(s)")

    jobs = {}
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
        for t in texts:
            out = os.path.join(clips, os.path.basename(t).replace(".txt", ".mp3"))
            jobs[pool.submit(speak, t, out, take)] = out
        failed = []
        for f in concurrent.futures.as_completed(jobs):
            try:
                print(f"  {os.path.basename(f.result())}")
            except Exception as e:                      # one line, not the take
                failed.append(str(e))
    if failed:
        raise SystemExit("\n".join(["not every line was spoken:"] + failed))

    if not only:
        with open(record, "w", encoding="utf8", newline="\n") as f:
            json.dump(take, f, indent=1)
        print(f"wrote {record}")


if __name__ == "__main__":
    main(sys.argv)
