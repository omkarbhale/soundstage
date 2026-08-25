# soundstage

The vocabulary. Use these words, and never the ones on an `_Avoid_` line - in prose, in
filenames, and in identifiers.

## The three axes

**Format**:
The genre of a video: what it looks and sounds like. Narrated slides, screencast,
animated explainer. A new format is a new template, not a new tool.
_Avoid_: style, type, kind, output format, aspect ratio

**Topic**:
The subject matter a video is about. Never constrain it.
_Avoid_: content, subject, theme

**Source**:
The shape of the material a video is made from - a Word document, markdown, a URL,
loose notes. Read whatever you are given; never require a particular shape.
_Avoid_: input, source format, feed

## Making a video

**Module**:
One unit of a course, and the unit a single video covers. Each carries its own
objectives, script and quiz.
_Avoid_: chapter, lesson, section, part

**Script**:
The narration text for one video. Write it, and let the captain read it before it
becomes audio.
_Avoid_: copy, voiceover text, transcript

## The two halves

**Engine**:
HyperFrames. Renders a composition to video, generates narration, and returns
per-word timing. Never modify it and never wrap it.
_Avoid_: renderer, framework, HyperFrames (in prose about our own work)

**Studio**:
This repo. House style, reusable components, voice configuration, conventions, and
the instructions an agent reads instead of a briefing. Put no rendering code and no
content here.
_Avoid_: pipeline, framework, wrapper, harness

**Composition**:
The HTML that describes one video: what you write and what the engine renders.
_Avoid_: template, scene, project file
