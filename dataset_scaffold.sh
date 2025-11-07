#!/usr/bin/env bash
# ════════════════════════════════════════════════
# Hybrid Audio v3.6 NDF — Dataset Scaffold Script
# Creates placeholder datasets for rotational caching
# Author: José Soto
# ════════════════════════════════════════════════

set -e

DATA_DIR="data"
mkdir -p "$DATA_DIR"

echo "🧱 Scaffolding dataset directory → $DATA_DIR"

# ────────────────────────────────────────────────
# Common Names Dataset
# ────────────────────────────────────────────────
cat > "$DATA_DIR/common_names.json" <<'EOF'
{
  "items": [
    "John",
    "Sarah",
    "Michael",
    "Emily",
    "David",
    "Sophia"
  ],
  "description": "Common first names for rotational greeting stems (Hello {name})."
}
EOF
echo "✅ Created: $DATA_DIR/common_names.json"

# ────────────────────────────────────────────────
# Developer / Brand Dataset
# ────────────────────────────────────────────────
cat > "$DATA_DIR/developer_names.json" <<'EOF'
{
  "items": [
    "Hilton",
    "Marriott",
    "Hyatt",
    "Wyndham",
    "Westgate"
  ],
  "description": "Developer or brand names for rotational stems ({developer} timeshare)."
}
EOF
echo "✅ Created: $DATA_DIR/developer_names.json"

# ────────────────────────────────────────────────
# Rotations Meta File
# ────────────────────────────────────────────────
cat > "$DATA_DIR/rotations_meta.json" <<'EOF'
{
  "version": "v1.0",
  "description": "Metadata registry for rotational dataset caching.",
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "expected_structures": {
    "common_names": "data/common_names.json",
    "developer_names": "data/developer_names.json"
  },
  "notes": [
    "Used by batch_generate_stems.py to build rotational cache pools.",
    "Each entry corresponds to a reusable Cartesia stem."
  ]
}
EOF
echo "✅ Created: $DATA_DIR/rotations_meta.json"

echo "🎯 Dataset scaffolding complete."
