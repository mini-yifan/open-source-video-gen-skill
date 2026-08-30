#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSH into a SeetaCloud/AutoDL box, print SEETACLOUD_BASE_URL, GPU, H3 workflows.

用法:
  export SEETACLOUD_SSH_PASSWORD='...'
  python3 connect_server.py --host connect.westd.seetacloud.com --port 15331 --user root

不要把密码写进文件。依赖本机 expect。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import httpx

REMOTE_CMD = r"""echo PANEL_BEGIN
cat /root/面板地址.txt 2>/dev/null
cat /root/panel*.txt 2>/dev/null
find /root -maxdepth 2 -type f \( -name "*面板*" -o -name "*panel*" -o -name "*地址*" \) 2>/dev/null | head -5 | xargs -r -n1 cat 2>/dev/null
for p in 6006 8188 3000 7860; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "http://127.0.0.1:$p/api/system_stats" 2>/dev/null)
  [ "$code" = "200" ] && echo "LOCAL_COMFY:http://127.0.0.1:$p"
done
echo PANEL_END
echo GPU_BEGIN; nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu --format=csv,noheader 2>/dev/null; echo GPU_END
echo LORA_BEGIN; ls /root/ComfyUI/models/loras/minimax 2>/dev/null; echo LORA_END"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Discover SeetaCloud ComfyUI panel via SSH")
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=22)
    p.add_argument("--user", default="root")
    p.add_argument("--password", default=os.environ.get("SEETACLOUD_SSH_PASSWORD", ""))
    return p.parse_args()


def ssh_expect(host: str, port: int, user: str, password: str, command: str) -> str:
    expect_bin = shutil.which("expect")
    if not expect_bin:
        sys.exit("需要本机 expect（macOS 自带 /usr/bin/expect）")
    # Write expect script to a temp file so password quoting stays safe.
    fd, path = tempfile.mkstemp(prefix="h3ssh_", suffix=".exp")
    os.close(fd)
    try:
        # Tcl 双引号会替换 $ 和 [ ]，远程命令里的 shell 变量必须先转义；
        # 密码通过环境变量注入 expect，绝不写进脚本文本，避免引号/特殊字符问题。
        # 超时必须 ≥180s：实例刚开机时 ComfyUI 冷启动占满磁盘/CPU，远端探测命令
        # （find/nvidia-smi/curl）可能远慢于空闲期；40s 会在输出齐全前被 expect 杀掉，
        # 表现为“间歇性拿不到面板地址”。
        tcl_cmd = json.dumps(command).replace("$", "\\$").replace("[", "\\[")
        body = f"""set timeout 180
log_user 1
spawn ssh -o StrictHostKeyChecking=accept-new -o PreferredAuthentications=password -o PubkeyAuthentication=no -p {port} {user}@{host} {tcl_cmd}
expect {{
  -re "(?i)password:" {{ send "$env(SEETACLOUD_SSH_PW)\\r" }}
  timeout {{ puts "TIMEOUT_PASSWORD"; exit 1 }}
}}
expect eof
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        proc = subprocess.run(
            [expect_bin, path],
            capture_output=True,
            text=True,
            env={**os.environ, "SEETACLOUD_SSH_PW": password},
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0 and "PANEL_BEGIN" not in out:
            sys.exit(f"SSH 失败 (exit {proc.returncode}):\n{out[-2000:]}")
        return out
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def extract_panel(text: str) -> str:
    text = text.replace("\r", "")
    # 关键：expect 会把 spawn 的整条命令回显进输出，命令文本里就包含
    # PANEL_BEGIN/PANEL_END 字样；用 find（首个）会匹配到回显而不是远端输出。
    # 必须用最后一次出现的标记对（远端输出一定在回显之后）。
    b = text.rfind("PANEL_BEGIN")
    e = text.rfind("PANEL_END")
    if b != -1 and e != -1 and e > b:
        blob = text[b + len("PANEL_BEGIN"):e]
    else:
        blob = text
    urls = re.findall(r"https://[^\s\"'<>]+?\.(?:seetacloud|autodl)\.com:\d+", blob)
    if not urls:
        urls = re.findall(r"https://[^\s\"'<>]+?:\d{2,5}", blob)
    if not urls:
        sys.exit("未找到面板地址。确认 /root/面板地址.txt 存在。\n" + text[-1500:])
    return urls[0].rstrip("/")


def main() -> None:
    args = parse_args()
    if not args.password:
        sys.exit("设置 SEETACLOUD_SSH_PASSWORD 或传入 --password")
    raw = ssh_expect(args.host, args.port, args.user, args.password, REMOTE_CMD)
    panel = extract_panel(raw)
    gpu_m = re.search(r"GPU_BEGIN\s*(.*?)\s*GPU_END", raw, re.S)
    lora_m = re.search(r"LORA_BEGIN\s*(.*?)\s*LORA_END", raw, re.S)
    print("SEETACLOUD_BASE_URL=" + panel)
    if gpu_m:
        print("GPU:", " ".join(gpu_m.group(1).split()))
    print("== 健康检查 ==")
    client = httpx.Client(timeout=20, verify=False)
    try:
        st = client.get(panel + "/api/comfy/status")
        q = client.get(panel + "/api/comfy/queue-status")
        print("status:", st.text.strip())
        print("queue:", q.text.strip())
        wf = client.get(panel + "/api/workflow/list")
        data = wf.json()
        print("== H3 工作流 ==")
        for w in data.get("workflows") or []:
            wid = w.get("id") or ""
            if any(k in wid.lower() for k in ("u0", "minimax", "h3", "light2v")):
                print(f"  {w.get('run_count', 0):4}  {wid}")
    except Exception as e:
        print("API 失败:", e)
        sys.exit(1)
    if lora_m:
        names = [ln.strip() for ln in lora_m.group(1).splitlines() if ln.strip()]
        print("== turbo LoRA ==")
        for n in names:
            if "turbo" in n.lower() or "lightx2v" in n.lower() or "4step" in n.lower() or "8step" in n.lower():
                print(" ", n)
    print("export SEETACLOUD_BASE_URL=" + json.dumps(panel))


if __name__ == "__main__":
    main()
