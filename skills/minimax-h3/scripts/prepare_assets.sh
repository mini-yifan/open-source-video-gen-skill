#!/usr/bin/env bash
# 生成黑场/静音/暗帧占位，或缩小过大参考图。
#   bash prepare_assets.sh --placeholders [--dark 768x1344]
#   bash prepare_assets.sh --scale <输入目录> <输出目录>
set -euo pipefail

resolve_ffmpeg() {
  if command -v ffmpeg >/dev/null 2>&1; then
    command -v ffmpeg
    return
  fi
  python3 - <<'PY'
import shutil, sys
p = shutil.which("ffmpeg")
if p:
    print(p); sys.exit(0)
try:
    import imageio_ffmpeg
    print(imageio_ffmpeg.get_ffmpeg_exe())
except Exception:
    sys.exit(1)
PY
}

FFMPEG="$(resolve_ffmpeg)" || {
  echo "需要 ffmpeg，或 pip 安装 imageio-ffmpeg"
  exit 1
}

DO_PLACEHOLDERS=0
DO_SCALE=0
DARK_SIZE="768x1344"
SCALE_IN=""
SCALE_OUT=""

usage() {
  echo "用法:"
  echo "  bash prepare_assets.sh --placeholders [--dark 768x1344]"
  echo "  bash prepare_assets.sh --scale <输入目录> <输出目录>"
  exit "${1:-1}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --placeholders) DO_PLACEHOLDERS=1; shift ;;
    --dark) DARK_SIZE="${2:?}"; shift 2 ;;
    --scale)
      DO_SCALE=1
      SCALE_IN="${2:?}"
      SCALE_OUT="${3:?}"
      shift 3
      ;;
    -h|--help) usage 0 ;;
    *)
      if [[ $DO_SCALE -eq 0 && $DO_PLACEHOLDERS -eq 0 && -d "$1" ]]; then
        DO_PLACEHOLDERS=1
        DO_SCALE=1
        SCALE_IN="$1"
        SCALE_OUT="${2:-素材_small}"
        break
      fi
      usage
      ;;
  esac
done

if [[ $DO_PLACEHOLDERS -eq 0 && $DO_SCALE -eq 0 ]]; then
  usage
fi

if [[ $DO_PLACEHOLDERS -eq 1 ]]; then
  echo "== 生成占位素材 =="
  "$FFMPEG" -y -loglevel error -f lavfi -i color=black:s=64x64:r=24 -t 1 \
    -c:v libx264 -pix_fmt yuv420p blank_1s.mp4
  "$FFMPEG" -y -loglevel error -f lavfi -i anullsrc=r=44100:cl=mono -t 1 \
    -c:a libmp3lame silence_1s.mp3
  "$FFMPEG" -y -loglevel error -f lavfi -i "color=c=0x0a0a0a:s=${DARK_SIZE}:d=1" \
    -frames:v 1 neutral_dark.png
  echo "  blank_1s.mp4 / silence_1s.mp3 / neutral_dark.png (${DARK_SIZE})"
fi

if [[ $DO_SCALE -eq 1 ]]; then
  mkdir -p "$SCALE_OUT"
  echo "== 缩小过大参考图（等比放入 1024x1820） =="
  shopt -s nullglob
  files=("$SCALE_IN"/*.png "$SCALE_IN"/*.jpg "$SCALE_IN"/*.jpeg "$SCALE_IN"/*.webp)
  if [[ ${#files[@]} -eq 0 ]]; then
    echo "  目录内没有图: $SCALE_IN"
    exit 1
  fi
  for f in "${files[@]}"; do
    name=$(basename "$f")
    "$FFMPEG" -y -loglevel error -i "$f" \
      -vf "scale='min(1024,iw)':'min(1820,ih)':force_original_aspect_ratio=decrease" \
      "$SCALE_OUT/$name"
    echo "  $name -> $SCALE_OUT/$name"
  done
fi

echo "== 完成 =="
