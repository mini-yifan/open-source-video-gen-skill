# MiniMax Music 3 Prompt Writing Guide

本指南用于构造 `generate_music.py --caption` 的曲风描述与 `--lyrics` 的歌词。
caption 用**英文**生成质量最好（内部实现细节，不必给用户看原文）；歌词用用户的语言。

## Caption 三段结构（必须）

MiniMax Music 3 的 caption 是结构化文档，三段缺一不可（纯音乐省略 Vocal Details）：

```
### Global Metadata   ← 时长/BPM/拍号/曲风/乐器编制/整体情绪
### Vocal Details     ← 人声歌专用：性别、音色、唱法、咬字、副歌处理、禁则
### Arrangement       ← 逐段编排：开场方式、乐器进入时点、副歌铺开、结尾处理
```

### 各段要素

**Global Metadata**：时长 + BPM + 拍号 + 曲风 + 乐器清单 + 情绪词 + 一个画面比喻。
例：`A warm, romantic 3-minute Mandarin pop love ballad at 76 BPM in 4/4. Gentle
fingerpicked acoustic guitar, soft piano, lush sustained strings... Intimate, sincere,
dreamy, and heartfelt, like a quiet night confession under moonlight.`

**Vocal Details**（人声歌）：性别与音色（`gentle, sweet young female vocalist with a
clear, airy voice`）、唱法（`intimate close-mic delivery, delicate breathy touches at
line endings`）、副歌处理（`blossoms in the Chorus with fuller, soaring yet tender high
notes`）、语言与咬字（`Clear Mandarin diction`）、禁则（`No laughter, spoken ad-libs,
or vocal improvisation`）。

**Arrangement**：开场（`no long instrumental intro`，从第一句人声/主题进）、
中段（哪段进弦乐/鼓）、副歌（`bloom into full strings and soft brushed drums`）、
桥段（`pull back to piano and voice alone`）、结尾（`one last warm string swell fading
gently after the final word`）。

### 完整示例 A：女声中文情歌（约 2 分钟成品）

```
### Global Metadata
A warm, romantic 3-minute Mandarin pop love ballad at 76 BPM in 4/4. Gentle fingerpicked
acoustic guitar, soft piano, lush sustained strings, subtle electric piano pads, and a
tender slow groove with soft brushed drums. Intimate, sincere, dreamy, and heartfelt,
like a quiet night confession under moonlight.

### Vocal Details
A gentle, sweet young female Mandarin vocalist with a clear, airy voice and soft
head-tone. Intimate close-mic delivery, delicate breathy touches at line endings, and
emotional warmth that blossoms in the Chorus with fuller, soaring yet tender high notes.
Clear Mandarin diction at a relaxed pace. Start singing on the first downbeat. No
laughter, spoken ad-libs, or vocal improvisation.

### Arrangement
Open with soft piano and fingerpicked acoustic guitar under the first line; no long
instrumental intro. Keep the pulse gentle and continuous beneath the vocal. Add sustained
strings from the second Verse, bloom into full strings and soft brushed drums at the
first Chorus, then pull back to piano and voice alone in the Bridge. Build the final
Chorus slightly fuller, then close with the Outro: piano, guitar and one last warm string
swell fading gently after the final word.
```

### 完整示例 B：30 秒纯音乐（钢琴+弦乐，短片尾曲感）

```
### Global Metadata
A warm, heartfelt instrumental piece of exactly 30 seconds at 80 BPM in 4/4 (10 bars
total), like the ending theme of a short film. Gentle piano lead with soft sustained
strings, light acoustic guitar, and a subtle warm pad. Tender, hopeful, and nostalgic.
No vocals.

### Arrangement
Bar 1-2 (Intro): solo piano states the main theme. Bar 3-5 (Theme A): strings and
acoustic guitar enter beneath the piano melody, texture gently grows. Bar 6-8 (Theme B):
the melody lifts to a higher, warmer phrase, full strings carry the emotional peak.
Bar 9-10 (Ending): pull back to piano alone, play a short closing cadence and let the
last chord ring out, finishing cleanly at exactly 30.0 seconds. Do not end before 30
seconds.
```

## 时长控制（重要）

`--duration`（max_duration）是**上限不是保证**——模型按内容密度自己决定实际长度。

- 30s 上限 + 稀疏编排 → 实测只出 15.1s；
- 30s 上限 + 按小节写满 10 小节结构 + `exactly 30 seconds / Do not end before 30 seconds`
  → 实测 27.6s；
- 210s 上限 + 完整歌词 → 实测 2 分 03 秒。

做法：按 `每小节 ≈ 240/BPM 秒`（4/4 拍）规划小节数，在 Arrangement 里逐段标
`Bar x-y (段落名): 内容`；纯音乐直接标到每一小节，人声歌写清每段怎么进怎么出。
想留余量就把 `--duration` 设为目标值的 1.1 倍左右，不要设得远超目标（超出部分模型
基本用不满，还浪费采样时间）。

## 歌词写作（--lyrics）

- 段落标记：`[intro] [verse] [chorus] [bridge] [outro]`（纯音乐则整个留空）。
- 纯音乐时可给 `[intro]\n(轻柔的钢琴与木吉他)` 这类提示行；完全留空也行。
- 中文歌词直接写，模型能唱；每行 7~12 字最易唱，主歌 4 行/段、押宽韵（an/ang、iu/ou）。
- 副歌写 4~5 行，第二遍副歌换 1~2 句制造推进（参考示例 A 的《晚安，我的月光》）。
- 行与行之间用两个空格或换行分隔即可，不需要标时值。

```
[Verse 1]
晚风把街灯轻轻调暗
我们并肩走过旧巷
想说的话在舌尖打转
说出口却变成了晚安

[Chorus]
我喜欢你 像月光落满肩膀
不声不响 却把夜晚点亮
世界那么忙 人潮来回流淌
我只想站在 你目光的方向
```

## 曲风/人声词汇速查

| 维度 | 常用英文词 |
|---|---|
| 曲风 | Mandopop ballad, city pop, folk, R&B, lo-fi hip-hop, guochao hip-hop, cinematic, bossa nova, synthwave |
| 人声 | airy / breathy / husky / powerful chest voice / soft head-tone / commanding / tender female vocalist |
| 乐器 | fingerpicked acoustic guitar, lush strings, electric piano pads, brushed drums, sub-bass, suona, guzheng, erhu, dapu drum |
| 情绪 | intimate, heartfelt, nostalgic, hopeful, fiery, cinematic, dreamy, bittersweet |
| 制作 | close-mic, warm analog saturation, wide stereo strings, gentle sidechain pumping |
