# Word-level timing for the narration, straight from whisper-1.
#
#   OPENAI_API_KEY=... python3 transcribe.py narration.mp3 raw.json
#
# ADR-0003 requires that every on-screen reveal lands on a cue derived from the
# real audio, which requires per-word timestamps; this is the step that produces
# them. It writes the RAW alignment on purpose. Run verify.py against it to prove
# no word was dropped, then repair.py to fix collapsed word runs, and derive cues
# only from the repaired file.
import json, os, sys, urllib.request, uuid

AUDIO, OUT = sys.argv[1], sys.argv[2]
KEY = os.environ["OPENAI_API_KEY"]

b = open(AUDIO, "rb").read()
bnd = uuid.uuid4().hex
parts = []
for k, v in (("model", "whisper-1"), ("response_format", "verbose_json"),
             ("timestamp_granularities[]", "word")):
    parts.append(f'--{bnd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
parts.append(f'--{bnd}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\n'
             f'Content-Type: audio/mpeg\r\n\r\n'.encode() + b + b"\r\n")
parts.append(f"--{bnd}--\r\n".encode())
req = urllib.request.Request(
    "https://api.openai.com/v1/audio/transcriptions", data=b"".join(parts),
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": f"multipart/form-data; boundary={bnd}"})
words = json.load(urllib.request.urlopen(req))["words"]
out = [{"id": f"w{n}", "text": w["word"], "start": round(w["start"], 3), "end": round(w["end"], 3)}
       for n, w in enumerate(words)]
json.dump(out, open(OUT, "w"), indent=1)
print(f"wrote {len(out)} words, {out[-1]['end']:.2f}s")
