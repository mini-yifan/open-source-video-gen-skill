---
name: beauty-video-gen
description: 生成超写实、真实感、亲近感的美女时尚竖屏短视频（MiniMax H3 云端生成）。当用户要求"生成美女视频 / 真实感美女 / 亲近感美女视频 / 美女短视频 / 时尚美女视频 / 定制美女视频"，或用"可爱、亲切、性感、清纯、轻熟"等风格词，或用"夸张身材 / 大长腿 / 丰满身材 / 腿占画面大半 / 低机位拉腿"等身材词要求生成真人女性视频时使用；即使用户没提"美女"二字，只要是"生成真人女性出镜的短视频"也应触发。整合《真人时尚短视频提示词写作框架》提示词写作、可选的人物面部参考图生成（仅用户明确要求"先定脸/出面部参考图"时执行，默认直接文生视频；生图优先用当前 Agent 自带的生图能力，备选 cursor-image-gen）、minimax-h3 全流程（AutoDL 开关机、工作流发现、提交轮询、本地归一化、抽帧验收）。
---

# Skill: beauty-video-gen
# 真实感·亲近感美女视频生成

生成超写实、真实感、亲近感的美女时尚竖屏短视频：按《真人时尚短视频提示词写作框架》写提示词，
可选先用人像生图定脸，再用 `minimax-h3` 技能在云端 GPU 上出片，最后本地归一化与抽帧验收。

## 触发场景

用户要求"生成美女视频 / 真实感美女 / 亲近感美女视频 / 美女短视频 / 时尚美女视频"，
或用"可爱 / 亲切 / 性感 / 清纯 / 轻熟"等风格词，或用"夸张身材 / 大长腿 / 丰满 / 拉腿"等
身材词要求生成真人女性视频时使用（身材词命中时走 Step 3.5 夸张身材批量配方）。

## 总流程

```text
用户提需求
  → [用户已自带参考图?] ──是──→ 直接进入 Step 3（Ref2VA 模式）
  → [用户明确要求先生成面部参考图?] ──否──→ 直接进入 Step 3（T2VA 模式，默认不出参考图、不询问）
  →                                  ──是──→ Step 2 生成面部参考图 → 展示 → 询问是否修改（循环直到用户满意）
  → Step 3 按框架写 H3 提示词
  → Step 4 minimax-h3 云端生成（开机→发现→提交→轮询→下载→秒级校验→**立即关机**）
  → Step 5 本地归一化 + 抽帧验收（关机后本地做）
  → Step 5.5 默认提亮 + 皮肤光泽滤镜（关机后本地做）
  → Step 6 交付
```

## Step 0 收集需求

从用户消息中提取；未提及的用默认值并告知用户，不要反复追问：

| 项 | 默认值 | 说明 |
|---|---|---|
| 风格 | 可爱 + 亲切 + 性感（色情擦边零容忍，性感=露肩锁骨/S曲线/细高跟等 tasteful 表达） | 用户词原样保留进提示词意图 |
| 画幅 | 9:16 竖屏 720×1280 | 用户要 1080P 时用 1080×1920 |
| 时长 | 10 秒（5–15 内按动作量定） | 单场景 6–8 个动作节拍 ≈ 10s（轻快节奏）；H3 只支持 5–15s |
| 动作节奏 | 轻快真实生活速度（每拍 1.2–1.5s，主动作用 quickly/briskly 连接） | 2026-08-28 实测：慢速少拍版被用户差评"动作很慢不像正常人"；快节奏版获明确认可，见 Step 3 第 6 条 |
| 画面亮度 | 高调明亮布光 + 交付前默认跑 Step 5.5 提亮滤镜，滤镜版为推荐成片 | 提示词层写 bright airy high-key 场景，滤镜层再抬亮度与皮肤光泽 |
| 实例 | 无 | AutoDL 实例 UUID（如 pro-787880159a61）；用户未提供时在 Step 4 前询问，不要开机前瞎猜 |
| 参考图 | 无 | 用户消息里附图则直接采用，跳过 Step 1/2 |

## Step 1 面部参考图：可选流程，仅用户明确要求时执行（2026-08-29 调整）

**默认不出面部参考图**：用户没有明确要求时，一律直接进 Step 3（T2VA 模式）——
不扫描生图技能、不发 AskUserQuestion 询问。面部参考从"默认推荐"降级为"按需可选"，
交付报告里说明一句"本次未用面部参考，长相由模型决定，需要定脸可随时补"即可。

仅当出现以下任一信号才进入 Step 2（Ref2VA）：

- 用户明确说"先生成面部参考图 / 先定脸 / 出一张人像确认"；
- 用户自带参考图（图片直接采用，跳过 Step 2 的生成环节）。

## Step 2 生成并确认面部参考图（可选流程，Step 1 命中时才执行）

仅在 Step 1 命中可选流程时执行：优先用当前 Agent 自带的生图工具或技能（如 Codex 的 ImageGen，
不要求安装 Cursor）生成一张**肩部以上竖构图人像**；环境没有自带生图能力，或用户明确点名
用 Cursor 生成时，才改用 [`cursor-image-gen`](../cursor-image-gen/SKILL.md) 生成。
保存到工作目录（建议命名 `face_ref.png`）。提示词按下方模板填空，风格词映射见表。

**参考图提示词模板**（素颜哑光逻辑，与视频提示词同源，防止定脸与成片肤色妆感不一致）：

```text
超写实真人肖像摄影，竖屏，一位明确成年的年轻东亚女性，约{X}-{Y}岁，{气质，如甜美亲切}。
人物拥有精致小巧的{脸型}，{下颌线特征}。完全素颜、无妆感：肤色{白皙奶调}通透，
呈现自身自然健康气色与细腻真实纹理，零底妆、零粉，完全无油光、无腻光。
五官精致，眼睛偏{大}，深棕色虹膜，睫毛自然纤长，眉形自然柔和，鼻梁秀气，
嘴唇只保留自身自然血色，{甜美温和地微笑看向镜头}。
她留有{发色}{长度}{卷度}，{刘海样式}。穿{一件简单服装，如奶油白针织衫}。
肩部以上半身构图，浅灰或奶白纯色背景，窗边柔和散射光，皮肤上无硬高光点。
4K超高清，真实手机摄影质感，真实发丝，真实皮肤纹理，轻微景深。
禁止：幼态脸、未成年感、塑料皮肤、过度磨皮、油光、浓妆、夸张修图、多余人物。
```

**风格词 → 视觉要素映射**（拼模板时参考）：

| 用户风格词 | 参考图要素 | 视频侧 Look/机位/动作倾向 |
|---|---|---|
| 可爱 | 大眼、空气刘海、圆脸幼齿感但明确成年、甜笑 | 浅色针织、高机位自拍俯拍 C1、眨眼歪头 |
| 亲切 | 柔和眼神、温笑、生活感 | 家居晨光 L-F、窗边散射光、凑近互动 |
| 性感 | 锁骨肩线、微卷长发、红唇血色（素颜逻辑下用唇色深一点的自然血色） | 一字肩/吊带裙、S 曲线、尖头细跟高跟鞋 |
| 清纯 | 直发或微卷、淡然表情 | 棉麻长裙、逆光回眸 C6 |
| 轻熟/高级 | 利落眉眼、盘发或大波浪 | 西装裙 L-B、低机位 C3 或环绕 C5 |

生成后**用 Read 展示图片**给用户，然后 AskUserQuestion：

```json
{"question": "面部参考图是否需要修改？", "header": "参考确认", "multiSelect": false, "options": [
  {"label": "不用修改，开始生成视频（推荐）", "description": "以此定脸进入视频生成"},
  {"label": "需要修改", "description": "说明要调整的长相/发型/气质等，重新生成参考图"}]}
```

用户选"需要修改"时，按其描述改模板重新生成，再次询问，**循环直到用户点头**。
用户点击不修改后立即进入 Step 3，不再追问其他问题。

## Step 3 按框架写 H3 提示词

**先读 `references/fashion-framework.md`**（完整框架：M0–M14 模块、人物/Look/机位/动作四个参数库、
防翻车规则、疫苗句、实测复盘），再按 `h3-prompt-writing` 技能的格式规范写英文提示词。

要点浓缩（细节以框架文档为准）：

1. **模式**：有参考图 → Ref2VA（`<Subject 1>` 定义人物身份，声明"参考图中的同一人、全片仅一人"）；
   无参考图 → T2VA。负面清单在 H3 里不单列，改为正文正向点名（"completely free of oily shine…"
   / "remain completely identical from the first frame to the last"）。
2. **六个保命句任何情况不删**：①显式成年年龄（约20–24岁，防幼态）②自然协调的比例
   ③保留自然肌肤纹理 ④第一帧到最后一帧完全一致 ⑤人物身份全程一致 ⑥结尾定格+看向镜头。
3. **结构**：全局规格 → 人（体型→脸→发→饰→装→鞋六件套）→ 景 → 机位 → 秒级脚本 → 氛围 → 光色
   → 画质标签 → 一致性锁。所有数字用区间（俯拍30–45°、24–28mm、8–10cm 跟高）。
4. **素颜哑光三锁**（防油光+防浓妆，光/料/词三层必须同时在场）：
   皮肤：`completely bare-faced and makeup-free … zero visible foundation, zero powder,
   completely free of oily shine, greasy glow or plastic smoothing`；
   光线：默认**高调明亮窗光**（2026-08-28 实测：亮与哑光可兼得）——
   `bright airy high-key daylight, glowing white walls, sheer white curtains, abundant soft morning daylight`，
   同时保留疫苗句 `absolutely no harsh specular hot spots`，亮而不油；
   面料：`fully matte with no sheen`（忌缎面/微光泽）；配饰≤1–3件。
   禁词：粉感/雾面底妆/powder/foundation（会被当成化妆指令出全妆脸）。
5. **从参数库选卡**：Look 卡（L-A~L-F）× 机位（C1~C7）× 动作三拍整套取用不混搭；
   **当前默认配方（2026-08-28 实测，用户对比后明确认可，动作更自然、画面更亮）**：
   高调明亮白墙纱帘晨光场景 × C1 高机位自拍俯拍 × 修身裙 × 7 拍快节奏
   （快步入画→撩发别耳歪头→凑近眨单眼→退步展裙→一次 90° 转身甩发→碎步左右移动+踮脚→凑近定格看镜头；
   这只是节拍骨架，血肉由第 7 条微动作层填充）。
   机位与视线必须物理自洽（俯拍配抬头看镜头）；一条视频只允许一个大转向动作。
6. **秒级脚本**按 "From 0 to about 1.2 seconds …" 连续叙事写入
   `detailed_description`/`integrated_multimodal_description`，结尾必须是清晰可暂停的定格+眼神落镜头。
   **节奏铁律（2026-08-28 实测，必写）**：每拍 1.2–1.5 秒、10 秒 6–8 拍，主动作之间用
   quickly / briskly / one quick step 连接；正文必须含一句
   `Every movement in this video runs at brisk, natural real-life speed, quick and energetic,
   with absolutely no slow-motion or dreamy pacing.`——缺这句动作极易被模型拖成慢动作，
   是"动作很慢、不像正常人"差评的直接根因。
7. **微动作与物理反馈层（防 AI 呆板的核心，每条提示词必写满）**：呆板感来自"只写主动作"——
   模型拿到什么密度就生成什么密度。每个秒级段落按公式填充：
   **1 个主动作 + 2–3 个微动作 + 表情渐变 + 物理联动**，并遵守：
   - **表情渐变三段式**：唇角先动 → 眼睛跟上（眼角微弯、睫毛半垂再抬起）→ 头部微配合
     （倾 10–15°）。用 first/then/finally 写明先后，禁止表情瞬跳；表情自然不夸张，
     禁用 exaggerated / dramatic / sudden。
   - **笑容幅度锁（2026-08-29 新增，防"咧嘴诡异感"）**：笑容写得太满（bright open smile /
     big smile / showing teeth）会把嘴咧到耳根，近景俯身定格尤其诡异。锁法：唇角只上提
     `a few millimeters`，唇轻闭或只微开一条缝，正面写 small / soft / gentle / natural smile，
     并点名 `never stretching into a wide grin, no exaggerated grinning`；
     **禁用** bright / big / wide / open 修饰 smile，露齿最多 a hint of teeth。
   - **眨眼有分布**：10 秒 2–4 次，绑定在动作转换点（转头后立刻眨一次），禁止全程不眨或高频眨眼。
   - **物理联动每 2–3 秒至少一处**：转头→发丝滞后半拍甩动再落肩；迈步→裙摆轻摆+高跟点击地；
     凑近→衣料褶皱加深；抬臂→袖口下滑堆在腕部；释放发丝→发丝回弹贴颊；转头→耳钉反光一闪。
   - **生命感永不停**：呼吸贯穿全片（胸口肩部轻微起伏）；收尾定格是构图定格不是生命定格——
     定格中仍保留呼吸起伏、碎发余摆、衣料微沉。
   - **幅度量词压住 AI 夸张感**：slowly / gently / a few millimeters / 10–15 degrees / a beat，
     微动作都是厘米级、秒级的小事（只约束微动作的幅度；主动作的整体节奏按第 6 条铁律保持轻快，
     两者不冲突——v2 实测"quickly tucks + hair springs back"式的快主动作+小微动作组合最自然）。
   可直接复用的英文短语库（按需选用、改写，不要整段照抄到每条提示词）：
   `her chest and shoulders rise and fall gently with relaxed breathing`（呼吸）；
   `the corners of her mouth lift a few millimeters into a small, soft, natural smile, her lips staying gently closed or barely parted`（唇；勿用 bright open smile / wide grin 类放大词）；
   `her eyes narrow slightly and crinkle at the corners as the smile reaches them`（眼）；
   `her gaze drops shyly for a beat, then lifts back to the lens`（眼神）；
   `she blinks naturally, once right after each head turn`（眨眼）；
   `tilts her head about 10 to 15 degrees to her right`（头）；
   `her fingertips slide slowly through the strand and release it, letting it spring back against her cheek`（手）；
   `strands sway with a slight lag behind each turn and settle softly over her shoulder`（发）；
   `the knit hem sways gently with each step and settles against her thighs`（裙摆）；
   `fabric folds deepen as she leans closer to the lens, then smooth out as she straightens`（衣褶）；
   `the off-shoulder neckline slips a few millimeters and she nudges it back with her thumb`（领口）；
   `her earrings catch the window light and glint as her head turns`（饰品）。
8. H3 三段齐备：正文描述 + `overall_soundscape`（环境声+动作声）+ `non_diegetic_music`（配乐淡出）。

### Step 3.5 夸张身材批量配方（2026-08-29 实测定型，v1→v3 三版迭代，用户逐版确认）

用户要求"夸张身材 / 大长腿 / 丰满 / 腿占画面大半"类视频时整卡取用（T2VA 无参考图，U03 文生视频），
替换第 5 条的默认配方，其余第 1–4、6–8 条照常生效：

- **机位**：C3 低机位仰拍——镜头位于膝盖高度、前方约 1.2–1.5m、仰角 15–25°、24–30mm 广角，
  正文点明 "classic street-snap stretched-legs effect"；腿+高跟鞋占画面下半主体。
  **构图优先级（2026-08-29 新增，防鞋被裁）**：人物整体在画面中略微上移，
  **鞋底与画面底边之间必须留约 5–10% 画高的地面空隙**，高跟鞋跟尖绝不可贴边或出画；
  头部允许贴近甚至略微超出画面顶边（顶部裁掉一点头/脸可接受）——**宁可裁头顶，不可裁鞋**。
  英文构图句（可抄）：`her legs and heels stay fully inside the frame with a clear strip of floor
  beneath her soles — about 5 to 10 percent of the frame height between her heels and the bottom
  frame edge; the top of her head may sit close to or slightly beyond the top frame edge`。
  视线物理自洽写"她低头看向镜头"（仰拍配低头，写反眼神必飘）。
- **身材**：时尚编辑式夸张体型——extraordinarily long, slim, straight legs / slim cinched waist /
  full bust / narrow shoulders / exaggerated hourglass S-curve；保命句②在此改写为
  `her elongated proportions remain graceful, elegant and anatomically coherent`（防畸形总闸仍要在）。
- **两条腿解剖锁（必写，v1"三条腿"事故的直接修复）**：`she has exactly two legs and two arms at
  every moment — no duplicated, split or extra limbs, the gap between her legs always shows clean
  background instead of any third leg, the faint floor reflections never read as additional legs,
  natural five-fingered fingers`。**禁用膝部交叉腿站姿**（肢体复制重灾区），改双脚前后微错开
  （one foot slightly in front of the other, ankles almost touching）。
- **俯身互动（必写，用户点名要求的亲近感来源）**：至少两次俯身凑近镜头——中段一次
  （`bends forward at the waist toward the camera ... her face coming down and closer to the lens`
  + 挥手 wave near her cheek + bright grin + 一声轻笑），结尾定格也用俯身凑近 + bright eye contact，
  让"可暂停封面帧"自带亲近感。物理自洽：俯拍机位下人物俯身=脸靠近镜头，画面自然放大。
- **俯身遮胸锁（必写，用户点名要求的防走光过审项）**：`the moment she starts to bend, one forearm
  rises to press lightly over her chest, holding the neckline flat and fully covered against her
  chest — the camera never looks down inside the dress`，并加常驻句
  `the neckline always sits flat and fully closed against her chest, modest and camera-safe`。
  措辞只用 cover / flat / closed / modest / camera-safe，不出现敏感部位词。
- **Look（已验证组合）**：灰蓝挂脖修身哑光针织超短裙（bodycon mini, halter neck, hem mid-thigh,
  fully matte）+ 超薄深色丝袜（ultra-sheer dark stockings, soft satin sheen along the calves）+
  黑漆皮尖头细高跟（black patent-leather pointed-toe stiletto pumps, fully visible with a clear
  strip of floor beneath her soles, catching sharp glints）+ 小银耳钉一件 + 亮灰房间/走廊 +
  亮面地砖微反射 + 高调柔和窗光。
- **实测参数**：1080×1920 / 10s / U03-light2v / speed 档，推理约 345–693s；成片本地归一化 30fps。
- **已知瑕疵与补救**：起身换手瞬间（约 0.3s）领口可能短暂松开；需 100% 全程遮盖时在提示词追加
  `her hand stays on her chest until she is fully upright again, then smooths the neckline once`。

提示词保存为工作目录下的 `prompt.txt`（或 `h3_prompt.txt`）。

## Step 4 minimax-h3 云端生成

执行引擎是 `minimax-h3` 技能（其 SKILL.md 有完整规则），本技能固定走以下已实测链路。
**整个批次只开一次机，try/finally 保证最终关机**；实例按秒计费，等待窗口做本地活，不干等。

```bash
source ~/.zshrc   # AUTODL_TOKEN 在 ~/.zshrc，非交互 shell 需先加载

# 1) 开机（整个批次一次；记下输出的 SEETACLOUD_BASE_URL）
python3 ~/.zcode/skills/autodl-app-instance/scripts/autodl_app.py boot --uuid <UUID>

export SEETACLOUD_BASE_URL=<面板地址>

# 2) 工作流发现（有参考图用 --kind u06；纯文字用 --kind u03）
#    ⚠ 必须核对自动选中的是 H3 生成工作流（U03/U06/U02 系列）。
#    若选成 InfiniteTalk/U11/U09 等对口型/其他工作流，用 --workflow-id 强制指定，例如：
python3 ~/.zcode/skills/minimax-h3/scripts/discover_workflow.py --kind u06 \
  --workflow-id "U06-9图3音频-V5" --out slot_map.json

# 3) 提交（submit_video.py 自动上传参考图、给空图槽/音频槽填占位，防模板素材污染）
python3 ~/.zcode/skills/minimax-h3/scripts/submit_video.py \
  --prompt prompt.txt --slot-map slot_map.json \
  --seconds 10 --width 720 --height 1280 --preset speed \
  --image face_ref.png --out-json task_info.json

# 4) 轮询下载（只认 history；运行中绝不取 result 接口，会拿到旧视频）
python3 ~/.zcode/skills/minimax-h3/scripts/poll_video.py <PROMPT_ID> --download raw.mp4
# 720p/10s 实测约 195s；1080p/10s 实测约 417s

# 5) 下载落盘 + ffprobe 秒级校验通过 → 立即关机（同批次全部完成时；唯一例外：用户说保持开机）
python3 ~/.zcode/skills/autodl-app-instance/scripts/autodl_app.py off --uuid <UUID> --wait
#    归一化/抽帧验收/滤镜/调参重跑全是本地活，一律放到关机之后（Step 5/5.5），绝不拖着开机做本地事
```

参数速记：`--width/--height` 按用户画幅（720×1280 默认 / 1080×1920 要 1080P 时）；
固定种子下同提示词+同图会生成逐字节相同的视频，重提前必须改提示词或参考图。

**下载完立即关机（2026-08-29 铁律，省钱）**：所有任务下载落盘并用 `ffprobe` 秒级校验
（确为视频、时长/分辨率/音轨符合预期）通过后，立刻执行 `off --uuid <UUID> --wait`。
GPU 空转也按秒计费，而归一化、抽帧验收、滤镜、按用户反馈调参重跑动辄几十秒到几分钟——
这些全是本地活，必须放在关机之后，Step 5 / 5.5 / 6 全程无服务器。try/finally 保证批次终态
必关机（任务失败/超时/用户中断也一样）。例外只有两个：同批次还有未完成任务；
用户明确说保持开机（或 `AUTODL_KEEP_ON=1`）。本地验收不达标要重生成时，重新开机走一遍
Step 4 即可——重开机的成本远低于为等本地处理而空转计费。

## Step 5 本地归一化 + 抽帧验收（服务器已关机，纯本地）

**本步在 Step 4 关机之后进行，全程不占 GPU。**H3 输出会量化：宽高对齐 32（请求 720 实得 704、
请求 1080 实得 1056；1280/1920 不变）、
时长按 17 帧块取整（10s 实得 10.125s@24fps）。**交付前必须归一化**：

```bash
# 归一到目标规格（W×H=目标分辨率，T=目标秒数）
ffmpeg -y -i raw.mp4 \
  -vf "scale=W:H:force_original_aspect_ratio=increase:flags=lanczos,crop=W:H" \
  -t T -r 24 -c:v libx264 -crf 17 -preset slow -c:a aac -b:a 192k final.mp4

# 抽首/中/尾三帧拼图（n≈帧率×秒：24fps 10s 取 5/120/235）
ffmpeg -y -i final.mp4 -vf "select='eq(n\,5)+eq(n\,120)+eq(n\,235)',tile=3x1" -frames:v 1 check.png
```

用 Read 查看 `check.png`，逐项核对：人物身份与参考图/首帧一致、皮肤哑光无油光、
发型服装鞋履全程稳定（用户点名过的物品重点查）、结尾定格看镜头、**俯身段遮胸在位**
（用了 Step 3.5 配方时，抽俯身区间首/中/尾三帧查手是否按胸、领口是否闭合）、
**转身/站姿段无肢体复制**（逐帧数腿，见下条排查）、
**鞋跟完整且鞋底与画面底边留有明显空隙**（约 5–10% 画高；顶部裁掉一点头/脸可接受）；
并通读秒级脚本自查
动作密度与节奏是否达标（表情渐变/眨眼/微动作/物理联动是否写满，每拍是否 ≤1.5s，
real-life speed 疫苗句是否在位）。抽多帧（如 5 帧）比对姿态差异，帧间姿态变化小 = 动作太慢。
有问题按框架文档第七节排查表定位根因（脸漂→补特征/身份锁；油光→查光/料/词三层；
妆重→删粉感词改素颜声明；手崩→换机位或动作；画面偏暗→查高调布光句 + 跑 Step 5.5 滤镜；
动作呆板/拖沓 AI 感→回查 Step 3 第 6 条节奏铁律与第 7 条微动作层，加密节拍与表情渐变后重生成；
肢体复制（三条腿等）→ 补两条腿解剖锁句、交叉腿改双脚微错开后重生成；
俯身走光 → 补俯身遮胸锁句后重生成；
鞋贴底边/鞋跟被裁 → 补构图优先级句（鞋底留 5–10% 画高、头顶可贴近或略超顶边）后重生成），
改提示词后**重新走 Step 4**，不要凭印象微调。

## Step 5.5 默认后期：提亮 + 皮肤光泽滤镜

**默认必跑**（2026-08-28 实测：提示词层高调布光 + 本滤镜默认档的组合获用户明确认可，
滤镜版作为推荐成片交付）。仅当用户明确说"要原始观感/别加滤镜"时跳过本步；
用户要求"加滤镜 / 更亮 / 皮肤更有光泽 / 更通透 / 更自然"时也走本步。
本步与用户后续的调参重跑都在服务器关机后本地进行，零 GPU 费用。
在归一化之后运行本技能自带的
`scripts/beauty_glow_filter.py`（Python + OpenCV 逐帧处理，ffmpeg 管道编解码，原音轨无损保留）：

```bash
python3 <本技能目录>/scripts/beauty_glow_filter.py 输入.mp4 输出.mp4
```

五步处理链与参数（都在脚本顶部；按用户反馈调参重跑即可，1080p×10s 约 20 秒）：

| 步骤 | 参数（默认） | 作用 | 调参方向 |
|---|---|---|---|
| 伽马提亮 | `GAMMA=0.90` | 中间调变亮，黑白场锚定，亮而不发灰 | 想更亮降到 0.85；发灰回调 0.92+ |
| 饱和补偿 | `SAT=1.045` | 补回提亮损失的色彩 | 肤色偏淡加大到 1.06 |
| 皮肤局部增亮 | `SKIN_LIFT=0.05` | YCrCb 肤色掩膜+大半径羽化，提亮集中在皮肤 | 皮肤不够亮加到 0.08 |
| 高光 Bloom 辉光 | `BLOOM_STRENGTH=0.35`、`BLOOM_SIGMA=21`、软阈值 0.60–0.92 | 高光扩散回混，皮肤呈现柔光镜般的光泽 | 光泽更强加到 0.45；出现塑料感降到 0.25 |
| 高光软压缩 | `KNEE_START=236` | 指数软拐点防止提亮后过曝死白 | 出现死白下调到 228 |

跑完后从原片与滤镜片各抽同一帧（如 `select=eq(n\,120)`）拼左右对比图，用 Read 展示给用户确认；
用户觉得效果不够或过头时，只调对应参数重跑，不要改处理链结构。

## Step 6 交付

向用户报告：最终文件路径与规格（分辨率/时长/帧率/音轨）、验收结论、
保留的中间产物（原始未裁切版、提示词 txt、验收帧图）；Step 5.5 滤镜默认跑：
报告滤镜版（推荐成片）与未滤镜版两个文件及所用参数档位，方便后续复调。多条视频按批次汇总。
此时服务器已在 Step 4 末尾关机；若验收发现问题需要重生成，先改提示词或参考图再重新开机走 Step 4
（固定种子+同素材会逐字节复现旧结果，直接重提没有意义）。
