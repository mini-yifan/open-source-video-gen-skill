---
name: h3-prompt-writing
description: >-
  Write MiniMax H3 video generation prompts for T2VA, I2VA, FL2VA, L2VA, and
  Ref2VA. Use when rewriting multimodal requests into H3 prompt structures,
  composing integrated_multimodal_description, overall_soundscape, and
  non_diegetic_music, aligning keyframes, defining reference labels, or when
  the caller hands off a structured handoff (the production's own shot/segment
  notes, or a minimax-h3 brief) after choosing a workflow.
  Do not SSH, pick ComfyUI workflows, or submit GPU jobs.
---

# H3 Prompt Writing

This skill writes the prompt body only. Connecting to SeetaCloud, choosing U03/U06/U02, acceleration, upload, and download belong to [`minimax-h3`](../minimax-h3/SKILL.md).

It is portable to any agent that can read local files and requires no external API calls, MiniMax Hub tools, or proprietary runtime. The `agents/openai.yaml` file only adds optional ChatGPT/Codex UI metadata and does not restrict the skill to OpenAI agents.

## Workflow

1. If the caller passed a **structured handoff** — the production's own shot/segment notes, or a `minimax-h3` brief — read `references/comfy-handoff.md`, lock `prompt_mode` from it, and apply its override table. Do not re-guess the mode from the images alone.
2. Otherwise identify the input mode: T2VA, I2VA, FL2VA, L2VA, or full-reference Ref2VA. Use only `references/base-en.txt` or `references/ref-en.txt` — do not apply Comfy patches.
3. For base text/keyframe modes, follow `references/base-en.txt`.
4. For full-reference mode, follow `references/ref-en.txt`.
5. Preserve the exact field names, section order, labels, and timing notation from the selected guide.

## Base Modes

- T2VA: build the full audiovisual timeline from text.
- I2VA: start from the first frame and develop forward from it. Picture 1 is the first frame.
- FL2VA: describe the continuous path between the first and last frames.
- L2VA: infer a plausible opening and converge to the supplied last frame.

Use `integrated_multimodal_description`, `overall_soundscape`, and `non_diegetic_music` in the order shown in `references/base-en.txt`.

## Full-Reference Mode

Ref2VA rewrites use `subject_definitions`, `summary`, `retention_analysis`, `detailed_description`, `overall_soundscape`, and `non_diegetic_music` in that order. Reference labels stay consistent across all sections.

Read `references/ref-en.txt` for label rules, retention analysis, and complete examples.

## Output Rules

- Write rewrite sections in English; preserve dialogue, lyrics, and visible scene text in their original language.
- Describe each shot by composition, subjects, environment, actions, camera, sound, and the exact point where referenced content appears.
- **皮肤真实感锁（仅写实真人项目适用；项目为写实且有人物出镜时必写、写进正文；H3 无独立负面提示词栏，必须正向点名）**：matte realistic skin with visible pores and fine texture, `completely free of oily shine, greasy glow, waxy highlights or plastic smoothing`；脸部特写另加 `absolutely no harsh specular hot spots`。光线优先用柔光写法（soft diffused daylight / window light / soft diffused overhead light with gentle falloff + subtle bounce fill），并点明额头、鼻梁、颧骨在光下保持哑光。动漫、卡通等非写实项目不写此锁。参考图质感必须与项目风格一致（见 `character-three-view`）；写实项目的参考图若带 CG 感会锁死油腻观感。
- **禁写颗粒与美化词**：不得出现 `film grain`、`35mm`、`grain`、`beautified`、`retouched`、`flawless skin` 之类的词——模型会把它们放大成重噪点或磨皮油腻脸。写实风格用 `documentary-style live-action`、`natural muted colors`、`clean crisp digital cinema image` 表达。
- Write camera motion as natural English inside the shot (`references/base-en.txt` §4.3).
- When the handoff (production handoff notes or minimax-h3 brief) provides `VISIBLE_CAST`, `IDENTITY_CONTINUITY`, or `DUPLICATION_GUARD`, carry them into the official prompt body as natural English. State the exact visible count of each named character positively, then add the relevant no-duplication constraints; do not invent extra top-level output fields. Use this canonical guard form, adapted to the shot: `Exactly one instance of <Subject 1> is visible in the frame. <Subject 1> remains one single physical person with one continuous complete body throughout the shot. No duplicate, clone, twin, doppelganger, extra copy, lookalike, ghost image, afterimage, motion trail, split body, or suddenly appearing extra person.` In multi-character shots, write `exactly one` for each named character and add `Background extras must not resemble any named character.` Avoid mirrors, glass reflections, and person-shaped shadows unless the story needs them; when a mirror is required, state that the reflection is an optical copy of the one real person, not a second individual. Intentional duplicates (clones, mirror doubles, time-states) are exempt only where the handoff explicitly approves each instance.
- In Ref2VA, multiple reference pictures of one character define one `<Subject N>`. Explicitly say they are alternate identity views of the same single physical person, not separate people, and keep that subject to the exact per-shot count from `VISIBLE_CAST`.
- Avoid plot summaries, unresolved reference labels, and timing that does not match the requested duration.

## Tips for Better Results

- Match the total duration of the description to the requested video length (4–15 seconds unless the handoff specifies otherwise).
- Keep reference labels consistent (e.g. `<Picture 1>`, `<Video 1>`, `<Audio 1>`) across every section.
- Prefer concrete visual and audio details over empty praise such as "beautiful". Style tokens at the start of Shot 1 (`live-action`, `cinematic`, `2D-animated`) are allowed; for realistic character work prefer `Documentary-style live-action footage, natural muted colors, clean crisp digital cinema image` as the opening token block.
- When using keyframes (I2VA / FL2VA / L2VA), clearly state how the first and/or last frame connects to the timeline.
