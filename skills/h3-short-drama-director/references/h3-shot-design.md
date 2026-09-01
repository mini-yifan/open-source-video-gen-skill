# H3 Shot Design and Handoff

Turn the approved episode into 5–15 second MiniMax H3 segments and structured briefs for `h3-prompt-writing`. Every field must either enter the final prompt text or be verifiable on the generated clip. Internal documentation that reaches neither is not written.

## 1. Episode Look Block

Decide once per episode, before segmentation. This block carries the look levers the model actually responds to, and every segment's final prompt carries the part it uses.

```text
STYLE_TOKENS      style tokens allowed by h3-prompt-writing, e.g. live-action, cinematic | 2D-animated — placed at the start of Shot 1
LOOK_GRADE        palette and grade in concrete words: cold teal shadows with warm highlights, low-saturation daylight, crushed blacks
LIGHT_LANGUAGE    dominant light direction and contrast policy motivated by the world: window key light, practical neon, hard noon sun
LENS_LANGUAGE     one or two per episode: shallow depth of field with compressed background, wide deep-focus staging
CAMERA_GRAMMAR    the moves this episode uses, matched to H3 capability: slow push-in, lateral track, static locked-off, handheld follow
SOUND_APPROACH    environment layer and music space; dialogue and breath stay dominant
```

Rules:

- Concrete only. "Cinematic feel" is not a plan; "cold teal shadows, warm highlights, shallow depth of field" is.
- One look per episode. Change it only at a deliberate pattern break. `MEMORY`/`FLASHBACK` time-state cues follow the approved script and override the base look consistently.
- The look block constrains per-segment camera and light plans; it does not replace them.

## 2. Segment for Drama and Generation

Each segment must be 5–15 seconds. Choose duration from the action and approved dialogue, not a fixed default.

Prefer a boundary after:

- a complete line or natural dialogue breath;
- a received trigger and its consequence;
- a reveal or recognition;
- a completed spatial action;
- a transition-ready look, movement, sound, or object contact.

Judge each boundary from the content: split when the segment would contain two conflicting emotional turns, too many simultaneous actions, unreliable identity load, or a transition that needs a new reference setup; keep one segment when performance escalation, spatial causality, or a reveal is stronger inside it.

Shot structure inside a segment is a per-segment decision with no default. A segment may be one continuous take or multiple hard-cut shots. Decide from the dramatic content every time, and record the decision in the card (`CUTS`): a take without cuts needs a reason just as much as a cut does. Do not fall back to a single take because it is the familiar shape.

## 3. Director Card Schema

One card per segment:

```text
SEGMENT_ID
TIME_RANGE
DURATION_SECONDS
WORKFLOW
PROMPT_MODE
ASPECT
RESOLUTION
PICTURES
VIDEO_SLOTS
AUDIO_SLOTS
SOURCE_LINES
DIALOGUE
DRAMATIC_FUNCTION
VISIBLE_CAST
START_STATE
ACTION_FLOW
PERFORMANCE_ARC
CAMERA_PLAN
MOVEMENT_REASON
LIGHTING_PLAN
SOUND_PLAN
CUTS
END_STATE
TRANSITION_IN
TRANSITION_OUT
REFERENCE_ROLE_MAP
IDENTITY_CONTINUITY
DUPLICATION_GUARD
STORYBOARD_LIMIT
MOTION_AUTHORITY: H3_PROMPT
CONTINUITY_DEPENDENCY: CANONICAL | OBSERVED_PREVIOUS_END
STATUS: PLANNED | PROVISIONAL | LOCKED | GENERATED | ACCEPTED | RETAKE
```

Rules:

- `SOURCE_LINES` points to exact approved timeline and script locations.
- `WORKFLOW`, `PROMPT_MODE`, `ASPECT`, and `RESOLUTION` are the technical envelope: which ComfyUI workflow and prompt mode (T2VA / I2VA / FL2VA / L2VA / Ref2VA) this segment uses, chosen from what its references actually support. Write `UNRESOLVED` when unknown and let `minimax-h3` or `h3-prompt-writing` resolve it; never guess.
- `PICTURES` declares the upload order; that order **is** the `<Picture N>` numbering the final prompt cites.
- `DIALOGUE` carries the verbatim approved lines for this segment with their speakers; never paraphrased, never re-ordered.
- `DRAMATIC_FUNCTION` is one line: what this beat does to the story.
- `VISIBLE_CAST` gives every named character's exact visible count; `0 / off-screen` for voice-only presence.
- `START_STATE` is the opening frame: positions, spatial axis, eyelines, and what the audience already knows.
- `ACTION_FLOW` is chronological and physically continuous: positions, levels, distances, occlusion, hand-object-body contact.
- `PERFORMANCE_ARC` follows the 情绪规则 chain — 情绪起点 → 触发 → 接收 → 克制/策略 → 一次泄露 → 行动或台词 → 对手反应 → 余波 — with concrete eyes, breath, hands, and distance signals, and 1–5 intensity levels on key emotional beats.
- `CAMERA_PLAN` describes starting frame, motivated changes, focus behavior, and ending frame.
- `MOVEMENT_REASON` names why the camera moves, or why it stays static.
- `LIGHTING_PLAN` and `SOUND_PLAN` stay inside the episode look block. Sound names which event earns emphasis and what carries out; never constant score, never constant loudness.
- `CUTS` is a per-segment decision with no default: either `one continuous take, do not cut` or multiple hard-cut shots, each `[Shot N]` carrying its cut time and reason. A cut earns its place by introducing new information — subject, space, state, viewpoint, or time (a listener's reaction, an insert of the evidence, a wide-to-close reveal); when only distance or angle changes, move the camera instead. A continuous take earns its place when the performance escalation, spatial causality, or the reveal lives inside one framing. State the reason for whichever you chose.
- In multi-shot segments, restate the exact visible cast per shot, keep screen axis, light, costume, and prop state continuous across cuts, and mark dialogue that continues across a cut.
- `END_STATE` must be visually testable and useful to the next segment.
- `STORYBOARD_LIMIT` is present only when user-required storyboard images exist for this segment; it describes static spatial responsibility and explicitly rejects pose or motion copying.

## 4. Continuity Ledger

`02-连续性与参考素材台账.md` tracks, per segment:

- exact visible cast and background-extras policy;
- wardrobe, hair, makeup, damage, carried items;
- room axis, screen direction, eyelines, camera side, entrances and exits;
- positions, levels, distances, occlusion, body orientation;
- hand-object-body contact and which hand holds what;
- prop location, state, and orientation;
- light direction and important shadows or reflections;
- open movement at cut, unresolved gesture, active gaze, and open sound;
- the actual final-frame state of the accepted clip.

If a later segment depends on how the previous generated clip truly ended, mark it `OBSERVED_PREVIOUS_END` and keep its card `PROVISIONAL` — do not generate its prompt until the previous clip is accepted. After accepting the previous clip, record `OBSERVED_END_STATE`, compare it with the planned end state, and lock or revise only the dependent fields.

## 5. Reference Roles

Assign every reference explicit roles:

```text
IDENTITY / COSTUME / EXPRESSION / ENVIRONMENT / PROP / COMPOSITION
FIRST_FRAME / LAST_FRAME / MOTION / CAMERA_RHYTHM / AUDIO / STORYBOARD
```

Use the minimum sufficient set:

- character turnarounds are different views of the same person, never multiple instances;
- expression references are reserved for acting-critical, high-risk beats, and must be single-expression images — never a multi-expression grid (the model reads multiple faces as multiple people);
- environment references define place, not blocking, unless explicitly assigned;
- composition and storyboard references define static spatial duties only;
- no decorative mood-filler references;
- when references conflict, the approved art canon wins; record the rejected role.

Storyboard references exist only when the user explicitly requires them; the parent production skill owns that decision and the image skill creates any requested image. When they exist, they take the `STORYBOARD` role and the brief carries `STORYBOARD_LIMIT`.

## 6. Handoff: The Director Card Is the Prompt Input

There is no intermediate brief file. `h3-prompt-writing` generates `视频制作/提示词/NN.txt` directly from each locked director card, together with the episode look block in `01-导演镜头表.md`, the approved script and dialogue timeline at `SOURCE_LINES`, and the referenced art assets.

The card must be self-sufficient for prompting. `h3-prompt-writing` reads it as follows:

- `WORKFLOW` / `PROMPT_MODE` decide the prompt structure and mode; `ASPECT` / `RESOLUTION` must match target delivery; `UNRESOLVED` values are resolved by `minimax-h3` or `h3-prompt-writing`, never guessed.
- `PICTURES` upload order is the `<Picture N>` numbering cited in the prompt; `VIDEO_SLOTS` / `AUDIO_SLOTS` say which slots carry real assets.
- `DIALOGUE` enters the prompt verbatim, with speakers preserved.
- `CUTS` is the shot-structure decision verbatim — `one continuous take, do not cut` or the hard-cut list with times and reasons — and becomes the `[Shot N]` body.
- `VISIBLE_CAST`, `IDENTITY_CONTINUITY`, `DUPLICATION_GUARD`, and `MOTION_AUTHORITY: H3_PROMPT` must reach the final prompt body as natural English, not stay in the card; `STORYBOARD_LIMIT` joins when user-required storyboards exist.
- The card describes observable behavior and chronological change. Do not pad with abstract mood adjectives; style tokens come from the look block.

## 7. Calibration Plan

Before batch generation, choose the smallest calibration set that tests:

1. baseline: ordinary dialogue, identity, performance restraint, standard camera language;
2. high risk: the hardest acting, cast load, physical interaction, VFX, reflection, or camera move;
3. pattern break: the visual or sound exception, emotional peak, or final image.

One segment may cover several tests. For each clip specify what is tested, pass/fail evidence, decisions locked on pass, and the fallback simplification order. Lock only demonstrated behavior; a strong static dialogue calibration does not prove a complex orbit or multi-character action setup.

## 8. Creative Take Review

Watch the complete clip at normal speed, then inspect high-risk frames. Review in this order:

1. dramatic function — did the beat land;
2. trigger-to-reaction causality and performance specificity: containment, leak, opponent reaction, aftermath;
3. blocking, spatial axis, prop and body contact, and continuity with neighboring segments;
4. camera motivation, shot structure (was the cut-or-take choice a decision with a reason), framing progression, focus, and transition value;
5. exact cast, identity stability, body integrity, no duplicate or lookalike named characters;
6. dialogue accuracy, sound hierarchy, duration, decoding, and technical quality.

Record one decision to `04-样片与返修记录.md`:

- `KEEP` — creatively and technically usable;
- `FIX_IN_POST` — the core performance and continuity work; the remaining defect is safely editable;
- `REGENERATE` — the brief is sound, but execution failed stochastically;
- `REWRITE_PROMPT` — intent, chronology, constraints, or reference roles were unclear or overloaded;
- `SPLIT_SEGMENT` — the model load or dramatic action is structurally too dense.

For a retake, name the failed evidence and change one principal variable. Simplify in this order: remove decorative references or competing style instructions; reduce simultaneous actions and background behavior; simplify camera movement while preserving the dramatic function; reduce visible cast; split at a completed beat. Do not stack near-synonymous negative prompts; preserve exact counts and identity guards while making the positive chronology clearer.
