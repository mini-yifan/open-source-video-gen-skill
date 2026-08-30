#!/usr/bin/env bash
# 环境自检：凭证与本地工具逐项检查，输出 ✓/✗ 与修复提示。
# 用法：bash scripts/doctor.sh [--probe]
#   --probe 额外真实探活（调 AutoDL API 列实例、探测 TokenHub 端点可达性）
# 退出码：0 全部硬必需项就绪；1 存在缺失（详见输出）。

set -u
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROBE="${1:-}"
MISSING_HARD=0

head -3 "$REPO_ROOT/SETUP.md" >/dev/null 2>&1 || true

line() { printf '%s\n' "$*"; }
ok()   { line "  [✓] $*"; }
bad()  { line "  [✗] $*"; }
tip()  { line "      → $*"; }

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
line "=== 二、默认可换：生图（默认 Cursor） ==="
CURSOR_MJS="$REPO_ROOT/skills/cursor-image-gen/scripts/generate_with_cursor.mjs"
if command -v node >/dev/null 2>&1 && [ -f "$CURSOR_MJS" ]; then
  if node "$CURSOR_MJS" --doctor 2>/dev/null | grep -q '"logged_in"[[:space:]]*:[[:space:]]*true'; then
    ok "Cursor Agent 已登录"
  else
    bad "Cursor Agent 未登录（默认生图执行器）"
    tip "登录：cursor-agent login（或设置 CURSOR_API_KEY）"
    tip "替代：Codex 自带生图等其他工具也可，告知 AI 即可，见 SETUP.md 第 2 节"
  fi
else
  bad "无法检查 Cursor 登录状态（缺 node 或脚本不存在）"
  tip "安装 Node.js 后重试；或改用其他生图工具，见 SETUP.md 第 2 节"
fi

line ""
line "=== 三、可选增强：TokenHub 音乐 API ==="
TOKENHUB_ENV="${TOKENHUB_ENV_FILE:-$HOME/.config/tokenhub.env}"
LEGACY_ENV="${MINIMAX_MUSIC_ENV_FILE:-$HOME/.config/minimax-music.env}"
if [ -n "${TOKENHUB_API_KEY:-}" ] || [ -n "${MINIMAX_API_KEY:-}" ] \
  || env_file_has "$TOKENHUB_ENV" TOKENHUB_API_KEY \
  || env_file_has "$TOKENHUB_ENV" MINIMAX_API_KEY \
  || env_file_has "$LEGACY_ENV" TOKENHUB_API_KEY \
  || env_file_has "$LEGACY_ENV" MINIMAX_API_KEY; then
  ok "TokenHub API key 已配置（可选增强已启用）"
else
  line "  [－] TokenHub API key 未配置（可选，不影响出片）"
  tip "H3 生成的视频自带音轨；想叠加独立背景音乐见 SETUP.md 第 3 节"
fi

line ""
line "=== 四、本地工具 ==="
for tool in python3 node ffmpeg ffprobe expect; do
  if command -v "$tool" >/dev/null 2>&1; then
    ok "$tool"
  else
    bad "$tool 未安装"
    tip "macOS: brew install $tool （ffmpeg/expect 常缺）"
    [ "$tool" = "ffmpeg" ] || [ "$tool" = "ffprobe" ] || [ "$tool" = "expect" ] || MISSING_HARD=1
  fi
done

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
  line "  -- TokenHub 端点可达性"
  ENDPOINT="${TOKENHUB_ENDPOINT:-https://tokenhub.tencentmaas.com/v1/wand/minimax-music/generation}"
  CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 "$ENDPOINT" 2>/dev/null || echo 000)"
  if [ "$CODE" != "000" ]; then
    ok "TokenHub 端点可达（HTTP $CODE；401/404/405 属正常，仅验证连通）"
  else
    line "  [－] TokenHub 端点不可达（音乐为可选项，仅影响独立配乐）"
  fi
fi

line ""
if [ "$MISSING_HARD" -eq 0 ]; then
  line "结论：硬必需项全部就绪，可以开始生成视频。详细教程见 SETUP.md。"
else
  line "结论：存在硬必需项缺失，按上面每条 → 提示修复后重跑。详细教程见 SETUP.md。"
fi
exit "$MISSING_HARD"
