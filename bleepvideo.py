#!/usr/bin/env python3
"""
Podcast/Video Bleeper - Video Version
--------------------------------------
Downloads (if URL) or loads a local video file, bleeps/silences banned words,
and saves a clean video file. Uses bleep.py under the hood for audio processing.

Usage:
    # Local file:
    python3 bleepvideo.py myvideo.mp4

    # YouTube or archive.org URL:
    python3 bleepvideo.py https://www.youtube.com/watch?v=XXXXX

    # With options:
    python3 bleepvideo.py myvideo.mp4 --mode bleep
    python3 bleepvideo.py myvideo.mp4 --model medium
    python3 bleepvideo.py https://www.youtube.com/watch?v=XXXXX --mode bleep --model small
"""

import sys
import os
import argparse
import subprocess
import shutil
import tempfile

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def check_tool(name: str) -> bool:
    return shutil.which(name) is not None


def download_video(url: str, output_dir: str) -> str:
    """Download video from URL using yt-dlp. Returns path to downloaded file."""
    print(f"⬇️   Downloading video from URL …")
    print(f"    {url}\n")

    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    result = subprocess.run(
        [
            "yt-dlp",
            "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--output", output_template,
            "--no-playlist",
            url,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"❌  yt-dlp failed:\n{result.stderr}")
        sys.exit(1)

    # Find the downloaded file
    files = [f for f in os.listdir(output_dir) if f.endswith(".mp4")]
    if not files:
        print("❌  Could not find downloaded video file.")
        sys.exit(1)

    downloaded = os.path.join(output_dir, files[0])
    print(f"✅  Downloaded: {os.path.basename(downloaded)}\n")
    return downloaded


def extract_audio(video_path: str, audio_path: str):
    """Extract audio track from video to a temporary MP3."""
    print(f"🎵  Extracting audio from video …")
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",                  # no video
            "-acodec", "libmp3lame",
            "-q:a", "2",            # high quality MP3
            audio_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌  ffmpeg audio extraction failed:\n{result.stderr}")
        sys.exit(1)
    print(f"✅  Audio extracted.\n")


def merge_audio_video(video_path: str, clean_audio_path: str, output_path: str):
    """Replace audio track in video with the clean version."""
    print(f"🎬  Merging clean audio back into video …")
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", clean_audio_path,
            "-c:v", "copy",         # copy video stream unchanged
            "-map", "0:v:0",        # use video from original
            "-map", "1:a:0",        # use audio from clean file
            "-shortest",
            output_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌  ffmpeg merge failed:\n{result.stderr}")
        sys.exit(1)
    print(f"✅  Video and audio merged.\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bleep bad words from a video file or URL.")
    parser.add_argument("input", help="Path to local video file OR a YouTube/archive.org URL")
    parser.add_argument(
        "--mode",
        choices=["bleep", "silence"],
        default="silence",
        help="Replace flagged words with 'silence' or 'bleep' tone (default: silence)",
    )
    parser.add_argument(
        "--model",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Whisper model size — larger = more accurate but slower (default: base)",
    )
    args = parser.parse_args()

    # ── Check required tools ──────────────────────────────────────────────────
    missing = []
    if not check_tool("ffmpeg"):
        missing.append("ffmpeg (run: brew install ffmpeg)")
    if is_url(args.input) and not check_tool("yt-dlp"):
        missing.append("yt-dlp (run: brew install yt-dlp)")
    if missing:
        print("❌  Missing required tools:")
        for m in missing:
            print(f"    • {m}")
        sys.exit(1)

    # ── Find bleep.py (should be in same folder as this script) ───────────────
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bleep_script = os.path.join(script_dir, "bleep.py")
    if not os.path.exists(bleep_script):
        print(f"❌  Could not find bleep.py in {script_dir}")
        print(f"    Make sure bleep.py and bleepvideo.py are in the same folder!")
        sys.exit(1)

    # ── Work in a temp directory so we don't leave junk around ───────────────
    with tempfile.TemporaryDirectory() as tmpdir:

        # ── Step 1: Get the video file ────────────────────────────────────────
        if is_url(args.input):
            video_path = download_video(args.input, tmpdir)
            # Output goes next to where the script is run from
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(os.getcwd(), f"{base_name}_clean.mp4")
        else:
            video_path = args.input
            if not os.path.exists(video_path):
                print(f"❌  File not found: {video_path}")
                sys.exit(1)
            base, _ = os.path.splitext(video_path)
            output_path = f"{base}_clean.mp4"

        # ── Step 2: Extract audio ─────────────────────────────────────────────
        temp_audio = os.path.join(tmpdir, "audio.mp3")
        extract_audio(video_path, temp_audio)

        # ── Step 3: Run bleep.py on the audio ────────────────────────────────
        print(f"🤐  Running audio bleeper (model={args.model}, mode={args.mode}) …\n")
        result = subprocess.run(
            [
                sys.executable, bleep_script,
                temp_audio,
                "--mode", args.mode,
                "--model", args.model,
            ]
        )
        if result.returncode != 0:
            print("❌  Audio bleeping failed. See errors above.")
            sys.exit(1)

        # bleep.py saves to audio_clean.mp3 next to the input
        clean_audio = os.path.join(tmpdir, "audio_clean.mp3")
        if not os.path.exists(clean_audio):
            print("✅  No banned words found in video — no changes made!")
            sys.exit(0)

        # ── Step 4: Merge clean audio back into video ─────────────────────────
        merge_audio_video(video_path, clean_audio, output_path)

    print(f"🎉  Done! Clean video saved as:\n    {output_path}\n")
    print(f"💡  Tip: Open with VLC or QuickTime — don't double-click into a media library!")


if __name__ == "__main__":
    main()
