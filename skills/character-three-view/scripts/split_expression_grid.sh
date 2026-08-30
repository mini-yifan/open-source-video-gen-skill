#!/usr/bin/env bash
# 将 2×2 表情网格图切分为四张单表情图（表情参考专用）。
# 用法: split_expression_grid.sh <网格图> <输出文件前缀>
# 例:   split_expression_grid.sh /tmp/grid.jpg "美术设定集/表情与表演参考/01_林晚_表情_"
# 输出: <前缀>基线.<ext>  <前缀>受压.<ext>  <前缀>临界.<ext>  <前缀>爆发.<ext>
# 象限映射（与 reference.md 表情网格模板一致）：左上=基线 右上=受压 左下=临界 右下=爆发
# 本脚本不删除网格图；四张切分图逐张验收合格后由调用方删除。

set -euo pipefail

SRC="${1:?用法: $0 <2x2网格图> <输出前缀>}"
PREFIX="${2:?用法: $0 <2x2网格图> <输出前缀>}"

command -v ffmpeg >/dev/null 2>&1 || { echo "错误：需要 ffmpeg" >&2; exit 1; }
[ -f "$SRC" ] || { echo "错误：找不到 $SRC" >&2; exit 1; }

EXT="${SRC##*.}"
[ "$EXT" = "$SRC" ] && EXT="jpg"
DIR="$(dirname "$PREFIX")"
mkdir -p "$DIR"

# 宽高各取一半，crop 支持在 x/y 里用 iw/ih 表达式
ffmpeg -y -v error -i "$SRC" -vf "crop=iw/2:ih/2:0:0"       -frames:v 1 "${PREFIX}基线.${EXT}"
ffmpeg -y -v error -i "$SRC" -vf "crop=iw/2:ih/2:iw/2:0"    -frames:v 1 "${PREFIX}受压.${EXT}"
ffmpeg -y -v error -i "$SRC" -vf "crop=iw/2:ih/2:0:ih/2"    -frames:v 1 "${PREFIX}临界.${EXT}"
ffmpeg -y -v error -i "$SRC" -vf "crop=iw/2:ih/2:iw/2:ih/2" -frames:v 1 "${PREFIX}爆发.${EXT}"

echo "切分完成（请逐张验收后删除网格原图 ${SRC}）："
for name in 基线 受压 临界 爆发; do
  OUT="${PREFIX}${name}.${EXT}"
  SIZE="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$OUT")"
  echo "  $OUT  ${SIZE}"
done
