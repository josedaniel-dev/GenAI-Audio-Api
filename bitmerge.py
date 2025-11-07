#!/usr/bin/env python3
"""
bitmerge.py — Natural pacing bit-exact float merge

v3.3 NDF — Template-Aware Segment Timing
• Accepts an optional `timing_map` dict for per-transition control
• Applies gap_ms / crossfade_ms from template if provided
• Logs each transition with UTC timestamps and parameters
• Maintains full backward compatibility with simple runs
Author: José Soto
"""

import soundfile as sf
import numpy as np
import datetime
from pathlib import Path


# ────────────────────────────────────────────────
# 🕒 Timestamped Logging Utility
# ────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.datetime.now(datetime.UTC).strftime("[%Y-%m-%d %H:%M:%S UTC]")
    print(f"{ts} {msg}")


# ────────────────────────────────────────────────
# 🎚️ Cosine-Shaped Crossfade Curves
# ────────────────────────────────────────────────
def cosine_fade(length: int):
    """Return fade-out/in curves shaped by a raised cosine."""
    t = np.linspace(0, np.pi, length)
    fade_out = (1 + np.cos(t)) / 2
    fade_in = 1 - fade_out
    return fade_out, fade_in


# ────────────────────────────────────────────────
# 🔗 Crossfade with Optional Pause
# ────────────────────────────────────────────────
def crossfade_arrays(a: np.ndarray, b: np.ndarray, fade_ms: float, gap_ms: float, sr: int) -> np.ndarray:
    """Crossfade two float arrays with optional silence gap and cosine window."""
    n = int(sr * fade_ms / 1000)
    gap_n = int(sr * gap_ms / 1000)
    if n <= 0:
        n = 1

    # Handle mono/stereo arrays
    if a.ndim == 1:
        a = a.reshape(-1, 1)
        b = b.reshape(-1, 1)

    fade_out, fade_in = cosine_fade(n)
    fade_out = fade_out[:, None]
    fade_in = fade_in[:, None]

    silence = np.zeros((gap_n, a.shape[1]), dtype=np.float32)
    cross = a[-n:] * fade_out + b[:n] * fade_in
    merged = np.concatenate((a[:-n], cross, silence, b[n:]), axis=0)
    return merged.squeeze()


# ────────────────────────────────────────────────
# 🧩 Main Merge Function
# ────────────────────────────────────────────────
def merge_wavs(
    output_path: str,
    input_paths: list[str],
    fade_ms: float = 20,
    gap_ms: float = 130,
    timing_map: dict | None = None,
):
    """
    Bit-exact float merge with natural pacing.
    If `timing_map` is provided, uses per-transition gap_ms and crossfade_ms.
    """
    if not input_paths:
        raise ValueError("No input WAV files provided.")

    for p in input_paths:
        if not Path(p).exists():
            raise FileNotFoundError(f"Missing input file: {p}")

    data, sr = sf.read(input_paths[0], dtype="float32")
    merged = data
    base = sf.info(input_paths[0])
    log(f"🔍 Base format: {base.samplerate} Hz · {base.subtype} · {base.channels} ch")

    for idx, path in enumerate(input_paths[1:], start=2):
        info = sf.info(path)
        if info.samplerate != base.samplerate or info.channels != base.channels:
            raise ValueError(f"Format mismatch in {path}")

        d, _ = sf.read(path, dtype="float32")

        # Derive identifiers for map lookup
        prev_name = Path(input_paths[idx - 2]).stem if idx > 1 else Path(input_paths[0]).stem
        curr_name = Path(path).stem

        # Determine timing parameters
        if timing_map and (prev_name, curr_name) in timing_map:
            tm = timing_map[(prev_name, curr_name)]
            this_gap = tm.get("gap_ms", gap_ms)
            this_fade = tm.get("crossfade_ms", fade_ms)
            log(f"🧭 Using timing_map → {prev_name} → {curr_name} | gap={this_gap} ms | xfade={this_fade} ms")
        else:
            this_gap = gap_ms
            this_fade = fade_ms
            log(f"🎧 Merging {prev_name} → {curr_name} (default gap={this_gap} ms | xfade={this_fade} ms)")

        merged = crossfade_arrays(merged, d, this_fade, this_gap, sr)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, merged, sr, subtype=base.subtype)

    log(f"✅ Float merge complete → {out}")
    log(f"🕒 Parameters → default_crossfade={fade_ms} ms | default_gap={gap_ms} ms | sr={sr} Hz")
    return str(out)


# ────────────────────────────────────────────────
# 🧪 Local Test Run
# ────────────────────────────────────────────────
if __name__ == "__main__":
    stems = [
        "stems/static_1_hey.wav",
        "stems/name_john.wav",
        "stems/static_3_its_luis.wav",
        "stems/dev_hilton.wav",
        "stems/static_5_closing.wav",
    ]

    # Example per-transition control (template-style)
    timing_map = {
        ("static_1_hey", "name_john"): {"gap_ms": 80, "crossfade_ms": 15},
        ("name_john", "static_3_its_luis"): {"gap_ms": 90, "crossfade_ms": 15},
        ("static_3_its_luis", "dev_hilton"): {"gap_ms": 70, "crossfade_ms": 10},
        ("dev_hilton", "static_5_closing"): {"gap_ms": 40, "crossfade_ms": 25},  # tighter Hilton → Timeshare
    }

    merge_wavs(
        "output/John_Hilton_bitmerge_timed.wav",
        stems,
        fade_ms=20,
        gap_ms=100,
        timing_map=timing_map,
    )
