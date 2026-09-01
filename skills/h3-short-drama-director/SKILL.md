---
name: h3-short-drama-director
description: >-
  Turn an approved short-drama episode (script, dialogue timeline, art bible)
  into H3-ready director shot cards for MiniMax H3: dramatic segmentation into
  5–15 second shots, concrete action and performance chains, an episode look
  block (style tokens, grade, lighting, lens language), motivated camera,
  light and sound plans, exact visible-cast counts, duplication guards,
  continuity end states, technical handoff fields (workflow, prompt mode,
  aspect, resolution, picture slots), calibration clips, and creative take
  review. Cards hand off directly to h3-prompt-writing — no intermediate
  brief. Use when an episode is ready to be shot or generated. Do not use for
  story writing, asset generation, H3 prompt syntax, ComfyUI submission, or
  editing.
---

# H3 Short Drama Director

Turn approved dramatic source material into per-segment shot decisions a video model can actually execute. Every field written by this skill must end up visible or audible in the generated clip, or enter the final prompt text. A field that reaches neither is not written.

The cinematic look of the final video comes from two places this skill controls: the episode look block (style tokens, color grade, lighting, lens language) and simple, motivated camera work — not from abstract directing intent. Do not spend budget on fields the model cannot render.

## Boundary

This skill owns:

- dramatic segmentation of the approved dialogue timeline into 5–15 second segments;
- per-segment director cards: action and performance chains, camera, light, sound, cast counts, end states, and the technical handoff envelope (workflow, prompt mode, aspect, resolution, picture slots);
- the episode look block carried into every card and prompt;
- continuity ledgers and reference-role assignments;
- calibration plans and creative take review (`KEEP | FIX_IN_POST | REGENERATE | REWRITE_PROMPT | SPLIT_SEGMENT`).

This skill does not:

- rewrite approved dialogue, plot, character facts, or episode duration;
- generate character art, expression references, storyboard images, music, or video;
- write final MiniMax H3 syntax, choose undocumented model parameters, submit ComfyUI jobs, edit footage, or mix audio;
- replace `h3-prompt-writing`, `minimax-h3`, `autodl-app-instance`, or the parent production skill.

Emotion, performance, and rhythm follow the parent production skill's [短剧情绪表演与节奏规则.md](../short-drama-production/references/短剧情绪表演与节奏规则.md): performable trigger→reaction chains, visible signals, and 1–5 intensity levels. This skill applies those rules at segment level; it never restates or weakens them.

## Required Inputs

Resolve before directing:

- approved project Brief and complete episode outline;
- approved episode dialogue timeline and performance-directed script;
- approved episode art bible and exact paths to usable identity, costume, expression, prop, and environment references;
- prior accepted episode or preceding-shot end state when continuity depends on it;
- target aspect ratio, resolution, total runtime, and available H3 workflows if known.

Source precedence when approved sources disagree: dialogue timeline (speaker, wording, order, duration) → script (playable action, causality, emotional beats) → episode outline (structural promise) → Brief (series promise, tone, limits) → art bible (identity). If two approved sources conflict and the conflict changes story meaning or identity, write `SOURCE_CONFLICT` (source_a, source_b, affected_segments, decision_needed), continue unaffected material, and stop only the affected decision. Do not silently invent a resolution.

## Core Rules

1. Write only what the model can execute: concrete bodies, objects, space, light, sound, and camera. No episode-level psychology fields, no voice taxonomies, no abstract trend tracking.
2. One segment carries one dominant emotional direction and at most one decisive turn; split when two collide (情绪规则 §六).
3. Performance is written as a visible chain — trigger, reception, containment or tactic, one leak, action or line, opponent reaction, aftermath — with concrete eyes, breath, hands, and distance signals (情绪规则 §三、§五). Emotion adjectives alone are not direction.
4. Cut and move the camera by decision, never by default. For every segment choose the shot structure — one continuous take or multiple hard-cut shots — and the camera behavior, then name the reason for what you chose, including stillness or a take without cuts. A cut is an information event (new subject, space, state, viewpoint, or time); camera motion is a framing event. Record the structure in `CUTS` and the movement reason in `MOVEMENT_REASON`.
5. Keep exact visible-cast counts and the minimum reference set needed for identity and space. Repeated views of one character are identity evidence for one person, never multiple instances.
6. Make storyboard references only when the user explicitly requires them (the parent skill owns that decision). When they exist, they anchor static space, never motion, and the segment brief carries `STORYBOARD_LIMIT`.
7. Plan continuity globally, but finalize continuity-dependent prompts from the observed end state of the accepted previous clip (`OBSERVED_PREVIOUS_END`).
8. Preserve the approved dialogue timeline exactly.

## Workflow

Read [h3-shot-design.md](references/h3-shot-design.md) before segmentation, cards, briefs, calibration, or take review. Then:

1. **Lock sources.** Record paths and approval states; run the conflict check above.
2. **Episode look block.** Choose style tokens, color grade, lighting and lens language, camera grammar, and sound approach for the whole episode, in concrete H3-executable wording. One look per episode; change only at a deliberate pattern break. `MEMORY`/`FLASHBACK` time-state cues follow the approved script.
3. **Segment.** Cut the approved timeline into 5–15 second segments at completed actions, dialogue breaths, reveals, or spatial resets — never at a fixed interval.
4. **Director cards.** Write `视频制作/导演/01-导演镜头表.md` (look block on top, one row per segment) and `视频制作/导演/片段/NN-导演卡.md` per the schema in `h3-shot-design.md`.
5. **Continuity ledger.** Write `视频制作/导演/02-连续性与参考素材台账.md`: cast, positions and axis, wardrobe and props, light, open movement and sound, accepted end states.
6. **Handoff.** `h3-prompt-writing` writes `视频制作/提示词/NN.txt` directly from each locked card plus the look block, the approved dialogue at `SOURCE_LINES`, and the referenced assets. There is no intermediate brief file; the card carries the technical envelope and every constraint. Do not invent final H3 tags here.
7. **Calibration.** Write `视频制作/导演/03-校准片方案.md`: the smallest set covering baseline, highest risk, and the pattern break.
8. **Take review.** Per generated clip, inspect the whole take plus high-risk frames and record the verdict in `视频制作/导演/04-样片与返修记录.md`. Record the observed end state of accepted takes before finalizing the next continuity-dependent card.

## Completion Criteria

- every segment traces to approved source lines and has a locked card, or is explicitly provisional on an observed end state;
- the episode has one look block, and every brief carries the part of it the segment uses;
- every locked card carries the technical envelope, visible action and performance chains, exact cast counts, duplication guards, motivated camera, and a reasoned shot structure;
- calibration decisions are recorded before batch generation;
- every accepted take has a verdict and a continuity end-state record.
