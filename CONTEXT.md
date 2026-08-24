# soundstage

The captain's own toolkit for making videos with an LLM agent, built so the agent
opens the repo already knowing how to use the tools rather than being taught them
each time.

## The three axes

**Format**:
The genre of a video: what it looks and sounds like. Narrated slides, screencast,
animated explainer. A new format is a new template, not a new tool.
_Avoid_: style, type, kind, output format, aspect ratio

**Topic**:
The subject matter a video is about. Free by design; the tool never constrains it.
_Avoid_: content, subject, theme

**Source**:
The shape of the material a video is made from - a Word document, markdown, a URL,
loose notes. Deliberately unconstrained: the agent reads whatever it is given.
_Avoid_: input, source format, feed

## Making a video

**Module**:
One unit of a course, and the unit a single video covers. The first course has
nine, each carrying its own objectives, script and quiz.
_Avoid_: chapter, lesson, section, part

**Script**:
The narration text for one video. Written by the agent, read by the captain before
it becomes audio.
_Avoid_: copy, voiceover text, transcript

## The two halves

**Engine**:
HyperFrames. Renders a composition to video, generates narration, and returns
per-word timing. Adopted, not built, and never modified here.
_Avoid_: renderer, framework, HyperFrames (in prose about our own work)

**Studio**:
This repo. Everything about how the captain makes videos - house style, reusable
components, voice configuration, conventions, and the instructions an agent reads
so it needs no briefing. Holds no rendering code and no content.
_Avoid_: pipeline, framework, wrapper, harness

**Composition**:
The HTML that describes one video. What the agent writes and the engine renders.
_Avoid_: template, scene, project file
