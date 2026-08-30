# H3 Shot Design and Handoff

This document turns the locked director's read into 5–15 second MiniMax H3 segments without taking over final prompt syntax or generation.

## 1. Segment for Drama and Generation

Each segment must be 5–15 seconds. Choose duration from the action and approved dialogue, not a fixed default.

Prefer a boundary after:

- a complete line or natural dialogue breath;
- a received trigger and its consequence;
- a decisive power turn;
- a reveal or recognition;
- a completed spatial action;
- a transition-ready look, movement, sound, or object contact.

Keep a continuous take when it protects performance escalation, screen geography, a physical cause-and-effect chain, or a reveal inside the same space. Split when the segment contains incompatible intentions, two major turns, too many simultaneous actions, unreliable identity load, or a transition that needs a new reference setup.

Every internal or inter-segment cut requires `CUT_REASON`.

## 2. Director Card Schema

Create one card per segment:

```text
SEGMENT_ID
TIME_RANGE
DURATION_SECONDS
SOURCE_LINES
DRAMATIC_FUNCTION
ARC_POSITION
FELT_INTENT
DIRECTORIAL_VOICE
POV
POWER_START
POWER_END
SUBTEXT_CARRIER
NON_TRANSFERABLE_DETAIL
STOCK_SOLUTION_REFUSED
VISIBLE_CAST
SPATIAL_AXIS
START_STATE
TRIGGER
PERFORMANCE_ARC
ACTION_FLOW
BLOCKING
CAMERA_PLAN
MOVEMENT_REASON
CUTS
CUT_REASON
LIGHTING_PLAN
SOUND_PLAN
DIALOGUE
END_STATE
TRANSITION_IN
TRANSITION_OUT
REFERENCE_ROLE_MAP
IDENTITY_CONTINUITY
DUPLICATION_GUARD
STORYBOARD_TRIGGER
STORYBOARD_LIMIT
MOTION_AUTHORITY: H3_PROMPT
CONTINUITY_DEPENDENCY: CANONICAL | OBSERVED_PREVIOUS_END
STATUS: PLANNED | PROVISIONAL | LOCKED | GENERATED | ACCEPTED | RETAKE
```

Rules:

- `SOURCE_LINES` points to exact approved timeline and script locations.
- `VISIBLE_CAST` gives every named character's exact visible count; use `0 / off-screen` for voice-only presence.
- `PERFORMANCE_ARC` follows trigger -> reception -> containment/tactic -> leak -> choice/action -> opponent reaction -> aftermath.
- `ACTION_FLOW` is chronological and physically continuous.
- `CAMERA_PLAN` describes starting frame, motivated changes, focus behavior, and ending frame.
- `END_STATE` must be visually testable and useful to the next segment.
- `STORYBOARD_LIMIT` is present only when a storyboard is approved; it describes static spatial responsibility and explicitly rejects pose or motion copying.

## 3. Continuity Ledger

For every accepted or provisional segment, track:

- exact visible cast and background-extras policy;
- wardrobe, hair, makeup, damage, dirt, wetness, and carried items;
- room axis, screen direction, eyelines, entrances, exits, and camera side;
- character positions, levels, distances, occlusion, and body orientation;
- hand-object-body contact and which hand holds what;
- prop location, state, orientation, and damage;
- environment state, weather, time, particles, destruction, and practical lights;
- light direction, intensity relation, color relation, and important shadows/reflections;
- open movement at cut, unresolved gesture, active gaze, held breath, and emotional pressure;
- open sound or dialogue bridge;
- the actual final-frame state of the accepted clip.

If a later segment depends on how the previous generated clip truly ended, mark it `OBSERVED_PREVIOUS_END` and keep its prompt brief provisional. After accepting the previous clip, record `OBSERVED_END_STATE`, compare it with the planned end state, and lock or revise only the dependent fields.

## 4. Reference Roles

Assign every reference exactly one or more explicit roles:

```text
IDENTITY
COSTUME
EXPRESSION
ENVIRONMENT
PROP
COMPOSITION
FIRST_FRAME
LAST_FRAME
MOTION
CAMERA_RHYTHM
AUDIO
STORYBOARD
```

Use the minimum sufficient set:

- character turnarounds are different views of the same person;
- costume and identity references do not create extra visible instances;
- expression references are reserved for acting-critical, high-risk beats;
- environment references define place, not character blocking unless explicitly assigned;
- composition/storyboard references define static spatial duties only;
- do not add references as decorative mood filler;
- if references conflict, choose the approved canon and record the rejected role.

Apply the parent skill's storyboard trigger, five gates, per-segment limits, and episode budget. This skill recommends `STORYBOARD_TRIGGER` and `STORYBOARD_LIMIT`; the image skill creates any approved image.

## 5. H3 Prompt Brief Schema

Write a structured brief for `h3-prompt-writing`:

```text
H3 prompt brief:
- workflow
- prompt_mode
- duration_seconds
- aspect
- resolution
- pictures
- video_slots
- audio_slots
- dialogue
- cuts
- constraints
- creative:
  - DRAMATIC_FUNCTION
  - ARC_POSITION
  - FELT_INTENT
  - DIRECTORIAL_VOICE
  - POV
  - POWER_SHIFT
  - SUBTEXT_CARRIER
  - NON_TRANSFERABLE_DETAIL
  - VISIBLE_CAST
  - SPATIAL_AXIS
  - START_STATE
  - TRIGGER
  - PERFORMANCE_ARC
  - ACTION_FLOW
  - BLOCKING
  - CAMERA_PLAN
  - MOVEMENT_REASON
  - LIGHTING_PLAN
  - SOUND_PLAN
  - END_STATE
  - TRANSITION_IN
  - TRANSITION_OUT
  - REFERENCE_ROLE_MAP
  - IDENTITY_CONTINUITY
  - DUPLICATION_GUARD
  - STORYBOARD_LIMIT
  - MOTION_AUTHORITY: H3_PROMPT
```

Use documented workflow values when known. Leave an unresolved technical value for `h3-prompt-writing` or `minimax-h3` to determine rather than guessing. Keep approved dialogue verbatim.

The brief must express observable behavior and chronological change. Do not rely on “cinematic,” “tense,” “premium,” “epic,” or named-style adjectives as substitutes for direction.

## 6. Calibration Plan

Before batch generation, choose the smallest calibration set that tests:

1. baseline: ordinary dialogue, identity, performance restraint, standard camera language;
2. high risk: the hardest acting, cast load, physical interaction, VFX, reflection, or camera move;
3. pattern break: the visual/sound exception, emotional peak, or final image.

One segment may cover multiple tests. For each calibration clip, specify:

- what is being tested;
- pass/fail evidence;
- decisions that will be locked if it passes;
- fallback simplification order if it fails.

Lock only demonstrated behavior. A strong static dialogue calibration does not prove a complex orbit or multi-character action setup.

## 7. Creative Take Review

Watch the complete clip at normal speed, then inspect high-risk frames. Review in this order:

1. dramatic function and felt intention;
2. trigger-to-reaction causality;
3. POV and information timing;
4. power shift and subtext carrier;
5. performance specificity, restraint, leakage, choice, opponent reaction, and aftermath;
6. blocking, spatial axis, prop/body contact, and continuity;
7. camera motivation, framing progression, focus, and transition value;
8. exact cast, identity stability, body integrity, and no duplicate or lookalike named characters;
9. dialogue accuracy, sound hierarchy, duration, decoding, and other technical quality.

Record one decision:

- `KEEP`: creatively and technically usable;
- `FIX_IN_POST`: the core performance and continuity work; the remaining defect is safely editable;
- `REGENERATE`: the brief is sound, but execution failed stochastically;
- `REWRITE_PROMPT`: intent, chronology, constraints, or reference roles were unclear or overloaded;
- `SPLIT_SEGMENT`: the model load or dramatic action is structurally too dense.

For a retake, name the failed evidence and change one principal variable. Simplify in this order when appropriate:

1. remove decorative references or competing style instructions;
2. reduce simultaneous actions and background behavior;
3. simplify camera movement while preserving dramatic function;
4. reduce visible cast or stage reactions sequentially;
5. split at a completed dramatic beat.

Do not respond to failure by stacking near-synonymous negative prompts. Preserve exact counts and identity guards while making positive chronology clearer.
