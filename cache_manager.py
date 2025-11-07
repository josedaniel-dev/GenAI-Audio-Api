"""
Cache Manager — tracks generated stems in stems_index.json.

v3.6 NDF — Rotational Dataset-Aware Cache
• Adds rotational awareness (rotational flag + dataset origin tracking)
• Adds helper register_rotational_stem() for batch dataset caching
• Extends summarize_cache() to report rotational and dataset metrics
• Retains Sonic-3 metadata, TTL logic, and backward compatibility
"""

import json
import os
import datetime
from threading import Lock
from pathlib import Path
from typing import Optional, Dict, Any

from config import (
    STEMS_INDEX_FILE,
    CACHE_TTL_DAYS,
    DEBUG,
    MODEL_ID,
    VOICE_ID,
    SAMPLE_RATE,
    COMMON_NAMES_FILE,
    DEVELOPER_NAMES_FILE,
)

# Thread-safety lock
_index_lock = Lock()

# Initialize index file if missing
if not STEMS_INDEX_FILE.exists():
    STEMS_INDEX_FILE.write_text(json.dumps({"stems": {}}, indent=2, ensure_ascii=False))


# ────────────────────────────────────────────────
# 📖 Core Load / Save
# ────────────────────────────────────────────────
def load_index() -> dict:
    """Load stem registry JSON into memory; auto-repairs malformed file."""
    with _index_lock:
        try:
            with open(STEMS_INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "stems" not in data:
                    data = {"stems": data}
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            if DEBUG:
                print("⚠️ Index file corrupted or missing — recreating.")
            return {"stems": {}}


def save_index(data: dict) -> None:
    """Safely write stem registry JSON to disk."""
    with _index_lock:
        with open(STEMS_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ────────────────────────────────────────────────
# 🧱 Registry Operations
# ────────────────────────────────────────────────
def register_stem(
    name: str,
    text: str,
    path: str,
    voice_id: str = VOICE_ID,
    model_id: str = MODEL_ID,
    rotational: bool = False,
    dataset_origin: Optional[str] = None,
) -> None:
    """
    Register or update a stem entry with version bump and metadata.
    Non-destructive: preserves any unknown keys.
    Now tracks if stem came from a rotational dataset (for caching audits).
    """
    data = load_index()
    now = datetime.datetime.utcnow().isoformat()
    existing = data["stems"].get(name, {})

    entry = {
        **existing,
        "text": text,
        "path": str(path),
        "voice_id": voice_id,
        "model_id": model_id,
        "sample_rate": SAMPLE_RATE,
        "created": now,
        "rotational": rotational,
        "dataset_origin": dataset_origin,
        "version": existing.get("version", 0) + 1,
    }

    data["stems"][name] = entry
    save_index(data)

    if DEBUG:
        tag = "🔁 rotational" if rotational else "🗂️ static"
        print(f"{tag} stem registered/updated: {name} (v{entry['version']}) @ {path}")


def register_rotational_stem(
    name: str,
    text: str,
    path: str,
    dataset_origin: str,
    voice_id: str = VOICE_ID,
    model_id: str = MODEL_ID,
) -> None:
    """
    Convenience wrapper for registering stems generated in rotational batches.
    Marks stems as rotational and associates dataset origin (e.g., 'common_names').
    """
    register_stem(
        name=name,
        text=text,
        path=path,
        voice_id=voice_id,
        model_id=model_id,
        rotational=True,
        dataset_origin=dataset_origin,
    )


def get_cached_stem(name: str, max_age_days: int = CACHE_TTL_DAYS) -> Optional[str]:
    """
    Retrieve cached stem if file exists and entry is within TTL.
    Returns None if expired or missing.
    """
    data = load_index()
    entry = data["stems"].get(name)
    if not entry:
        return None

    path = Path(entry["path"])
    if not path.exists():
        if DEBUG:
            print(f"⚠️ Cached stem missing file: {path}")
        return None

    try:
        created = datetime.datetime.fromisoformat(entry["created"])
        age = (datetime.datetime.utcnow() - created).days
    except Exception:
        if DEBUG:
            print(f"⚠️ Invalid date format for {name}, skipping TTL check.")
        age = 0

    if age > max_age_days:
        if DEBUG:
            print(f"🕒 Stem expired: {name} ({age} days old)")
        return None

    return str(path)


def cleanup_expired_stems(max_age_days: int = CACHE_TTL_DAYS) -> int:
    """
    Remove expired stems and delete corresponding audio files.
    Returns count of deleted entries.
    """
    data = load_index()
    now = datetime.datetime.utcnow()
    deleted = []

    for name, entry in list(data["stems"].items()):
        try:
            created = datetime.datetime.fromisoformat(entry.get("created", now.isoformat()))
            if (now - created).days > max_age_days:
                path = Path(entry["path"])
                if path.exists():
                    path.unlink()
                deleted.append(name)
                del data["stems"][name]
        except Exception as e:
            if DEBUG:
                print(f"⚠️ Cleanup error on {name}: {e}")

    if deleted:
        save_index(data)
        if DEBUG:
            print(f"🧹 Removed {len(deleted)} expired stems: {deleted}")

    return len(deleted)


# ────────────────────────────────────────────────
# 🧪 Diagnostics
# ────────────────────────────────────────────────
def summarize_cache() -> dict:
    """Return cache stats and Sonic-3 metadata for monitoring or API use."""
    data = load_index()
    stems = data.get("stems", {})
    total = len(stems)
    missing = [n for n, e in stems.items() if not Path(e["path"]).exists()]
    expired = 0
    now = datetime.datetime.utcnow()

    # Count rotational vs static stems
    rotational_count = sum(1 for e in stems.values() if e.get("rotational"))
    dataset_sources = {}
    for e in stems.values():
        src = e.get("dataset_origin")
        if src:
            dataset_sources[src] = dataset_sources.get(src, 0) + 1
        try:
            created = datetime.datetime.fromisoformat(e["created"])
            if (now - created).days > CACHE_TTL_DAYS:
                expired += 1
        except Exception:
            continue

    return {
        "total_stems": total,
        "rotational_stems": rotational_count,
        "dataset_sources": dataset_sources,
        "missing_files": len(missing),
        "expired_entries": expired,
        "ttl_days": CACHE_TTL_DAYS,
        "index_file": str(STEMS_INDEX_FILE),
        "default_voice": VOICE_ID,
        "default_model": MODEL_ID,
        "sample_rate": SAMPLE_RATE,
        "datasets": {
            "common_names_file": str(COMMON_NAMES_FILE),
            "developer_names_file": str(DEVELOPER_NAMES_FILE),
        },
    }


if __name__ == "__main__":
    print("🗂️ Cache Manager (v3.6 NDF — Rotational Dataset Aware) ready.")
    print(json.dumps(summarize_cache(), indent=2))
