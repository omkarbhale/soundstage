# Guard 4: prove every reveal has exactly one element to land on.
#
#   python3 id_check.py <composition>/index.html
#
# A composition animates by selector - tl.fromTo("#ct-1", ...) - and two ways of
# writing one silently stop it landing where it was meant to:
#
#   A DUPLICATE id. A scene that writes literal ids (id="dr-1" on a sentence) and
#   also generates numbered ids in a loop (id="dr-{i}" on a row of pills) can
#   collide. GSAP resolves "#dr-1" to the FIRST match in document order, so one
#   element is tweened twice and the other has no reveal at all - it is simply on
#   screen from the moment its scene fades in.
#
#   A SELECTOR THAT MATCHES NOTHING. Rename an element and leave the tween behind,
#   or typo the id in the tween, and GSAP animates an empty set. The element is
#   again on screen from the start of its scene.
#
#   A CLIP THAT IS NEVER ON SCREEN. Same failure one level up, and measured in this
#   repo's own corpus rather than imagined: a scene table listed out of spoken order
#   gave one clip `data-duration="-63.59"` and let another overlay ninety-seven
#   seconds of the module. Every reveal inside the negative clip had exactly one
#   element to land on and none of them were ever seen. A clip with no duration has
#   no reveals, so it belongs to this guard.
#
# Both fail exactly the way the narration guards do, which is why this lives here
# beside them (ADR-0007): nothing errors, nothing warns, cue_check.py still passes
# because every cue phrase still resolves, and the SETTLED frame of the scene is
# identical either way. The only frame that shows it is one sampled between the
# two cues - which is exactly the frame nobody picks by hand, and which
# review_frames.py does not promise to pick either, because it samples a scene's
# reveals and not the gaps between them.
#
# This reads the BUILT document rather than the generator, because the built
# document is what the engine renders and it carries both halves - the markup and
# the timeline - in one file. Keep no hand-written list of ids: a list goes stale
# the first time a scene is rewritten.
#
# Run it after building and before rendering, beside cue_check.py.
import re, sys, collections

PATH = sys.argv[1] if len(sys.argv) > 1 else sys.exit("usage: id_check.py <composition>/index.html")
doc = open(PATH, encoding="utf8").read()

# Markup only: the timeline is JavaScript in the same file and its string
# literals must not be read as if they were attributes.
body = re.sub(r"<script\b.*?</script>", "", doc, flags=re.S | re.I)

ids = re.findall(r'\bid="([^"]+)"', body)
classes = {c for attr in re.findall(r'\bclass="([^"]+)"', body) for c in attr.split()}

dupes = {i: n for i, n in collections.Counter(ids).items() if n > 1}

# Every GSAP target written as a string literal. The methods are the ones the
# house generators use; a target built from a variable is not checkable here and
# is not written in this series.
CALL = re.compile(r'\btl\.(?:fromTo|from|to|set|add)\(\s*"([^"]+)"')
targets = sorted(set(CALL.findall(doc)))

# Every clip, and how long it is on screen for. Read off the markup because that is
# what the engine reads; a duration that is zero or negative is a clip the viewer
# never sees, whatever the timeline says about it.
CLIP = re.compile(r'id="([^"]+)"[^>]*class="[^"]*\bclip\b[^"]*"[^>]*data-start="([-\d.]+)"'
                  r'[^>]*data-duration="([-\d.]+)"')
unseen = [(i, float(d)) for i, _s, d in CLIP.findall(body) if float(d) <= 0]

missing = []
for sel in targets:
    # "#in-door", "#tn-fig .fg-door", ".pill.no" - check the leading token, which
    # is what has to exist for the rest of the selector to have anywhere to look.
    head = sel.split()[0]
    if head.startswith("#"):
        name = re.split(r"[.\[:]", head[1:])[0]
        if name not in ids:
            missing.append((sel, f'no element has id="{name}"'))
    elif head.startswith("."):
        name = re.split(r"[.\[:]", head[1:])[0]
        if name not in classes:
            missing.append((sel, f'no element carries class "{name}"'))

print(f"{len(ids)} id(s), {len(targets)} animated selector(s) in {PATH}")
for i, n in sorted(dupes.items()):
    print(f'  DUPLICATE id="{i}" on {n} elements - a reveal lands on the first only')
for sel, why in missing:
    print(f"  MATCHES NOTHING  {sel!r} - {why}")
for i, d in unseen:
    print(f'  NEVER ON SCREEN  id="{i}" has data-duration="{d}" - nothing in it is ever seen. '
          f"A scene table out of spoken order does this: each scene's end is taken from the "
          f"NEXT entry's start.")
if dupes or missing or unseen:
    n = len(dupes) + len(missing) + len(unseen)
    print(f"{n} fault(s) - an element is revealed twice, never, or inside a clip nobody sees")
    sys.exit(1)
print("every reveal has exactly one element to land on, inside a clip that is")
