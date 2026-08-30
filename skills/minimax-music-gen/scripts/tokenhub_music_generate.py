#!/usr/bin/env python3
"""Generate MiniMax Music v2.6 audio through Tencent Cloud TokenHub.

The API key is read only from MINIMAX_API_KEY. It is never accepted as a
command-line argument, so shell history and process listings do not contain it.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


ENDPOINT = "https://tokenhub.tencentmaas.com/v1/wand/minimax-music/generation"
DEFAULT_MODEL = "minimax-music-v2.6"


def tls_context() -> ssl.SSLContext:
    """Use a system CA bundle when the bundled Python has no CA path configured."""
    candidates = []
    configured = os.getenv("SSL_CERT_FILE")
    if configured:
        candidates.append(Path(configured))
    candidates.extend(
        [
            Path("/etc/ssl/cert.pem"),
            Path(sys.prefix) / "etc" / "openssl" / "cert.pem",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return ssl.create_default_context(cafile=str(candidate))
    return ssl.create_default_context()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate MiniMax Music v2.6 audio via Tencent Cloud TokenHub."
    )
    parser.add_argument("--prompt", required=True, help="Music description, up to 2000 characters.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--instrumental", action="store_true", help="Generate without vocals.")
    mode.add_argument("--lyrics", help="Custom lyrics for a vocal song.")
    mode.add_argument(
        "--lyrics-optimizer",
        action="store_true",
        help="Let the model write lyrics from the prompt.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output audio path. Defaults to MINIMAX_MUSIC_OUTPUT_DIR with a timestamped name.",
    )
    parser.add_argument("--format", choices=("mp3", "wav", "pcm"), default="mp3")
    parser.add_argument("--sample-rate", type=int, default=44100)
    parser.add_argument("--bitrate", type=int, default=256000)
    parser.add_argument("--aigc-watermark", action="store_true")
    parser.add_argument("--model", default=os.getenv("MINIMAX_MUSIC_MODEL", DEFAULT_MODEL))
    return parser.parse_args()


def compact_error(response: object) -> str:
    if not isinstance(response, dict):
        return str(response)
    base = response.get("base_resp")
    if isinstance(base, dict):
        message = base.get("status_msg") or base.get("status_message")
        status = base.get("status_code")
        if message or status:
            return f"status_code={status}, status_msg={message}"
    return json.dumps(response, ensure_ascii=False)[:1000]


def request_json(payload: dict[str, object], api_key: str) -> dict[str, object]:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300, context=tls_context()) as response:
            body = response.read()
    except urllib.error.HTTPError as error:
        try:
            details = json.loads(error.read().decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            details = error.reason
        raise RuntimeError(f"TokenHub HTTP {error.code}: {compact_error(details)}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"TokenHub network error: {error.reason}") from error

    try:
        result = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError("TokenHub returned invalid JSON") from error
    if not isinstance(result, dict):
        raise RuntimeError("TokenHub returned an unexpected response")

    base = result.get("base_resp")
    if isinstance(base, dict) and base.get("status_code", 0) not in (0, "0", None):
        request_id = result.get("request_id") or result.get("trace_id") or "unknown"
        raise RuntimeError(f"TokenHub generation failed: {compact_error(result)}; request_id={request_id}")
    return result


def save_audio(result: dict[str, object], output: Path) -> dict[str, object]:
    data = result.get("data")
    if not isinstance(data, dict) or not data.get("audio"):
        raise RuntimeError(f"TokenHub response did not contain audio: {compact_error(result)}")

    audio = data["audio"]
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".part")
    try:
        if isinstance(audio, str) and audio.startswith(("http://", "https://")):
            try:
                with urllib.request.urlopen(audio, timeout=300, context=tls_context()) as response:
                    temporary.write_bytes(response.read())
            except urllib.error.URLError as error:
                raise RuntimeError(f"Audio download failed: {error.reason}") from error
        elif isinstance(audio, str):
            try:
                temporary.write_bytes(bytes.fromhex(audio))
            except ValueError as error:
                raise RuntimeError("TokenHub returned malformed hex audio") from error
        else:
            raise RuntimeError("TokenHub returned an unsupported audio value")
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return data


def default_output(extension: str) -> Path:
    directory = Path(
        os.getenv("MINIMAX_MUSIC_OUTPUT_DIR", str(Path.home() / "Music" / "minimax-gen"))
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return directory / f"{stamp}_minimax_music.{extension}"


def load_api_key() -> str | None:
    """Read the inherited env var, with a private-file fallback for Agent shells."""
    api_key = os.getenv("MINIMAX_API_KEY")
    if api_key:
        return api_key

    env_file = Path(
        os.getenv(
            "MINIMAX_MUSIC_ENV_FILE",
            str(Path.home() / ".config" / "minimax-music.env"),
        )
    )
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            parts = shlex.split(line, comments=True)
            if len(parts) == 2 and parts[0] == "export" and parts[1].startswith("MINIMAX_API_KEY="):
                value = parts[1].split("=", 1)[1]
                if value:
                    return value
    except (OSError, ValueError):
        pass
    return None


def main() -> int:
    args = parse_args()
    api_key = load_api_key()
    if not api_key:
        print("MINIMAX_API_KEY is not set", file=sys.stderr)
        return 2
    if not args.prompt.strip() or len(args.prompt) > 2000:
        print("--prompt must be 1-2000 characters", file=sys.stderr)
        return 2

    payload: dict[str, object] = {
        "model": args.model,
        "prompt": args.prompt,
        "output_format": "url",
        "audio_setting": {
            "sample_rate": args.sample_rate,
            "bitrate": args.bitrate,
            "format": args.format,
        },
        "aigc_watermark": args.aigc_watermark,
    }
    if args.instrumental:
        payload["is_instrumental"] = True
    elif args.lyrics_optimizer:
        payload["lyrics_optimizer"] = True
    else:
        if not args.lyrics or len(args.lyrics) > 3500:
            print("--lyrics must be 1-3500 characters", file=sys.stderr)
            return 2
        payload["lyrics"] = args.lyrics

    output = args.out or default_output(args.format)
    try:
        result = request_json(payload, api_key)
        data = save_audio(result, output)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1

    extra = result.get("extra_info")
    duration = extra.get("music_duration") if isinstance(extra, dict) else None
    request_id = result.get("request_id") or result.get("trace_id")
    print(f"Generated: {output}")
    if duration is not None:
        print(f"Duration: {duration} ms")
    if request_id:
        print(f"Request ID: {request_id}")
    if isinstance(data, dict) and data.get("status") not in (None, 2, "2"):
        print(f"Generation status: {data.get('status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
