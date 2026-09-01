#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AutoDL 实例 MiniMax Music 3 音乐生成：开机 → 提交 → 轮询 → scp 下载 → 校验 → 关机。

复用 autodl-app-instance 技能的开关机/API 与 minimax-h3 技能的 SSH 通道。
用法示例见同目录 SKILL.md。密码只经环境变量进入 expect，绝不打印、不落盘。
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import os
import re
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ZCODE_HOME = Path(os.environ.get("ZCODE_HOME", Path.home() / ".zcode"))
CANDIDATE_APP = [
    ZCODE_HOME / "skills/autodl-app-instance/scripts",
    Path.home() / ".codex/skills/autodl-app-instance/scripts",
]
CANDIDATE_SSH = [
    ZCODE_HOME / "skills/minimax-h3/scripts",
    Path.home() / ".codex/skills/minimax-h3/scripts",
]
for p in CANDIDATE_APP:
    if (p / "autodl_app.py").is_file():
        sys.path.insert(0, str(p))
        break
for p in CANDIDATE_SSH:
    if (p / "connect_server.py").is_file():
        sys.path.insert(0, str(p))
        break

import autodl_app as app  # noqa: E402
from connect_server import ssh_expect  # noqa: E402

UNET_FILES = {
    "fp16": "minimax_music3/minimax_music3_dit_fp16.safetensors",
    "fp32": "minimax_music3/minimax_music3_dit_fp32.safetensors",
    "int8": "minimax_music3/minimax_music3_dit_int8_convrot.safetensors",
}


def build_prompt(caption: str, lyrics: str, seed: int, max_duration: float,
                 steps: int, unet: str) -> dict:
    """最小可跑的 MiniMax Music 3 API 图（对应 N08 基础工作流，去掉 bypass 节点）。

    硬规则：保存节点必须用 SaveAudioMP3。SaveAudioAdvanced 的
    COMFY_DYNAMICCOMBO_V3 格式参数经 /prompt API 反序列化会丢 format，
    报 TypeError: missing 1 required positional argument: 'format'。
    """
    slug = "audio/music3_gen"
    return {
        "35": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "minimax_music3_text_encoder_bf16.safetensors",
            "type": "minimax", "device": "default"}},
        "36": {"class_type": "UNETLoader", "inputs": {
            "unet_name": unet, "weight_dtype": "default"}},
        "37": {"class_type": "VAELoader", "inputs": {
            "vae_name": "minimax_music3_dav.safetensors"}},
        "40": {"class_type": "MiniMaxMusic3TextEncode", "inputs": {
            "clip": ["35", 0],
            "caption": caption,          # 英文结构化曲风描述（三段模板）
            "lyrics": lyrics,            # 空 = 纯音乐；带 [verse]/[chorus] = 人声歌
            "seed": seed,
            "max_duration": max_duration,  # 上限而非保证，模型可能提前结束
            "cfg_scale": 1.5,
            "top_k": 60}},
        "41": {"class_type": "ConditioningZeroOut", "inputs": {
            "conditioning": ["40", 0]}},
        "42": {"class_type": "EmptyMiniMaxMusic3LatentAudio", "inputs": {
            "seconds": ["40", 1], "batch_size": 1}},
        "43": {"class_type": "KSampler", "inputs": {
            "model": ["36", 0], "positive": ["40", 0], "negative": ["41", 0],
            "latent_image": ["42", 0],
            "seed": seed, "steps": steps, "cfg": 1.7,
            "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "44": {"class_type": "VAEDecodeAudio", "inputs": {
            "samples": ["43", 0], "vae": ["37", 0]}},
        "45": {"class_type": "SaveAudioMP3", "inputs": {
            "audio": ["44", 0], "filename_prefix": slug, "quality": "V0"}},
    }


def boot_with_stock_retry(uuid: str, retries: int, wait_run: int, wait_comfy: int) -> None:
    for attempt in range(1, retries + 1):
        try:
            app.boot(uuid, wait_run=wait_run, wait_comfy=wait_comfy)
            return
        except RuntimeError as e:
            if "暂无库存" not in str(e):
                raise
            if attempt == retries:
                raise
            print(f"(第 {attempt} 次无库存，等 30s 重试)", flush=True)
            time.sleep(30)


def download_scp(uuid: str, remote: str, local: str) -> None:
    """scp 拉回成品。不要用 base64 走 expect 通道——大文件会被 expect 缓冲截断。"""
    snap = app.snapshot(uuid)
    expect_bin = shutil.which("expect")
    if not expect_bin:
        sys.exit("需要本机 expect（macOS 自带）")
    fd, path = tempfile.mkstemp(prefix="music3_scp_", suffix=".exp")
    os.close(fd)
    with open(path, "w") as f:
        f.write(f"""set timeout 300
log_user 0
spawn scp -O -o StrictHostKeyChecking=accept-new -o PreferredAuthentications=password -o PubkeyAuthentication=no -P {snap['ssh_port']} root@{snap['proxy_host']}:{remote} "{local}"
expect {{
  -re "(?i)password:" {{ send "$env(MUSIC3_SCP_PW)\\r" }}
  timeout {{ puts "TIMEOUT"; exit 1 }}
}}
expect {{
  eof {{ puts "SCP_DONE" }}
  timeout {{ puts "TIMEOUT_TRANSFER"; exit 1 }}
}}
""")
    try:
        proc = subprocess.run([expect_bin, path], capture_output=True, text=True,
                              env={**os.environ, "MUSIC3_SCP_PW": snap["root_password"]})
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    if not (os.path.exists(local) and os.path.getsize(local) > 0):
        print((proc.stdout or "") + (proc.stderr or ""))
        sys.exit(f"scp 下载失败：{local}（0 字节或不存在；检查远端路径是否含 audio/ 子目录）")


def power_off(uuid: str) -> None:
    try:
        if app.instance_status(uuid) == "shutdown":
            print("POWER_OFF_OK already_shutdown", flush=True)
            return
        app.power_off(uuid)
        app.wait_status(uuid, {"shutdown"}, timeout=240)
        print("POWER_OFF_OK", flush=True)
    except SystemExit:
        raise
    except Exception as e:  # 关机失败也要报出来，但不能吞掉主流程的错误
        print(f"POWER_OFF_WARN: {e}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="MiniMax Music 3 on AutoDL 生成音乐")
    ap.add_argument("--caption", required=True,
                    help="英文结构化曲风描述（三段模板，见 references/prompt_guide.md）")
    ap.add_argument("--caption-file")
    ap.add_argument("--lyrics", default="",
                    help="歌词（含 [verse]/[chorus] 标记）= 人声歌；留空 = 纯音乐")
    ap.add_argument("--lyrics-file")
    ap.add_argument("--duration", type=float, default=30.0,
                    help="max_duration 秒数（上限，模型可能提前结束），默认 30")
    ap.add_argument("--seed", type=int, default=None, help="随机种子（默认随机，会打印）")
    ap.add_argument("--steps", type=int, default=30, help="KSampler 步数，默认 30")
    ap.add_argument("--model", choices=list(UNET_FILES), default="fp16",
                    help="DiT 精度：fp16 快（默认）/ fp32 质量 / int8 省显存")
    ap.add_argument("--slug", default="music3", help="输出文件名 slug")
    ap.add_argument("--out", default=None, help="输出 mp3 绝对路径（默认 ~/Music/minimax-gen/）")
    ap.add_argument("--uuid", default=os.environ.get("AUTODL_INSTANCE_UUID", ""),
                    help="实例 UUID（默认读环境变量，否则按 MINIMAX-H3 应用匹配）")
    ap.add_argument("--keep-on", action="store_true",
                    help="生成后不关机（批量生成时中间曲目使用，最后一首不加）")
    ap.add_argument("--stock-retries", type=int, default=6, help="无库存重试次数")
    args = ap.parse_args()

    caption = Path(args.caption_file).read_text() if args.caption_file else args.caption
    lyrics = Path(args.lyrics_file).read_text() if args.lyrics_file else args.lyrics
    if not args.uuid:
        ns = argparse.Namespace(uuid="", app=os.environ.get("AUTODL_APP_HINT", "MINIMAX-H3"))
        uuid = app.resolve_uuid(ns)
    else:
        uuid = args.uuid

    seed = args.seed if args.seed is not None else random.randrange(1, 2**31)
    prompt = build_prompt(caption, lyrics, seed, args.duration, args.steps, UNET_FILES[args.model])
    print(f"uuid={uuid} seed={seed} duration<={args.duration} "
          f"lyrics={'yes' if lyrics.strip() else 'NONE(纯音乐)'}", flush=True)

    boot_with_stock_retry(uuid, args.stock_retries, wait_run=240, wait_comfy=240)
    try:
        # 提交（base64 走 SSH，规避中文/换行引号问题）
        snap = app.snapshot(uuid)
        b64 = base64.b64encode(json.dumps({"prompt": prompt}).encode()).decode()
        out = ssh_expect(snap["proxy_host"], int(snap["ssh_port"]), "root",
                         snap["root_password"],
                         f"echo {b64} | base64 -d > /tmp/music3_prompt.json && "
                         'curl -s --max-time 30 -X POST http://127.0.0.1:6006/prompt '
                         '-H "Content-Type: application/json" -d @/tmp/music3_prompt.json')
        line = next((l for l in out.splitlines() if l.startswith("{")), None)
        if not line:
            print(out[-1500:])
            sys.exit("提交失败：ComfyUI 无 JSON 响应（确认 ComfyUI 在 6006 端口）")
        resp = json.loads(line)
        if "prompt_id" not in resp:
            print(json.dumps(resp, ensure_ascii=False)[:2000])
            sys.exit("提交被拒绝（常见：节点参数名不符 / 模型文件缺失）")
        pid = resp["prompt_id"]
        print("prompt_id =", pid, flush=True)

        # 轮询 /history 到终态（10s 一次，上限 30 分钟）
        t0 = time.time()
        filename = None
        while time.time() - t0 < timeout_s_default():
            time.sleep(10)
            h = run_ssh_snapshot(uuid, f'curl -s --max-time 30 "http://127.0.0.1:6006/history/{pid}"')
            start = h.find("{")
            if start < 0:
                print(f"  [{time.time()-t0:6.1f}s] 等待中", flush=True)
                continue
            try:
                hist = json.loads(h[start:])
            except json.JSONDecodeError:
                print(f"  [{time.time()-t0:6.1f}s] 等待中(截断)", flush=True)
                continue
            if pid not in hist:
                print(f"  [{time.time()-t0:6.1f}s] 排队/运行中", flush=True)
                continue
            entry = hist[pid]
            status = entry.get("status", {})
            elapsed = time.time() - t0
            print(f"终态 {status.get('status_str')}，耗时 {elapsed:.1f}s", flush=True)
            if status.get("status_str") == "error":
                errs = [m for m in status.get("messages", []) if m[0] == "execution_error"]
                print(json.dumps(errs, ensure_ascii=False)[:3000], flush=True)
                sys.exit("生成执行出错（读上方 execution_error 定位节点）")
            outputs = entry.get("outputs", {})
            for o in outputs.values():
                for f in o.get("audio", []) or []:
                    filename = f.get("filename")
            if filename:
                break
            print("outputs 为空，继续等", flush=True)
        if not filename:
            sys.exit("轮询超时（30 分钟）")

        # 定位远端实际路径（filename_prefix 带 audio/ 子目录）
        h = run_ssh_snapshot(uuid,
                             'find /root/ComfyUI/output -name "%s" 2>/dev/null' % filename)
        hits = [l.strip() for l in h.splitlines() if "/output/" in l]
        if not hits:
            sys.exit(f"远端找不到 {filename}")
        remote = hits[-1]

        # 下载
        out_dir = Path(os.environ.get("MINIMAX_MUSIC_OUTPUT_DIR")
                       or Path.home() / "Music/minimax-gen")
        local = args.out or str(out_dir / "{}_{}.mp3".format(
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
            re.sub(r"[^\w\u4e00-\u9fff-]+", "_", args.slug)))
        Path(local).parent.mkdir(parents=True, exist_ok=True)
        download_scp(uuid, remote, local)
        print("SAVED:", local, os.path.getsize(local), "bytes", flush=True)

        # 校验
        if shutil.which("ffprobe"):
            p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=noprint_wrappers=1:nokey=1", local],
                               capture_output=True, text=True)
            if p.returncode == 0:
                print("DURATION: %.1fs" % float(p.stdout.strip()), flush=True)
    finally:
        if not args.keep_on:
            power_off(uuid)


def timeout_s_default() -> int:
    return 1800


def run_ssh_snapshot(uuid: str, cmd: str) -> str:
    snap = app.snapshot(uuid)
    return ssh_expect(snap["proxy_host"], int(snap["ssh_port"]), "root",
                      snap["root_password"], cmd)


if __name__ == "__main__":
    main()
