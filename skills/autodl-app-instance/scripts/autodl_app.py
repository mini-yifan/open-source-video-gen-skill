#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AutoDL 应用实例：list / status / power-on / power-off / boot / ensure / snapshot.

环境变量:
  AUTODL_TOKEN            开发者 Token（不要加 Bearer）；缺环境变量时回退读
                          ~/.config/autodl.env（可用 AUTODL_ENV_FILE 覆盖路径）
  AUTODL_INSTANCE_UUID    默认实例，如 pro-78672ec11b9c
  AUTODL_APP_HINT         无 UUID 时按应用名匹配，默认 MINIMAX-H3
  AUTODL_API_BASE         默认 https://www.autodl.art
  AUTODL_KEEP_ON          设为 1 时 ensure/boot 结束不关机（仅文档约定，本脚本不自动关）

不要把 Token / SSH 密码写进仓库。本脚本不打印 root_password。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE_DEFAULT = "https://www.autodl.art"
PREFIX = "/api/v1/adl_dev/dev/instance/pro"
def connect_server_path() -> Path:
    sibling = Path(__file__).resolve().parents[2] / "minimax-h3" / "scripts" / "connect_server.py"
    for p in (
        sibling,
        Path.home() / ".zcode/skills/minimax-h3/scripts/connect_server.py",
        Path.home() / ".codex/skills/minimax-h3/scripts/connect_server.py",
        Path.home() / ".cursor/skills/minimax-h3/scripts/connect_server.py",
    ):
        if p.is_file():
            return p
    sys.exit("找不到 minimax-h3 connect_server.py")


def _token_from_env_file(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            parts = line.split("=", 1)
            if len(parts) == 2 and parts[0].strip().removeprefix("export ").strip() == "AUTODL_TOKEN":
                value = parts[1].strip().strip("'\"")
                if value:
                    return value
    except OSError:
        pass
    return ""


def token() -> str:
    t = os.environ.get("AUTODL_TOKEN", "").strip()
    if not t:
        override = os.environ.get("AUTODL_ENV_FILE", "").strip()
        candidates = [Path(override)] if override else [Path.home() / ".config" / "autodl.env"]
        for candidate in candidates:
            if candidate.is_file():
                t = _token_from_env_file(candidate)
                if t:
                    break
    if not t:
        sys.exit(
            "缺少 AUTODL_TOKEN（视频生成必需，无替代）。\n"
            "申请：autodl.com → 账号 → 设置 → 开发者 Token（不要加 Bearer）。\n"
            "存储（三选一）：ZCode 环境变量；~/.zshrc；~/.config/autodl.env\n"
            '  （内容：export AUTODL_TOKEN=...，chmod 600，Agent 非交互 shell 也能直接读取）。\n'
            "注意：终端里 export 不会传到 Agent。"
        )
    if t.lower().startswith("bearer "):
        t = t.split(" ", 1)[1].strip()
    return t


def api_base() -> str:
    return os.environ.get("AUTODL_API_BASE", BASE_DEFAULT).rstrip("/")


def curl_json(method: str, url: str, body: dict | None = None, timeout: int = 25) -> dict:
    cmd = [
        "curl", "-sk", "--max-time", str(timeout),
        "-X", method, url,
        "-H", f"Authorization: {token()}",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json",
        "-w", "\n__HTTPSTATUS__:%{http_code}",
    ]
    if body is not None:
        cmd += ["--data-binary", json.dumps(body)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout or ""
    if p.returncode != 0:
        sys.exit(f"curl 失败 ({p.returncode}): {(p.stderr or out)[-800:]}")
    body_text, _, tail = out.rpartition("\n__HTTPSTATUS__:")
    status = tail.strip()
    try:
        obj = json.loads(body_text)
    except json.JSONDecodeError:
        sys.exit(f"HTTP {status} 非 JSON: {body_text[:500]}")
    return obj


def api(method: str, path: str, body: dict | None = None, query: str = "") -> dict:
    url = api_base() + PREFIX + path + query
    obj = curl_json(method, url, body)
    if obj.get("code") != "Success":
        raise RuntimeError(f"{method} {path} code={obj.get('code')} msg={obj.get('msg')} {obj}")
    return obj


def list_instances(page_size: int = 20) -> list[dict]:
    obj = api("POST", "/list", {"page_index": 1, "page_size": page_size})
    return ((obj.get("data") or {}).get("list")) or []


def instance_status(uuid: str) -> str:
    obj = api("GET", "/status", query=f"?instance_uuid={uuid}")
    return str(obj.get("data") or "")


def snapshot(uuid: str) -> dict:
    obj = api("GET", "/snapshot", query=f"?instance_uuid={uuid}")
    return obj.get("data") or {}


def power_on(uuid: str) -> dict:
    return api("POST", "/power_on", {"instance_uuid": uuid, "payload": "gpu"})


def power_off(uuid: str) -> dict:
    return api("POST", "/power_off", {"instance_uuid": uuid})


def wait_status(uuid: str, want: set[str], timeout: int, interval: float = 5.0) -> str:
    t0 = time.time()
    last = ""
    while time.time() - t0 < timeout:
        last = instance_status(uuid)
        print(f"status={last}", flush=True)
        if last in want:
            return last
        time.sleep(interval)
    sys.exit(f"等待状态 {sorted(want)} 超时 {timeout}s，最后是 {last!r}")


def resolve_uuid(args: argparse.Namespace) -> str:
    if args.uuid:
        return args.uuid
    env = os.environ.get("AUTODL_INSTANCE_UUID", "").strip()
    if env:
        return env
    hint = (args.app or os.environ.get("AUTODL_APP_HINT") or "MINIMAX-H3").lower()
    items = list_instances()
    hits = []
    for i in items:
        app = ((i.get("cg_application_info") or {}).get("application_name") or "")
        name = i.get("name") or ""
        blob = f"{app} {name} {i.get('uuid')}".lower()
        if hint.lower() in blob:
            hits.append(i)
    if len(hits) == 1:
        return hits[0]["uuid"]
    if not hits:
        print("没有匹配的实例。当前列表：", flush=True)
        for i in items:
            app = ((i.get("cg_application_info") or {}).get("application_name") or "")
            print(f"  {i.get('uuid')}  {i.get('status')}  {app}", flush=True)
        sys.exit("请传 --uuid 或设置 AUTODL_INSTANCE_UUID")
    print("匹配到多台，请指定 --uuid：", flush=True)
    for i in hits:
        app = ((i.get("cg_application_info") or {}).get("application_name") or "")
        print(f"  {i.get('uuid')}  {i.get('status')}  {app}", flush=True)
    sys.exit(2)


def redact_snap(d: dict) -> dict:
    out = dict(d)
    for k in ("root_password", "jupyter_token"):
        if k in out:
            out[k] = "<redacted>"
    return out


def print_list(items: list[dict]) -> None:
    print(f"n={len(items)}", flush=True)
    for i in items:
        app = ((i.get("cg_application_info") or {}).get("application_name") or "")
        print(
            f"{i.get('uuid')}\t{i.get('status')}\t{i.get('region_name')}\t{app}",
            flush=True,
        )


def cmd_list(_: argparse.Namespace) -> None:
    print_list(list_instances())


def cmd_status(args: argparse.Namespace) -> None:
    uuid = resolve_uuid(args)
    print(f"uuid={uuid}", flush=True)
    print(f"status={instance_status(uuid)}", flush=True)


def cmd_snapshot(args: argparse.Namespace) -> None:
    uuid = resolve_uuid(args)
    d = redact_snap(snapshot(uuid))
    print(json.dumps(d, ensure_ascii=False, indent=2), flush=True)


def cmd_on(args: argparse.Namespace) -> None:
    uuid = resolve_uuid(args)
    st = instance_status(uuid)
    print(f"uuid={uuid} before={st}", flush=True)
    if st == "running":
        print("already_running", flush=True)
        return
    if st == "shutting_down":
        wait_status(uuid, {"shutdown"}, timeout=args.timeout)
        st = "shutdown"
    try:
        obj = power_on(uuid)
    except RuntimeError as e:
        if "无法进行开机" in str(e):
            st2 = instance_status(uuid)
            if st2 == "running":
                print("already_running", flush=True)
                return
        raise
    print(json.dumps(obj, ensure_ascii=False), flush=True)
    if args.wait:
        wait_status(uuid, {"running"}, timeout=args.timeout)
        print("POWER_ON_OK", flush=True)


def cmd_off(args: argparse.Namespace) -> None:
    uuid = resolve_uuid(args)
    st = instance_status(uuid)
    print(f"uuid={uuid} before={st}", flush=True)
    if st == "shutdown":
        print("already_shutdown", flush=True)
        return
    try:
        obj = power_off(uuid)
    except RuntimeError as e:
        if "无法进行关机" in str(e) or "关机" in str(e):
            st2 = instance_status(uuid)
            if st2 == "shutdown":
                print("already_shutdown", flush=True)
                return
        raise
    print(json.dumps(obj, ensure_ascii=False), flush=True)
    if args.wait:
        wait_status(uuid, {"shutdown"}, timeout=args.timeout)
        print("POWER_OFF_OK", flush=True)


def ssh_and_panel(host: str, port: int, password: str) -> tuple[str, str]:
    """Return (panel_url, gpu_line). Password stays in env for connect_server."""
    connect = connect_server_path()
    env = os.environ.copy()
    env["SEETACLOUD_SSH_PASSWORD"] = password
    p = subprocess.run(
        [sys.executable, str(connect), "--host", host, "--port", str(port), "--user", "root"],
        env=env,
        text=True,
        capture_output=True,
    )
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    if password:
        out = out.replace(password, "<redacted>")
    panel = ""
    m = re.search(r"SEETACLOUD_BASE_URL=(\S+)", out)
    if m:
        panel = m.group(1).strip().strip('"')
    if not panel:
        urls = re.findall(
            r"https://[^\s\"'<>]+?\.(?:seetacloud|autodl)\.com:\d+",
            out.replace("\r", ""),
        )
        if urls:
            panel = urls[0].rstrip("/")
    gpu = ""
    gm = re.search(r"^GPU:\s*(.+)$", out, re.M)
    if gm:
        gpu = gm.group(1).strip()
    if not gpu:
        gm = re.search(r"GPU_BEGIN\s*(.*?)\s*GPU_END", out.replace("\r", ""), re.S)
        if gm:
            gpu = " ".join(gm.group(1).split())
    print(out[-2500:], flush=True)
    if not panel:
        sys.exit("SSH 已试过，但没解析到面板 URL。确认 /root/面板地址.txt")
    return panel.rstrip("/"), gpu


def curl_text(url: str, timeout: int = 20, method: str = "GET") -> tuple[int, str]:
    p = subprocess.run(
        [
            "curl", "-sk", "--max-time", str(timeout),
            "-X", method, url,
            "-w", "\n__HTTPSTATUS__:%{http_code}",
        ],
        capture_output=True,
        text=True,
    )
    out = p.stdout or ""
    body, _, tail = out.rpartition("\n__HTTPSTATUS__:")
    try:
        code = int(tail.strip() or "0")
    except ValueError:
        code = 0
    return code, body.strip()


def comfy_probe(panel: str, timeout: int = 20) -> str:
    """三态探活：ready / starting / dead。
    dead = 404/不可达连续 3 次（秒级放弃死候选，可安全拉黑）；
    starting = 200 但未 ready（服务在启动，绝不能拉黑，稍后重试）。"""
    url = panel.rstrip("/") + "/api/comfy/status"
    bad = 0
    t0 = time.time()
    while time.time() - t0 < timeout:
        code, body = curl_text(url, timeout=8)
        if code == 200:
            try:
                obj = json.loads(body)
                if obj.get("reason") == "ready" and obj.get("running") is True:
                    return "ready"
            except json.JSONDecodeError:
                pass
            return "starting"
        elif code in (0, 404, 502, 503):
            bad += 1
            if bad >= 3:
                return "dead"
        time.sleep(2)
    return "starting"


def comfy_ready(panel: str, timeout: int) -> bool:
    """轮询 panel 直到 ComfyUI reason=ready；超时返回 False（不抛错、不退出）。"""
    t0 = time.time()
    url = panel.rstrip("/") + "/api/comfy/status"
    while time.time() - t0 < timeout:
        code, body = curl_text(url)
        try:
            obj = json.loads(body)
            if obj.get("reason") == "ready" and obj.get("running") is True:
                return True
        except json.JSONDecodeError:
            pass
        time.sleep(5)
    return False


def wait_comfy(panel: str, timeout: int) -> None:
    t0 = time.time()
    last = ""
    url = panel.rstrip("/") + "/api/comfy/status"
    while time.time() - t0 < timeout:
        code, body = curl_text(url)
        last = body
        print(f"comfy_http={code} {body[:200]}", flush=True)
        try:
            obj = json.loads(body)
            if obj.get("reason") == "ready" and obj.get("running") is True:
                qcode, qbody = curl_text(panel.rstrip("/") + "/api/comfy/queue-status")
                print(f"queue_http={qcode} {qbody[:200]}", flush=True)
                if "unreachable" in qbody:
                    print("queue unreachable，stop + start", flush=True)
                    curl_text(panel.rstrip("/") + "/api/comfy/stop", method="POST")
                    time.sleep(3)
                    curl_text(panel.rstrip("/") + "/api/comfy/start", method="POST")
                    time.sleep(8)
                    continue
                print("COMFY_READY", flush=True)
                return
        except json.JSONDecodeError:
            pass
        time.sleep(5)
    sys.exit(f"ComfyUI 未 ready，超时 {timeout}s。最后: {last[:400]}")


def snapshot_panel(snap: dict) -> str:
    """面板地址直接从快照的 service_6006_* 推导，不依赖实例内的地址文件。

    注意两个真实坑（2026-08-27）：
    - 端口可能已内嵌在 domain 里（如 `xxx.seetacloud.com:8443`），而
      `service_6006_port` 字段是 0——此时不能因为 port 为空就放弃；
    - `service_6006_port_protocol` 可能是 http，但 8443/443 代理端口实际是
      https（实例内地址文件写的是 https），这里做纠偏。
    """
    proto = str(snap.get("service_6006_port_protocol") or "").strip().lower()
    dom = str(snap.get("service_6006_domain") or "").strip()
    port = str(snap.get("service_6006_port") or "").strip()
    if not dom:
        return ""
    if re.search(r":\d+$", dom):
        url_port = dom.rsplit(":", 1)[-1]
        if not proto or (proto == "http" and url_port in ("8443", "443")):
            proto = "https"
        return f"{proto}://{dom}"
    if port and port != "0":
        return f"{(proto or 'https')}://{dom}:{port}"
    return ""


def boot(uuid: str, wait_run: int, wait_comfy: int) -> None:
    # 注意：本函数内调用模块级 wait_comfy()，参数名必须避开（此处用 wait_comfy_secs 传参）
    _run_boot(uuid, wait_run=wait_run, wait_comfy_secs=wait_comfy)


def _run_boot(uuid: str, wait_run: int, wait_comfy_secs: int) -> None:
    st = instance_status(uuid)
    print(f"uuid={uuid} before={st}", flush=True)
    if st != "running":
        if st == "shutting_down":
            wait_status(uuid, {"shutdown"}, timeout=wait_run)
        try:
            power_on(uuid)
        except RuntimeError as e:
            if "无法进行开机" not in str(e):
                raise
        wait_status(uuid, {"running"}, timeout=wait_run)

    # 快路径候选循环（2026-08-27 二次修正）：ComfyUI 的 ready 是服务端启动时间
    # （本实例实测冷开机 >27s，快照死链与 SSH 正链并存）。策略：
    # 快照 URL 与 SSH 文件 URL 立即并行取得；dead（404×3）拉黑；
    # starting 保留轮询，绝不因"尚未就绪"而拉黑——这是上一版的致命 bug。
    t_boot = time.time()
    deadline = time.time() + max(wait_comfy_secs + 60, 300)
    dead: set[str] = set()
    host = port = 0
    password = ""
    panel = ""
    ssh_url = ""
    ssh_next = 0.0  # 立即做第一次 SSH
    round_i = 0
    while time.time() < deadline and not panel:
        round_i += 1
        snap_url = ""
        try:
            snap = snapshot(uuid)
            snap_url = snapshot_panel(snap)
            host = snap.get("proxy_host") or host
            port = int(snap.get("ssh_port") or port) or port
            password = password or (snap.get("root_password") or "")
        except Exception as e:
            print(f"(快照错误: {str(e)[:100]})", flush=True)
        if host and port and password and time.time() >= ssh_next:
            ssh_next = time.time() + 30
            try:
                got, _gpu = ssh_and_panel(host, port, password)
                if got:
                    ssh_url = got
            except SystemExit:
                pass
        cands: list[str] = []
        for c in (snap_url, ssh_url):
            if c and c not in dead and c not in cands:
                cands.append(c)
        for cand in cands:
            st = comfy_probe(cand, timeout=20)
            print(f"[{time.time()-t_boot:6.1f}s] {cand} -> {st}", flush=True)
            if st == "ready":
                panel = cand
                break
            if st == "dead":
                dead.add(cand)
        if not panel:
            time.sleep(5)
    if not panel:
        sys.exit(f"面板发现超时（{int(time.time()-t_boot)}s）：dead={sorted(dead)}")
    print(f"[{time.time()-t_boot:6.1f}s] 面板就绪: {panel}", flush=True)

    print("COMFY_READY", flush=True)
    print(f"export SEETACLOUD_BASE_URL={json.dumps(panel)}", flush=True)
    print(f"export AUTODL_INSTANCE_UUID={json.dumps(uuid)}", flush=True)
    # GPU/LoRA 诊断信息默认关闭（省 5-10s）；AUTODL_BOOT_DIAG=1 打开
    if os.environ.get("AUTODL_BOOT_DIAG") == "1" and host and port and password:
        try:
            _, gpu = ssh_and_panel(host, port, password)
            if gpu:
                print(f"GPU={gpu}", flush=True)
        except SystemExit:
            pass


def _unused_wait_comfy(panel: str, timeout: int) -> None:
    print(f"export SEETACLOUD_BASE_URL={json.dumps(panel)}", flush=True)
    print(f"export AUTODL_INSTANCE_UUID={json.dumps(uuid)}", flush=True)
    # GPU/LoRA 信息仅诊断用，失败不影响主流程
    if host and port and password:
        try:
            _, gpu = ssh_and_panel(host, port, password)
            if gpu:
                print(f"GPU={gpu}", flush=True)
        except SystemExit:
            pass


def cmd_boot(args: argparse.Namespace) -> None:
    boot(resolve_uuid(args), wait_run=args.timeout, wait_comfy=args.comfy_timeout)


def cmd_ensure(args: argparse.Namespace) -> None:
    cmd_boot(args)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AutoDL 应用实例开关机 + SSH 发现面板")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_id(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--uuid", default="", help="实例 UUID，默认 AUTODL_INSTANCE_UUID")
        sp.add_argument("--app", default="", help="无 UUID 时按应用名子串匹配")

    sp = sub.add_parser("list", help="列出应用实例")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("status", help="查状态")
    add_id(sp)
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("snapshot", help="查详情（密码脱敏）")
    add_id(sp)
    sp.set_defaults(func=cmd_snapshot)

    sp = sub.add_parser("on", help="开机")
    add_id(sp)
    sp.add_argument("--wait", action="store_true", default=True)
    sp.add_argument("--no-wait", action="store_false", dest="wait")
    sp.add_argument("--timeout", type=int, default=180)
    sp.set_defaults(func=cmd_on)

    sp = sub.add_parser("off", help="关机")
    add_id(sp)
    sp.add_argument("--wait", action="store_true", default=True)
    sp.add_argument("--no-wait", action="store_false", dest="wait")
    sp.add_argument("--timeout", type=int, default=180)
    sp.set_defaults(func=cmd_off)

    sp = sub.add_parser("boot", help="开机并等到 ComfyUI ready，打印 SEETACLOUD_BASE_URL")
    add_id(sp)
    sp.add_argument("--timeout", type=int, default=180, help="等到 running 的秒数")
    sp.add_argument("--comfy-timeout", type=int, default=300, help="等到 Comfy ready 的秒数")
    sp.set_defaults(func=cmd_boot)

    sp = sub.add_parser("ensure", help="同 boot：已运行则只连 SSH")
    add_id(sp)
    sp.add_argument("--timeout", type=int, default=180)
    sp.add_argument("--comfy-timeout", type=int, default=300)
    sp.set_defaults(func=cmd_ensure)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
