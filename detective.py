#!/usr/bin/env python3
"""
Podcast Bleeper - Transcript Inspector
---------------------------------------
Shows exactly what Whisper heard around a specific timestamp.
Useful for debugging why a word was missed!

Usage:
    python3 detective.py podcast.mp3 35:46
    python3 detective.py podcast.mp3 2146
    python3 detective.py podcast.mp3 35:46 --window 60
    python3 detective.py podcast.mp3 35:46 --model medium
"""

import sys
import argparse
import whisper

# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_timestamp(ts: str) -> float:
    """Accept either seconds (2146) or mm:ss (35:46) format."""
    if ":" in ts:
        parts = ts.strip().split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(ts)


def seconds_to_timestamp(s: float) -> str:
    """Convert seconds to mm:ss format."""
    m = int(s) // 60
    sec = s % 60
    return f"{m}:{sec:05.2f}"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Inspect what Whisper transcribed around a timestamp.")
    parser.add_argument("input", help="Path to podcast MP3 file")
    parser.add_argument("timestamp", help="Timestamp to inspect — either seconds (2146) or mm:ss (35:46)")
    parser.add_argument(
        "--window",
        type=int,
        default=30,
        help="How many seconds before and after the timestamp to show (default: 30)"
    )
    parser.add_argument(
        "--model",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Whisper model size — larger = more accurate but slower (default: base)",
    )
    args = parser.parse_args()

    center = parse_timestamp(args.timestamp)
    start  = max(0, center - args.window)
    end    = center + args.window

    print(f"\n🔍  Inspecting '{args.input}'")
    print(f"⏱️   Showing words between {seconds_to_timestamp(start)} and {seconds_to_timestamp(end)}")
    print(f"🎯  Target timestamp: {seconds_to_timestamp(center)}\n")
    print(f"{'Timestamp':<12} {'Word':<20}")
    print("-" * 32)

    model = whisper.load_model(args.model)
    result = model.transcribe(args.input, word_timestamps=True)

    found_any = False
    for segment in result["segments"]:
        for word_info in segment.get("words", []):
            if start <= word_info["start"] <= end:
                ts  = seconds_to_timestamp(word_info["start"])
                word = word_info["word"].strip()
                # Mark the closest word to target timestamp
                marker = " ◀ YOU ARE HERE" if abs(word_info["start"] - center) < 1.0 else ""
                print(f"{ts:<12} {word:<20}{marker}")
                found_any = True

    if not found_any:
        print("  (no words found in this range)")

    print("\n✅  Done! If a word looks wrong above, Whisper misheared it.")
    print("    Try adding what Whisper actually heard to your wordlist.txt instead.\n")


if __name__ == "__main__":
    main()
