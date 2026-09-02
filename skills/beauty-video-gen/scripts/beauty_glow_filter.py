#!/usr/bin/env python3
"""美女视频"提亮+皮肤光泽"滤镜
处理链: 伽马提亮 → 饱和补偿 → 皮肤掩膜局部增亮 → 高光 Bloom 辉光(screen 混合) → 高光软压缩
用法: python3 beauty_glow_filter.py 输入.mp4 输出.mp4
"""
import subprocess, sys, threading
import numpy as np
import cv2

# ---- 可调参数（保守自然档）----
GAMMA = 0.90            # <1 中间调提亮，防死白防发灰
SAT = 1.045             # 提亮后的轻微饱和补偿
SKIN_LIFT = 0.05        # 皮肤区域额外提亮比例
BLOOM_LO, BLOOM_HI = 0.60, 0.92   # 高光带软阈值(亮度归一化)
BLOOM_SIGMA = 21        # 辉光扩散半径(px @1080宽，随分辨率缩放)
BLOOM_STRENGTH = 0.35   # screen 混合强度
KNEE_START = 236        # 高光软压缩起点，防止过曝死白

def gamma_lut(g):
    lut = (np.arange(256) / 255.0) ** g * 255.0
    return np.clip(lut, 0, 255).astype(np.uint8)

def knee_lut(start):
    lut = np.arange(256, dtype=np.float64)
    top = 255.0 - start
    hi = lut >= start
    lut[hi] = start + top * (1.0 - np.exp(-3.0 * (lut[hi] - start) / top)) / (1.0 - np.exp(-3.0))
    return np.clip(lut, 0, 255).astype(np.uint8)

def smoothstep(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)

def process(frame, W):
    # 1) 伽马提亮（LUT，中间调变亮、黑场白场锚定，画面不发灰）
    frame = cv2.LUT(frame, GAMMA_LUT)
    # 2) 饱和补偿
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] *= SAT
    frame = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)
    # 3) 皮肤掩膜（YCrCb 经典肤色域 + 大 σ 羽化），只在皮肤上局部增亮
    ycc = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    skin = ((ycc[..., 1] >= 133) & (ycc[..., 1] <= 177) &
            (ycc[..., 2] >= 77) & (ycc[..., 2] <= 133)).astype(np.float32)
    skin = cv2.GaussianBlur(skin, (0, 0), sigmaX=W / 120.0)[..., None]
    lift = frame.astype(np.float32) * (1.0 + SKIN_LIFT * skin)
    # 4) 高光 Bloom：取高光带亮度做辉光层，screen 混合回画面 → 皮肤呈现光泽感
    luma = lift[..., 2] * 0.299 + lift[..., 1] * 0.587 + lift[..., 0] * 0.114
    glow_mask = smoothstep(luma / 255.0, BLOOM_LO, BLOOM_HI)
    glow = (lift * glow_mask[..., None]).astype(np.float32)
    glow = cv2.GaussianBlur(glow, (0, 0), sigmaX=BLOOM_SIGMA * W / 1080.0)
    out = 255.0 - (255.0 - lift) * (255.0 - glow * BLOOM_STRENGTH) / 255.0
    # 5) 高光软压缩
    return cv2.LUT(np.clip(out, 0, 255).astype(np.uint8), KNEE_LUT)

GAMMA_LUT, KNEE_LUT = gamma_lut(GAMMA), knee_lut(KNEE_START)

def main(src, dst):
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", src],
        capture_output=True, text=True, check=True).stdout.strip()
    wh, fps = probe.split(",")[0:2], probe.split(",")[2]
    W, H = int(wh[0]), int(wh[1])
    fps = round(eval(fps))
    frames = int(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", src],
        capture_output=True, text=True, check=True).stdout.strip())
    print(f"输入 {W}x{H} @{fps}fps, {frames} 帧")

    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo",
                           "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    wr = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
         "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
         "-i", src, "-map", "0:v", "-map", "1:a?",
         "-c:v", "libx264", "-crf", "16", "-preset", "slow",
         "-c:a", "copy", "-shortest", dst], stdin=subprocess.PIPE)

    def pump():
        i = 0
        while True:
            buf = rd.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            wr.stdin.write(process(np.frombuffer(buf, np.uint8).reshape(H, W, 3), W))
            i += 1
            if i % 60 == 0:
                print(f"  已处理 {i}/{frames} 帧")
        wr.stdin.close()

    t = threading.Thread(target=pump); t.start(); t.join()
    wr.wait(); rd.wait()
    print("完成" if wr.returncode == 0 else f"ffmpeg 退出码 {wr.returncode}")
    sys.exit(wr.returncode)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
