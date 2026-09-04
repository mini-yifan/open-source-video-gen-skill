---
name: minimax-h3
description: >-
  Use a remote SeetaCloud or AutoDL ComfyUI GPU instance to generate MiniMax H3
  videos. Connects over SSH, discovers the current H3 workflows, helps choose
  U03/U06/U02, uploads references, submits a job, and downloads the result.
  MiniMax H3 supports 5–15 seconds per generation; choose the duration from the
  user's request and the scene instead of assuming a fixed default. Use when the
  user asks for MiniMax H3, ComfyUI, SeetaCloud, AutoDL video generation,
  text-to-video, image-to-video, or reference-guided video. When the target is
  an AutoDL application instance, use autodl-app-instance as the lifecycle
  wrapper: boot once before an H3 batch and power off after all jobs finish.
---

# MiniMax H3：云端视频生成

本技能负责使用远程 GPU 上的 MiniMax H3 / ComfyUI 生成视频。它提供连接、工作流发现、参数选择、素材上传、任务提交、轮询和下载能力，不替用户做不必要的导演决策。

MiniMax H3 单次生成时长为 **5–15 秒**。如果用户指定时长，严格使用用户的时长；如果用户没有指定，Agent 根据动作数量、对白长度、节奏和目标用途自行选择一个 5–15 秒的时长，并在提交前说明选择结果。不要因为技能示例、脚本默认值或过去的任务而固定使用 10 秒或 15 秒。

## 分工

- 本技能：连接云端机器、发现当前工作流、选择生成路径、准备上传、提交任务、轮询和下载。
- [`h3-prompt-writing`](../h3-prompt-writing/SKILL.md)：编写 H3 提示词正文。本技能只整理 brief，不在这里发明提示词格式。
- [`autodl-app-instance`](../autodl-app-instance/SKILL.md)：当用户使用 AutoDL 应用实例且没有提供 SSH 时，负责开机、等待可用和关机。

不要把 SSH 密码、AutoDL Token 或其他凭据写入仓库、提示词或技能文件。

## AutoDL 组合模式（批次开始开机，批次结束关机）

当目标是 AutoDL 应用实例，或用户明确要求“开机后生成、全部完成后关机”时，本技能必须先调用 `autodl-app-instance` 的 `boot`，再进行任何 H3 连接、上传或提交。一个用户请求中包含多个视频时，把它们视为一个 H3 批次；只有 `boot` 返回实例已 running、`COMFY_READY` 且队列可访问后，才能进入 H3 流程。

组合模式的生命周期由 AutoDL 技能管理：

1. 在批次开始前解析并记录实例 UUID，建立本批次的 job 清单。
2. 每个批次只执行一次 `boot`；捕获最新 `SEETACLOUD_BASE_URL`，在当前执行环境中显式设置。子进程里的 `export` 不会自动传回父进程。
3. 在同一个生命周期内完成全部 H3 job 的 brief、提示词、上传、提交、轮询、下载与落盘秒级校验。单个视频使用一次 submit/poll 脚本，不代表要重新 boot。归一化、抽帧验收、滤镜、调参重跑等本地后处理放到关机之后，不得因此推迟关机。
4. 跟踪每个 job 的状态：`pending`、`running`、`succeeded`、`failed` 或 `cancelled`。重试和用户在关机前追加的视频仍属于同一个批次。
5. 所有计划 job 都进入终态、结果已下载（并通过落盘秒级校验）或明确记录失败，且没有仍在运行的 H3 任务时，**立即**执行一次 `autodl_app.py off --uuid <uuid> --wait`；不要为归一化/验收/滤镜等本地后处理推迟关机。
6. 用 `try/finally` 包住整个批次：批次成功、部分失败、超时、轮询异常或用户中断，都执行清理。只有用户明确说“保持开机/别关机”，或设置 `AUTODL_KEEP_ON=1` 时，才跳过 `off`。

如果用户只给了一个不受 AutoDL API 管理的 SSH 服务器，不要擅自调用 AutoDL 开关机；此时直接走 SSH 模式。

不要在单个视频的完成分支里调用 AutoDL `off`。AutoDL 关机只能由父批次的最终清理分支触发。

## 最快链路（2026-08-27 实测定型，照此执行）

实例按秒计费。以下链路已用秒表实测：自身开销 ~15s，其余全是 GPU 推理。**核心效率原则：先把队列填满，GPU 绝不空转；等待窗口只用来做本地活；终态即关机。**

```bash
# 0) Token：推荐写 ~/.config/autodl.env（脚本自动回退读取，无需 source）；
#    若只写在 ~/.zshrc，非交互 shell 常不加载——先 source
[ -f ~/.config/autodl.env ] || source ~/.zshrc

# 1) 开机（整个批次只此一次）：三态探活，warm 发现实测 5.8s；冷开机一般 <1min ready
python3 ~/.zcode/skills/autodl-app-instance/scripts/autodl_app.py boot --uuid <UUID>
#   → 记下输出里的 export SEETACLOUD_BASE_URL=...，后续每条命令都带上

# 2) 工作流发现（换实例必做，3s）：自动选流 + 推导全部槽位键 → slot_map.json
export SEETACLOUD_BASE_URL=<面板地址>
python3 scripts/discover_workflow.py --kind u06 --out slot_map.json

# 3) 批量提交——不要生成一条等一条！逐条提交把队列填满（每条含上传 ~1s/图）
python3 scripts/submit_video.py --prompt NN.txt --slot-map slot_map.json \
  --seconds <5-15> --width 1280 --height 720 --preset speed \
  --image 参考图1.png --image 参考图2.png --out-json NN_task.json   # × N 条

# 4) 并发轮询下载（history 优先 + 队列守卫；多任务用线程池并发 poll）
python3 scripts/poll_video.py <prompt_id> --download NN.mp4
# 生成 5s 片实测 ~112s/条（服务端推理，不可压缩）；等待窗口去做本地活
#（音乐复用、素材校验、归一化脚本准备），别干等

# 5) 下载落盘即 ffprobe 秒级校验（时长/分辨率/音轨）→ 同批次全部通过立即关机
#    （唯一例外：用户说保持开机 / AUTODL_KEEP_ON=1）
python3 ~/.zcode/skills/autodl-app-instance/scripts/autodl_app.py off --uuid <UUID> --wait

# 6) 关机后的本地活：归一化（H3 输出 17 帧块取整 + 32 对齐，如 720→704、5.0→5.17s）、
#    交付前 scale/pad 到目标分辨率、裁齐槽长、统一帧率，以及抽帧验收、滤镜、调参重跑——
#    全程零 GPU 占用，绝不为了做这些拖着不关机
```

**四条铁律（违反任意一条都会浪费时间或钱）：**
1. **不沿用旧键位**——工作流/节点键每台实例都不同，必须用 slot_map（见下）；
2. **不留空槽**——包括用不到的音频槽，空槽会读到服务器模板素材（如 `p2.MP3`）污染生成；
3. **不取运行中任务的 result 接口**——只认 history；且固定种子下同提示词+同图会生成逐字节相同的视频，重提前必须改提示词或参考图。
4. **下载完就关机**——落盘文件过 `ffprobe` 秒级校验即 `off`，归一化/验收/滤镜/调参全是本地活，放到关机后做（GPU 空转照常计费，晚关一分钟多烧一分钟）；验收不达标要重生成就先改提示词/参考图再重新开机，重开成本远低于空转。

换新实例/新工作流首次使用时，先按 `reference.md` 的"单参考图最小验证流程"跑一次 5 秒冒烟再上批量。

## 任意实例通用流程（细节与原理）

不同实例上的工作流名字和节点键**几乎必然不同**（同一用户先后遇到过 `U06-…优化版X` 与 `U06-9图3音频-V5`，提示词/秒数/步数/LoRA/音视频槽的节点号完全不一样）。因此提交前必须做槽位发现，禁止沿用上一次任务的节点键：

1. **发现**：`python3 scripts/discover_workflow.py --out slot_map.json`（可用 `--kind u06/u03`、`--workflow-id` 收窄）。它会拉取本机工作流列表，按能力分（图槽数、采样器、提示词节点、秒数节点）+ 运行次数自动选出最合适的工作流，并从 workflow JSON 推导出 `image_keys / video_keys / audio_keys / prompt_key / seconds_key / steps_key / size_keys / lora_keys`。
2. **提交**：`submit_video.py --slot-map slot_map.json …`；不加 `--slot-map` 时脚本也会**自动发现**（`--no-auto-discover` 可关闭），自动发现失败才回退到内置键位。
3. **占位纪律**：所有媒体槽（包括本次用不到的音频/视频槽）必须填占位文件（暗帧/1s 黑场/1s 静音）。部分实例的 `LoadAudio` 默认指向服务器上的模板文件（如 `p2.MP3`），不占位就会当作参考音频灌进生成，污染画面与声音。
4. **轮询纪律**：`poll_video.py` 以 **history** 为唯一可信结果来源；任务还在队列里时绝不调 `/api/workflow/result`——部分部署对运行中的 prompt 会返回"最近一个已完成任务"的旧结果，导致重提后下载到旧视频。重新提交任务后，等队列空闲再收文件。
5. **输出量化**：H3 时长按 17 帧块取整、宽高对齐 32（如请求 720 实得 704）。交付前必须本地归一化（缩放/补边到目标分辨率、裁齐槽长、统一帧率）。
6. **Token**：脚本报缺少 `AUTODL_TOKEN` 时，先确认 `~/.config/autodl.env` 是否存在（推荐存储方式，脚本自动回退读取）；仍缺则向用户转达申请与存储指引（autodl.com → 账号 → 设置 → 开发者 Token），`source ~/.zshrc` / `zsh -ic` 只作兜底。
7. **冒烟测试**：新实例/新工作流首次正式生成前，先跑一次"单参考图 → 5 秒视频"最小验证（提示词用 Ref2VA 单 `Picture 1`，一张人设图即可）；全链路（发现→提交→轮询→下载→ffprobe 核时长分辨率）通过后再上批量。完整命令见 `reference.md` 的"单参考图最小验证流程"。

## 基本流程

### 1. 连接并发现当前机器

先判断运行模式：

- **AutoDL 生命周期模式**：目标是 AutoDL 应用实例，或用户要求自动开关机。先执行 AutoDL `boot`，记录 UUID 和新的面板地址，再打开本技能的 H3 流程。
- **直接 SSH 模式**：用户只提供普通远程 GPU 服务器的 SSH 信息。直接连接，不执行 AutoDL power_on/power_off。

用户提供 SSH 主机、端口、用户名和密码时，使用当前技能目录下的 `scripts/connect_server.py` 连接服务器，并从服务器发现面板地址、GPU 和工作流。

如果使用 AutoDL 生命周期模式，先使用 `autodl-app-instance` 的 `boot`，得到 `SEETACLOUD_BASE_URL` 后再继续；不要使用旧的面板地址、SSH 端口或密码。

每次换服务器都重新查询：

- `GET /api/workflow/list`
- `GET /api/comfy/status`
- `GET /api/comfy/queue-status`

以当前机器返回的 workflow id 为准，不沿用旧机器的域名或 workflow id。提交前应确认 ComfyUI 已 ready；队列不可访问时先排查服务状态，不要盲目提交。

### 2. 根据素材和目标选择工作流

| 目标 | 常用工作流 | 说明 |
|---|---|---|
| 纯文字生成 | U03 | 没有必须锁定的参考图 |
| 多图参考生成 | U06 / U06-X | 人物、场景、道具或风格参考 |
| 从首帧到尾帧 | U02 | 第一张图和最后一张图定义变化起点与终点 |

提示词模式由实际输入决定：T2VA、Ref2VA、I2VA、FL2VA 或 L2VA。人物三视图通常是身份参考，不自动等于视频第 0 秒；只有用户明确要求 Picture 1 作为第一帧时，才使用 I2VA 逻辑。

不要为了套用某种模式强行改变用户的素材用途，也不要把多个短镜头机械拼成一条视频。是否切镜、是否一镜到底、镜头数量和动作密度，都交给用户意图和提示词决定。

### 3. 自由选择时长和生成参数

提交前必须明确传入一个 `5–15` 秒的 `--seconds` 值，不要依赖 `submit_video.py` 当前的脚本默认值。时长选择可以参考：

- 单一动作、短反应或通路测试：可以选择较短时长。
- 多个动作、较长对白或需要完整起承转合：可以选择较长时长。
- 用户指定的时长优先级最高。

分辨率、画幅、帧率、是否插帧、LoRA、采样步数和加速组件，根据用户目标、当前机器能力和工作流实际节点选择。不要默认强制使用某个画幅、某个分辨率、speed 档、Turbo LoRA、RIFE 或固定切镜方式。

**用户长期默认（2026-09-04 三轮实拍对比后确认，用户明示"以后人物就按这样生成"）**：含人物的镜头一律用 **speed 档（Turbo 4 步 LoRA）+ 1920×1088 原生分辨率**（10s 约 7.3 分钟/5090）。配合 `h3-prompt-writing` 的皮肤锁/高光锁句式即可实现不油腻写实质感；turbo 本身不是油腻来源。用户点名要更高细节时才升级为 12 步无 LoRA 720p + 服务器 OmniSR X2 超分（约 8.8 分钟，超分脚本见项目《去油腻实验/新参考图测试/服务器超分_omnisr.sh》）；草稿预览可用 1280×720 + turbo（约 4 分钟）。

**工作流避坑**：不要用 `U03-minimax_h3_基础版` 类 res_multistep 采样器的工作流跑高步数——实测 24 步在 int8 量化模型上满画面 speckle 噪点。U03 选 light2v（euler），U06 选 euler 采样器的版本（如 `U06-9图版API-V5`）。另：同实例同工作流的 slot map 可复用，但每次换实例必须重新 discover；U03 基础版工作流的秒数节点（PrimitiveFloat）discover 会漏，需手工补 `seconds_key`。

如果使用 Turbo LoRA，采样步数必须与该 LoRA 的适用步数相匹配；这是技术兼容性要求，不是创作上的默认画质选择。具体节点和文件名以当前机器的 workflow JSON 与模型目录为准。

### 4. 整理 brief 并交给提示词技能

brief 至少包含：

```text
H3 prompt brief:
- workflow: U03 | U06 | U02
- prompt_mode: T2VA | Ref2VA | I2VA | FL2VA | L2VA
- duration_seconds: <chosen value from 5 to 15>
- aspect: <user choice or agent choice>
- resolution: <user choice or agent choice>
- pictures: <only the references that matter, with their intended roles>
- video_slots: <only when needed>
- audio_slots: <only when needed>
- dialogue: <original-language dialogue or none>
- cuts: <only if the user or creative intent requires it>
- constraints: <only user-requested or technically necessary constraints>
- creative: <what should happen>
```

把 brief 交给 `h3-prompt-writing` 生成 `prompt.txt`。不要在本技能里添加固定的 `Core idea:`、`Camera:` 等自创标签，也不要因为模板示例擅自增加镜头数量、对白或视觉禁令。

### 5. 上传必要素材并提交

只上传对当前生成有作用的参考图片、视频或音频。U06 类工作流的槽位数量以当前 workflow JSON 为准；不要为了填满槽位复制素材，也不要凭空添加参考内容。

如果工作流会读取未使用的默认素材，使用当前技能的占位资源填充空槽，避免模板素材污染结果或造成额外显存占用。U03 通常不需要上传参考槽位。

提交命令的结构如下，`<chosen_seconds>` 必须替换成 Agent 选择的 5–15 秒数值：

```bash
python3 <skill-dir>/scripts/submit_video.py \
  --preset <chosen-preset> \
  --seconds <chosen_seconds> \
  --width <chosen-width> --height <chosen-height> \
  --prompt prompt.txt \
  [--workflow u03] [--image-dir ./refs] \
  --out-json task_info.json
```

随后使用 `poll_video.py` 轮询并下载 MP4。任务提交、轮询和下载过程中不要把密码打印到日志中。

### 6. 做基本结果检查

确认结果确实是视频，并检查实际时长、分辨率、帧率、音轨和文件完整性。`pending:false` 且结果为空不代表成功；必要时读取 ComfyUI history 查看执行错误。

如果画面效果不好，根据实际问题调整提示词、参考素材、时长、工作流或参数后再试。不要套用固定的“必须几镜、必须几张图、必须某个速度档”的补救规则，也不要在失败结果上盲目叠加滤镜。

### 7. 批次结束并释放 AutoDL GPU

如果本次任务使用了 AutoDL 生命周期模式，只有全部 H3 job 结束后才能回到 `autodl-app-instance` 执行关机。把 UUID 和 job 状态保存在父批次上下文中，不要依赖重新匹配应用名；确认没有任务仍在运行后执行 `off --wait`，并等待实例进入 `shutdown`。清理动作必须放在整个批次的 finally/退出路径中。

## 重要边界

- H3 的可选生成时长是 5–15 秒，不代表每次默认 10 秒或 15 秒。
- 用户没有指定时长时，由 Agent 根据内容自行判断，并明确告诉用户实际选择的时长。
- 用户指定的画幅、分辨率、时长、镜头方式和创作风格优先于本技能的任何示例。
- 当前服务器的工作流列表和 workflow JSON 优先于旧文档中的固定 id、节点编号和参数名。
- `reference.md` 只在排查槽位、API、LoRA、显存或 OOM 等技术问题时读取；`examples.md` 只用于 brief 结构不清楚时参考。
