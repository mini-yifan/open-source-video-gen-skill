#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提交 MiniMax H3 任务（U06 多参考 / U03 文生）并写入加速槽。

环境变量: SEETACLOUD_BASE_URL（必填）、SEETACLOUD_WORKFLOW_ID、
DARK_PLACEHOLDER、BLANK_VIDEO、SILENCE_AUDIO
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import httpx

BASE = os.environ.get("SEETACLOUD_BASE_URL", "").rstrip("/")
DEFAULT_U06 = "U06-minimax_h3_light2v多图参考生视频叠加加速插帧优化版X"
DEFAULT_U03 = "U03-minimax_h3_light2v-文生视频加速版"
LORA_768_4 = "minimax/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors"
LORA_FAST_4 = "minimax/minimax_h3_fl2v_lightx2v_turbo_4step_v0.1_comfy_resized_avg_rank_21_bf16.safetensors"
LORA_8 = "minimax/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"

# U06-X MiniMaxH3ReferenceToVideo: ref_image_0 … ref_image_8
IMAGE_SLOT_KEYS = [
    "137:image",
    "139:image",
    "144:image",
    "151:image",
    "653:image",
    "654:image",
    "655:image",
    "656:image",
    "657:image",
]
VIDEO_SLOT_KEYS = ["638:video", "659:video", "660:video"]
AUDIO_SLOT_KEYS = ["143:audio", "661:audio", "662:audio"]
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
VIDEO_EXTS = (".mp4", ".mov", ".webm")
AUDIO_EXTS = (".mp3", ".wav", ".aac", ".m4a")


def resolve_asset(path: str) -> str:
    if os.path.isfile(path):
        return path
    alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(path))
    return alt if os.path.isfile(alt) else path


DARK = resolve_asset(os.environ.get("DARK_PLACEHOLDER", "neutral_dark.png"))
BLANK_VIDEO = resolve_asset(os.environ.get("BLANK_VIDEO", "blank_1s.mp4"))
SILENCE_AUDIO = resolve_asset(os.environ.get("SILENCE_AUDIO", "silence_1s.mp3"))


def mime_for(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".aac": "audio/aac",
        ".m4a": "audio/mp4",
    }.get(ext, "application/octet-stream")


def list_media(directory: str, exts: tuple[str, ...]) -> list[str]:
    if not directory:
        return []
    return sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith(exts)
    )


def pick_lora(preset: str, width: int, height: int) -> str | None:
    if preset == "quality":
        return None
    if preset == "balanced":
        return LORA_8
    short = min(width, height)
    if short >= 768:
        return LORA_768_4
    return LORA_FAST_4


def pick_steps(preset: str, override: int | None) -> int:
    if override is not None:
        return override
    return {"speed": 4, "balanced": 8, "quality": 24}[preset]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Submit MiniMax H3 job")
    p.add_argument("--prompt", required=True)
    p.add_argument("--seconds", type=float, default=10)
    p.add_argument("--width", type=int, default=768)
    p.add_argument("--height", type=int, default=1344)
    p.add_argument("--steps", type=int, default=None, help="覆盖 preset 步数")
    p.add_argument("--preset", choices=("speed", "balanced", "quality"), default="speed")
    p.add_argument("--workflow", choices=("auto", "u06", "u03"), default="auto")
    p.add_argument("--workflow-id", default=os.environ.get("SEETACLOUD_WORKFLOW_ID", ""))
    p.add_argument("--slot-map", default=os.environ.get("SEETACLOUD_SLOT_MAP", ""),
                   help="discover_workflow.py 生成的槽位映射 JSON；未提供且 --auto-discover 开启时自动推导")
    p.add_argument("--auto-discover", dest="auto_discover", action="store_true", default=True,
                   help="没有 slot map 时自动发现工作流并推导槽位键（换实例不用改代码）")
    p.add_argument("--no-auto-discover", dest="auto_discover", action="store_false")
    p.add_argument("--lora", default="", help="覆盖 LoRA 文件名")
    p.add_argument("--image-dir")
    p.add_argument("--image", action="append", default=[], dest="images")
    p.add_argument("--video", action="append", default=[], dest="videos")
    p.add_argument("--audio", action="append", default=[], dest="audios")
    p.add_argument("--out-json", default="task_info.json")
    return p.parse_args()


def upload(client: httpx.Client, path: str) -> str:
    if not os.path.isfile(path):
        sys.exit(f"找不到文件: {path}")
    with open(path, "rb") as f:
        resp = client.post(
            f"{BASE}/api/comfy/upload/file",
            files={"file": (os.path.basename(path), f, mime_for(path))},
            data={"overwrite": "true"},
        )
    resp.raise_for_status()
    name = resp.json()["name"]
    print("  upload ok:", os.path.basename(path), "->", name, flush=True)
    return name


def fill_slots(client: httpx.Client, keys: list[str], paths: list[str], filler: str | None, label: str) -> dict:
    uploaded: dict[str, str] = {}
    for key, path in zip(keys, paths):
        uploaded[key] = upload(client, path)
    if len(paths) > len(keys):
        extra = [os.path.basename(p) for p in paths[len(keys) :]]
        print(f"  警告: {label} 共 {len(paths)} 个，只用 {len(keys)} 槽，未上传: {', '.join(extra)}", flush=True)
    if len(paths) < len(keys):
        if not filler:
            sys.exit(f"{label} 不足 {len(keys)} 槽且没有占位文件")
        fill_name = upload(client, filler)
        for key in keys[len(paths) :]:
            print(f"  {label}槽 {key} 空，占位 {os.path.basename(filler)}", flush=True)
            uploaded[key] = fill_name
    return uploaded


def resolve_workflow(client: httpx.Client, kind: str, explicit: str, has_images: bool) -> tuple[str, str]:
    if explicit:
        return explicit, "u03" if ("U03" in explicit or "文生" in explicit) else "u06"
    want = kind if kind in ("u03", "u06") else ("u03" if not has_images else "u06")
    target = "U03" if want == "u03" else "U06"
    try:
        data = client.get(f"{BASE}/api/workflow/list").json()
        cands = [w for w in (data.get("workflows") or []) if target in (w.get("id") or "")]
        if want == "u06":
            x = [w for w in cands if (w.get("id") or "").endswith(("X", "x"))]
            pool = x or cands
            pool.sort(key=lambda w: w.get("run_count") or 0, reverse=True)
        else:
            pool = [w for w in cands if "文生" in (w.get("id") or "")] or cands
        if pool:
            return pool[0]["id"], want
    except Exception as e:
        print("workflow list 失败，用默认 id:", e, flush=True)
    return (DEFAULT_U03 if want == "u03" else DEFAULT_U06), want


def generate(client: httpx.Client, workflow: str, input_values: dict) -> dict:
    resp = client.post(f"{BASE}/api/workflow/generate", json={"workflow_id": workflow, "input_values": input_values})
    print("status:", resp.status_code, flush=True)
    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    if data.get("success"):
        return data
    print("提交失败，改 workflow_template:", data, flush=True)
    resp = client.post(
        f"{BASE}/api/workflow/generate",
        json={"workflow_template": workflow, "input_values": input_values},
    )
    print("status:", resp.status_code, flush=True)
    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    if not data.get("success"):
        print("resp:", resp.text[:1500], flush=True)
        sys.exit(1)
    return data


def load_slot_map(args, client):
    """slot map：--slot-map / SEETACLOUD_SLOT_MAP 文件优先；否则自动发现；失败返回 None 走内置键位。"""
    if args.slot_map:
        if not os.path.isfile(args.slot_map):
            sys.exit(f"slot map 不存在: {args.slot_map}")
        with open(args.slot_map, encoding="utf-8") as f:
            m = json.load(f)
        print("使用 slot map:", args.slot_map, "->", m.get("workflow_id"), flush=True)
        return m
    if args.auto_discover:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import discover_workflow as dw
            has_media = bool(args.images or args.image_dir)
            want = "u06" if has_media else ("u03" if args.workflow == "u03" else "auto")
            m = dw.discover(client, want=want, workflow_id=args.workflow_id or "")
            print("自动发现工作流:", m.get("workflow_id"), flush=True)
            return m
        except SystemExit as e:
            print("slot map 自动发现失败，回退内置键位:", e, flush=True)
        except Exception as e:
            print("slot map 自动发现失败，回退内置键位:", e, flush=True)
    return None


def build_inputs_from_map(client, m: dict, prompt: str, images: list[str], videos: list[str],
                          audios: list[str], seconds: float, width: int, height: int,
                          steps: int, lora: str) -> dict:
    """按 slot map 组装 input_values；所有媒体槽全部占位，防止服务器模板素材污染（如默认 p2.MP3）。"""
    if not m.get("prompt_key"):
        sys.exit(f"slot map 缺少 prompt_key，无法提交: {m.get('workflow_id')}")
    input_values: dict = {}
    input_values.update(fill_slots(client, m.get("image_keys") or [], images, DARK, "图"))
    input_values.update(fill_slots(client, m.get("video_keys") or [], videos, BLANK_VIDEO, "视频"))
    # 音频槽即使不用也必须占位：部分实例的 LoadAudio 默认文件会被当作参考音频灌进生成
    input_values.update(fill_slots(client, m.get("audio_keys") or [], audios, SILENCE_AUDIO, "音频"))
    input_values[m["prompt_key"]] = prompt
    if m.get("seconds_key"):
        input_values[m["seconds_key"]] = seconds
    if m.get("steps_key") and steps:
        input_values[m["steps_key"]] = steps
    for k in m.get("size_keys") or []:
        input_values[k] = width if ("宽" in k or "width" in k.lower()) else height
    if lora:
        for lk, sk in (m.get("lora_keys") or {}).items():
            input_values[lk] = lora
            input_values[sk] = 1
    return input_values


def main() -> None:
    args = parse_args()
    if not BASE:
        sys.exit("请设置 SEETACLOUD_BASE_URL（先跑 connect_server.py）")
    with open(args.prompt, encoding="utf-8") as f:
        prompt = f.read().strip()
    if not prompt:
        sys.exit("prompt 为空")

    images = list(args.images)
    if args.image_dir:
        images.extend(list_media(args.image_dir, IMAGE_EXTS))
    seen: set[str] = set()
    images = [p for p in images if not (p in seen or seen.add(p))]

    steps = pick_steps(args.preset, args.steps)
    lora = args.lora or pick_lora(args.preset, args.width, args.height)

    client = httpx.Client(timeout=180, verify=False)
    slot_map = load_slot_map(args, client)
    if slot_map:
        workflow = slot_map["workflow_id"]
        kind = slot_map.get("kind", "u06")
        print(
            f"== 提交 {kind} id={workflow} preset={args.preset} "
            f"steps={steps} {args.width}x{args.height} {args.seconds}s lora={lora}",
            flush=True,
        )
        input_values = build_inputs_from_map(
            client, slot_map, prompt, images, list(args.videos), list(args.audios),
            args.seconds, args.width, args.height, steps, args.lora or lora,
        )
        data = generate(client, workflow, input_values)
        pid = data["prompt_id"]
        print("\nPROMPT_ID:", pid, flush=True)
        payload = {
            "prompt_id": pid,
            "workflow": workflow,
            "kind": kind,
            "preset": args.preset,
            "seconds": args.seconds,
            "steps": steps,
            "width": args.width,
            "height": args.height,
            "lora": args.lora or lora,
            "images": [os.path.basename(p) for p in images[:9]],
            "videos": [os.path.basename(p) for p in args.videos[:3]],
            "audios": [os.path.basename(p) for p in args.audios[:3]],
            "slot_map": {k: slot_map.get(k) for k in ("image_keys", "video_keys", "audio_keys",
                                               "prompt_key", "seconds_key", "steps_key",
                                               "size_keys", "lora_keys")},
            "prompt_file": args.prompt,
        }
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print("saved", args.out_json, flush=True)
        return

    workflow, kind = resolve_workflow(client, args.workflow, args.workflow_id, bool(images))
    if kind == "u03" and images:
        print("有参考图，改走 U06", flush=True)
        workflow, kind = resolve_workflow(client, "u06", "", True)

    print(
        f"== 提交 {kind} id={workflow} preset={args.preset} "
        f"steps={steps} {args.width}x{args.height} {args.seconds}s lora={lora}",
        flush=True,
    )

    input_values: dict = {}
    if kind == "u03":
        input_values = {
            "105:104:prompt": prompt,
            "105:111:value": args.seconds,
            "105:9:steps": steps,
            "120:自定义宽": args.width,
            "120:自定义高": args.height,
            "121:offload_model": False,
            "121:offload_cache": False,
        }
        if lora:
            input_values["105:127:lora_name"] = lora
            input_values["105:127:strength_model"] = 1
    else:
        if not os.path.isfile(DARK) or not os.path.isfile(BLANK_VIDEO) or not os.path.isfile(SILENCE_AUDIO):
            sys.exit("缺少占位文件。先: bash prepare_assets.sh --placeholders --dark %dx%d" % (args.width, args.height))
        print("== 上传参考图 ==", flush=True)
        if images:
            print("  使用:", ", ".join(os.path.basename(p) for p in images[:9]), flush=True)
            input_values.update(fill_slots(client, IMAGE_SLOT_KEYS, images, DARK, "图"))
        else:
            print("  无参考图，9 个图槽用暗帧", flush=True)
            input_values.update(fill_slots(client, IMAGE_SLOT_KEYS, [], DARK, "图"))
        print("== 上传参考视频 ==", flush=True)
        input_values.update(fill_slots(client, VIDEO_SLOT_KEYS, args.videos, BLANK_VIDEO, "视频"))
        print("== 上传参考音频 ==", flush=True)
        input_values.update(fill_slots(client, AUDIO_SLOT_KEYS, args.audios, SILENCE_AUDIO, "音频"))
        input_values["664:prompt"] = prompt
        input_values["124:steps"] = steps
        input_values["132:value"] = args.seconds
        input_values["665:自定义宽"] = args.width
        input_values["665:自定义高"] = args.height
        if lora:
            input_values["669:lora_name"] = lora
            input_values["669:strength_model"] = 1
        if args.preset != "quality":
            input_values["676:mode"] = "H3 Fast — 0.10 / max 2"
            input_values["676:threshold"] = 0.1
            input_values["676:max_consecutive_hits"] = 3 if args.preset == "speed" else 2
            input_values["685:enabled"] = True
            input_values["685:warmup_steps"] = 1
            input_values["687:sage_attention"] = "auto"
            input_values["147:batch_size"] = 4
            input_values["147:use_fp16"] = True
            input_values["146:value"] = 60

    data = generate(client, workflow, input_values)
    pid = data["prompt_id"]
    print("\nPROMPT_ID:", pid, flush=True)
    payload = {
        "prompt_id": pid,
        "workflow": workflow,
        "kind": kind,
        "preset": args.preset,
        "seconds": args.seconds,
        "steps": steps,
        "width": args.width,
        "height": args.height,
        "lora": lora,
        "images": [os.path.basename(p) for p in images[:9]],
        "videos": [os.path.basename(p) for p in args.videos[:3]],
        "audios": [os.path.basename(p) for p in args.audios[:3]],
        "prompt_file": args.prompt,
    }
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("saved", args.out_json, flush=True)


if __name__ == "__main__":
    main()
