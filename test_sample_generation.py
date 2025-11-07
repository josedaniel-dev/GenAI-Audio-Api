#!/usr/bin/env python3
"""
Hybrid Audio MVP — Single Message Generation Test (v3.4 NDF · Bit-Exact Contract)
Evaluates full pipeline (Cartesia → Cache → Bitmerge) for hybrid audio assembly.

Updates:
  • Compatible with new list-based timing_map (v3.3 contract)
  • Delegates to bitmerge_semantic assembler when detected
  • Keeps legacy dict-based path for backwards compatibility
  • Full telemetry with timestamps, format validation, and pacing logs

Author: José Soto
"""

import os
import sys
import json
import datetime
import argparse
from pathlib import Path
from dotenv import load_dotenv

from assemble_message import cartesia_generate
from audio_utils import describe, assemble_with_timing_map, load_clip
from config import (
    DEBUG,
    STEMS_DIR,
    OUTPUT_DIR,
    ENABLE_SEMANTIC_TIMING,
    summarize_config,
    get_template_path,
)

load_dotenv()


# ────────────────────────────────────────────────
# 🕒 Timestamp Helper
# ────────────────────────────────────────────────
def ts() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


# ────────────────────────────────────────────────
# 📄 Template Loader & Segment Builder
# ────────────────────────────────────────────────
def load_template(template_name: str):
    """Load phrasing/timing JSON template."""
    path = get_template_path(template_name)
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_segments(template: dict, name: str, developer: str) -> list[tuple[str, str]]:
    """Return (segment_id, substituted_text)."""
    segments = []
    for seg in template.get("segments", []):
        seg_id = seg.get("id", "")
        text = seg.get("text", "").replace("{name}", name).replace("{developer}", developer)
        segments.append((seg_id, text))
    return segments


# ────────────────────────────────────────────────
# 🧩 Main Test Routine
# ────────────────────────────────────────────────
def run_single_sample(first_name: str = "John",
                      developer: str = "Hilton",
                      staple_only: bool = False,
                      template_name: str = "double_anchor_hybrid_v3_3.json"):
    """
    Run one complete generation or stapling test using a phrasing template.
    Compatible with bitmerge (v3.4 NDF).
    """
    mode_label = "STAPLE ONLY (offline)" if staple_only else "FULL GENERATION (Cartesia Sonic-3)"
    start_time = datetime.datetime.now(datetime.UTC)

    print(f"\n🕒 [{ts()}] Starting single message test (v3.4 NDF — {mode_label})")
    print("🧠 Config summary:")
    for k, v in summarize_config().items():
        print(f"  • {k}: {v}")

    try:
        # ───────────────
        # 1️⃣ Load Template
        # ───────────────
        print(f"\n🕓 [{ts()}] Stage 1 — Loading phrasing template")
        template = load_template(template_name)
        segments = build_segments(template, first_name, developer)
        print(f"  🧩 Template: {template_name} ({len(segments)} segments)")

        # ───────────────
        # 2️⃣ Generate / Staple Stems
        # ───────────────
        print(f"\n🕓 [{ts()}] Stage 2 — Preparing stems...")
        stems = []
        for i, (seg_id, text) in enumerate(segments, 1):
            stem_path = Path(STEMS_DIR) / f"{seg_id}.wav"
            if staple_only:
                if stem_path.exists():
                    print(f"  📎 [{i}/{len(segments)}] Using existing stem → {stem_path.name}")
                    stems.append(str(stem_path))
                else:
                    raise FileNotFoundError(f"❌ Missing stem: {stem_path}")
            else:
                print(f"  🎙️ [{i}/{len(segments)}] Generating stem: {seg_id}")
                stems.append(cartesia_generate(text, seg_id))

        # ───────────────
        # 3️⃣ Assemble
        # ───────────────
        print(f"\n🕓 [{ts()}] Stage 3 — Assembling with semantic timing")
        timing_raw = template.get("timing_map", [])

        # Detect type: list (v3.3 contract) or dict (legacy)
        if isinstance(timing_raw, list):
            timing_type = "list-based (bitmerge)"
            print(f"  🧩 Timing map type: list ({len(timing_raw)} transitions)")
        elif isinstance(timing_raw, dict):
            timing_type = "dict-based (legacy)"
            print(f"  🧩 Timing map type: dict ({len(timing_raw)} entries)")
        else:
            raise ValueError(f"Unexpected timing_map type: {type(timing_raw)}")

        output_name = f"{first_name}_{developer}_sample_semantic"
        out_path = Path(OUTPUT_DIR) / f"{output_name}.wav"

        if ENABLE_SEMANTIC_TIMING:
            result = assemble_with_timing_map(stems, timing_raw, str(out_path))
        else:
            from audio_utils import assemble_clean_merge
            result = assemble_clean_merge(stems, str(out_path), crossfade_ms=10)

        print(f"\n[{ts()}] ✅ Assembly complete → {result}")

        # ───────────────
        # 4️⃣ Diagnostics
        # ───────────────
        print(f"\n🕓 [{ts()}] Stage 4 — Audio diagnostics")
        audio = load_clip(result)
        info = describe(audio)
        duration = (datetime.datetime.now(datetime.UTC) - start_time).total_seconds()

        print(f"\n✅ [{ts()}] Test finished in {duration:.2f}s")
        print(f"📊 Audio diagnostics:\n{json.dumps(info, indent=2)}")
        print(f"🔖 Mode: {mode_label} | Timing: {timing_type}")
        print("🧪 Verify sound quality and pacing manually under v3.4 contract.\n")

    except Exception as e:
        print(f"❌ [{ts()}] Test run failed: {e}")
        if DEBUG:
            raise


# ────────────────────────────────────────────────
# ⚙️ CLI Interface
# ────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hybrid Audio MVP — Single Message Test (v3.4 NDF)")
    parser.add_argument("--first", type=str, default="John", help="First name for personalization")
    parser.add_argument("--dev", type=str, default="Hilton", help="Developer/company name")
    parser.add_argument("--staple", action="store_true", help="Skip TTS generation (use cached stems)")
    parser.add_argument("--template", default="double_anchor_hybrid_v3_3.json",
                        help="Template JSON file (default: v3.3 contract)")
    args = parser.parse_args()

    run_single_sample(
        first_name=args.first,
        developer=args.dev,
        staple_only=args.staple,
        template_name=args.template,
    )
