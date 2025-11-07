"""
Audio utilities for normalization, loudness alignment, and
basic waveform operations for the Hybrid Audio MVP.

v3.4 NDF — Bit-Exact Hybrid Bridge
• Delegates list-based timing_map assemblies to bitmerge_semantic
• Keeps legacy pydub pipeline for dict-based or fallback merges
• Ensures no resampling / re-encoding when bitmerge is used
"""

import math
from pathlib import Path
from typing import Optional, Tuple, Any
from pydub import AudioSegment
from pydub.effects import normalize as peak_normalize
from config import LUFS_TARGET, CROSSFADE_MS, DEBUG

# bit-exact assembler import (added)
try:
    from bitmerge_semantic import assemble_with_timing_map_bitmerge
except ImportError:
    assemble_with_timing_map_bitmerge = None

# ────────────────────────────────────────────────
# 🎚️ Core Normalization
# ────────────────────────────────────────────────
def normalize_audio(audio: AudioSegment, target_lufs: float = LUFS_TARGET) -> AudioSegment:
    """Approximate loudness normalization to target LUFS using RMS energy."""
    if audio.rms == 0:
        return audio
    rms = audio.rms
    current_dbfs = 20 * math.log10(rms / (audio.max_possible_amplitude or 1))
    gain = max(min(target_lufs - current_dbfs, 12), -12)
    return audio.apply_gain(gain)

def peak_normalize_audio(audio: AudioSegment) -> AudioSegment:
    """Normalize to peak amplitude without clipping."""
    return peak_normalize(audio)

# ────────────────────────────────────────────────
# 🧪 Introspection & Safe Loading
# ────────────────────────────────────────────────
def load_clip(path: str) -> AudioSegment:
    """Load an audio file preserving its native properties."""
    return AudioSegment.from_file(path)

def clip_signature(clip: AudioSegment) -> Tuple[int, int, int]:
    """Return (frame_rate, sample_width_bits, channels)."""
    return (clip.frame_rate, clip.sample_width * 8, clip.channels)

def read_info(path: str) -> dict:
    """Read file metadata safely."""
    clip = load_clip(path)
    return {
        "duration_ms": len(clip),
        "frame_rate": clip.frame_rate,
        "sample_width_bits": clip.sample_width * 8,
        "channels": clip.channels,
        "dBFS": round(clip.dBFS, 2) if clip.rms else None,
    }

def ensure_same_format(a: AudioSegment, b: AudioSegment):
    """Raise ValueError if frame_rate / width / channels differ."""
    sig_a = clip_signature(a)
    sig_b = clip_signature(b)
    if sig_a != sig_b:
        raise ValueError(f"Format mismatch: {sig_a} vs {sig_b}")

# ────────────────────────────────────────────────
# 🔗 Minimal-impact Appends
# ────────────────────────────────────────────────
def append_with_crossfade(base: AudioSegment, nxt: AudioSegment, crossfade_ms: int = CROSSFADE_MS) -> AudioSegment:
    return base.append(nxt, crossfade=crossfade_ms)

def append_minimal(base: AudioSegment, nxt: AudioSegment,
                   tiny_crossfade_ms: int = 8, strict_format: bool = True) -> AudioSegment:
    if strict_format:
        ensure_same_format(base, nxt)
    return base.append(nxt, crossfade=max(0, tiny_crossfade_ms))

# ────────────────────────────────────────────────
# 🧩 Clean Merge Assembly
# ────────────────────────────────────────────────
def assemble_clean_merge(stem_paths, output_path, crossfade_ms: int = 8) -> str:
    if not stem_paths:
        raise ValueError("No stems provided.")
    clips = [load_clip(p) for p in stem_paths]
    base_sig = clip_signature(clips[0])
    for p, c in zip(stem_paths, clips):
        if clip_signature(c) != base_sig:
            raise ValueError(f"Format mismatch in {p}: {clip_signature(c)} vs base {base_sig}")
    merged = clips[0]
    for nxt in clips[1:]:
        merged = append_minimal(merged, nxt, tiny_crossfade_ms=crossfade_ms, strict_format=False)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    merged.export(output_path, format="wav")
    print(f"✅ Clean-merge file saved → {output_path}")
    return str(output_path)

# ────────────────────────────────────────────────
# 🧭 Semantic Timing Assembly (Bit-Exact Bridge)
# ────────────────────────────────────────────────
def assemble_with_timing_map(stems: list[str], timing_map: Any, output_path: str) -> str:
    """
    Dispatches to bitmerge_semantic when timing_map is a list.
    Falls back to pydub minimal append for dict-based maps.
    """
    if not stems:
        raise ValueError("No stems provided for semantic assembly.")
    # Use bitmerge if possible
    if isinstance(timing_map, list) and assemble_with_timing_map_bitmerge:
        print("🔊 Using bit-exact merge (bitmerge_semantic)...")
        return assemble_with_timing_map_bitmerge(stems, timing_map, output_path)

    # Legacy dict-based path (kept)
    print("🧭 Using legacy semantic-timing assembly...")
    clips = [load_clip(p) for p in stems]
    merged = clips[0]
    for i in range(len(clips) - 1):
        a_id = Path(stems[i]).stem
        b_id = Path(stems[i + 1]).stem
        cfg = timing_map.get((a_id, b_id), {}) if isinstance(timing_map, dict) else {}
        gap = cfg.get("gap_ms", 0)
        crossfade = cfg.get("crossfade_ms", 10)
        merged = append_minimal(merged, clips[i + 1], tiny_crossfade_ms=crossfade, strict_format=False)
        if DEBUG:
            print(f"  ↔ {a_id} → {b_id}: gap={gap} | xfade={crossfade}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    merged.export(output_path, format="wav")
    print(f"✅ Semantic-timing merge complete → {output_path}")
    return str(output_path)

# ────────────────────────────────────────────────
# 🧪 Diagnostics
# ────────────────────────────────────────────────
def describe(audio: AudioSegment) -> dict:
    if len(audio) == 0:
        return {"error": "empty_audio"}
    data = {
        "duration_sec": round(len(audio) / 1000, 2),
        "rms": audio.rms,
        "dBFS": round(audio.dBFS, 2),
        "frame_rate": audio.frame_rate,
        "sample_width_bits": audio.sample_width * 8,
        "channels": audio.channels,
        "target_lufs": LUFS_TARGET,
    }
    try:
        data["lufs_delta"] = round(LUFS_TARGET - data["dBFS"], 2)
    except Exception:
        data["lufs_delta"] = None
    return data

# ────────────────────────────────────────────────
# 🏁 Module confirmation
# ────────────────────────────────────────────────
if __name__ == "__main__":
    print("🎚️ audio_utils v3.4 NDF loaded — bit-exact hybrid bridge active.")
