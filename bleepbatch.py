#!/usr/bin/env python3
"""
Podcast Bleeper - Batch Version
---------------------------------
Processes every audio and video file in a folder automatically.
Runs multiple passes per file to catch stragglers.
Skips files that have already been cleaned (_clean in filename).

Usage:
    python3.11 bleepbatch.py /path/to/folder
    python3.11 bleepbatch.py /path/to/folder --passes 1
    python3.11 bleepbatch.py /path/to/folder --passes 3
    python3.11 bleepbatch.py /path/to/folder --mode bleep --model medium
"""

import sys
import os
import argparse
import subprocess

# ── Config ────────────────────────────────────────────────────────────────────

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".flac", ".aac", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_media_files(folder: str) -> list[tuple[str, str]]:
    """
    Returns list of (filepath, type) tuples where type is 'audio' or 'video'.
    Skips any file that already has '_clean' in the name.
    """
    results = []
    for filename in sorted(os.listdir(folder)):
        # Skip already-cleaned files
        if "_clean" in filename:
            continue

        filepath = os.path.join(folder, filename)
        if not os.path.isfile(filepath):
            continue

        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext in AUDIO_EXTENSIONS:
            results.append((filepath, "audio"))
        elif ext in VIDEO_EXTENSIONS:
            results.append((filepath, "video"))

    return results


def run_bleep(script: str, input_path: str, mode: str, model: str) -> bool:
    """Run bleep.py or bleepvideo.py on a single file. Returns True if successful."""
    result = subprocess.run(
        [
            sys.executable, script,
            input_path,
            "--mode", mode,
            "--model", model,
        ]
    )
    return result.returncode == 0


def get_clean_path(filepath: str) -> str:
    """Get the expected _clean output path for a file."""
    base, ext = os.path.splitext(filepath)
    # Video bleeper always outputs mp4
    if os.path.splitext(filepath)[1].lower() in VIDEO_EXTENSIONS:
        return f"{base}_clean.mp4"
    return f"{base}_clean{ext}"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batch bleep all media files in a folder.")
    parser.add_argument("folder", help="Path to folder containing media files")
    parser.add_argument(
        "--passes",
        type=int,
        default=2,
        help="Number of passes per file (default: 2)",
    )
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
        help="Whisper model size (default: base)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f"❌  Not a folder: {args.folder}")
        sys.exit(1)

    # Find bleep.py and bleepvideo.py in same folder as this script
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    bleep_audio = os.path.join(script_dir, "bleep.py")
    bleep_video = os.path.join(script_dir, "bleepvideo.py")

    for s in [bleep_audio, bleep_video]:
        if not os.path.exists(s):
            print(f"❌  Could not find {os.path.basename(s)} in {script_dir}")
            print(f"    Make sure all scripts are in the same folder!")
            sys.exit(1)

    # Find all media files
    files = find_media_files(args.folder)

    if not files:
        print(f"🤷  No media files found in '{args.folder}' (skipping any _clean files)")
        sys.exit(0)

    print(f"\n📂  Found {len(files)} file(s) to process in '{args.folder}'")
    print(f"🔁  Passes per file: {args.passes}")
    print(f"🔇  Mode: {args.mode} | Model: {args.model}\n")
    print("=" * 60)

    # Track results
    succeeded = []
    failed    = []

    for i, (filepath, filetype) in enumerate(files, 1):
        filename = os.path.basename(filepath)
        script   = bleep_audio if filetype == "audio" else bleep_video

        print(f"\n[{i}/{len(files)}] 🎬  Processing: {filename} ({filetype})")
        print("-" * 60)

        current_input = filepath

        for pass_num in range(1, args.passes + 1):
            print(f"\n  ── Pass {pass_num}/{args.passes} ──")

            success = run_bleep(script, current_input, args.mode, args.model)

            if not success:
                print(f"  ❌  Pass {pass_num} failed for {filename}")
                failed.append(filename)
                break

            # The output of this pass becomes the input for the next pass
            clean_path = get_clean_path(current_input)

            if not os.path.exists(clean_path):
                # No banned words found — file is already clean!
                print(f"  ✅  No banned words found on pass {pass_num} — file is clean!")
                if pass_num == 1:
                    succeeded.append(filename)
                break

            # If there are more passes, use clean file as next input
            if pass_num < args.passes:
                current_input = clean_path
            else:
                succeeded.append(filename)

        print(f"\n  ✅  Done: {filename}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"🎉  Batch complete!")
    print(f"    ✅  Succeeded: {len(succeeded)} file(s)")
    if failed:
        print(f"    ❌  Failed:    {len(failed)} file(s)")
        for f in failed:
            print(f"        • {f}")
    print(f"\n💡  Clean files are saved next to their originals with '_clean' in the name.")
    print(f"    Open with QuickTime or VLC — don't double-click into Apple Music!\n")


if __name__ == "__main__":
    main()
