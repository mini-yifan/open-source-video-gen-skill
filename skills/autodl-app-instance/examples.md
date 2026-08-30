# 示例

已知 H3 应用实例：`pro-78672ec11b9c`（MINIMAX-H3提速500高画质）。

## 1. 只开关机

```bash
export AUTODL_TOKEN='…'          # 不要提交、不要贴聊天
export AUTODL_INSTANCE_UUID=pro-78672ec11b9c
APP="${ZCODE_HOME:-$HOME/.zcode}/skills/autodl-app-instance/scripts/autodl_app.py"

python3 "$APP" list
python3 "$APP" on --uuid "$AUTODL_INSTANCE_UUID"
python3 "$APP" off --uuid "$AUTODL_INSTANCE_UUID"
```

## 2. 一批视频出片全流程（配合 minimax-h3）

```bash
APP="${ZCODE_HOME:-$HOME/.zcode}/skills/autodl-app-instance/scripts/autodl_app.py"
python3 "$APP" boot --uuid pro-78672ec11b9c
# 输出里有：
#   export SEETACLOUD_BASE_URL="https://uu….westd.seetacloud.com:8443"
# 立刻 export，然后执行一个或多个 minimax-h3 的 prepare / submit / poll
# 所有 job 完成、失败或取消，且没有仍在运行的任务后：
python3 "$APP" off --uuid pro-78672ec11b9c --wait
```

Agent 侧伪代码：

```text
try:
  解析并记录实例 UUID
  boot 一次
  读出 SEETACLOUD_BASE_URL
  for job in jobs:
    打开 minimax-h3（brief → h3-prompt-writing → submit → poll → 抽帧）
  等所有 job 进入 succeeded / failed / cancelled
finally:
  除非用户说保持开机：off --wait 一次
```

## 3. 用户原话怎么映射

| 用户说 | 做什么 |
|---|---|
| 「用 API 把 H3 那台开起来」 | `on --wait` |
| 「开起来出一条再关」 | `boot` → minimax-h3 → `off` |
| 「开起来出多条，全部完成再关」 | `boot` → 多个 minimax-h3 job → 全部终态 → `off --wait` |
| 「别关」 | 跳过 `off` |
| 「关掉刚才那台」 | `off --uuid pro-78672ec11b9c` |
