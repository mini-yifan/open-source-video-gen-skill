#!/usr/bin/env bash
# 环境自检：凭证与本地工具逐项检查，输出 ✓/✗ 与修复提示。
# 用法：bash scripts/doctor.sh [--probe]
#   --probe 额外真实探活（调 AutoDL API 列实例）
# 退出码：0 全部硬必需项就绪；1 存在缺失（详见输出）。
#
# 音乐不再走 TokenHub/腾讯云 API（2026-08-31 已移除）。独立配乐与 TTS
# 共用 AUTODL_TOKEN，在同一台 MINIMAX-H3 实例上跑。

set -u
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROBE="${1:-}"
MISSING_HARD=0

head -3 "$REPO_ROOT/SETUP.md" >/dev/null 2>&1 || true

line() { printf '%s\n' "$*"; }
ok()   { line "  [✓] $*"; }
bad()  { line "  [✗] $*"; }
tip()  { line "      → $*"; }
skip() { line "  [－] $*"; }

# 不 source 私有文件（避免执行任意内容），只做只读存在性检查
env_file_has() { # $1=file $2=var
  [ -f "$1" ] && grep -qE "^[[:space:]]*(export[[:space:]]+)?$2=.." "$1"
}

line ""
line "=== 一、硬必需：AutoDL Token 与实例 ==="
AUTODL_ENV="${AUTODL_ENV_FILE:-$HOME/.config/autodl.env}"
if [ -n "${AUTODL_TOKEN:-}" ] || env_file_has "$AUTODL_ENV" AUTODL_TOKEN; then
  ok "AUTODL_TOKEN 已配置（环境变量或 $AUTODL_ENV）"
else
  bad "AUTODL_TOKEN 未配置（视频生成必需，无替代）"
  tip "申请：autodl.com → 账号 → 设置 → 开发者 Token（不要加 Bearer）"
  tip "存储：echo 'export AUTODL_TOKEN=...' > ~/.config/autodl.env && chmod 600 ~/.config/autodl.env"
  MISSING_HARD=1
fi

line ""
line "=== 二、默认可换：生图（优先 Agent 自带，备选 Cursor） ==="
CURSOR_MJS="$REPO_ROOT/skills/cursor-image-gen/scripts/generate_with_cursor.mjs"
if command -v node >/dev/null 2>&1 && [ -f "$CURSOR_MJS" ]; then
  if node "$CURSOR_MJS" --doctor 2>/dev/null | grep -q '"logged_in"[[:space:]]*:[[:space:]]*true'; then
    ok "Cursor Agent 已登录（备选生图执行器可用）"
  else
    skip "Cursor Agent 未登录（可换：Agent 自带生图优先，不必装 Cursor）"
    tip "当前 Agent 有生图能力即可零配置；点名 Cursor 时再 login 或设 CURSOR_API_KEY"
    tip "见 SETUP.md 第 2 节"
  fi
else
  skip "无法检查 Cursor 登录状态（缺 node 或脚本不存在）——Agent 自带生图仍可用"
  tip "需要 Cursor 生图时安装 Node.js 后重试；见 SETUP.md 第 2 节"
fi

line ""
line "=== 三、可选增强：音乐生成与 TTS 配音 ==="
skip "MiniMax Music 3 / Qwen3-TTS 共用上面的 AUTODL_TOKEN，无需新凭证"
tip "H3 视频自带音轨与对白；独立配乐/配音见 SETUP.md 第 3 节"
if command -v expect >/dev/null 2>&1; then
  ok "expect（音乐 scp 与 TTS SSH 通道需要）"
else
  skip "expect 未安装（视频生成不需要；minimax-music-gen / qwen3-tts 需要）"
  tip "macOS 自带；Debian/Ubuntu: sudo apt install expect"
fi

line ""
line "=== 四、本地工具 ==="
for tool in python3 node ffmpeg ffprobe curl; do
  if command -v "$tool" >/dev/null 2>&1; then
    ok "$tool"
  else
    bad "$tool 未安装"
    tip "macOS: brew install $tool （ffmpeg 常缺；curl 系统一般自带）"
    MISSING_HARD=1
  fi
done

if command -v python3 >/dev/null 2>&1; then
  if python3 -c "import httpx" >/dev/null 2>&1; then
    ok "python3 模块 httpx（minimax-h3 提交/轮询必需）"
  else
    bad "python3 缺少 httpx（minimax-h3 无法提交或轮询）"
    tip "pip3 install httpx    或    pip3 install -r requirements.txt"
    MISSING_HARD=1
  fi
  if python3 -c "import numpy, cv2" >/dev/null 2>&1; then
    ok "numpy + opencv-python（beauty-video-gen 滤镜）"
  else
    skip "numpy/opencv-python 未安装（仅 beauty-video-gen 提亮滤镜需要）"
    tip "pip3 install numpy opencv-python    或    pip3 install -r requirements.txt"
  fi
fi

# expect/sshpass 只是面板发现的 SSH 兜底（主路径是快照域名直探，见 autodl-app-instance SKILL.md）
if command -v sshpass >/dev/null 2>&1; then
  ok "sshpass（面板发现的 SSH 兜底可用）"
else
  skip "sshpass 没有——不影响开机找面板（Windows 默认如此）"
fi

if [ "$PROBE" = "--probe" ]; then
  line ""
  line "=== 五、真实探活（--probe） ==="
  AUTODL_APP="$REPO_ROOT/skills/autodl-app-instance/scripts/autodl_app.py"
  if command -v python3 >/dev/null 2>&1 && [ -f "$AUTODL_APP" ]; then
    line "  -- AutoDL API（列实例，同时验证 Token 与实例存在）"
    if python3 "$AUTODL_APP" list 2>&1 | head -20; then
      :
    else
      bad "AutoDL API 调用失败（检查 Token 或网络）"
      MISSING_HARD=1
    fi
  fi
  skip "音乐/TTS 探活：与 AutoDL 实例相同，不再探测已移除的 TokenHub 端点"
fi

line ""
if [ "$MISSING_HARD" -eq 0 ]; then
  line "结论：硬必需项全部就绪，可以开始生成视频。详细教程见 SETUP.md。"
else
  line "结论：存在硬必需项缺失，按上面每条 → 提示修复后重跑。详细教程见 SETUP.md。"
fi
exit "$MISSING_HARD"
