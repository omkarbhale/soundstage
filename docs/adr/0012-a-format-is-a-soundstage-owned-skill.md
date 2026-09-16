# A format is a soundstage-owned skill, and it lives in `/formats/`

CONTEXT.md calls the genre of a video its **format**, and says a new format is a new
piece of house material rather than a new tool. Each format the captain wants is
written as one skill: a visual language defined completely enough that an agent
reading it produces that kind of video without a briefing.

There is an obvious place to put such a skill and it is the wrong one. All 26 skills
under `.agents/skills/` are vendored from the engine and version-locked in
`skills-lock.json`; `.claude/skills/<name>` is a symlink into that directory, which is
how an agent discovers them. `hyperframes skills update` rewrites those files from
upstream. A format skill written there is overwritten by the next engine update, with
no conflict, no warning and nothing in the diff to notice - ADR-0001's rule that the
engine is adopted whole and never modified, arriving as data loss.

So a format is owned by the studio and lives at `formats/<name>/SKILL.md`, beside
`components/` and `docs/`. Discovery is a symlink, `.claude/skills/<name> ->
../../formats/<name>`, which is the only part of the arrangement an engine update can
touch: if it disappears the format is still in `formats/`, and re-creating the symlink
is one command. The README and `AGENTS.md` name `formats/` directly, so the path
survives even the symlink going missing.

Two collisions follow and both are closed by the same rule: **a format's name must not
appear in `skills-lock.json`**. A name shared with a vendored skill makes two
directories claim one slash-command, and which one an agent loads is not something the
studio decides. Check before naming:

    grep -q '"<name>"' skills-lock.json && echo TAKEN

## Considered Options

A `.agents/skills/` entry excluded from the lock file was rejected: the exclusion lives
in the engine's own file, so keeping it is a promise the engine makes to the studio
rather than one the studio can keep for itself.

Publishing formats upstream was rejected for the reason ADR-0002 gives. A format
encodes how the captain's videos look; that is house material, and the engine's skill
set is not the place to keep it.

## Consequences

`formats/` holds only repo material - the language, its component and its guard - and
never a composition, a script or a rendered frame (ADR-0002). A format that needs
something the studio does not have puts the component in `components/` and the guard
at the repo root with the others (ADR-0007), so a second format inherits both.
