# OpenAI for speech, though the engine does not support it

HyperFrames supports HeyGen's own voice, ElevenLabs, and local Kokoro, and none of them is
OpenAI - so using OpenAI means writing and maintaining an adapter in a repo that otherwise
has almost no code. The captain chose it anyway: the key already exists, this is a tool he
builds for himself and maintains himself, and hiccups are acceptable in exchange for
starting from what he already has. Kokoro was recommended instead, for being local, free,
keyless and self-contained in a public repo, and was declined with that reasoning stated.

## Consequences

The adapter is ours to keep working when the engine's audio layer changes. The key lives in
a gitignored `.env` and nowhere else, which matters more than usual here because the repo is
public. Switching to a supported provider later is deliberately left open.
