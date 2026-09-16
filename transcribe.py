# Word-level timing for the narration.
#
#   python3 transcribe.py narration.mp3 raw.json [--engine auto|openai|local]
#
# ADR-0003 requires that every on-screen reveal lands on a cue derived from the
# real audio, which requires per-word timestamps; this is the step that produces
# them. It writes the RAW alignment on purpose. Run verify.py against it to prove
# no word was dropped, then repair.py to fix collapsed word runs, and derive cues
# only from the repaired file.
#
# words() is the whole of the transcription path, here so a caller that needs the
# alignment rather than the file imports it instead of posting its own request
# (dub_script.py reads a line at a time). One path to whisper, as tts.mjs is the
# one path to speech.
#
# TWO ENGINES BEHIND THAT ONE PATH (ADR-0009), for the same reason tts.mjs has
# two: a local voice with no local alignment is audio you cannot cue, so both
# halves are local or neither is.
#
#   auto    whisper-1 when a key is present, falling back - loudly - to the local
#           model when the key is refused or out of credit.
#   openai  whisper-1 only.
#   local   faster-whisper only. No key, no network, no account.
#
# The local model runs in the Python named by HYPERFRAMES_PYTHON (the same venv
# the engine's Kokoro needs), because this file runs under the system Python and
# faster-whisper is not installed there. README, "Speaking without an account".
import json, os, re, subprocess, sys, urllib.error, urllib.request, uuid

QUOTA = re.compile(r"insufficient_quota|credit_balance_exhausted|no credits remaining|invalid_api_key", re.I)


def words(audio, key, vocab=None):
    """Every word of the audio, with its start and end in seconds.

    vocab biases the spelling of proper nouns and part numbers - whisper's own
    prompt parameter. It matters more here than it looks: a re-voice reads this
    text back out, so a product name heard wrong is not a typo in a transcript,
    it is the finished video saying the wrong word.
    """
    b = open(audio, "rb").read()
    bnd = uuid.uuid4().hex
    fields = [("model", "whisper-1"), ("response_format", "verbose_json"),
              ("timestamp_granularities[]", "word")]
    if vocab:
        fields.append(("prompt", vocab))
    parts = []
    for k, v in fields:
        parts.append(f'--{bnd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{bnd}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\n'
                 f'Content-Type: audio/mpeg\r\n\r\n'.encode() + b + b"\r\n")
    parts.append(f"--{bnd}--\r\n".encode())
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions", data=b"".join(parts),
        headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={bnd}"})
    try:
        heard = json.load(urllib.request.urlopen(req))["words"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"openai {e.code}: {e.read().decode('utf8', 'replace')}") from None
    return [{"id": f"w{n}", "text": w["word"], "start": round(w["start"], 3), "end": round(w["end"], 3)}
            for n, w in enumerate(heard)]


# The local model is loaded and run by a separate interpreter, so this is the
# whole of the contract with it: audio path and model name in, word rows out.
LOCAL_SCRIPT = r'''
import json, sys
from faster_whisper import WhisperModel
audio, model_name = sys.argv[1], sys.argv[2]
m = WhisperModel(model_name, device="cpu", compute_type="int8")
segs, _ = m.transcribe(audio, word_timestamps=True, language="en", beam_size=5)
rows = [{"text": w.word.strip(), "start": w.start, "end": w.end}
        for s in segs for w in s.words if w.word.strip()]
json.dump(rows, sys.stdout)
'''


def local_words(audio, model="small.en"):
    """The same rows as words(), from a model on this machine."""
    py = os.environ.get("HYPERFRAMES_PYTHON")
    if not py:
        default = os.path.expanduser("~/.cache/soundstage/voice-venv/bin/python")
        if os.path.exists(default):
            py = default
    if not py or not os.path.exists(py):
        raise RuntimeError("HYPERFRAMES_PYTHON is not set to a Python that has faster-whisper "
                           "(README, \"Speaking without an account\")")
    r = subprocess.run([py, "-c", LOCAL_SCRIPT, audio, model], capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stderr or "").strip().splitlines()[-6:]
        raise RuntimeError("faster-whisper failed:\n  " + "\n  ".join(tail))
    rows = json.loads(r.stdout)
    if not rows:
        raise RuntimeError("faster-whisper returned no words - is the audio silent?")
    return [{"id": f"w{n}", "text": w["text"], "start": round(w["start"], 3), "end": round(w["end"], 3)}
            for n, w in enumerate(rows)]


if __name__ == "__main__":
    # A flag takes a value, so skip both - counting the value as a positional is
    # how "--engine local" turns into one argument too many and a usage error.
    TAKES_VALUE = {"--engine", "--model"}
    argv, args, flags = sys.argv[1:], [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in TAKES_VALUE:
            if i + 1 >= len(argv):
                sys.exit(f"{a} needs a value")
            flags[a] = argv[i + 1]; i += 2; continue
        if a.startswith("--"):
            sys.exit(f"unknown flag {a}")
        args.append(a); i += 1
    if len(args) != 2:
        sys.exit("usage: transcribe.py <audio> <out.json> [--engine auto|openai|local] [--model small.en]")
    AUDIO, OUT = args
    ENGINE = flags.get("--engine", "auto")
    if ENGINE not in ("auto", "openai", "local"):
        sys.exit(f"unknown --engine {ENGINE}: use auto, openai or local")
    MODEL = flags.get("--model", "small.en")

    def write(rows, engine):
        json.dump(rows, open(OUT, "w"), indent=1)
        print(f"wrote {len(rows)} words, {rows[-1]['end']:.2f}s [engine: {engine}]")

    if ENGINE == "local":
        write(local_words(AUDIO, MODEL), f"faster-whisper {MODEL}")
    else:
        try:
            key = os.environ.get("OPENAI_API_KEY")
            if not key:
                raise RuntimeError("OPENAI_API_KEY is not set")
            write(words(AUDIO, key), "whisper-1")
        except RuntimeError as e:
            if ENGINE == "openai":
                sys.exit(str(e))
            print(f"openai refused, falling back to the local model:\n{e}", file=sys.stderr)
            if not QUOTA.search(str(e)):
                print("(the refusal was not about credit - worth reading before trusting these timings)",
                      file=sys.stderr)
            write(local_words(AUDIO, MODEL), f"faster-whisper {MODEL}")
