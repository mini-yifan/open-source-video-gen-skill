# MiniMax H3 → h3-prompt-writing 交接卡

只示范 **brief**。提示词正文由 `h3-prompt-writing` 写。提交默认见 SKILL §4 / §6。

U06 Ref2VA 的 `pictures` **最多 9 张**（Picture 1…9）。不够 9 张的槽由脚本用暗帧占位；不要为了凑满去复制同一张。真图 + 真视频 + 真音频合计 ≤12。

## U06 Ref2VA（一场戏、硬切）

```text
H3 prompt brief:
- workflow: U06-X
- prompt_mode: Ref2VA
- duration_seconds: 10
- aspect: 9:16
- resolution: 768x1344
- cuts: hard cuts
- pictures (upload order = Picture N; max 9):
  1. character turnaround; lock face and costume; do not copy white studio backdrop or turnaround grid
  2. old apartment living room and wardrobe; lock the room
- video_slots: unused 1s placeholders
- audio_slots: unused 1s placeholders
- dialogue: [Chinese] 谁在里面？
- constraints: no on-screen text/captions/UI; 3 shots; same woman, same room
- creative: She notices the wardrobe is not empty.
```

一镜到底：同一模板，把 `cuts` 改成 `one continuous take, do not cut`。若 Picture 1 是实拍首帧而不是三视图，把 `prompt_mode` 改成 I2VA。

## U03 T2VA（无参考）

```text
H3 prompt brief:
- workflow: U03
- prompt_mode: T2VA
- duration_seconds: 5
- aspect: 9:16
- resolution: 768x1344
- cuts: one continuous take, do not cut
- pictures: none
- video_slots: none (U03)
- audio_slots: none (U03)
- dialogue: none
- constraints: no people; no on-screen text/captions/UI
- creative: A single red paper lantern hangs under a wet stone alley arch at night. Fine rain.
```

## U02 FL2VA（短卡）

```text
H3 prompt brief:
- workflow: U02
- prompt_mode: FL2VA
- duration_seconds: 8
- aspect: 9:16
- resolution: 768x1344
- cuts: one continuous take, do not cut
- pictures: 1 first frame (closed wardrobe); 2 last frame (door ajar, eye in the seam)
- video_slots: none (U02)
- audio_slots: none (U02)
- dialogue: none
- constraints: no people; no extra shot changes
- creative: The door yields by itself from Picture 1 to Picture 2.
```

## 反例

- 跳过 h3-prompt-writing，在本技能里直接写提示词正文。
- 把三视图标成 I2VA（`at 0.00 seconds, <Picture 1> is fully referenced`）。
- 空视频/音频槽不标 unused、也不让脚本占位。
