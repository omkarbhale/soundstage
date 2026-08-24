# The repo owns every path, the agent invents none

Every artifact - script, generated audio, composition, intermediate, finished video - has
a defined place declared in the repo, and the agent writes nowhere else. The first attempt
at this work failed on exactly this point: the model created temp files wherever it liked
and would have handled revisions across the filesystem however it saw fit, which is why
that video was never revised rather than why it was hard to revise.

## Consequences

This is the repo's core value and it costs no code. A prescriptive layout that looks
excessive for a personal project is deliberate: predictability is the feature.
