#!/usr/bin/env python3
"""
Batch Stem Generator — pre-generates stems from lists or template contracts.

v3.6 NDF — Rotational Mode (Dynamic Stem Provisioning)
• Adds rotational batch mode for dynamic stems ("Hello {name}", "{developer} timeshare")
• Integrates with data/common_names.json and data/developer_names.json
• Skips immutable stems (intro, followup, closing)
• Reuses Sonic-3 (tts/bytes) endpoint and cache safety
• Retains v3.5 template, CSV, JSON, and inline batch modes
"""

import sys
import csv
import json
import time
import concurrent.futures
from pathlib import Path
from typing import Iterable, Dict, Any

from assemble_message import cartesia_generate, load_template, build_segments_from_template
from config import DEBUG, MODEL_ID, VOICE_ID, SAMPLE_RATE, CARTESIA_API_URL, BASE_DIR


# ────────────────────────────────────────────────
# ⚙️ Core Batch Function
# ────────────────────────────────────────────────
def generate_from_list(
    items: Iterable[str],
    prefix: str,
    voice_overrides: Dict[str, Any] = None,
    max_workers: int = 4,
    retries: int = 2,
) -> None:
    """
    Generate stems concurrently from a list of text items.
    Applies optional voice_config (speed, tone, volume) if provided.
    """
    items = list(items)
    total = len(items)
    print(f"🚀 Starting batch generation for prefix '{prefix}' ({total} items)")
    print(
        f"🧠 API: {'sonic-3' if 'tts/bytes' in CARTESIA_API_URL else 'legacy'} "
        f"| voice: {VOICE_ID} | model: {MODEL_ID} | rate: {SAMPLE_RATE} Hz\n"
    )

    def process_item(item: str):
        """Worker for generating a single stem with retry logic."""
        name = item.strip().lower().replace(" ", "_")
        stem_name = f"{prefix}_{name}"
        attempt = 0

        while attempt <= retries:
            try:
                stem_path = cartesia_generate(item, stem_name, voice_id=VOICE_ID)
                return (item, stem_path, attempt)
            except Exception as e:
                attempt += 1
                if attempt > retries:
                    print(f"❌  {stem_name} failed after {attempt} attempts → {e}")
                    return (item, None, attempt)
                print(f"⚠️  Retry {attempt}/{retries} → {stem_name}")
                time.sleep(1)

    completed = 0
    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_item, item): item for item in items}

        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            _, path, attempt = future.result()
            completed += 1
            pct = (completed / total) * 100

            if path:
                if DEBUG:
                    print(f"✅ [{completed}/{total}] {prefix}_{item.lower()} (try {attempt+1})")
            else:
                print(f"❌ [{completed}/{total}] {item} failed permanently")

            if completed % 5 == 0 or completed == total:
                elapsed = round(time.time() - start, 1)
                print(f"⏱️  Progress: {completed}/{total} ({pct:.1f} %) in {elapsed}s")

    print(f"\n🎯 Batch completed for '{prefix}'. {completed}/{total} processed.")
    print(f"⏳ Total time: {round(time.time() - start, 2)} s\n")


# ────────────────────────────────────────────────
# 📦 Template-Driven Batch Mode
# ────────────────────────────────────────────────
def generate_from_template(
    template_path: str,
    first_name: str = "John",
    developer: str = "Hilton",
    max_workers: int = 4,
) -> None:
    """Generate all stems defined in a phrasing/timing template."""
    tpl = load_template(template_path)
    voice_cfg = tpl.get("voice_config", {})
    segs = build_segments_from_template(tpl, first_name, developer)
    texts = [t for _, t in segs]

    print(
        f"📜 Template: {Path(template_path).name} | Segments: {len(texts)} "
        f"| Voice config: {voice_cfg}"
    )
    generate_from_list(texts, prefix="tpl", voice_overrides=voice_cfg, max_workers=max_workers)


# ────────────────────────────────────────────────
# 🔁 Rotational Mode — Dynamic Stem Provisioning
# ────────────────────────────────────────────────
def generate_rotational_stems(names_path: Path, developers_path: Path, max_workers: int = 6) -> None:
    """
    Generate dynamic stems for all name and developer entries.
    - "Hello {name}"          → stem_name_<name>.wav
    - "{developer} timeshare" → stem_brand_<developer>.wav
    """
    print(f"\n🔁 Rotational Batch Mode (names + developers)")
    start = time.time()

    # Load datasets
    try:
        with open(names_path, "r", encoding="utf-8") as f:
            names = json.load(f).get("items", [])
        with open(developers_path, "r", encoding="utf-8") as f:
            devs = json.load(f).get("items", [])
    except Exception as e:
        print(f"❌ Failed to load datasets: {e}")
        return

    print(f"📘 Names: {len(names)} | Developers: {len(devs)}")

    # Build phrase lists
    name_phrases = [f"Hello {n}" for n in names]
    dev_phrases = [f"{d} timeshare" for d in devs]

    # Generate both types concurrently
    generate_from_list(name_phrases, prefix="stem_name", max_workers=max_workers)
    generate_from_list(dev_phrases, prefix="stem_brand", max_workers=max_workers)

    elapsed = round(time.time() - start, 2)
    print(f"\n✅ Rotational batch complete in {elapsed}s")
    print(f"🧠 Total stems targeted: {len(name_phrases) + len(dev_phrases)}")


# ────────────────────────────────────────────────
# 📥 Input Utilities
# ────────────────────────────────────────────────
def load_items_from_csv(csv_path: str, column: str) -> list[str]:
    """Load items from a CSV column."""
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        items = [row[column] for row in reader if row.get(column)]
    print(f"📄 Loaded {len(items)} items from CSV: {csv_path}")
    return items


def load_items_from_json(json_path: str, key: str = "items") -> list[str]:
    """Load items from a JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        items = data.get(key, [])
    print(f"📘 Loaded {len(items)} items from JSON: {json_path}")
    return items


# ────────────────────────────────────────────────
# 🧪 Command-Line Execution
# ────────────────────────────────────────────────
if __name__ == "__main__":
    """
    CLI Examples:
      python batch_generate_stems.py csv data/names.csv name name
      python batch_generate_stems.py json data/devs.json items dev
      python batch_generate_stems.py inline "John,Sarah" name
      python batch_generate_stems.py template templates/double_anchor_hybrid_v3_5.json
      python batch_generate_stems.py rotations data/common_names.json data/developer_names.json
    """
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python batch_generate_stems.py [csv|json|inline|template|rotations] <args>")
        sys.exit(1)

    mode = sys.argv[1].lower()

    try:
        if mode == "csv":
            path, column, prefix = sys.argv[2:5]
            items = load_items_from_csv(path, column)
            generate_from_list(items, prefix)

        elif mode == "json":
            path, key, prefix = sys.argv[2:5]
            items = load_items_from_json(path, key)
            generate_from_list(items, prefix)

        elif mode == "inline":
            raw_items, prefix = sys.argv[2:4]
            items = [i.strip() for i in raw_items.split(",") if i.strip()]
            generate_from_list(items, prefix)

        elif mode == "template":
            template_path = sys.argv[2]
            first_name = sys.argv[3] if len(sys.argv) > 3 else "John"
            developer = sys.argv[4] if len(sys.argv) > 4 else "Hilton"
            generate_from_template(template_path, first_name, developer)

        elif mode == "rotations":
            names_path = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE_DIR / "data/common_names.json"
            devs_path = Path(sys.argv[3]) if len(sys.argv) > 3 else BASE_DIR / "data/developer_names.json"
            generate_rotational_stems(names_path, devs_path)

        else:
            print(f"❌ Unsupported mode: {mode}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Execution failed: {e}")
        if DEBUG:
            raise
