# 配置教程：从零到能出片

整套流程的凭证分三级——**哪些必须配、哪些可以换、哪些可以不配**，一张表说清：

| 级别 | 依赖 | 不配会怎样 |
|---|---|---|
| 🔴 硬必需 | [AutoDL 账号 + 实例 + Token](#1-硬必需autodl-账号实例与-token) | 无法生成视频，AI 会停下并告诉你怎么配 |
| 🟡 默认可换 | [生图能力](#2-默认可换生图优先-agent-自带备选-cursor)（优先 Agent 自带生图） | 有自带生图就零配置；没有时 AI 会引导你登录 Cursor，或改用其他生图工具 |
| 🟢 可选增强 | [音乐生成](#3-可选增强音乐生成minimax-music-3) 与 [Qwen3-TTS 配音](#另一个可选增强qwen3-tts-配音)（同一实例同一 Token，无需新凭证） | 各自跳过；**H3 生成的视频自带音轨与对白，成片照样有声** |

配置完任何一步，都可以跑 [一键自检](#5-一键自检) 验证。

---

## 1. 硬必需：AutoDL 账号、实例与 Token

视频生成跑在 AutoDL 的 GPU 实例上的开源 MiniMax H3 模型里，没有替代路径。三样东西都要有：

### 第 0 步：注册并创建一台实例（一次性）

1. 注册 [AutoDL](https://www.autodl.com) 账号并充值（按量计费，10 秒 1080p 视频约 ¥0.3）。
2. 控制台 → 应用实例（ autodl.art ），按应用市场选择 **MINIMAX-H3** 应用，创建一台实例（如「MINIMAX-H3提速500高画质」）。
3. 完成。**实例 ID（形如 `pro-78672ec11b9c`）不需要记**——AI 会通过 Token 自动在你账号下找到它；有多台时会列出候选让你选一次。

### 第 1 步：申请开发者 Token

AutoDL 官网 → 账号 → 设置 → **开发者 Token**，创建并复制（注意：不要带 `Bearer` 前缀）。

### 第 2 步：存到本地（推荐私有文件）

```bash
mkdir -p ~/.config
echo 'export AUTODL_TOKEN=你的Token' > ~/.config/autodl.env
chmod 600 ~/.config/autodl.env
```

为什么推荐这个方式：AI 的非交互 shell 常常不加载 `~/.zshrc`，脚本会自动回退读这个文件，避免「明明配了却报缺少 Token」的坑。也可以选：ZCode 环境变量，或写入 `~/.zshrc`（然后重启 ZCode）。

### 验证

```bash
python3 skills/autodl-app-instance/scripts/autodl_app.py list
```

能列出你的实例即配置成功。

---

## 2. 默认可换：生图（优先 Agent 自带，备选 Cursor）

美术设定（人物三视图、场景、分镜参考图）与面部参考图等位图，优先用你当前 Agent 自带的生图工具或技能（如 Codex 的 ImageGen）生成，不要求安装 Cursor。

### 首选方案：Agent 自带生图

Agent 环境自带生图能力（如 Codex 的内置 ImageGen）就零配置直接用，AI 会自动选择。

### 备选方案：Cursor Agent

环境没有自带生图能力，或你明确点名要用 Cursor 生成时，由 `cursor-image-gen` 技能调用本地 Cursor Agent：

1. 安装 Cursor 并订阅，CLI 里有 `cursor-agent` 命令。
2. 登录一次：`cursor-agent login`（或设置 `CURSOR_API_KEY` 环境变量做无头认证）。
3. 验证：`node skills/cursor-image-gen/scripts/generate_with_cursor.mjs --doctor`，`logged_in: true` 即可。

无论用哪个执行器，都只需遵守两条约定：

- 图片保存到项目的 `第N集/美术设定集/` 对应子目录（或 `视频制作/分镜参考图/`）；
- 参考 `character-three-view` 的验收要点与命名约定，生成后逐图验收。

流程其余部分不变。

---

## 3. 可选增强：音乐生成（MiniMax Music 3）

**先说结论：不用任何新配置也能出片。** MiniMax H3 生成的视频自带音轨（对白、音效和 H3 自己生成的音乐）。`minimax-music-gen` 技能的作用是在此之上叠加**独立的背景音乐**（跨集复用的配乐 cue、精确卡点、对白闪避），也能按歌词生成人声演唱的完整歌曲。

音乐生成跑在**同一台** AutoDL MINIMAX-H3 实例的 ComfyUI 上（MiniMax Music 3 模型已预装在应用镜像里），**用的就是第 1 节的 `AUTODL_TOKEN`，不需要任何新账号、新 Key**。成本约每首 0.3~0.5 元 GPU 费，单首全程 2~4 分钟。

实例不可用（没配 Token / 抢不到库存 / 生成失败）时：AI 自动跳过独立配乐，交付自带音轨的母版，并明确告诉你「哪些配乐没生成、原因、后续怎么补」。

> 兼容说明：旧的 TokenHub/腾讯云音乐 API 路径（`TOKENHUB_API_KEY`、`MINIMAX_API_KEY`）已于 2026-08-31 全部移除，音乐不再需要任何专用凭证；以前配过的 env 文件可以删掉。

### 另一个可选增强：Qwen3-TTS 配音

旁白、画外音、特定声线（甜妹音、低沉旁白）或声音克隆由 `qwen3-tts` 技能完成，跑在与 H3 **同一台** AutoDL 实例上。**不需要任何新凭证**——用的就是同一个 `AUTODL_TOKEN`。唯一要求：

- 实例需预装 `ComfyUI-TD-Qwen3TTS` 节点与 Qwen3-TTS 1.7B 模型。选实例时留意镜像描述；报 `TTS_NODE_MISSING` 说明当前实例没装，换预装实例即可，不要在视频实例上临时安装。
- 不配置的效果：AI 不做独立配音，交付 H3 自带音轨（含 H3 自己生成的对白）的成片，并说明跳过原因。首次生成需加载 3.8GB 模型（约 40–60 秒），属正常等待。

---

## 4. 可选独立技能：beauty-video-gen（真人时尚单片）

`beauty-video-gen` 是短剧剧组之外的独立技能：生成超写实、真实感的真人美女时尚竖屏短视频（提示词框架 → 可选面部参考图定脸 → H3 云端生成 → 提亮滤镜 → 抽帧验收）。

- 复用第 1 节的 AutoDL 实例与 Token，无需新凭证。
- 面部参考图的生图遵循第 2 节的优先级：Agent 自带生图优先，备选 Cursor。
- 本地额外依赖：`numpy` 与 `opencv-python`（`pip3 install numpy opencv-python`，供技能自带的美肤提亮滤镜脚本使用）；`ffmpeg` / `ffprobe` 见第 5 节清单。

不装也不影响短剧全流程；需要时尚单片时直接对 AI 说「用 beauty-video-gen 生成……」即可。

---

## 5. 一键自检

```bash
bash scripts/doctor.sh          # 检查凭证与本地工具
bash scripts/doctor.sh --probe  # 额外真实探活（调 AutoDL API 列实例并探活）
```

也可以直接对 AI 说「检查一下环境配置」，它会跑这个脚本并逐项解释缺什么、怎么补。

本地工具清单（`doctor.sh` 会一并检查）：`python3`、`node`、`ffmpeg`、`ffprobe`、`expect`。macOS 可用 `brew install ffmpeg expect` 补齐。

---

## 常见报错对照

| 报错/现象 | 原因 | 解法 |
|---|---|---|
| `缺少 AUTODL_TOKEN` | Token 没配或 Agent shell 没继承 | 按 1.2 写入 `~/.config/autodl.env`；不要加 Bearer |
| `没有匹配的实例` | 账号下还没有 MINIMAX-H3 实例 | 控制台创建一台（一次性），ID 不用记 |
| `匹配到多台，请指定 --uuid` | 有多台同名实例 | 把候选表发给 AI 让用户选一次，或设 `AUTODL_INSTANCE_UUID` |
| 音乐报「当前算力规格暂无库存」 | MINIMAX-H3 实例抢不到 GPU（可选能力） | 脚本每 30s 自动重试；连续失败则跳过独立配乐，稍后补生成 |
| 音乐生成失败 / 实例连不上 | 实例没开机、模型缺失或提交被拒 | AI 跳过该 cue 并交付自带音轨母版，列明未生成清单；按 generate_music.py 的输出定位原因 |
| TTS 报 `TTS_NODE_MISSING` | 实例未预装 Qwen3TTS 节点（可选能力） | 换预装节点与模型的实例；不在视频实例上临时安装 |
| `--doctor` 报 `logged_in: false` | Cursor Agent 未登录 | `cursor-agent login` 或设 `CURSOR_API_KEY`；或改用其他生图工具 |
| 脚本能跑但 Agent 报缺 Token | 非交互 shell 不加载 `~/.zshrc` | 用 `~/.config/autodl.env` 私有文件方案 |

## 安全约定

- Key/Token 永远不进仓库、不进提示词、不进命令行参数（所有脚本只认环境变量或私有文件）。
- 私有文件权限 600：`chmod 600 ~/.config/*.env`。
- 本仓库 `.gitignore` 已挡住 `.env`、`*.token`、`*.key`，误放也会被忽略。
