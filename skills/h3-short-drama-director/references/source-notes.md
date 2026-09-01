# Source Notes and Maintenance

This skill is an original integration for the local MiniMax H3 short-drama workflow. Its directing model was synthesized from the public projects below and the existing local H3 production rules.

## 2026-09 Slim-Down

The skill was deliberately reduced to fields that enter the final prompt or are verifiable on the generated clip. The following upstream-derived material was **removed** and is no longer retained in any file:

- the episode director's read (EPISODE_FUNCTION, VALUE_TURN, PRIMARY_POV, POWER_ARC, CORE_SUBTEXT, NON_TRANSFERABLE_DETAIL, STOCK_SOLUTION_REFUSED, FINAL_IMAGE) and per-segment psychology fields (HIDDEN_OBJECTIVE, OBSTACLE, TACTIC, SUBTEXT), previously adapted from the Seedance 2.0 Directing System;
- the directorial-voice taxonomy, instrument-function table, scene-type strategies, long-form spine, and consistency checklist, previously adapted from the Seedance 2.0 Directing System;
- the abstract-emotion-to-visible-carrier table, previously adapted from Visual Skills Dramaturgy (CC BY 4.0, Serge Shima). Visible-performance requirements are now delegated to the parent production skill's 短剧情绪表演与节奏规则.md, which is an original local document.

Because the dramaturgy material is no longer retained, no CC BY 4.0 attribution obligation applies to the current distribution. The notices below cover material still retained.

## Retained Upstream Sources

### WenWu / Oh My MiniMax H3 Director

- Repository: https://github.com/TFboy1/oh-my-minimaxh3-director
- License: MIT
- Copyright notice: Copyright (c) 2026 TFboy1
- Contribution retained: H3-native director framing, visible direction, and the principle that the director layer hands off to model-specific prompt writing.

### AI Director Skill

- Repository: https://github.com/tuoxie0102/ai-director-skill
- License: MIT
- Copyright notice: Copyright (c) 2026 AI Director Skill Contributors
- Contribution retained: explicit shot-card fields, dramatic segmentation boundaries, continuity tracking with observed generated end states, and reference-role discipline.

### Official MiniMax H3 Skill

- Repository: https://github.com/MiniMax-AI/MiniMax-H3
- Relevant skill: https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills/h3-prompt-writing
- Contribution retained: authoritative boundary for H3 modes, prompt structure, duration, reference labels, and model-specific syntax (enforced in `h3-prompt-writing`, not here).

## Maintenance Rules

1. Verify model syntax, duration, workflow names, reference limits, parameters, and capabilities against the official MiniMax repository and the current local `h3-prompt-writing` and `minimax-h3` skills before changing technical instructions.
2. Treat directing methods as cross-model principles, but never assume Seedance, Runway, Kling, Veo, or another model's syntax is valid for H3.
3. Preserve upstream license notices for retained material in redistributed versions.
4. Keep this skill focused on model-executable shot decisions. Route final prompt syntax, job submission, image generation, music, and editing to their dedicated skills.
5. Test updates against at least one dialogue scene, one high-risk action or VFX scene, and one continuity-dependent transition before replacing the working version.
