"""
Hybrid Audio Assembly MVP — Cartesia Sonic 3
Core script: Assembles personalized message from reusable stems.

v3.5 NDF — Contract-Driven Voice Config + Bit-Exact Hybrid Merge
• Integrates voice_config from template (speed, volume, tone)
• Uses bitmerge_semantic for float32-exact, resample-free joining
• Preserves samplerate, channels, and bit depth of source stems
• Fully supports dict- and list-style timing_map formats
• Emits detailed timestamped diagnostics
• Maintains backward-compatible clean_merge for legacy calls
Author: José Soto
"""

import os
import time
import json
import datetime
import requests
from dotenv import load_dotenv
from pathlib import Path

from config import (
    STEMS_DIR,
    OUTPUT_DIR,
    CARTESIA_URL,
    CARTESIA_API_URL,
    CARTESIA_VERSION,
    VOICE_ID,
    MODEL_ID,
    CROSSFADE_MS,
    SAMPLE_RATE,
    DEBUG,
    ENABLE_SEMANTIC_TIMING,
    get_template_path,
)
from cache_manager import register_stem, get_cached_stem
from audio_utils import assemble_clean_merge
from bitmerge_semantic import assemble_with_timing_map_bitmerge as assemble_with_timing_map

load_dotenv()
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")


# ────────────────────────────────────────────────
# ⏱️ Timestamp Helper
# ────────────────────────────────────────────────
def ts() -> str:
    """Return formatted UTC timestamp."""
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


# ────────────────────────────────────────────────
# 📖 Template Loader (NDF-safe)
# ────────────────────────────────────────────────
def load_template(template_name: str = None) -> dict:
    """Safely load phrasing/timing JSON template from disk."""
    try:
        path = get_template_path(template_name)
        if not path or not Path(path).exists():
            raise FileNotFoundError(f"Template not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            template = json.load(f)
        if DEBUG:
            print(f"[{ts()}] 🧩 Loaded template → {Path(path).name}")
        return template
    except Exception as e:
        print(f"[{ts()}] ⚠️ Failed to load template ({template_name}): {e}")
        return {"segments": [], "timing_map": [], "voice_config": {}}


# ────────────────────────────────────────────────
# 🧩 Build Segments from Template
# ────────────────────────────────────────────────
def build_segments_from_template(template: dict, name: str, developer: str) -> list[tuple[str, str]]:
    """Return (segment_id, text) pairs with variables replaced."""
    segs = []
    for seg in template.get("segments", []):
        seg_id = seg.get("id", "")
        text = seg.get("text", "").replace("{name}", name).replace("{developer}", developer)
        segs.append((seg_id, text))
    return segs


# ────────────────────────────────────────────────
# 🧠 Cartesia Sonic-3 Generation (Contract-Aware)
# ────────────────────────────────────────────────
def cartesia_generate(text: str, stem_name: str, voice_id: str = VOICE_ID,
                      template: dict | None = None) -> str:
    """Generate or reuse a single stem; reads voice_config from template if provided."""
    start_time = time.time()
    cached_path = get_cached_stem(stem_name)
    if cached_path:
        print(f"[{ts()}] ✅ Cached stem → {stem_name}")
        return cached_path

    print(f"[{ts()}] 🧠 Generating new stem: {stem_name}")
    STEMS_DIR.mkdir(exist_ok=True)
    stem_path = Path(STEMS_DIR) / f"{stem_name}.wav"

    # Read contract-level voice config (safe defaults)
    voice_cfg = (template or {}).get("voice_config", {}) if template else {}
    speed = float(voice_cfg.get("speed", 1.0))
    volume = float(voice_cfg.get("volume", 1.0))
    tone = voice_cfg.get("tone", "neutral")

    try:
        if CARTESIA_API_URL and "tts/bytes" in CARTESIA_API_URL:
            headers = {
                "Cartesia-Version": CARTESIA_VERSION,
                "X-API-Key": CARTESIA_API_KEY,
                "Content-Type": "application/json",
            }
            payload = {
                "model_id": MODEL_ID,
                "transcript": text,
                "voice": {"mode": "id", "id": voice_id, "tone": tone},
                "output_format": {
                    "container": "wav",
                    "encoding": "pcm_f32le",
                    "sample_rate": SAMPLE_RATE,
                },
                "generation_config": {"speed": speed, "volume": volume},
            }
            if DEBUG:
                print(f"[{ts()}] 🌐 Using Sonic-3 API ({CARTESIA_API_URL}) · speed={speed} · volume={volume} · tone={tone}")
            resp = requests.post(CARTESIA_API_URL, headers=headers, json=payload, timeout=90)
        else:
            headers = {"Authorization": f"Bearer {CARTESIA_API_KEY}"}
            payload = {"text": text, "voice": voice_id, "format": "wav", "sample_rate": SAMPLE_RATE}
            if DEBUG:
                print(f"[{ts()}] 🌐 Using legacy API ({CARTESIA_URL})")
            resp = requests.post(CARTESIA_URL, headers=headers, json=payload, timeout=60)

        resp.raise_for_status()
        with open(stem_path, "wb") as f:
            f.write(resp.content)
        register_stem(stem_name, text, str(stem_path), voice_id)
        print(f"[{ts()}] 💾 Stem saved → {stem_path.name} ({time.time() - start_time:.2f}s)")
        return str(stem_path)

    except requests.RequestException as e:
        print(f"[{ts()}] ❌ Error generating '{stem_name}': {e}")
        raise


# ────────────────────────────────────────────────
# 🎚️ Assembly with Bit-Exact Semantic Timing
# ────────────────────────────────────────────────
def assemble_with_timing_map_ndf(stems: list[str], timing_map, output_name: str) -> str:
    """
    NDF wrapper — delegates to bitmerge_semantic (float32-exact, resample-free).
    Accepts both dict- and list-style timing_map inputs.
    """
    out_path = Path(OUTPUT_DIR) / f"{output_name}.wav"
    if isinstance(timing_map, dict):
        # convert to list form
        timing_map_list = []
        for (a, b), vals in timing_map.items():
            timing_map_list.append({"from": a, "to": b, **vals})
        timing_map = timing_map_list
    return assemble_with_timing_map(stems, timing_map, str(out_path))


# ────────────────────────────────────────────────
# 🧩 Main Assembly Orchestrator
# ────────────────────────────────────────────────
def assemble_pipeline(name: str, developer: str,
                      clean_merge: bool = True, template_name: str = None) -> str:
    """Full assembly orchestration pipeline with NDF safety and logging."""
    print(f"\n[{ts()}] 🚀 Starting Double-Anchor assembly for {name}/{developer}")

    template = load_template(template_name)
    segments = build_segments_from_template(template, name, developer)
    if not segments:
        print(f"[{ts()}] ⚠️ No template segments found — using fallback order.")
        segments = [
            ("static_1_hey", "Hey"),
            (f"name_{name.lower()}", name),
            ("static_3_its_luis", "it's Luis - about your"),
            (f"dev_{developer.lower()}", developer),
            ("stem_4_closing", "But I wanted to make sure everything is handled, thank you."),
        ]

    stems = []
    for seg_id, text in segments:
        path = get_cached_stem(seg_id)
        if path:
            stems.append(path)
            continue
        stems.append(cartesia_generate(text, seg_id, voice_id=VOICE_ID, template=template))

    print(f"[{ts()}] 🌿 {len(stems)} stems ready.")
    timing_map = template.get("timing_map", [])

    if ENABLE_SEMANTIC_TIMING:
        return assemble_with_timing_map_ndf(stems, timing_map, f"{name}_{developer}_semantic")
    else:
        return assemble_clean_merge(stems, Path(OUTPUT_DIR) / f"{name}_{developer}.wav", crossfade_ms=10)


# ────────────────────────────────────────────────
# 🔄 NDF Compatibility Wrapper (legacy assemble alias)
# ────────────────────────────────────────────────
def assemble(stems: list[str], output_name: str, clean_merge: bool = True) -> str:
    """Compatibility layer for legacy imports."""
    try:
        print(f"[{ts()}] ♻️ Legacy assemble() invoked — redirecting to assemble_pipeline()")
        base = Path(output_name).stem
        parts = base.split("_")
        name = parts[0].title() if parts else "John"
        developer = parts[1].title() if len(parts) > 1 else "Hilton"

        if ENABLE_SEMANTIC_TIMING:
            return assemble_pipeline(name, developer, clean_merge=True)
        else:
            return assemble_clean_merge(stems, Path(OUTPUT_DIR) / f"{output_name}.wav", crossfade_ms=10)
    except Exception as e:
        print(f"[{ts()}] ❌ Legacy assemble() failed: {e}")
        raise


# ────────────────────────────────────────────────
# 🧪 Local Test Run (Non-Destructive)
# ────────────────────────────────────────────────
if __name__ == "__main__":
    start_all = datetime.datetime.now(datetime.UTC)
    name, developer = "John", "Hilton"
    try:
        out = assemble_pipeline(name, developer, clean_merge=True)
        print(f"\n[{ts()}] ✅ Completed in {(datetime.datetime.now(datetime.UTC)-start_all).total_seconds():.2f}s")
        print(f"[{ts()}] 📦 Output → {out}")
    except Exception as e:
        print(f"[{ts()}] ⚠️ Pipeline failed: {e}")
