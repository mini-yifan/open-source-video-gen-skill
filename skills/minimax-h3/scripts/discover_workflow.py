#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任意 MiniMax H3 ComfyUI 实例上的工作流发现与槽位键推导。

换实例、换工作流都不用手改键名：本脚本拉取当前机器的工作流列表与
workflow JSON，自动选出最适合当前素材的任务工作流，并把它的输入键
推导成一份 slot map（图片/视频/音频槽、提示词、秒数、宽高、步数、LoRA）。

用法:
  export SEETACLOUD_BASE_URL=...
  python3 discover_workflow.py                      # 自动选 u06/u03，写 slot_map.json
  python3 discover_workflow.py --kind u06           # 只在多图参考类里选
  python3 discover_workflow.py --workflow-id "U06-9图3音频-V5"
  python3 discover_workflow.py --out 我的map.json

输出 slot map 结构:
{
  "workflow_id": "...", "kind": "u06",
  "image_keys": ["137:image", ...], "video_keys": [...], "audio_keys": [...],
  "prompt_key": "664:prompt", "seconds_key": "132:value",
  "steps_key": "728:steps", "size_keys": ["665:自定义宽", "665:自定义高"],
  "lora_keys": {"710:lora_name": "710:strength_model"},
  "default_lora": "...", "default_steps": 8, "default_strength": 0.75
}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import httpx

BASE = os.environ.get("SEETACLOUD_BASE_URL", "").rstrip("/")

U06_HINTS = ("u06", "多图", "ref", "9图", "参考")
U03_HINTS = ("u03", "文生")


def client() -> httpx.Client:
    if not BASE:
        sys.exit("请设置 SEETACLOUD_BASE_URL")
    return httpx.Client(timeout=60, verify=False)


def list_workflows(c: httpx.Client) -> list[dict]:
    data = c.get(f"{BASE}/api/workflow/list").json()
    return data.get("workflows") or []


def fetch_workflow_json(c: httpx.Client, wf_id: str) -> dict:
    r = c.get(f"{BASE}/workflows/{wf_id}.json")
    r.raise_for_status()
    return r.json()


def node_iter(wf: dict):
    nodes = wf.get("nodes", wf)
    if isinstance(nodes, dict):
        for nid, n in nodes.items():
            yield str(nid), (n or {})
    else:
        for n in nodes or []:
            yield str(n.get("id")), (n or {})


def class_of(n: dict) -> str:
    return str(n.get("class_type") or n.get("type") or "")


def scalar_inputs(n: dict) -> dict:
    out = {}
    for k, v in (n.get("inputs") or {}).items():
        if not isinstance(v, list):  # links are ["id", idx]
            out[k] = v
    return out


def node_inputs_map(wf: dict) -> dict[str, dict]:
    """nid -> {input_name: value_or_link} for every node."""
    return {nid: dict(n.get("inputs") or {}) for nid, n in node_iter(wf)}


def connected_targets(wf: dict) -> dict[str, set[str]]:
    """nid -> set of input names on OTHER nodes that consume it (via links)."""
    cons: dict[str, set[str]] = {}
    for nid, ins in node_inputs_map(wf).items():
        for iname, v in ins.items():
            if isinstance(v, list) and len(v) >= 2:
                cons.setdefault(str(v[0]), set()).add(f"{nid}:{iname}")
    return cons


def score_candidate(c: httpx.Client, wf_id: str, want: str) -> tuple[int, dict] | None:
    """返回 (能力分, slot map)；不适格返回 None。"""
    try:
        wf = fetch_workflow_json(c, wf_id)
    except Exception:
        return None
    cls = {nid: class_of(n) for nid, n in node_iter(wf)}
    text = " ".join(cls.values()).lower()
    img_nodes = sorted(
        [nid for nid, cl in cls.items() if "loadimage" in cl.lower()],
        key=lambda x: int(x) if x.isdigit() else 0,
    )
    vid_nodes = [nid for nid, cl in cls.items() if "loadvideo" in cl.lower()]
    aud_nodes = [nid for nid, cl in cls.items() if "loadaudio" in cl.lower()]
    ks_nodes = [nid for nid, cl in cls.items()
                if any(k in cl.lower() for k in ("ksampler", "samplercustom", "basicscheduler", "scheduler"))]
    if want == "u06" and not img_nodes:
        return None
    if want == "u03" and img_nodes:
        return None

    cons = connected_targets(wf)
    inputs_map = {nid: scalar_inputs(n) for nid, n in node_iter(wf)}

    # prompt 键：有较大文本或被采样链消费的 text/prompt 输入
    prompt_key = ""
    best_len = 0
    for nid, ins in inputs_map.items():
        for k, v in ins.items():
            if isinstance(v, str) and k in ("prompt", "text", "positive", "正文", "提示词"):
                score = len(v)
                if re.search(r"picture|subject_definitions|镜头|shot", v[:4000], re.I):
                    score += 10_000
                if score > best_len:
                    best_len, prompt_key = score, f"{nid}:{k}"
    if want == "u06" and not prompt_key:
        return None

    # 秒数键：名字像时长且数值在 [3, 60]；按名字优先级选，排除音频裁剪类节点
    seconds_key = ""
    name_tiers = (("value", "seconds", "秒数", "视频时长"), ("duration", "时长"))
    for tier in name_tiers:
        for nid, ins in inputs_map.items():
            cl = cls.get(nid, "").lower()
            if "audio" in cl or "trim" in cl:
                continue
            for k in tier:
                v = ins.get(k)
                if isinstance(v, (int, float)) and 3 <= float(v) <= 60:
                    seconds_key = f"{nid}:{k}"
                    break
            if seconds_key:
                break
        if seconds_key:
            break
    # 宽高键
    size_keys: list[str] = []
    for nid, ins in inputs_map.items():
        names = set(ins)
        if {"自定义宽", "自定义高"} <= names:
            size_keys = [f"{nid}:自定义宽", f"{nid}:自定义高"]
            break
        if {"width", "height"} <= names:
            size_keys = [f"{nid}:width", f"{nid}:height"]
            break
    # 步数 / LoRA
    steps_key = ""
    for nid in ks_nodes:
        if "steps" in inputs_map.get(nid, {}):
            steps_key = f"{nid}:steps"
            break
    lora_keys: dict[str, str] = {}
    for nid, cl in cls.items():
        if "loraloader" in cl.lower() and "lora_name" in inputs_map.get(nid, {}):
            lora_keys[f"{nid}:lora_name"] = f"{nid}:strength_model"

    score = len(img_nodes) * 10 + len(ks_nodes) * 5 + (10 if prompt_key else 0) + (5 if seconds_key else 0)
    run_count = 0
    for w in list_workflows(c):
        if w.get("id") == wf_id:
            run_count = int(w.get("run_count") or 0)
            break
    score += min(run_count, 50) // 5

    amap = {
        "workflow_id": wf_id,
        "kind": want,
        "image_keys": [f"{nid}:image" for nid in img_nodes],
        "video_keys": [f"{nid}:video" for nid in vid_nodes],
        "audio_keys": [f"{nid}:audio" for nid in aud_nodes],
        "prompt_key": prompt_key,
        "seconds_key": seconds_key,
        "steps_key": steps_key,
        "size_keys": size_keys,
        "lora_keys": lora_keys,
        "default_steps": next((inputs_map[nid].get("steps") for nid in ks_nodes if "steps" in inputs_map.get(nid, {})), None),
        "notes": {"image_node_types": sorted({cls[nid] for nid in img_nodes})},
    }
    return score, amap


def discover(c: httpx.Client, want: str = "auto", workflow_id: str = "") -> dict:
    wfs = list_workflows(c)
    if workflow_id:
        got = score_candidate(c, workflow_id, "u06" if not U03_HINTS_KW(workflow_id) else "u03")
        if not got:
            sys.exit(f"指定工作流 {workflow_id} 解析失败或不适格")
        return got[1]
    results: list[tuple[int, str, dict]] = []
    for w in wfs:
        wid = w.get("id") or ""
        low = wid.lower()
        kind = None
        if want in ("u06", "u03"):
            kind = want
        elif any(h in low for h in U06_HINTS):
            kind = "u06"
        elif any(h in low for h in U03_HINTS):
            kind = "u03"
        if not kind:
            continue
        got = score_candidate(c, wid, kind)
        if got:
            results.append((got[0] + min(int(w.get("run_count") or 0), 100) // 10, wid, got[1]))
    if not results:
        sys.exit("没有发现可用的工作流（检查 SEETACLOUD_BASE_URL / ComfyUI 状态）")
    results.sort(key=lambda r: r[0], reverse=True)
    score, wid, amap = results[0]
    print(f"选中 {wid} (score={score})；候选：", [(s, i) for s, i, _ in results[:5]], flush=True)
    return amap


def U03_HINTS_KW(wf_id: str) -> bool:
    low = wf_id.lower()
    return any(h in low for h in U03_HINTS) and not any(h in low for h in U06_HINTS)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--kind", choices=("auto", "u03", "u06"), default="auto")
    p.add_argument("--workflow-id", default="")
    p.add_argument("--out", default="slot_map.json")
    a = p.parse_args()
    c = client()
    amap = discover(c, a.kind, a.workflow_id)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(amap, f, ensure_ascii=False, indent=2)
    print(json.dumps(amap, ensure_ascii=False, indent=2))
    print("saved", a.out, flush=True)


if __name__ == "__main__":
    main()
