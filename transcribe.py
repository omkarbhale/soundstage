# Word-level timing for the narration, straight from whisper-1.
#
#   OPENAI_API_KEY=... python3 transcribe.py narration.mp3 raw.json
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
import json, os, sys, urllib.request, uuid


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
    heard = json.load(urllib.request.urlopen(req))["words"]
    return [{"id": f"w{n}", "text": w["word"], "start": round(w["start"], 3), "end": round(w["end"], 3)}
            for n, w in enumerate(heard)]


if __name__ == "__main__":
    AUDIO, OUT = sys.argv[1], sys.argv[2]
    out = words(AUDIO, os.environ["OPENAI_API_KEY"])
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"wrote {len(out)} words, {out[-1]['end']:.2f}s")
