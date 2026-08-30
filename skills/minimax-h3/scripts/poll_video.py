#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轮询 H3 任务并下载 mp4。result 里 type=image 但 url 以 .mp4 结尾也算成功。

用法:
  python3 poll_video.py <prompt_id> [--timeout 1800] [--download 输出.mp4]
环境变量: SEETACLOUD_BASE_URL
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import httpx

BASE = os.environ.get("SEETACLOUD_BASE_URL", "").rstrip("/")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("prompt_id")
    p.add_argument("timeout_pos", nargs="?", type=int)
    p.add_argument("--timeout", type=int, default=1800)
    p.add_argument("--download")
    args = p.parse_args()
    if args.timeout_pos is not None:
        args.timeout = args.timeout_pos
    return args


def mp4_name(obj) -> str | None:
    """Return a downloadable path: /output[/subfolder]/file.mp4 or a URL."""
    if isinstance(obj, str) and obj.lower().split("?")[0].endswith(".mp4"):
        s = obj.split("?")[0]
        if s.startswith("http") or s.startswith("/"):
            return s
        return os.path.basename(s)
    if isinstance(obj, dict):
        url = obj.get("url")
        if isinstance(url, str) and url.lower().split("?")[0].endswith(".mp4"):
            s = url.split("?")[0]
            if s.startswith("http") or s.startswith("/"):
                return s
            return os.path.basename(s)
        filename = obj.get("filename") or obj.get("name") or obj.get("file")
        if isinstance(filename, str) and filename.lower().split("?")[0].endswith(".mp4"):
            name = os.path.basename(filename.split("?")[0])
            sub = (obj.get("subfolder") or "").strip("/")
            if sub:
                return f"/output/{sub}/{name}"
            return name
        raw = obj.get("raw")
        if isinstance(raw, dict):
            return mp4_name(raw)
    return None


def history_mp4s_and_error(client: httpx.Client, pid: str) -> tuple[list[str], dict | None, dict]:
    h = client.get(f"{BASE}/api/comfy/proxy/history", params={"prompt_id": pid})
    hd = h.json()
    if pid not in hd:
        return [], None, {}
    entry = hd[pid]
    names: list[str] = []
    for _nid, out in (entry.get("outputs") or {}).items():
        if not isinstance(out, dict):
            continue
        for key in ("videos", "images", "gifs", "files"):
            for item in out.get(key) or []:
                n = mp4_name(item)
                if n and n not in names:
                    names.append(n)
    status = entry.get("status") or {}
    err = None
    t0 = t1 = None
    for msg in status.get("messages") or []:
        if not (isinstance(msg, (list, tuple)) and len(msg) >= 2):
            continue
        if msg[0] == "execution_error":
            err = msg[1] if isinstance(msg[1], dict) else {"raw": msg[1]}
        if msg[0] == "execution_start" and isinstance(msg[1], dict):
            t0 = msg[1].get("timestamp")
        if msg[0] == "execution_success" and isinstance(msg[1], dict):
            t1 = msg[1].get("timestamp")
    if t0 and t1:
        status = dict(status)
        status["comfy_sec"] = round((t1 - t0) / 1000, 1)
    return names, err, status


def download_file(filename: str, dest: str) -> None:
    if filename.startswith("http"):
        url = filename
    elif filename.startswith("/"):
        url = BASE + filename
    else:
        url = f"{BASE}/output/{filename}"
    last_err = None
    for attempt in range(1, 6):
        try:
            r = httpx.Client(timeout=300, verify=False).get(url)
            r.raise_for_status()
            os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
            with open(dest, "wb") as f:
                f.write(r.content)
            print("downloaded:", dest, "bytes:", len(r.content), "url:", url, flush=True)
            return
        except Exception as e:
            last_err = e
            print(f"[download retry {attempt}/5] {e}", flush=True)
            time.sleep(4 * attempt)
    raise last_err


def names_from_results(results: list) -> list[str]:
    names = []
    for item in results:
        n = mp4_name(item)
        if n and n not in names:
            names.append(n)
    return names


def queue_ids(client: httpx.Client) -> tuple[set[str], set[str]]:
    """返回 (running, pending) 两个 prompt_id 集合；兼容多种 queue-status 返回形状。"""
    try:
        d = client.get(f"{BASE}/api/comfy/queue-status").json()
    except Exception:
        return set(), set()
    running: set[str] = set()
    pending: set[str] = set()
    for i in d.get("queue_running") or []:
        if isinstance(i, dict) and i.get("prompt_id"):
            running.add(str(i["prompt_id"]))
    for i in d.get("queue_pending") or []:
        if isinstance(i, dict) and i.get("prompt_id"):
            pending.add(str(i["prompt_id"]))
    for pid in d.get("prompt_ids") or []:
        pending.add(str(pid))
    return running, pending


def main() -> None:
    args = parse_args()
    if not BASE:
        sys.exit("请设置 SEETACLOUD_BASE_URL")
    client = httpx.Client(timeout=30, verify=False)
    start = time.time()
    stale_warned = False
    while time.time() - start < args.timeout:
        try:
            hist_names, err, status = history_mp4s_and_error(client, args.prompt_id)
            running, waiting = queue_ids(client)
            queued = args.prompt_id in (running | waiting)
            elapsed = int(time.time() - start)
            print(f"[{elapsed}s] queued={queued} history_mp4s={hist_names[:2]}", flush=True)

            # 1) history 里已有本 prompt 的 mp4 → 唯一可信来源
            if hist_names:
                if status.get("comfy_sec") is not None:
                    print("COMFY_SEC", status["comfy_sec"], flush=True)
                if args.download:
                    download_file(hist_names[0], args.download)
                print("DONE", flush=True)
                sys.exit(0)

            # 2) 任务仍在排队/执行：绝不能取 /api/workflow/result——
            #    部分部署对运行中 prompt 会返回“最近一个已完成任务”的旧结果
            if queued:
                if not stale_warned:
                    print("任务运行中；等待 history 出现本 prompt 的结果（不取 result 接口，避免拿到旧视频）", flush=True)
                    stale_warned = True
                time.sleep(15)
                continue

            # 3) 不在队列且 history 无结果：退回 result 接口（旧版机器兼容）
            r = client.get(f"{BASE}/api/workflow/result", params={"prompt_id": args.prompt_id})
            data = r.json()
            results = data.get("results") or []
            pending = data.get("pending")
            names = names_from_results(results)
            if names:
                print("history 为空，使用 result 接口结果（兼容模式）", flush=True)
                if args.download:
                    download_file(names[0], args.download)
                print("DONE", flush=True)
                sys.exit(0)
            if pending is False and not names:
                print("EMPTY_RESULTS: 不是成功", flush=True)
                if err:
                    print("execution_error:", json.dumps(err, ensure_ascii=False, indent=2), flush=True)
                print(json.dumps(status, ensure_ascii=False), flush=True)
                sys.exit(1)
        except Exception as e:
            print(f"[poll error] {e}", flush=True)
        time.sleep(15)
    print("TIMEOUT", flush=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
