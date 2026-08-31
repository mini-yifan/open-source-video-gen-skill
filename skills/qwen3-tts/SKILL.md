---
name: qwen3-tts
description: >-
  用 AutoDL GPU 实例上的 Qwen3-TTS 生成配音语音（TTS）。当用户需要旁白、画外音、
  配音、台词朗读、文字转语音、特定声线（如甜妹音、大叔音、御姐音）、克隆某个人的
  声音，或为 MiniMax H3 视频补对白/旁白音轨时使用。触发词包括：TTS、配音、旁白、
  语音合成、文字转语音、音色、声线、克隆声音、voiceover、text-to-speech。
  三种音色控制：文字描述设计音色（VoiceDesign）、9 种内置音色+风格指令
  （CustomVoice）、参考音频克隆（VoiceClone）。不要用于生成歌曲或背景音乐
  （那用 minimax-music-gen）；不生成本地已有音频的转码或播放。
---

# Qwen3-TTS 语音生成

在 AutoDL 应用实例（与 MiniMax H3 视频同一台机器）上，通过 ComfyUI 的
`ComfyUI-TD-Qwen3TTS` 节点调用 Qwen3-TTS（1.7B，24kHz 单声道）生成语音。
一条命令完成：构建工作流 → SSH 提交 → 轮询 → 下载落盘 → ffprobe 校验。

## 三种音色模式

| 模式 | 参数 | 适用 | 模型 |
|---|---|---|---|
| **VoiceDesign**（默认首选） | `--voice-design "音色描述"` | 任意想象得到的声线：甜妹音、御姐音、低沉男声、少年音、机器人音……用一句话描述说话人+语气 | VoiceDesign |
| **CustomVoice** | `--speaker Serena --instruct "风格指令"` | 要稳定复用一个固定音色时；内置 Aiden/Dylan/Eric/Ono_anna/Ryan/Serena/Sohee/Uncle_fu/Vivian，instruct 可微调语气 | CustomVoice |
| **VoiceClone** | `--clone 参考音频 --ref-text "参考音频说的话"` | 克隆指定人声；ref_text 必须是参考音频里实际说的内容，实在没有才加 `--x-vector-only`（相似度下降） | Base |

用户说「随便来个甜妹声」这类模糊需求时直接用 VoiceDesign，把声线特征翻译成
描述（年龄段+性别+音色质感+语气+语速），不要追问。

## 用法

实例生命周期由 `autodl-app-instance` 管理：先 `boot`，再跑本脚本，全部结束后 `off --wait`。
本脚本不开关机。Token 读取规则与 `autodl_app.py` 相同：环境变量，缺时自动回退读
`~/.config/autodl.env` 私有文件。

```bash
SCRIPT="$HOME/.zcode/skills/qwen3-tts/scripts/generate_tts.py"

# 1) 文字设计音色：甜妹声 5 秒旁白
python3 "$SCRIPT" --uuid <UUID> \
  --text "哈喽～今天也要开开心心的哦，我们一起加油吧！" \
  --voice-design "一个二十岁左右的年轻女性声音，甜美软萌，音色清亮可爱，语气活泼俏皮" \
  --out 旁白01.flac

# 2) 内置音色 + 风格指令
python3 "$SCRIPT" --uuid <UUID> \
  --text "欢迎回到本频道。" \
  --speaker Serena --instruct "沉稳大气，语速适中" \
  --out 开场白.flac

# 3) 克隆参考音频的音色
python3 "$SCRIPT" --uuid <UUID> \
  --text "这段台词用她的声音读出来。" \
  --clone 参考音频.flac --ref-text "参考音频里实际说的话" \
  --out 克隆台词.flac
```

其他参数：`--language`（默认 Auto）、`--timeout`（轮询超时，默认 900s）、
`--prefix`（服务器端文件前缀）。

## 与 MiniMax H3 视频批次配合

1. **共用同一批次生命周期**：H3 视频批次已 `boot` 的实例直接跑 TTS，绝不单独开关机；
   视频 job 轮询等待窗口正是跑 TTS 的时机。批次终态仍由 `autodl-app-instance` 统一 `off`。
2. **TTS 音频进 H3 音频槽**时走 `minimax-h3` 的槽位纪律：不留空槽、占位文件垫其他音频槽，
   防止服务器模板音频（如 `p2.MP3`）污染生成。
3. **只做后期配音**（不进 H3 生成）时，把 TTS 文件混入成片音轨属于关机后的本地活。
4. H3 自带对白能力。用户没有明确要旁白/替换声线时，不要默认给每段视频配 TTS。

## 时长与文本

- 中文语速约 4–5 字/秒：5 秒 ≈ 20–25 字。按目标时长控制台词字数。
- 想要「～」「～啦」「么么哒」这类软萌语气，直接写进文本，模型会带出来。
- 输出为 24kHz 单声道 FLAC。要 mp3/wav 时本机用 ffmpeg 转（脚本 `--out x.mp3` 会自动转，
  无 ffmpeg 时保留 FLAC 并提示）。

## 硬规则

1. 首次生成要加载 3.8GB 模型（约 40–60s），同模型连续生成每次仅十几秒；不要因为第一次慢就中断重试。
2. `--ref-text` 与参考音频内容不符会显著降低克隆质量；`--x-vector-only` 是兜底不是捷径。
3. SSH 密码只经环境变量注入 expect，Token、密码不写入任何文件、提示词或日志。
4. 脚本会自动检查实例是否安装了 `TDQwen3TTSModelLoader` 节点；报 `TTS_NODE_MISSING` 时
   换预装节点与模型的实例，不要试图在视频实例上临时装节点。
5. 下载后脚本自动校验 FLAC 头与大小；最终交付前用 ffprobe 确认时长。

## 依赖缺失处理

| 缺失 | 动作 |
|---|---|
| `AUTODL_TOKEN` | 按 `autodl_app.py` 报错转达申请与存储指引（`~/.config/autodl.env`），不启动生成 |
| 实例无 Qwen3TTS 节点/模型 | 阻断并说明需要预装节点与三个 1.7B 模型的实例；不在用户实例上临时改装 |
| `expect` 缺失 | macOS 自带；Linux 提示 `apt install expect` |
| 克隆缺 ref_text 且拒绝 x-vector-only | 向用户要参考音频的文字内容，不要静默降级 |

在 `short-drama-production` 管线内：TTS 配音是可选增强（H3 视频自带音轨与对白）。
失败时按上表说明原因，交付自带音轨的母版并把配音阶段标记待更新，不伪装完成。
