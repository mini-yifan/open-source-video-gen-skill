---
name: h3-short-drama-director
description: >-
  Direct an approved short-drama episode for MiniMax H3 after its script,
  dialogue timeline, and art are locked. Produces an episode treatment, a
  unified directorial voice, 5–15 second shot cards, continuity and reference
  maps, calibration-shot plans, H3 prompt briefs, and creative take reviews.
  Use when an episode is ready to be shot or generated. Do not use for story
  writing, asset generation, H3 prompt syntax, ComfyUI submission, or editing.
---

# H3 Short Drama Director

Act as the director layer between an approved short-drama package and the existing MiniMax H3 generation pipeline. Turn dramatic intent into visible performance, blocking, camera, light, sound, and continuity decisions. Preserve the approved dialogue and story.

## Boundary

This skill owns:

- the episode-level directorial treatment and unified visual voice;
- dramatic segmentation into H3-sized shots;
- point of view, power shifts, subtext, performance arcs, blocking, motivated camera, light, sound, and transitions;
- reference-role planning, continuity ledgers, calibration clips, and creative take review;
- structured creative briefs handed to `h3-prompt-writing`.

This skill does not:

- rewrite approved dialogue, plot, character facts, or episode duration;
- generate character art, expression references, storyboard images, music, or video;
- write final MiniMax H3 syntax, choose undocumented model parameters, submit ComfyUI jobs, edit footage, or mix audio;
- replace `h3-prompt-writing`, `minimax-h3`, `autodl-app-instance`, or the parent production skill.

When a requested directing choice conflicts with approved source material, write `SOURCE_CONFLICT`, cite both locations, and stop only the affected decision. Do not silently invent a resolution.

## Read Supporting Guidance

1. For every narrative episode, read [directors-read.md](references/directors-read.md).
2. For multi-scene work, dialogue performance, or a request for more cinematic quality, also read [directing-engine.md](references/directing-engine.md).
3. Before segmentation, reference planning, calibration, H3 handoff, or take review, read [h3-shot-design.md](references/h3-shot-design.md).
4. Read [source-notes.md](references/source-notes.md) only when maintaining this skill, checking provenance, or updating it from upstream repositories.

## Required Inputs

Resolve these before directing:

- approved project Brief and complete episode outline;
- approved episode dialogue timeline and performance-directed script;
- approved episode art bible and exact paths to usable identity, costume, expression, prop, and environment references;
- prior accepted episode or preceding-shot end state when continuity depends on it;
- target aspect ratio, resolution, total runtime, delivery constraints, and available H3 workflows if already known.

Treat the dialogue timeline as immutable for speaker, wording, order, and duration. Treat the approved art as identity canon. If an input is missing, mark the affected field `UNRESOLVED`; continue with independent decisions unless the missing fact can change story meaning or identity.

## Core Directing Rules

1. Give each segment one dominant felt intention and at most one decisive turn.
2. Make camera, blocking, performance, light, sound, and duration serve the same intention.
3. Plan the episode globally before finalizing shots locally.
4. Plan continuity globally, but finalize continuity-dependent prompts from the observed end state of the accepted previous clip.
5. Direct actors through objective, obstacle, tactic, containment, leakage, choice, and opponent reaction—not emotion adjectives alone.
6. Move the camera only for a dramatic, spatial, or perceptual reason. A static camera is valid when movement would weaken the scene.
7. Treat reactions and aftermath as part of the event. Do not cut away before the consequence lands.
8. Preserve the approved dialogue timeline exactly; use performance and staging to interpret it.
9. Keep exact visible-cast counts and use the minimum reference set needed for identity and space.
10. Decide storyboard-reference eligibility only after the camera plan exists. A storyboard is an exception for static spatial information, never a substitute for directing motion.

## Workflow

### 1. Lock Sources and Read the Episode

Create `视频制作/导演/00-本集导演方案.md`. Record source paths and source status, then define:

- the episode function, value turn, primary POV, power arc, audience feeling, core subtext, and final image;
- one directorial voice and its restrained secondary variation;
- scale, movement, light, blocking, and sound progression across the episode;
- the non-transferable dramatic detail and at least one stock solution the episode will refuse.

Use `directors-read.md` for the episode read. Do not start from shot vocabulary.

### 2. Segment by Dramatic Action

Divide the approved timeline into 5–15 second segments. Cut at a completed action, dialogue breath, power turn, reveal, spatial reset, or continuity-safe handoff—not at a fixed interval. Keep a continuous take when performance or spatial causality is stronger without a cut.

Create `视频制作/导演/01-导演镜头表.md` with one row per segment and a `视频制作/导演/片段/NN-导演卡.md` for every segment. Follow the schema in `h3-shot-design.md`.

### 3. Build Continuity and Reference Plans

Create `视频制作/导演/02-连续性与参考素材台账.md`. Track exact cast, screen direction, positions, eyelines, body/prop contact, costume state, environment state, light, open movement, open sound, and the previous accepted end state.

Assign each reference one explicit role. Repeated character views are identity evidence for one person, never multiple instances. Keep expression references for high-risk performance beats. Apply the parent production skill's storyboard trigger and total-budget rules; this skill only recommends candidates and static responsibilities. It does not generate images.

### 4. Produce H3 Prompt Briefs

Write `视频制作/提示词/NN-brief.md` from the locked director card. Include the complete creative handoff schema from `h3-shot-design.md`, exact visible-cast counts, identity continuity, duplication guards, and `MOTION_AUTHORITY: H3_PROMPT`.

Hand each brief to `h3-prompt-writing`. Let that skill choose the documented H3 prompt structure and reference syntax. Do not invent final H3 tags here.

### 5. Calibrate Before the Batch

Create `视频制作/导演/03-校准片方案.md`. Choose the smallest set that covers:

- the episode's baseline performance and visual voice;
- its highest technical or acting risk;
- the intended pattern break or ending language.

One clip may cover several categories. Generate and review calibration clips before committing the whole batch. Lock successful decisions and change one principal variable per failed retake.

### 6. Review Takes as a Director

For each generated clip, inspect the whole clip plus high-risk frames and write the decision to `视频制作/导演/04-样片与返修记录.md`:

- `KEEP`
- `FIX_IN_POST`
- `REGENERATE`
- `REWRITE_PROMPT`
- `SPLIT_SEGMENT`

Judge intention, performance causality, POV, power shift, blocking, motivated camera, reactions, continuity, cast uniqueness, and transition value before purely technical polish. When a clip is accepted, record its observed end state before finalizing the next continuity-dependent prompt.

## Completion Criteria

The directing pass is complete only when:

- every segment traces to approved source lines and a dramatic function;
- the episode has one coherent directorial voice with a deliberate progression and pattern break;
- every segment has a locked director card or is explicitly provisional on an observed end state;
- reference roles are minimal and unambiguous, and storyboard candidates obey the parent budget;
- every H3 brief contains visible action and performance carriers rather than abstract mood alone;
- calibration decisions are recorded before batch generation;
- every accepted take has a creative verdict and a continuity end-state record.
