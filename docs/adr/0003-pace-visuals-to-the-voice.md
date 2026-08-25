# Pace visuals to the voice, never voice to visuals

Narration is generated first and transcribed with per-word timestamps; every animation
lands on a spoken cue derived from that real audio, and nothing is timed by hand. This is
HyperFrames' own guidance, recorded here because the opposite order is the tempting one:
audio generated per paragraph against independently timed animations drifts out of sync
and clips audibly at every chunk boundary.

## Consequences

Narration for one video is generated in a single pass. Splitting it per paragraph or per
section reintroduces those boundary artefacts, and a recording carrying them is not worth
revising.
