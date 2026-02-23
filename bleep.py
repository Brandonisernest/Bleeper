#!/usr/bin/env python3
"""
Podcast Bleeper
---------------
Transcribes an MP3 using Whisper, finds words from your wordlist.txt,
and replaces them with silence or a bleep tone.

Usage:
    python3 bleep.py podcast.mp3
    python3 bleep.py podcast.mp3 --mode silence
    python3 bleep.py podcast.mp3 --mode bleep
    python3 bleep.py podcast.mp3 --model medium
    python3 bleep.py podcast.mp3 --mode silence --model small
"""

import sys
import os
import argparse
import math
import whisper
from pydub import AudioSegment
from pydub.generators import Sine

# ── Config ────────────────────────────────────────────────────────────────────

WORDLIST_FILE = "wordlist.txt"   # lives in the same folder as this script
PADDING_MS    = 80               # extra ms to mute on each side of a word
BLEEP_FREQ_HZ = 1000             # tone frequency for bleep mode

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_wordlist(path: str) -> set[str]:
    if not os.path.exists(path):
        print(f"⚠️  No wordlist found at '{path}'. Creating an empty one.")
        with open(path, "w") as f:
            f.write("# Add one word per line. Lines starting with # are ignored.\n")
        return set()
    words = set()
    with open(path) as f:
        for line in f:
            word = line.strip().lower()
            if word and not word.startswith("#"):
                words.add(word)
    return words


def make_bleep(duration_ms: int, freq: int = BLEEP_FREQ_HZ) -> AudioSegment:
    """Generate a sine-wave bleep of the given duration."""
    # Fade in/out to avoid clicks
    tone = Sine(freq).to_audio_segment(duration=duration_ms)
    fade = min(30, duration_ms // 4)
    return tone.fade_in(fade).fade_out(fade)


def clean_word(w: str) -> str:
    """Strip punctuation so 'hell!' matches 'hell'."""
    return "".join(c for c in w.lower() if c.isalpha())


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bleep bad words from an MP3.")
    parser.add_argument("input", help="Path to input MP3 file")
    parser.add_argument(
        "--mode",
        choices=["bleep", "silence"],
        default="bleep",
        help="Replace flagged words with 'bleep' tone or 'silence' (default: bleep)",
    )
    parser.add_argument(
        "--model",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        help="Whisper model size — larger = more accurate but slower (default: base)",
    )
    args = parser.parse_args()

    input_path = args.input
    mode       = args.mode
    whisper_model = args.model

    if not os.path.exists(input_path):
        print(f"❌  File not found: {input_path}")
        sys.exit(1)

    # Build output filename
    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_clean{ext}"

    # ── Step 1: Load wordlist ──────────────────────────────────────────────────
    script_dir = os.path.dirname(os.path.abspath(__file__))
    wordlist_path = os.path.join(script_dir, WORDLIST_FILE)
    banned = load_wordlist(wordlist_path)

    if not banned:
        print("⚠️  Your wordlist is empty! Add words to wordlist.txt and try again.")
        sys.exit(0)

    print(f"📋  Loaded {len(banned)} word(s) from wordlist.")

    # ── Step 2: Transcribe ────────────────────────────────────────────────────
    print(f"🎙️  Loading Whisper model '{whisper_model}' …")
    model = whisper.load_model(whisper_model)

    print(f"🔍  Transcribing '{input_path}' … (this may take a while for long files)")
    result = model.transcribe(input_path, word_timestamps=True)

    # Collect (start_ms, end_ms) for every banned word
    hits: list[tuple[int, int]] = []
    for segment in result["segments"]:
        for word_info in segment.get("words", []):
            word = clean_word(word_info["word"])
            if word in banned:
                start_ms = int(word_info["start"] * 1000) - PADDING_MS
                end_ms   = int(word_info["end"]   * 1000) + PADDING_MS
                hits.append((max(0, start_ms), end_ms))
                print(f"   🚫  Found '{word}' at {word_info['start']:.2f}s")

    if not hits:
        print("✅  No banned words found! No changes made.")
        sys.exit(0)

    print(f"\n✂️   Replacing {len(hits)} instance(s) using mode='{mode}' …")

    # ── Step 3: Edit audio ────────────────────────────────────────────────────
    print("🎵  Loading audio …")
    audio = AudioSegment.from_file(input_path)

    # Process hits in reverse order so timestamps stay valid
    for start_ms, end_ms in sorted(hits, reverse=True):
        end_ms   = min(end_ms, len(audio))
        duration = end_ms - start_ms

        if mode == "silence":
            replacement = AudioSegment.silent(duration=duration)
        else:
            replacement = make_bleep(duration)
            # Match original volume roughly
            segment_vol = audio[start_ms:end_ms].dBFS
            if math.isfinite(segment_vol):
                replacement = replacement.apply_gain(segment_vol - replacement.dBFS)

        audio = audio[:start_ms] + replacement + audio[end_ms:]

    # ── Step 4: Export ────────────────────────────────────────────────────────
    print(f"💾  Saving to '{output_path}' …")
    audio.export(output_path, format="mp3", bitrate="192k")
    print(f"\n🎉  Done! Clean file saved as:\n    {output_path}")


if __name__ == "__main__":
    main()
