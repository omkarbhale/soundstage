# Pace visuals to the voice, never voice to visuals

Narration is generated first and transcribed with per-word timestamps; every animation
lands on a spoken cue derived from that real audio, and nothing is timed by hand. This is
HyperFrames' own guidance and we are recording it because we already violated it once: an
earlier user guide generated audio in per-paragraph chunks against independently timed
animations, and the result was out of sync with audibly clipped chunk boundaries.

## Consequences

Narration for one video is generated in a single pass. Splitting it per paragraph or per
section reintroduces exactly the boundary artefacts that made the first attempt not worth
revising.
