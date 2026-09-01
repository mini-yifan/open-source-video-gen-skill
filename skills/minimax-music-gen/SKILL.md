---
name: minimax-music-gen
description: >
  用 AutoDL GPU 实例上的 MiniMax Music 3（ComfyUI）生成音乐：人声演唱的完整歌曲
  （自定义歌词、女声/男声、任意曲风）或纯音乐 BGM（instrumental）。Use when user wants
  to generate music, songs, or audio tracks — 生成音乐、写歌、把歌词变成歌曲、生成背景音乐/
  配乐/纯音乐、来首歌、MiniMax Music、BGM、伴奏、情歌 all trigger; match equivalent
  phrases in any language. Do NOT use for music playback of existing files, music theory
  questions, or recommendations without generation.
license: MIT
metadata:
  version: "3.0"
  category: creative
  backend: autodl-comfyui-minimax-music3
---

# Skill: minimax-music-gen
# MiniMax Music 3 × AutoDL 实例 音乐生成

在 AutoDL 应用实例的 ComfyUI 里跑 **MiniMax Music 3**（DiT + 专属 text encoder + DAV VAE），
一键完成 **开机 → 提交 → 轮询 → scp 下载 → ffprobe 校验 → 关机**。单首曲目全程约 2~4 分钟。

- 开关机/SSH 通道来自 [`autodl-app-instance`](../../autodl-app-instance/SKILL.md) 与
  minimax-h3 技能的 `connect_server.py`，本技能只管音乐生成。
- 视频生成走 [`minimax-h3`](../../minimax-h3/SKILL.md)，两者共用同一实例批次时遵循
  autodl-app-instance 的批次契约：**整批只开一次机、全部完成后只关一次机**。

## 前置条件

| 依赖 | 说明 |
|---|---|
| `AUTODL_TOKEN` | autodl.com → 设置 → 开发者 Token。脚本自动读环境变量或 `~/.config/autodl.env`，缺 Token 时向用户转述脚本的申请指引 |
| 实例 | MINIMAX-H3 应用镜像自带全部音乐模型。已验证可用：`pro-7880531ea6b3`（RTX 5090，2.88 元/小时）。**账号下有多台同名 MINIMAX-H3 实例，必须用 `--uuid` 或 `AUTODL_INSTANCE_UUID` 显式指定**；都不给时脚本会列出候选让你选 |
| 本机工具 | `expect`（macOS 自带，scp/SSH 密码通道必需）、可选 `ffprobe`（时长校验）、可选 `afplay`/`mpv`（播放） |

实例上的模型（缺失说明镜像不对，不要现下载大文件，直接换实例）：
`diffusion_models/minimax_music3/`（DiT 三精度）、`text_encoders/minimax_music3_text_encoder_bf16.safetensors`、
`vae/minimax_music3_dav.safetensors`。

## 生成一条音乐（核心命令）

```bash
python3 "$ZCODE_HOME/.zcode/skills/minimax-music-gen/scripts/generate_music.py" \
  --uuid pro-7880531ea6b3 \
  --caption "<英文三段式曲风描述，见 references/prompt_guide.md>" \
  --lyrics "<中文歌词，含 [verse]/[chorus]/[bridge]/[outro] 标记>" \
  --duration 180 \
  --slug "女声情歌" \
  --out "/绝对路径/成品.mp3"          # 可省，默认 ~/Music/minimax-gen/时间戳_slug.mp3
```

- **人声歌**：给 `--lyrics`（可中文）。**纯音乐**：不给 `--lyrics`（caption 里写明 "No vocals"）。
- `--duration` 是 max_duration **上限**，模型可能提前收尾——时长控制经验见下节。
- 脚本自动处理：无库存开机重试（每 30s 一次，默认 6 次）、提交、每 10s 轮询、scp 回传、
  ffprobe 校验、**成功后立即关机**（`--keep-on` 跳过关机，用于同批次连做多首；
  环境变量 `AUTODL_KEEP_ON=1` 等效）。
- 输出关键行：`SAVED: <路径> <字节>`、`DURATION: <秒>`、`终态 success，耗时 <秒>s`——
  这些就是要转述给用户的交付信息。

## 交互流程

1. **判断类型**：人声歌（有/无歌词都行）还是纯音乐；casual 一句话就直接按 Basic 生成，
   不必追问。
2. **预览再生成**（除非用户催促直接出）：用用户语言展示——类型、曲风描述（本地化转述，
   英文 caption 是内部实现不用贴原文）、歌词全文、目标时长。用户确认或改完再跑。
3. **歌词创作**（用户没给歌词时）：默认用用户的语言写原创歌词。段落标记
   `[intro] [verse] [chorus] [bridge] [outro]`；主歌每段 4 行、每行 7~12 字、
   押韵（中文常用 an/ang/iu 等宽韵）；副歌重复但有变化。更多模板与完整示例 →
   [references/prompt_guide.md](references/prompt_guide.md)。
4. **生成**：跑上面的命令。长歌词用 `--lyrics-file`，长 caption 用 `--caption-file`。
5. **播放 + 交付**：`afplay <路径>`（macOS）后台播放，报告绝对路径和实测时长。
6. **反馈迭代**：满意即收工；不满意按用户意见改歌词/改 caption/换 seed 重跑，旧文件加
   `_v1` 后缀保留对比。每首都是独立生成，旧版不会自动覆盖。

## 时长控制与耗时（RTX 5090 实测，2026-08-31）

`max_duration` 是**上限不是保证**：模型按内容密度自己决定实际长度，实测给 30s 上限 +
稀疏编排只出了 15s。控制手段是把 caption 的 `### Arrangement` 按**小节规划写满**
（明确 Bar 1-2 / Bar 3-5 … 的段落与内容，并写 "finishing cleanly at exactly N seconds.
Do not end before N seconds"）——实测同一 30s 目标从 15s 提到 27.6s。

| 目标时长 | 实测成品 | 合成耗时（提交→完成） |
|---|---|---|
| 30s 纯音乐 | 15.1s / 27.6s | 65.8s / 77.1s |
| 3min 女声情歌（上限 210s） | 2 分 03 秒 | 约 150s |

粗略估算：**合成时间 ≈ 成品时长 × 1.2 + 首任务 30~60s 模型加载**；开机到可提交 <1 分钟
（遇到"当前算力规格暂无库存"由脚本自动重试）。每首成本约 0.3~0.5 元 GPU 费。

## 硬规则（踩过的坑）

1. **保存节点必须用 `SaveAudioMP3`**。不要用工作流 UI 里的 `SaveAudioAdvanced`——它的
   `COMFY_DYNAMICCOMBO_V3` 格式参数经 `/prompt` API 提交会丢 `format`，报
   `TypeError: missing 1 required positional argument: 'format'`（采样结果会白算）。
2. **成品用 scp 拉回**（脚本已内置）。不要用 `base64 | cat` 走 expect SSH 通道——
   大文件会被 expect 缓冲截断导致 base64 解码失败。远端路径含 `audio/` 子目录
   （`/root/ComfyUI/output/audio/<file>`），路径写错会得到 0 字节文件。
3. **批次结束必须关机**（GPU 按秒计费）。多首连做：中间曲目 `--keep-on`，最后一首不加；
   任何失败路径也要走 try/finally 关机，除非用户明确要求保持开机。
4. **不要打印** `AUTODL_TOKEN` / SSH 密码；**不要调** `release` 接口（那是释放实例）。
5. ComfyUI 在实例内 `127.0.0.1:6006`；外网 8443 面板域名不透传 API。提交/轮询都走 SSH
   内网 curl。
6. 采样节点有 ComfyUI 缓存：只改保存节点重提，秒级出结果，不会重算采样。

## 故障排查

| 现象 | 处理 |
|---|---|
| `当前算力规格暂无库存` | 脚本已自动每 30s 重试；连续失败告知用户稍后再跑 |
| 提交被拒（无 prompt_id） | 看返回 JSON：节点参数名不符或模型文件缺失；对照脚本里 build_prompt 的参数 |
| `execution_error` | 读 history 里的 node_type 与 exception_message 定位节点 |
| 成品 0 字节 / scp 失败 | 远端路径少了 `audio/` 子目录，或实例 SSH 端口已变（重取 snapshot） |
| 时长远短于预期 | Arrangement 按小节写满 + 显式 "exactly N seconds"，重生成 |
| 想要的音色/曲风不像 | caption 的 Vocal Details 写具体（性别、音区、气声、副歌处理），换 seed 再试 |

## 视频流水线内的跳过策略

本技能在视频生产流水线（如 short-drama-production）中是**可选增强**：H3 视频自带音轨。
实例不可用（无 Token / 抢不到库存 / 生成失败）时不要阻塞交付，明确告知用户哪几段音乐
未生成、原因是什么，后续补配即可。旧的 TokenHub/腾讯云 API 路径（含其 402/429 错误码表）
已于 2026-08-31 全部移除，不要再用。
