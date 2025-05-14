import os
import subprocess
import argparse
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

from video_processor import get_ffmpeg_path

VIDEOS_DIR = "videos"
OUTPUT_DIR = "treated"


def build_ffmpeg_cmd(ffmpeg_bin: str, input_path: str, output_path: str, speed: float):
    """Return FFmpeg command list that changes playback speed without initial grey frame."""
    # Video: adjust PTS; use STARTPTS trick to avoid grey frame
    v_filter = f"setpts=(PTS-STARTPTS)/{speed}"

    # Audio: atempo supports 0.5–2.0. Chain filters if outside that range.
    def atempo_chain(rate: float):
        # Break rate into factors within 0.5–2 range
        factors = []
        while rate < 0.5:
            factors.append(0.5)
            rate /= 0.5
        while rate > 2.0:
            factors.append(2.0)
            rate /= 2.0
        factors.append(rate)
        return ",".join([f"atempo={f}" for f in factors if abs(f-1.0) > 1e-3]) or "anull"

    a_filter = atempo_chain(speed)

    cmd = [
        ffmpeg_bin,
        "-i", input_path,
        "-vf", v_filter,
        "-af", a_filter,
        "-map_metadata", "-1",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-c:a", "aac",
        "-y",
        output_path,
    ]
    return cmd


def process_files(speed: float, specific_file: str = None):
    ffmpeg_path = get_ffmpeg_path()

    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = []
    if specific_file:
        files = [specific_file]
    else:
        files = [f for f in os.listdir(VIDEOS_DIR) if f.lower().endswith(".mp4")]

    if not files:
        print("No video files found to process.")
        return

    for name in files:
        in_path = os.path.join(VIDEOS_DIR, name)
        base, ext = os.path.splitext(name)
        out_name = f"spd_{speed:.2f}x_{base}{ext}"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        cmd = build_ffmpeg_cmd(ffmpeg_path, in_path, out_path, speed)
        print("Running:", " ".join(cmd))
        try:
            subprocess.run(cmd, check=True)
            print(f"✔ {name} -> {out_name}")
        except subprocess.CalledProcessError as e:
            print(f"✖ Failed on {name}:", e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply slight playback-speed change to videos, fixing grey-screen issue.")
    parser.add_argument("--speed", type=float, default=1.03, help="Playback speed multiplier (e.g. 1.03 for 3% faster).")
    parser.add_argument("--file", type=str, help="Single filename in videos/ to process.")
    args = parser.parse_args()

    if args.speed <= 0:
        print("Speed must be positive.")
        exit(1)

    process_files(args.speed, args.file) 