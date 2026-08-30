# MiniMax H3：槽位、加速件、API、耗时

标准作业见 [SKILL.md](SKILL.md)。交接 brief 见 [examples.md](examples.md)。提示词正文由 [`h3-prompt-writing`](../h3-prompt-writing/SKILL.md) 写，Comfy 补丁见 [`../h3-prompt-writing/references/comfy-handoff.md`](../h3-prompt-writing/references/comfy-handoff.md)。

## 发现面板

SSH 上去读：

```text
/root/面板地址.txt
```

形如 `https://<user>-<instance>.<region>.seetacloud.com:8443`。SSH 主机是 `connect.<region>.seetacloud.com`，region 必须和面板一致（westd / weste 等）。

也可拼：实例名常是 `autodl-pro-<instance>`，面板 host 含同一 instance id。

## 工作流（以 list 为准）

| 用途 | 典型 id |
|---|---|
| 多图参考 + 加速 + RIFE 60fps | `U06-minimax_h3_light2v多图参考生视频叠加加速插帧优化版X` |
| 文生、无参考、24fps | `U03-minimax_h3_light2v-文生视频加速版` |
| 首尾帧 | `U02-minimax_h3_light2v首尾帧图生视频加速版` |

`GET /workflows/<id>.json` 拿 API 图。U06-X 约 50 节点；U03 约 22 节点（无 LoadImage / VHS_LoadVideo / LoadAudio / RIFE）。

U06-X 加速链（已在图里）：

```text
UNET INT8 → PatchSageAttentionKJ → MemEff Sage
  → SpectrumApplyMiniMaxH3 → FirstBlockCache → LightX2V Turbo LoRA
  → Sampler → VAEDecode → RIFE 24→60 → CreateVideo → SaveVideo
```

提交时仍要 **改 steps 和 lora_name**，否则可能停在图里默认的 12 步。

## U06 input_values

| key | 含义 |
|---|---|
| `137/139/144/151/653/654/655/656/657:image` | 参考图 ×**9**，顺序 = Picture 1…9；空槽用与输出同尺寸暗帧（盖掉模板里的 Untitled.jpg） |
| `638/659/660:video` | 运镜/动作参考；空则 1s 黑场 |
| `143/661/662:audio` | 音频参考；空则 1s 静音 |
| `664:prompt` | 提示词全文 |
| `124:steps` | 采样步数（必须对上 LoRA） |
| `132:value` | 时长秒 |
| `665:自定义宽` / `665:自定义高` | 分辨率 |
| `669:lora_name` / `669:strength_model` | Turbo LoRA |
| `676:mode` / `676:threshold` / `676:max_consecutive_hits` | FirstBlockCache |
| `685:enabled` / `685:warmup_steps` | Spectrum |
| `687:sage_attention` | SageAttention，一般 `auto` |
| `147:batch_size` / `147:use_fp16` / `146:value` | RIFE；`146:value` 目标 fps，默认 60 |

`workflow_id` 失败则改 `workflow_template`。上传返回的 `name` 才进槽，不要填本地路径。

**Ref2VA 上限（模型 + 这台 U06-X 节点）：图 ≤9、视频 ≤3、音频 ≤3，真文件合计 ≤12。** 不要把后 3 个图槽（655/656/657）当成只能塞暗帧——那是空槽占位，有真人设/场景/道具就上传。暗帧、1s 黑场、1s 静音不算「真参考」，但 9 张真图就不要再叠满 3 段真视频 + 3 段真音频。

## U03 input_values

| key | 含义 |
|---|---|
| `105:104:prompt` | 提示词 |
| `105:111:value` | 时长秒 |
| `105:9:steps` | 步数 |
| `120:自定义宽` / `120:自定义高` | 分辨率 |
| `105:127:lora_name` / `105:127:strength_model` | Turbo LoRA |
| `121:offload_model` | 测速时可 `false`，避免每次卸载模型 |

U03 不要上传 9 图 3 视频 3 音频。输出 24fps、无 RIFE。

## 时长公式（节点）

```text
max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17
```

| 秒 a | 约 24fps 源 | 插帧后 |
|---|---|---|
| 5 | ≈5.17s | 60fps（U06） |
| 8 | 8s | 60fps |
| 10 | ≈10.13s | 60fps |
| 15 | 以节点为准 | 60fps |

## 加速件目录（`/root/ComfyUI/models/loras/minimax/`）

换机后 `ls` 一次，文件名以机器为准。

| 文件 | 配 steps | 用途 |
|---|---|---|
| `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` | 4 | 竖屏 768 档默认，画质/速度平衡 |
| `minimax_h3_fl2v_lightx2v_turbo_4step_v0.1_comfy_resized_avg_rank_21_bf16.safetensors` | 4 | 更小更快，显存紧时用 |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` | 8 | balanced |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` | 4 | 参考生（ref2v UNet）可试 |
| `minimax_h3_fl2v_turbo_8step_v1.0_bf16.safetensors` | 8 | 非 comfyui 后缀，优先用 `*_comfyui_*` |

插件（U06-X 已接）：`ComfyUI-MiniMax-H3-Turbo`、`ComfyUI-MiniMaxH3-FirstBlockCache`、`ComfyUI-Spectrum-MiniMax-H3`、SageAttention。

**错配**：4 步 LoRA + steps=12/24 → 又慢又不一定更好。实测 5 秒从 4 步 ~103s 涨到 12 步 ~254s。

## API

| 端点 | 用途 |
|---|---|
| `POST /api/comfy/upload/file` | multipart，`overwrite=true`，返回 `name` |
| `POST /api/workflow/generate` | `workflow_id` + `input_values` |
| `GET /api/workflow/result?prompt_id=` | `pending` + `results` |
| `GET /api/comfy/proxy/history?prompt_id=` | execution_error、耗时戳 |
| `GET /api/comfy/status` | ready |
| `GET /api/comfy/queue-status` | busy / unreachable |
| `POST /api/comfy/stop` 与 `start` | 重启 |
| `GET /workflows/<id>.json` | 工作流图 |
| `GET $BASE/output/<file>.mp4` | 下载 |

SaveVideo 在 history 里可能叫 `images` + `animated`，result 里 `type:image` 但 `url` 是 `.mp4`。按扩展名判断。

history 里 `execution_start` / `execution_success` 的 `timestamp` 相减 /1000 = Comfy 推理秒。

## 4090 49GB 实测（热机）

| 工作流 | 参考 | 秒 | 分辨率 | steps | Comfy 秒 |
|---|---|---|---|---|---|
| U06-X | 暗帧占位 | 5 | 576×1024 | 4 | 103 |
| U06-X | 暗帧占位 | 5 | 576×1024 | 12 | 254 |
| U03 | 无 | 5 | 576×1024 | 4 | 67 |
| U06-X | 6 真图 | 10 | 576×1024 | 4 | 276 |
| U06-X | 6 真图 | 10 | 768×1344 | 4 + 768p LoRA + RIFE batch 4 | 322 |

像素从 576×1024 升到 768×1344（×1.75）时，4 步 + cache 下时间只到约 ×1.17。不要按像素线性估满。

## OOM 与假活

未覆盖的 video/audio 槽会解码模板默认素材（曾 ~28GiB）。空槽必须黑场+静音。长边 ≫ 1800 的图才缩。`pending:false` 且空 results = 失败。queue `unreachable`：先 stop 再 start。

## 片子废了（有 mp4 仍可能废）

一镜塞太多动作会熔；不写运镜动作会漂；屏幕文字乱码；三个人挤一条 10 秒远景脸糊。改切镜或减角色，不要在废片上叠滤镜。

## 实例无关性（2026-08-27 增补）

### 槽位发现：`scripts/discover_workflow.py`

- `GET /api/workflow/list` 只给 id 和运行次数，**不含输入键**；真正的键要从 `GET /workflows/<id>.json` 的节点定义里推导。
- 推导规则：`LoadImage*`→图槽 `<nid>:image`；`LoadVideo*`→`<nid>:video`；`LoadAudio*`→`<nid>:audio`；文本最长且含 `Picture/subject_definitions` 的 text/prompt 输入→`prompt_key`；名为 `value/seconds/秒数`（排除 audio/trim 类节点）的 3–60 数值→`seconds_key`；`KSampler*/SamplerCustom*/BasicScheduler` 的 `steps`→`steps_key`；`自定义宽/高` 或 `width/height`→`size_keys`；`LoraLoader*` 的 `lora_name`→`lora_keys`。
- 自动选流：按能力分（图槽数、采样器、prompt/秒数键齐全）+ 运行次数排序；`--kind u06/u03` 收窄，`--workflow-id` 指定。
- slot map 交给 `submit_video.py --slot-map`（或让它自动发现）；map 里没有的键一律不写，不要沿用别的实例的节点号。

### 两种真实工作流的键位差异（实例：同一用户先后两台机器）

| 功能 | 优化版X（旧机） | 9图3音频-V5（新机） |
|---|---|---|
| 图槽 | 137/139/144/151/653/654/655/656/657 | 相同 |
| 视频槽 | 638/659/660 | **无** |
| 音频槽 | 143/661/662 | **719/720/721**（默认读服务器 `p2.MP3`，不用也必须用静音占位，否则污染生成） |
| 提示词 | 664:prompt | 相同 |
| 秒数 | 132:value | 相同 |
| 步数 | 124:steps | **728:steps**（BasicScheduler） |
| 宽高 | 665:自定义宽/高 | 相同 |
| LoRA | 669:lora_name | **710:lora_name / 710:strength_model** |
| 加速节点 | 676/685/687/146/147 | **无**（不要写这些键） |

结论：键位表不可跨实例复用，每次以 discover_workflow.py 的输出为准。

### 重提任务的旧结果陷阱

`/api/workflow/result` 对**运行中**的 prompt 会返回最近一个已完成任务的结果。重新提交后直接用它下载会拿到旧视频（字节级完全相同）。正确顺序：`GET /api/comfy/queue-status` 确认该 prompt 已不在队列 → 再从 `/api/comfy/proxy/history?prompt_id=<id>` 取 mp4 文件名下载。`poll_video.py` 已内置此逻辑（history 优先 + 队列守卫）。

### 其他

- 输出量化：时长按 17 帧块取整；高/宽对齐 32（1280x720 请求实得 1280x704）。交付前本地 `scale/pad` 归一化并裁齐槽长。
- ComfyUI 首次开机写 `/root/面板地址.txt` 可能晚几分钟；AutoDL 模式下面板地址优先从快照 `service_6006_domain/port/port_protocol` 推导（autodl_app.py 已内置，SSH 文件只作回退）。

### 2026-08-27 实测追加：expect/extract 两个致命坑（已修复，勿回退）

1. **expect 超时必须 ≥180s**。`connect_server.py` 的 `set timeout` 作用于整个远端命令等待期。实例刚开机时 ComfyUI 冷启动占满磁盘/CPU，`find`/`nvidia-smi`/`curl` 循环可能远超 40s；超时会让 expect 携带**残缺输出**退出——PANEL 段被截断，表现为"间歇性拿不到面板地址"（空闲时完全正常，开机后必现，极难排查）。已从 40s 改为 180s。
2. **PANEL 标记会被命令回显污染**。expect 的 `log_user 1` 会把 spawn 的整条命令原样回显进输出，命令文本里天然包含 `PANEL_BEGIN`/`PANEL_END` 字样。`extract_panel` 若用**首个**标记对（`re.search` 非贪婪）截取，blob 会匹配到命令回显文本而不是远端输出，永远找不到 URL。必须用 `rfind` 取**最后一次**出现的标记对（远端输出一定在回显之后）。
3. **快照面板 URL 只能当候选**：`service_6006_*` 有三坑（端口内嵌进 domain 且 port 字段=0、协议字段 http 实为 https、域名与真实代理域名可能差一个前缀导致 404）。autodl `boot` 的统一候选循环会对每个候选探活 90s，不 ready 就换下一个，权威来源是实例内地址文件。
4. **wait_comfy 参数遮蔽**：`boot(uuid, wait_run, wait_comfy)` 的参数名与模块级 `wait_comfy()` 函数同名，函数体内一调用就 `TypeError: 'int' object is not callable`。现已拆出 `_run_boot`（参数名 `wait_comfy_secs`）。新增引导逻辑时不要再引入同名参数。
5. **submit_video.py slot-map 分支**：payload 变量名是 `slot_map`（曾是 `m` 导致 NameError，且崩在 generate 之后——任务已经提交、prompt_id 丢失）。改这类分支后必须连 payload 一起核对。

### 单参考图最小验证流程（换实例/换工作流后的冒烟测试）

```bash
export SEETACLOUD_BASE_URL=<面板地址>
python3 scripts/discover_workflow.py --kind u06 --out slot_map.json   # 实跑发现，核对输出键
python3 scripts/submit_video.py --prompt test.txt --slot-map slot_map.json \
  --seconds 5 --width 1280 --height 720 --preset speed \
  --image /path/to/一张参考图.png --out-json test_task.json
python3 scripts/poll_video.py <prompt_id> --timeout 1200 --download test.mp4
ffprobe test.mp4   # 期望：~5.2s（17帧块量化）、1280x704（32对齐）、有音轨
```

2026-08-27 在 pro-78781ae9fadb（RTX 5090，U06-9图3音频-V5）上按此流程实测通过：三视图单图 → 5.17s 人物走近日持紫能视频，身份/服装零漂移，全程 77s 下载完成。

### 2026-08-27 秒表复测：真实耗时基线（修正此前"冷启动慢"的误诊）

实测（pro-78781ae9fadb，RTX 5090，U06-9图3音频-V5，实例已 running）：

| 步骤 | 耗时 |
|---|---|
| 面板发现（快照死链秒弃 + SSH 文件 URL 探活） | **5.8s** |
| submit（1 图上传 + 占位 + 入队） | **0.9s** |
| GPU 生成 5s 视频（COMFY_SEC，服务端推理，不可压缩） | ~112s |
| 轮询开销（history 轮询超出生成时间的部分） | ~10s |
| 下载 2.4MB | ~2s |

结论：**慢的从来不是服务器，是发现逻辑的 bug**（标记回显污染、快照死链、"未 ready=拉黑"）。修正后 warm 发现 5.8s。冷开机（从 shutdown）ready 一般 <1 分钟。等待循环三态探活：`dead`（404×3）秒弃拉黑、`starting` 保留轮询绝不拉黑、`ready` 立即返回。另：固定种子下同提示词+同参考图会生成逐字节相同的视频——重提后想看到不同结果，必须改提示词或参考图（别误判为"下载到旧片"）。
