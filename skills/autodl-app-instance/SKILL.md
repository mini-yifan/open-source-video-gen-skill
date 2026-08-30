---
name: autodl-app-instance
description: >-
  Powers AutoDL Art application instances on and off via official API, SSHs
  into the box, and waits until ComfyUI is ready for MiniMax H3. Use when the
  user mentions AutoDL 应用实例, API开机, API关机, autodl.art, AUTODL_TOKEN,
  远程服务器开关机, or wants the agent to boot a GPU box before minimax-h3 and
  shut it down after video generation. It can wrap a minimax-h3 job with
  boot-before-generation and guaranteed power-off cleanup.
---

# AutoDL 应用实例（开机 → SSH → 关机）

管 **应用实例** 生命周期，不管提示词、不管出片。出片走 [`minimax-h3`](../minimax-h3/SKILL.md)。

官方文档：<https://autodl.art/docs/app_api/>  
脚本：当前技能目录下的 `scripts/autodl_app.py`（ZCode：`~/.zcode/skills/autodl-app-instance/scripts/autodl_app.py`）。  
接口细节 → [reference.md](reference.md)  
命令示例 → [examples.md](examples.md)

不要把 `AUTODL_TOKEN` / SSH 密码写入仓库或技能文件。不要打印 `root_password`。

---

## 和 minimax-h3 的组合执行契约（批次级）

```
解析并记录 UUID
  → boot 一次并导出最新 SEETACLOUD_BASE_URL
  → minimax-h3 执行一个或多个视频 job
  → 等所有 job 进入终态
  → finally: off 一次（本技能）
```

当目标是 AutoDL 应用实例，或用户要求“开机后生成、全部完成后关机”时：**先本技能，再 minimax-h3，最后关机。** 不要只 SSH 完就结束。

本技能只管理实例生命周期，不决定 H3 的工作流、提示词、时长、画幅或画面内容。`minimax-h3` 只有在本技能报告 `COMFY_READY`、队列可访问并提供最新面板地址后才能提交任务。

组合模式下，一个父任务就是一个 AutoDL 批次。必须先保存实例 UUID，再执行一次 `boot`；批次内的多个视频、重试和追加 job 都共用这次开机。单个视频完成时不得执行 `off`。

只有当批次内所有 job 都是 `succeeded`、`failed` 或 `cancelled`，并且没有仍在运行的 H3 任务、未下载的结果或未处理的重试时，就执行一次 `off --uuid <uuid> --wait`。成功、部分失败、超时、轮询异常或用户中断，都要走批次级 `try/finally` 清理；只有用户明确要求保持开机或设置 `AUTODL_KEEP_ON=1` 时例外。

**关机时点（2026-08-29 明确）**：批次产出全部下载落盘并通过 `ffprobe` 秒级校验后**立即关机**。归一化、抽帧验收、滤镜、按用户反馈调参重跑等本地后处理不得推迟关机——GPU 空转照常按秒计费，这些活放到关机后做零成本。本地验收不达标需要重生成时，先改提示词/素材再重新 `boot`（重开成本远低于空转等待）。

**最高效的完整链路（2026-08-27 秒表实测定型）**已写在 [`minimax-h3` SKILL.md](../minimax-h3/SKILL.md) 的"最快链路"一节：`source ~/.zshrc` → `boot`（warm 发现实测 5.8s）→ `discover_workflow.py` 生成 slot_map → **逐条提交把队列填满**（勿生成一条等一条）→ 并发 poll（history 优先）→ 等待窗口做本地活 → 终态即 `off --wait`。自身开销 ~15s/批，其余全是 GPU 推理时间。

---

## 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `AUTODL_TOKEN` | 是 | autodl.com → 账号 → 设置 → 开发者 Token。**不要**加 `Bearer`。缺环境变量时脚本回退读 `~/.config/autodl.env` |
| `AUTODL_ENV_FILE` | 否 | 覆盖 Token 私有文件路径，默认 `~/.config/autodl.env` |
| `AUTODL_INSTANCE_UUID` | 否 | 例如 `pro-78672ec11b9c`（MINIMAX-H3提速500高画质）。**用户不需要记它**，见下 |
| `AUTODL_APP_HINT` | 否 | 没 UUID 时按应用名匹配，默认 `MINIMAX-H3` |
| `AUTODL_KEEP_ON` | 否 | 设为 `1` 或用户说「别关 / 保持开机」→ 跳过关机 |

**Token 存储（推荐私有文件）**：Agent 的 shell **继承不到**另一个终端里的 `export`，非交互 shell 也常常不加载 `~/.zshrc`。推荐写入 `~/.config/autodl.env`：

```bash
mkdir -p ~/.config && echo 'export AUTODL_TOKEN=你的Token' > ~/.config/autodl.env && chmod 600 ~/.config/autodl.env
```

脚本缺 Token 时会自动读它，`source ~/.zshrc` / `zsh -ic` 只作为兜底手段。

**缺 Token / 找不到实例时**：向用户原样转达脚本报错中的申请与存储指引，不要绕过。实例解析链为 `--uuid` 参数 → `AUTODL_INSTANCE_UUID` → 按 `AUTODL_APP_HINT` 匹配账号下实例列表：唯一命中自动使用（`boot` 输出会打印 `export AUTODL_INSTANCE_UUID=...` 供本批次复用）；多台命中时把候选表给用户选一次；零台命中时提示用户先去 AutoDL 控制台创建一台 MINIMAX-H3 应用实例（一次性操作）。

---

## 流程

```
Task Progress:
- [ ] 1. 确认 AUTODL_TOKEN；解析并锁定父批次的实例 UUID
- [ ] 2. list / status
- [ ] 3. boot：关机则 power_on，等到 running
- [ ] 4. snapshot → SSH 发现面板；等到 ComfyUI reason=ready、队列空
- [ ] 5. 在当前执行环境设置 boot 输出的 SEETACLOUD_BASE_URL；打开 minimax-h3 执行全部 job
- [ ] 6. 全部 job 进入终态、产出落盘并通过秒级校验后，立即执行一次 power_off，等到 shutdown（除非 KEEP_ON）；本地后处理（归一化/验收/滤镜）在关机后做
```

脚本（在任意项目目录执行）：

```bash
APP="${ZCODE_HOME:-$HOME/.zcode}/skills/autodl-app-instance/scripts/autodl_app.py"

python3 "$APP" list
python3 "$APP" status --uuid "$AUTODL_INSTANCE_UUID"

# 开机 + SSH + 等 Comfy ready，打印 export SEETACLOUD_BASE_URL=...
python3 "$APP" boot --uuid "$AUTODL_INSTANCE_UUID"

# 出片（minimax-h3 的多个 submit / poll）…
# 全部 job 完成、失败或取消，且没有仍在运行的任务后：
python3 "$APP" off --uuid "$AUTODL_INSTANCE_UUID" --wait
```

已在运行只连 SSH：同样用 `boot` / `ensure`（内部会跳过重复开机）。

已经 `shutdown` 再 `off`、已经 `running` 再 `on`：脚本当成功，不报错。

---

## 硬规则

1. 走 `https://www.autodl.art` + `/api/v1/adl_dev/dev/instance/pro/…`，**不是** `api.autodl.com` 的容器 Pro，也不是网页非官方 `/api/v1/instance`。
2. `power_on` 的 `payload` 必须是 `"gpu"`。API 不能无卡开机。
3. `status` / `snapshot` 用 **GET + query** `?instance_uuid=`。JSON body 会 `RequestParameterIsWrong`。
4. 不要调 `release`。那是释放实例，不是关机。
5. `boot` 成功只说明容器在跑；H3 提交前必须看到 `reason=ready`。首启实例的 ComfyUI 初始化可能花几分钟——`boot` 会用快照面板地址轮询到 ready，不要因为面板文件暂不存在就手动放弃或换实例。
6. 出片失败、轮询超时、用户中断，也要在父批次结束时关机。多个 job 不能在单个视频完成后关机；用 `try/finally` 语义：先记 UUID，批次结束时执行一次 `off --wait`。
7. 本机 HTTPS 可能有自签证书链，脚本用 `curl -sk`。不要改回强制校验然后卡住。
8. 关机停的是 GPU 计费。系统盘仍按日扣。连续关机 60 天会释放应用实例。

---

## SSH 与面板

`boot` 内部是**统一候选循环**（2026-08-27 二次实测后定型）：快照 URL 与实例内地址文件 URL 都只是"候选"——轮流尝试、各自探活 90 秒、不 ready 换下一个、试过的记入已试集合，直到某个候选 `reason=ready` 为止。不要假设任何一个来源第一次就正确：

实测过的快照 `service_6006_*` 三个坑：

1. **端口内嵌在 domain 里**（`xxx.seetacloud.com:8443`）而 `service_6006_port` 字段是 `0`——不能因为 port 字段为空/为 0 就放弃；
2. **协议字段可能写 http**，但 8443 代理实际是 https（以实例内地址文件为准）；
3. **快照域名可能与真实代理域名不一致**（实测 `u450174-…` vs 真实 `uu450174-…`，快照地址 404）——所以快照 URL 探活失败就换下一个候选，权威来源是实例内 `/root/面板地址.txt`。

**Ready 时长（2026-08-27 秒表修正）**：ComfyUI 通常随开机几十秒内 ready；实测（实例已运行时）从发现到 ready 仅 **5.8s**。此前记录的"冷启动 3–6 分钟/十几分钟"是**误诊**——延迟全部来自发现逻辑的三处 bug（PANEL 标记被命令回显污染导致 SSH 解析必失败、快照 URL 域名错误 404、把"尚未 ready"的候选当死链永久拉黑），不是服务器慢。冷开机（从 shutdown 起）ComfyUI ready 一般 <1 分钟，磁盘缓存冷时更久；发现循环以 5s 节奏轮询、死链秒弃、`starting` 状态绝不拉黑，ready 一出现立即返回，不会浪费任何等待。expect 超时保持 180s 只是防极端慢命令的保险，不影响快路径。

密码只放子进程环境变量 `SEETACLOUD_SSH_PW`（expect 内 `$env(...)` 读取），不要 echo、不要写进脚本文本。端口、主机以 **snapshot** 为准（开机后会变）。
