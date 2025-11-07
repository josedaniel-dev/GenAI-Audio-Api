"""
Configuration constants for Hybrid Audio MVP.
Centralized configuration hub for all modules (assembler, cache, API, and utilities).

v3.6 NDF — Dataset Integration & Rotational Cache Support
• Adds DATA_DIR for common/developer dataset management
• Defines COMMON_NAMES_FILE, DEVELOPER_NAMES_FILE, and ROTATIONS_META_FILE
• Keeps Bit-Exact Hybrid contract configuration from v3.4
• Maintains backward compatibility and existing export parameters
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ────────────────────────────────────────────────
# 🔧 Load Environment Variables
# ────────────────────────────────────────────────
load_dotenv()

# ────────────────────────────────────────────────
# 📁 Core Directories
# ────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
STEMS_DIR = BASE_DIR / "stems"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
TEMPLATE_DIR = BASE_DIR / "templates"   # phrasing / timing templates
DATA_DIR = BASE_DIR / "data"            # ➕ new dataset directory for rotational caching

# Ensure directories exist
for _dir in (STEMS_DIR, OUTPUT_DIR, LOGS_DIR, TEMPLATE_DIR, DATA_DIR):
    _dir.mkdir(exist_ok=True)

# ────────────────────────────────────────────────
# 🎚️ Audio Processing Defaults
# ────────────────────────────────────────────────
CROSSFADE_MS: int = int(os.getenv("CROSSFADE_MS", 30))
LUFS_TARGET: float = float(os.getenv("LUFS_TARGET", -16))
SAMPLE_RATE: int = int(os.getenv("SAMPLE_RATE", 48000))
BIT_DEPTH: int = int(os.getenv("BIT_DEPTH", 16))

# v2.7 NDF additions (retained)
SAFE_GAIN_DB: float = float(os.getenv("SAFE_GAIN_DB", -1.0))   # headroom limiter
EXPORT_BIT_DEPTH: int = int(os.getenv("EXPORT_BIT_DEPTH", 16)) # final export precision
IN_MEMORY_ASSEMBLY: bool = os.getenv("IN_MEMORY_ASSEMBLY", "true").lower() == "true"

# v3.2–v3.4 Hybrid contract additions
ENABLE_SEMANTIC_TIMING: bool = os.getenv("ENABLE_SEMANTIC_TIMING", "true").lower() == "true"
DEFAULT_TEMPLATE: str = os.getenv("DEFAULT_TEMPLATE", "double_anchor_hybrid_v3_3.json")

# v3.4 NDF — physical integrity controls
DISABLE_NORMALIZATION: bool = os.getenv("DISABLE_NORMALIZATION", "true").lower() == "true"
DISABLE_RESAMPLING: bool = os.getenv("DISABLE_RESAMPLING", "true").lower() == "true"

# v3.6 NDF — dataset references for rotational generation
COMMON_NAMES_FILE = DATA_DIR / "common_names.json"
DEVELOPER_NAMES_FILE = DATA_DIR / "developer_names.json"
ROTATIONS_META_FILE = DATA_DIR / "rotations_meta.json"

# ────────────────────────────────────────────────
# 🧠 Cartesia API Configuration
# ────────────────────────────────────────────────
# Legacy fallback
CARTESIA_URL: str = os.getenv("CARTESIA_URL", "https://api.cartesia.ai/v1/generate")

# Sonic-3 TTS API configuration
CARTESIA_API_URL: str = os.getenv("CARTESIA_API_URL", "https://api.cartesia.ai/tts/bytes")
CARTESIA_VERSION: str = os.getenv("CARTESIA_VERSION", "2024-06-10")
MODEL_ID: str = os.getenv("MODEL_ID", "sonic-3")

# Credentials and voice setup
CARTESIA_API_KEY: str = os.getenv("CARTESIA_API_KEY", "")
VOICE_ID: str = os.getenv("VOICE_ID", "9e5605e6-e70a-4a78-bf39-7c6b0db9c359")

# ────────────────────────────────────────────────
# 🗂️ Cache / Registry Settings
# ────────────────────────────────────────────────
STEMS_INDEX_FILE = BASE_DIR / "stems_index.json"
CACHE_TTL_DAYS: int = int(os.getenv("CACHE_TTL_DAYS", 30))

# ────────────────────────────────────────────────
# 📊 Logging & Debugging
# ────────────────────────────────────────────────
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
LOG_FILE = LOGS_DIR / "hybrid_audio.log"

# ────────────────────────────────────────────────
# 🧩 Template & Semantic Timing Helpers
# ────────────────────────────────────────────────
def get_template_path(template_name: str = None) -> Path:
    """
    Return full path to the selected phrasing template JSON.
    Falls back to DEFAULT_TEMPLATE if not specified.
    """
    name = template_name or DEFAULT_TEMPLATE
    return TEMPLATE_DIR / name

# ────────────────────────────────────────────────
# ✅ Derived / Helper Configurations
# ────────────────────────────────────────────────
def summarize_config():
    """Quick summary for debugging and API health checks."""
    return {
        "stems_dir": str(STEMS_DIR),
        "output_dir": str(OUTPUT_DIR),
        "data_dir": str(DATA_DIR),
        "common_names_file": str(COMMON_NAMES_FILE),
        "developer_names_file": str(DEVELOPER_NAMES_FILE),
        "rotations_meta_file": str(ROTATIONS_META_FILE),
        "crossfade_ms": CROSSFADE_MS,
        "lufs_target": LUFS_TARGET,
        "sample_rate": SAMPLE_RATE,
        "bit_depth": BIT_DEPTH,
        "safe_gain_db": SAFE_GAIN_DB,
        "export_bit_depth": EXPORT_BIT_DEPTH,
        "in_memory_assembly": IN_MEMORY_ASSEMBLY,
        "enable_semantic_timing": ENABLE_SEMANTIC_TIMING,
        "template_dir": str(TEMPLATE_DIR),
        "default_template": DEFAULT_TEMPLATE,
        "disable_normalization": DISABLE_NORMALIZATION,
        "disable_resampling": DISABLE_RESAMPLING,
        "voice_id": VOICE_ID,
        "cartesia_url": CARTESIA_URL,
        "cartesia_api_url": CARTESIA_API_URL,
        "cartesia_version": CARTESIA_VERSION,
        "model_id": MODEL_ID,
        "cache_ttl_days": CACHE_TTL_DAYS,
        "debug": DEBUG,
    }

# ────────────────────────────────────────────────
# 🧩 Dataset Summary Helper
# ────────────────────────────────────────────────
def summarize_datasets():
    """Return current dataset configuration (rotational mode)."""
    return {
        "data_dir": str(DATA_DIR),
        "common_names_file": str(COMMON_NAMES_FILE),
        "developer_names_file": str(DEVELOPER_NAMES_FILE),
        "rotations_meta_file": str(ROTATIONS_META_FILE),
    }

# ────────────────────────────────────────────────
# 🧪 Local Diagnostic Run
# ────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔧 Current Hybrid Audio Config (v3.6 NDF — Dataset Integration):")
    for k, v in summarize_config().items():
        print(f"• {k}: {v}")
