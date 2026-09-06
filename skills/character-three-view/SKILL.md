---
name: character-three-view
description: >-
  Prepares reference art for video production from a script or asset list:
  character reference sheets (including outfit-state variants), prop
  references, and scene concept images, then verifies each generated image.
  Works for any project style — photoreal, anime, cartoon, fantasy creatures.
  Use when the user asks for 美术设定集, 人物三视图, 道具三视图, 场景概念图,
  角色立绘, or visual refs before video. Prefer the running agent's own image
  generation tool (e.g. Codex ImageGen); use cursor-image-gen only when no
  native image generation exists or the user explicitly requests Cursor; fall
  back to Seedream (seedream-image-gen) if blocked, filtered, or quality is
  insufficient.
---

# 美术参考图

从剧本或资产清单抽出需要锁定的形象资产（人物/形象、关键道具、主要场景），生成给后续视频当参考的设定图，逐张验收。本技能不规定每张图的版式与画法，只沉淀生图执行方式和这个环节踩过的坑。

## 出什么图

三类资产，共同目的都是给视频模型当外观与场景的锁定参考：

- **人物三视图**：把同一角色放进同一张图——常见做法是全身的正面、侧面、背面，外加一个面部特写；视频模型靠它从任意机位认出同一个人。用几个角度、怎么排布、什么背景，按项目需要定；核心是"一张图 = 一个角色的完整外观档案"。
- **道具三视图**：同一件关键道具的多个视角（大件可改用关闭/半开/打开等多个状态）放进同一张图，让道具在生成视频里保持同一外观。
- **场景概念图**：主要地点的单幅环境图，只画场景、不进主要角色（原因见坑 4）。

参考图画幅建议与成片一致（竖屏剧的场景图就用竖幅），避免模型从参考图学到错误构图；用户或项目已有样例图时，版式跟样例走。

## 生图工具

不绑定唯一 API。用户点名生图工具时以点名为准（点名 Cursor 即用 `cursor-image-gen`）；未点名时按默认顺序：

1. **当前 Agent 自带的生图能力（首选）**：环境自带生图工具或技能（如 Codex 的 ImageGen）就直接用；有样例或已有图就把图作为参考图传给生图工具。
2. **`cursor-image-gen`（备选）**：环境没有自带生图能力时，读 [`cursor-image-gen`](../cursor-image-gen/SKILL.md) 生成，可用 `reference_image_paths`。
3. **Seedream（兜底）**：默认执行器被拦截、拒生、重试后仍不合格，或需要精确像素/多张本地参考图时，读 `~/.cursor/skills/seedream-image-gen/SKILL.md` 再生成。

生成后把文件放进设定集目录（如 `美术设定集/{人物三视图, 道具三视图, 场景概念图}/`），统一按 `NN_名称.jpg` 命名。

## 踩过的坑

1. **参考图质感会被视频模型继承进成片**。动手前先从用户需求或 Brief 确认项目质感——写实、动漫、Q 版、幻想生物都可以——所有参考图与目标质感保持一致，不要混风格。
2. **写实项目的附加要求**（仅当用户要求真人写实）：参考图必须实拍质感、自然哑光皮肤、可见毛孔与真实纹理；出现 CG/3D 渲染感、油光、蜡质磨皮即不合格。修法：拿当前图当参考，加 `ultra-realistic photographic skin, matte, visible pores, no retouching` 一类指令重生成。
3. **不做表情参考图**：表情图经常与人物参考图一起被送进视频模型，同一角色多张形象参考叠加，容易产生人物重影、分身；表情与表演变化由视频提示词驱动。用户明确索要时，先说明风险再按其要求执行，且绝不与人物参考图同时作为同一角色的参考图使用。
4. **场景概念图不进主要角色**：主要形象只由人物参考图锁定，场景图里再出现会被视频模型当成同一角色的第二个形象参考，引发重影，也削弱场景锁定。与剧情无关的背景群众可留。
5. **参考图用于锁形象、锁场景、锁道具，不是逐镜关键帧**；动作、表演、运镜交给视频提示词。
6. **同一角色每个不同的装扮状态各出一张参考图**，否则视频会把不同状态的穿着混起来。画装扮变体时拿该角色的基准参考图当参考，写明「与参考图同一张脸、同一体型，仅更换装扮」，装扮描述写死互斥项（如基准「头盔拿在手中」、变体「头盔已戴上、双手空」），防止画串。
7. **改图采纳后旧图改名 `NN_名称_v旧版.jpg` 保留，新图沿用原名**，避免下游引用失效。

## 工作流

1. 从剧本抽出人物（含每个角色的装扮状态清单）、关键道具、主要场景，形成资产清单。
2. 先出主要形象的基准参考；其余资产和装扮变体可拿已验收的基准图当参考并行生成。
3. 逐张生成、逐张验收：用 Read 打开图，对照资产清单核对形象特征、装扮、质感与风格一致性。不合格改提示词重生成，最多 2 次；仍不行就拿当前图当参考修一版。
4. 交付时列出各目录的文件清单，不报任何生图 API 的 token。
