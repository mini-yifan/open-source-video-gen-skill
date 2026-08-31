#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qwen3-TTS 一键生成：构建工作流 → SSH 提交 → 轮询 → 下载落盘。

用法（三种音色模式三选一）:
  python3 generate_tts.py --uuid pro-xxx --text "台词" \
      --voice-design "甜美软萌的年轻女性声音，语气活泼俏皮" --out 旁白01.flac
  python3 generate_tts.py --uuid pro-xxx --text "台词" \
      --speaker Serena --instruct "轻快活泼一点" --out 台词02.flac
  python3 generate_tts.py --uuid pro-xxx --text "台词" \
      --clone 参考音频.flac --ref-text "参考音频里说的话" --out 克隆03.flac

实例生命周期（开机/关机）由 autodl-app-instance 技能管理，本脚本不开关机，
只要求实例 running 且 ComfyUI ready。SSH 密码只经环境变量注入 expect，绝不打印。
依赖：python3 标准库 + expect + curl（macOS 自带）；AUTODL_TOKEN 读取规则同 autodl_app。
"""
import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

# 定位 autodl_app.py：优先本仓库/技能同级目录，再回退常见安装位置
_SIBLING = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "autodl-app-instance", "scripts",
)
_CANDIDATES = [
    _SIBLING,
    os.path.expanduser("~/.zcode/skills/autodl-app-instance/scripts"),
    os.path.expanduser("~/.agents/skills/autodl-app-instance/scripts"),
    os.path.expanduser("~/.codex/skills/autodl-app-instance/scripts"),
    os.path.expanduser("~/.cursor/skills/autodl-app-instance/scripts"),
]
AUTODL_SCRIPTS = next(
    (c for c in _CANDIDATES if os.path.isfile(os.path.join(c, "autodl_app.py"))),
    _SIBLING,
)
if os.path.isdir(AUTODL_SCRIPTS) and AUTODL_SCRIPTS not in sys.path:
    sys.path.insert(0, AUTODL_SCRIPTS)
import autodl_app  # noqa: E402

MODELS = {
    "voice_design": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "custom": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    "base": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
}


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------- SSH / SCP（expect 模式，密码只在子进程环境变量里） ----------

def _tcl_escape(cmd: str) -> str:
    return json.dumps(cmd).replace("$", "\\$").replace("[", "\\[")


def _expect_spawn(spawn_line: str, timeout: int) -> str:
    expect_bin = shutil.which("expect")
    if not expect_bin:
        die("需要本机 expect（macOS 自带 /usr/bin/expect）")
    fd, path = tempfile.mkstemp(prefix="qtts_", suffix=".exp")
    os.close(fd)
    body = f"""set timeout {timeout}
log_user 1
{spawn_line}
expect {{
  -re "(?i)password:" {{ send "$env(SEETACLOUD_SSH_PW)\\r"; exp_continue }}
  timeout {{ puts "EXPECT_TIMEOUT"; exit 1 }}
  eof
}}
catch wait result
exit [lindex $result 3]
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    try:
        proc = subprocess.run(
            [expect_bin, path], capture_output=True, text=True,
            env={**os.environ, "SEETACLOUD_SSH_PW": _conn["password"]},
            timeout=timeout + 30,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    out = out.replace(_conn["password"], "<redacted>")
    if proc.returncode != 0 and "EXPECT_TIMEOUT" not in out and proc.returncode < 0:
        # 远端命令失败不一定是致命错误，由调用方按输出判断
        pass
    return out


_conn = {"host": "", "port": 22, "password": ""}


def get_conn() -> None:
    try:
        snap = autodl_app.snapshot(_UUID)
    except Exception as e:
        die(f"获取实例快照失败（检查 AUTODL_TOKEN）：{e}")
    host = snap.get("proxy_host")
    port = int(snap.get("ssh_port") or 22)
    password = snap.get("root_password") or ""
    if not (host and password):
        die("snapshot 缺 SSH host/密码，确认实例存在且已开机")
    _conn.update(host=host, port=port, password=password)


def ssh_cmd(command: str, timeout: int = 180) -> str:
    spawn = (
        f"spawn ssh -o StrictHostKeyChecking=accept-new "
        f"-o PreferredAuthentications=password -o PubkeyAuthentication=no "
        f"-p {_conn['port']} root@{_conn['host']} {_tcl_escape(command)}"
    )
    return _expect_spawn(spawn, timeout)


def _tcl_word(s: str) -> str:
    # expect 的 spawn 不经 shell，不能给参数加引号；含空格的路径用 Tcl 大括号包裹
    if " " in s and "{" not in s and "}" not in s:
        return "{" + s + "}"
    return s


def scp_to(local: str, remote: str, timeout: int = 180) -> str:
    spawn = (
        f"spawn scp -P {_conn['port']} -o StrictHostKeyChecking=accept-new "
        f"-o PreferredAuthentications=password -o PubkeyAuthentication=no "
        f"{_tcl_word(local)} {_tcl_word('root@' + _conn['host'] + ':' + remote)}"
    )
    return _expect_spawn(spawn, timeout)


# ---------- 工作流构建 ----------

def build_workflow(args) -> dict:
    if args.voice_design:
        model_key = "voice_design"
    elif args.speaker:
        model_key = "custom"
    else:
        model_key = "base"
    loader = {
        "class_type": "TDQwen3TTSModelLoader",
        "inputs": {
            "model_path": MODELS[model_key],
            "precision": "bf16",
            "device": "cuda",
            "attn_implementation": "sdpa",
            "auto_download": False,
            "download_source": "ModelScope",
        },
    }
    if args.voice_design:
        gen = {
            "class_type": "TDQwen3TTSVoiceDesign",
            "inputs": {
                "model": ["1", 0],
                "text": args.text,
                "instruct": args.voice_design,
                "language": args.language,
            },
        }
        wf = {"1": loader, "2": gen}
    elif args.speaker:
        gen = {
            "class_type": "TDQwen3TTSCustomVoice",
            "inputs": {
                "model": ["1", 0],
                "text": args.text,
                "speaker": args.speaker,
                "language": args.language,
                "instruct": args.instruct,
            },
        }
        wf = {"1": loader, "2": gen}
    else:  # clone
        gen = {
            "class_type": "TDQwen3TTSVoiceClone",
            "inputs": {
                "model": ["1", 0],
                "text": args.text,
                "ref_audio": ["4", 0],
                "language": args.language,
                "ref_text": args.ref_text,
                "x_vector_only_mode": bool(args.x_vector_only),
            },
        }
        wf = {
            "1": loader,
            "2": gen,
            "4": {"class_type": "LoadAudio",
                  "inputs": {"audio": os.path.basename(args.clone_remote)}},
        }
    wf["3"] = {
        "class_type": "SaveAudio",
        "inputs": {"audio": ["2", 0], "filename_prefix": f"audio/{args.prefix}"},
    }
    return wf


# ---------- 提交 / 轮询 / 下载 ----------

def submit(workflow: dict) -> tuple[str, str]:
    payload = base64.b64encode(
        json.dumps({"prompt": workflow, "client_id": "qwen3_tts_skill"},
                   ensure_ascii=False).encode("utf-8")
    ).decode()
    # 标记拆两段拼接：expect 会把整条命令回显进输出，若命令文本含连续标记，
    # 回显会先于真实输出命中检查逻辑（connect_server.py 踩过同款坑）
    cmd = (
        "P=$(head -1 /root/面板地址.txt 2>/dev/null | tr -d '\\r\\n '); "
        "echo TTS_PANEL=$P; "
        "if curl -s --max-time 60 http://127.0.0.1:6006/object_info "
        "| grep -q TDQwen3TTSModelLoader; then echo TTS_NODE_O\"K\"; "
        "else echo TTS_NODE_MISS\"ING\"; fi; "
        f"echo {payload} | base64 -d > /tmp/qtts_payload.json; "
        "echo TTS_SUBMIT_BE\"GIN\"; "
        "curl -s --max-time 30 -X POST http://127.0.0.1:6006/prompt "
        "-H 'Content-Type: application/json' -d @/tmp/qtts_payload.json; "
        "echo; echo TTS_SUBMIT_E\"ND\""
    )
    out = ssh_cmd(cmd)
    panel = ""
    for line in out.replace("\r", "").splitlines():
        if line.startswith("TTS_PANEL="):
            panel = line[len("TTS_PANEL="):].strip()
    if not panel:
        die(f"未能从实例读取面板地址（/root/面板地址.txt）。先跑 autodl_app.py boot。\n输出尾部：{out[-600:]}")
    if "TTS_NODE_MISSING" in out:
        die("本实例没有安装 ComfyUI-TD-Qwen3TTS 节点（object_info 里找不到 TDQwen3TTSModelLoader）。"
            "请换用预装该节点的实例，或先在实例内安装节点与 Qwen3-TTS 模型。")
    blob = out.split("TTS_SUBMIT_BEGIN")[-1].split("TTS_SUBMIT_END")[0].strip()
    try:
        resp = json.loads(blob)
    except Exception:
        die(f"提交响应解析失败：{blob[:800]}")
    if "error" in resp:
        node_errors = json.dumps(resp.get("node_errors", {}), ensure_ascii=False)[:1200]
        die(f"提交被 ComfyUI 校验拒绝：{resp['error']}\n{node_errors}")
    pid = resp.get("prompt_id")
    if not pid:
        die(f"提交响应缺 prompt_id：{blob[:500]}")
    return panel, pid


def poll_history(panel: str, prompt_id: str, timeout_s: int) -> dict:
    deadline = time.time() + timeout_s
    n = 0
    while time.time() < deadline:
        n += 1
        try:
            r = subprocess.run(
                ["curl", "-sk", "--max-time", "20",
                 f"{panel}/api/comfy/proxy/history?prompt_id={prompt_id}"],
                capture_output=True, text=True, timeout=30)
            d = json.loads(r.stdout or "{}")
            h = d.get(prompt_id)
            if h:
                st = h.get("status", {})
                s = st.get("status_str")
                if st.get("completed") and s == "success":
                    return h
                if s == "error":
                    for m in st.get("messages", []):
                        if m and m[0] == "execution_error":
                            die("节点执行错误: "
                                + json.dumps(m[1], ensure_ascii=False)[:1500])
                    die("任务失败（status=error），详见 ComfyUI 日志")
        except Exception as e:
            if n % 4 == 0:
                print(f"  (轮询重试: {e})", flush=True)
        if n % 4 == 1:
            print(f"  生成中... 已等待 {int(timeout_s - (deadline - time.time()))}s", flush=True)
        time.sleep(5)
    die(f"轮询超时（{timeout_s}s）。首次运行需加载 3.8GB 模型，可用 --timeout 加大。")


def download(panel: str, item: dict, dest_flac: str) -> None:
    filename = item.get("filename")
    subfolder = item.get("subfolder", "")
    if not filename:
        die(f"history 输出缺文件名：{item}")
    urls = [
        f"{panel}/output/{subfolder}/{filename}" if subfolder else f"{panel}/output/{filename}",
        f"{panel}/api/comfy/proxy/view?filename={filename}&subfolder={subfolder}&type=output",
    ]
    for url in urls:
        try:
            r = subprocess.run(["curl", "-sk", "--max-time", "180", "-o", dest_flac, url],
                               capture_output=True, timeout=200)
            if os.path.exists(dest_flac) and os.path.getsize(dest_flac) > 1000:
                with open(dest_flac, "rb") as f:
                    if f.read(4) == b"fLaC":
                        return
                os.remove(dest_flac)
        except Exception:
            pass
    die(f"下载失败：{urls}")


def finalize(dest: str, tmp_flac: str) -> None:
    ext = os.path.splitext(dest)[1].lower()
    if ext in ("", ".flac"):
        final = dest if ext else dest + ".flac"
        shutil.move(tmp_flac, final)
        report(final)
        return
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        r = subprocess.run([ffmpeg, "-y", "-v", "error", "-i", tmp_flac, dest],
                           capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 1000:
            os.remove(tmp_flac)
            report(dest)
            return
        print(f"  (ffmpeg 转码失败，保留 FLAC：{r.stderr[-300:]})", flush=True)
    final = os.path.splitext(dest)[0] + ".flac"
    shutil.move(tmp_flac, final)
    print(f"  (服务器输出为 24kHz 单声道 FLAC；本机无 ffmpeg，未转成 {ext}，已存 {final})")
    report(final)


def report(path: str) -> None:
    probe = shutil.which("ffprobe")
    dur = ""
    if probe:
        r = subprocess.run(
            [probe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True)
        try:
            dur = f"，时长 {float(r.stdout.strip()):.2f}s"
        except Exception:
            pass
    print(f"完成: {os.path.abspath(path)}{dur}")


# ---------- main ----------

_UUID = ""
ap = argparse.ArgumentParser(description="Qwen3-TTS 语音生成（AutoDL 实例）")
ap.add_argument("--uuid", default=os.environ.get("AUTODL_INSTANCE_UUID", ""),
                help="AutoDL 应用实例 UUID（默认读 AUTODL_INSTANCE_UUID）")
ap.add_argument("--text", required=True, help="要朗读的台词/旁白文本")
mode = ap.add_mutually_exclusive_group(required=True)
mode.add_argument("--voice-design", metavar="DESC",
                  help="用文字描述设计音色，如：一个二十岁左右的年轻女性声音，甜美软萌")
mode.add_argument("--speaker", metavar="NAME",
                  help="内置音色：Aiden/Dylan/Eric/Ono_anna/Ryan/Serena/Sohee/Uncle_fu/Vivian")
mode.add_argument("--clone", metavar="REF",
                  help="参考音频文件路径（本地），克隆其音色")
ap.add_argument("--instruct", default="", help="CustomVoice 模式的风格指令（可选）")
ap.add_argument("--ref-text", default="", help="参考音频里实际说的话（克隆模式强烈建议提供）")
ap.add_argument("--x-vector-only", action="store_true",
                help="克隆模式无法提供 ref_text 时开启（音色相似度会下降）")
ap.add_argument("--language", default="Auto",
                help="Auto/Chinese/English/Japanese/Korean/German/French/Russian/Portuguese/Spanish/Italian")
ap.add_argument("--out", default="", help="输出文件路径（默认 ./tts_<时间戳>.flac）")
ap.add_argument("--prefix", default="qtts_gen",
                help="服务器端保存前缀（默认 qtts_gen，文件在 ComfyUI output/audio/ 下）")
ap.add_argument("--timeout", type=int, default=900, help="轮询超时秒数")

args = ap.parse_args()
_UUID = args.uuid
if not _UUID:
    die("缺少实例 UUID：传 --uuid 或设置 AUTODL_INSTANCE_UUID")
if args.speaker and args.instruct is None:
    args.instruct = ""
if args.clone:
    if not os.path.isfile(args.clone):
        die(f"参考音频不存在：{args.clone}")
    if not args.ref_text and not args.x_vector_only:
        die("克隆模式必须提供 --ref-text（参考音频里说的话），或加 --x-vector-only")

if not args.out:
    args.out = f"tts_{time.strftime('%H%M%S')}.flac"

get_conn()

args.clone_remote = ""
if args.clone:
    remote_name = f"qtts_ref_{int(time.time())}{os.path.splitext(args.clone)[1] or '.wav'}"
    print(f"上传参考音频 {args.clone} ...", flush=True)
    scp_to(args.clone, f"/root/ComfyUI/input/{remote_name}")
    args.clone_remote = f"/root/ComfyUI/input/{remote_name}"
    # 验证上传成功
    chk = ssh_cmd(f"test -s /root/ComfyUI/input/{remote_name} && echo TTS_UPLOAD_O\"K\" || echo TTS_UPLOAD_FAI\"L\"")
    if "TTS_UPLOAD_OK" not in chk:
        die("参考音频上传失败")

workflow = build_workflow(args)
print("提交任务...", flush=True)
panel, pid = submit(workflow)
print(f"prompt_id: {pid}", flush=True)

hist = poll_history(panel, pid, args.timeout)
audio_items = []
for _, o in hist.get("outputs", {}).items():
    audio_items.extend(o.get("audio", []))
if not audio_items:
    die("任务成功但没有音频输出，检查工作流")
tmp_flac = os.path.join(tempfile.gettempdir(), f"qtts_dl_{pid[:8]}.flac")
download(panel, audio_items[0], tmp_flac)
finalize(args.out, tmp_flac)
