# Source Notes and Maintenance

This skill is an original integration for the local MiniMax H3 short-drama workflow. Its directing model was synthesized from the following public projects and the existing local H3 production rules.

## Upstream Sources

### WenWu / Oh My MiniMax H3 Director

- Repository: https://github.com/TFboy1/oh-my-minimaxh3-director
- Relevant file: https://github.com/TFboy1/oh-my-minimaxh3-director/blob/master/references/wenwu-director.md
- License: MIT
- Copyright notice: Copyright (c) 2026 TFboy1
- Contribution used: H3-native director framing, visible direction, cinematic shot logic, and the principle that the director layer should hand off to model-specific prompt writing.

### Seedance 2.0 Directing System

- Repository: https://github.com/Emily2040/seedance-2.0
- Relevant files:
  - https://github.com/Emily2040/seedance-2.0/blob/main/references/directors-read.md
  - https://github.com/Emily2040/seedance-2.0/blob/main/references/directing-engine.md
  - https://github.com/Emily2040/seedance-2.0/blob/main/seedance-sequence/SKILL.md
- License: MIT
- Copyright notice: Copyright (c) 2026 Iamemily2050 (@iamemily2050)
- Contribution used: director's read, felt intention, POV, power, subtext, non-transferable detail, refusal of generic coverage, unified directorial voice, and sequence-level progression.

### AI Director Skill

- Repository: https://github.com/tuoxie0102/ai-director-skill
- Relevant files:
  - https://github.com/tuoxie0102/ai-director-skill/blob/main/references/storyboard-continuity.md
  - https://github.com/tuoxie0102/ai-director-skill/blob/main/references/shot-card.md
- License: MIT
- Copyright notice: Copyright (c) 2026 AI Director Skill Contributors
- Contribution used: explicit shot-card fields, continuity tracking, reference-role discipline, and the distinction between planned continuity and observed generated end states.

### Visual Skills Dramaturgy

- Repository: https://github.com/smixs/visual-skills
- Relevant file: https://github.com/smixs/visual-skills/blob/main/video/references/dramaturgy.md
- License: CC BY 4.0
- Author attribution: Serge Shima
- Contribution used: intention-first dramaturgy, playable action, performance causality, and converting abstract emotional language into visible behavior.

Maintain the Serge Shima attribution when redistributing adaptations that retain material from the dramaturgy reference.

### Official MiniMax H3 Skill

- Repository: https://github.com/MiniMax-AI/MiniMax-H3
- Relevant skill: https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills/h3-prompt-writing
- Contribution used: authoritative boundary for H3 modes, prompt structure, duration, reference labels, and model-specific syntax.

## Maintenance Rules

1. Verify model syntax, duration, workflow names, reference limits, parameters, and capabilities against the official MiniMax repository and the current local `h3-prompt-writing` and `minimax-h3` skills before changing technical instructions.
2. Treat directing methods as cross-model principles, but never assume Seedance, Runway, Kling, Veo, or another model's syntax is valid for H3.
3. Preserve upstream license notices and attribution in redistributed versions.
4. Keep this skill focused on director decisions. Route final prompt syntax, job submission, image generation, music, and editing to their dedicated skills.
5. Test updates against at least one dialogue scene, one high-risk action or VFX scene, and one continuity-dependent transition before replacing the working version.
