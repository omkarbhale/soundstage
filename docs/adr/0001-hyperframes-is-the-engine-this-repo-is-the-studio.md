# HyperFrames is the engine, this repo is the studio

Rendering HTML to video is a solved problem and HyperFrames solves it under Apache 2.0
with no per-render cost, so we adopt it whole and never modify or wrap it. What this
repo holds instead is everything about how the captain makes videos: house style,
reusable components, voice configuration, conventions, and the instructions an agent
reads so it needs no briefing. The consequence a reader should expect is that there is
almost no code here and no rendering logic at all.

## Considered Options

Building a renderer was never seriously on the table; video encoding is a year of work.
The real alternative was a thin pipeline that drives HyperFrames from a fixed
document-in-video-out entry point. That was rejected because the friction being removed
is not "running the steps" - it is re-establishing context with the agent every time,
which a pipeline does not fix and documentation does.
