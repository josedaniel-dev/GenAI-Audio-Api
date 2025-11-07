#!/usr/bin/env python3
"""
bitmerge_semantic.py — Bit-exact float merge with semantic timing
v3.4 NDF — Bit-Exact Hybrid Contract Integration

• Reads stems as float32 (pcm_f32) without re-encoding
• Preserves samplerate, channels, and subtype from FIRST stem
• Applies per-transition gap/crossfade timing (cosine curve)
• Never normalizes, resamples, or alters dynamic range
• Adds verify_integrity() for diagnostics (used in Makefile test-merge)
Author: José Soto
"""

from __future__ import annotations
import numpy as np
import soundfile as sf
from pathlib import Path
import datetime
from typing import List, Dict, Any, Tuple

# ────────────────────────────────────────────────
# 🕓 Helpers
# ────────────────────────────────────────────────
def _ts() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("[%Y-%m-%d %H:%M:%S UTC]")

def _log(msg: str) -> None:
    print(f"{_ts()} {msg}")

def _cosine_fade(n: int) -> Tuple[np.ndarray, np.ndarray]:
    """Return cosine fade-out and fade-in arrays."""
    t = np.linspace(0, np.pi, n, dtype=np.float32)
    fade_out = (1 + np.cos(t)) / 2.0
    fade_in = 1.0 - fade_out
    return fade_out, fade_in

def _as_2d(x: np.ndarray) -> np.ndarray:
    """Ensure shape (frames, channels)."""
    if x.ndim == 1:
        return x[:, None]
    return x

# ────────────────────────────────────────────────
# 🎚️ Core Crossfade Logic
# ────────────────────────────────────────────────
def _crossfade_with_gap(a: np.ndarray, b: np.ndarray, sr: int, gap_ms: float, xfade_ms: int) -> np.ndarray:
    """Bit-exact crossfade + optional silence gap between a and b."""
    a = _as_2d(a)
    b = _as_2d(b)

    n_gap = max(0, int(round(sr * (gap_ms / 1000.0))))
    n_xf  = max(0, int(round(sr * (xfade_ms / 1000.0))))

    if n_xf == 0:
        # simple join + optional silence
        if n_gap > 0:
            gap = np.zeros((n_gap, a.shape[1]), dtype=np.float32)
            return np.concatenate([a, gap, b], axis=0)
        return np.concatenate([a, b], axis=0)

    n_xf = min(n_xf, a.shape[0], b.shape[0])
    fo, fi = _cosine_fade(n_xf)
    fo = fo[:, None]
    fi = fi[:, None]

    head = a[:-n_xf] if n_xf < a.shape[0] else np.zeros((0, a.shape[1]), dtype=np.float32)
    tail = b[n_xf:]  if n_xf < b.shape[0] else np.zeros((0, b.shape[1]), dtype=np.float32)
    cross = a[-n_xf:] * fo + b[:n_xf] * fi

    if n_gap > 0:
        gap = np.zeros((n_gap, a.shape[1]), dtype=np.float32)
        return np.concatenate([head, cross, gap, tail], axis=0)
    return np.concatenate([head, cross, tail], axis=0)

# ────────────────────────────────────────────────
# 🎧 Bit-Exact I/O
# ────────────────────────────────────────────────
def _read_wav_float32(path: str) -> Tuple[np.ndarray, int, str, int]:
    """Read as float32, return (data, samplerate, subtype, channels)."""
    info = sf.info(path)
    data, sr = sf.read(path, dtype="float32", always_2d=False)
    return data, sr, info.subtype, info.channels

def _assert_compatible(base: Dict[str, Any], current: Dict[str, Any], path: str) -> None:
    """Ensure samplerate/channel consistency."""
    if (current["samplerate"] != base["samplerate"]) or (current["channels"] != base["channels"]):
        raise ValueError(
            f"Format mismatch in {Path(path).name}: "
            f"{current['samplerate']} Hz/{current['channels']} ch ≠ base {base['samplerate']} Hz/{base['channels']} ch"
        )

# ────────────────────────────────────────────────
# 🧩 Main Bit-Exact Assembler
# ────────────────────────────────────────────────
def assemble_with_timing_map_bitmerge(
    stems: List[str],
    timing_map: List[Dict[str, Any]],
    output_path: str,
    tail_fade_ms: int = 5
) -> str:
    """
    Assemble stems using a per-transition timing_map (list of dicts).
    • Preserves first stem’s samplerate/channels/subtype
    • Never resamples or normalizes
    """
    if not stems:
        raise ValueError("No stems provided.")

    # Build lookup
    tm: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for tr in timing_map or []:
        if not isinstance(tr, dict) or "from" not in tr or "to" not in tr:
            continue
        key = (str(tr["from"]), str(tr["to"]))
        tm[key] = {
            "gap_ms": float(tr.get("gap_ms", 0.0)),
            "crossfade_ms": int(tr.get("crossfade_ms", 0)),
        }

    first_path = stems[0]
    a, sr, subtype, ch = _read_wav_float32(first_path)
    base_fmt = {"samplerate": sr, "subtype": subtype, "channels": ch}
    _log(f"🔍 Base format: {sr} Hz · {subtype} · {ch} ch  ({Path(first_path).name})")

    merged = a
    for i in range(len(stems) - 1):
        a_id = Path(stems[i]).stem
        b_id = Path(stems[i + 1]).stem
        b, sr_b, subtype_b, ch_b = _read_wav_float32(stems[i + 1])
        _assert_compatible(base_fmt, {"samplerate": sr_b, "subtype": subtype_b, "channels": ch_b}, stems[i + 1])

        tr = tm.get((a_id, b_id), {"gap_ms": 0.0, "crossfade_ms": 10})
        gap_ms = float(tr.get("gap_ms", 0.0))
        xfade  = int(tr.get("crossfade_ms", 10))

        _log(f"🎧 Merge {i+1}/{len(stems)-1}: {a_id} → {b_id} (gap {gap_ms:.1f} ms, xfade {xfade} ms)")
        merged = _crossfade_with_gap(merged, b, sr, gap_ms, xfade)

    # Tail fade (optional, inaudible safety)
    if tail_fade_ms > 0 and merged.shape[0] > 0:
        n_tail = max(1, int(round(sr * (tail_fade_ms / 1000.0))))
        n_tail = min(n_tail, merged.shape[0])
        fade = np.linspace(1.0, 0.0, n_tail, dtype=np.float32)
        merged[-n_tail:] *= fade[:, None] if merged.ndim == 2 else fade

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), merged, sr, subtype=subtype)
    _log(f"✅ Bit-merge semantic file → {out}")
    return str(out)

# ────────────────────────────────────────────────
# 🔍 Diagnostic Integrity Check
# ────────────────────────────────────────────────
def verify_integrity(base_dir: str = "stems") -> None:
    """
    Verify that all stems share identical sample rate, channels and subtype.
    Called by `make test-merge` for QA.
    """
    stems = sorted(Path(base_dir).glob("*.wav"))
    if not stems:
        _log("⚠️ No stems found.")
        return

    info_ref = sf.info(stems[0])
    _log(f"Ref: {info_ref.samplerate} Hz · {info_ref.channels} ch · {info_ref.subtype}")
    mismatches = []
    for s in stems[1:]:
        i = sf.info(s)
        if (i.samplerate != info_ref.samplerate) or (i.channels != info_ref.channels):
            mismatches.append((s.name, i.samplerate, i.channels))
    if mismatches:
        _log("❌ Inconsistent stems detected:")
        for name, sr, ch in mismatches:
            _log(f"   {name}: {sr} Hz / {ch} ch")
    else:
        _log("✅ All stems match base format — integrity OK.")

# ────────────────────────────────────────────────
# 🧪 Local Test
# ────────────────────────────────────────────────
if __name__ == "__main__":
    stems = [
        "stems/stem_1_intro.wav",
        "stems/stem_2_followup.wav",
        "stems/stem_3_brand.wav",
        "stems/stem_4_closing.wav",
    ]
    timing = [
        {"from": "stem_1_intro", "to": "stem_2_followup", "gap_ms": 90, "crossfade_ms": 18},
        {"from": "stem_2_followup", "to": "stem_3_brand", "gap_ms": 60, "crossfade_ms": 18},
        {"from": "stem_3_brand", "to": "stem_4_closing", "gap_ms": 120, "crossfade_ms": 25},
    ]
    out = assemble_with_timing_map_bitmerge(stems, timing, "output/bitmerge_test.wav")
    _log(f"Output → {out}")
    verify_integrity("stems")
