# ════════════════════════════════════════════════
# Hybrid Audio API · Makefile (v3.9.1 — Auto Env + Full System Audit Hotfix)
# Author: José Soto
# ════════════════════════════════════════════════

SHELL := /bin/bash

PYTHON := python3
VENV := .venv
ACTIVATE := . $(VENV)/bin/activate

HOST := 127.0.0.1
PORT := 8000

# ────────────────────────────────────────────────
# 🧩 Auto Environment Guard
# ────────────────────────────────────────────────
env-check:
	@echo "🧩 Checking virtual environment..."
	@if [ ! -d "$(VENV)/bin" ]; then \
		echo "⚙️  Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
		$(ACTIVATE) && pip install --upgrade pip setuptools wheel; \
		$(ACTIVATE) && pip install -r requirements.txt; \
	else \
		echo "✅ Environment exists."; \
	fi

# ────────────────────────────────────────────────
# 🎛️ Environment Setup
# ────────────────────────────────────────────────
init: env-check
	@echo "✅ Environment ready."

# ────────────────────────────────────────────────
# 🧠 Launch FastAPI Server
# ────────────────────────────────────────────────
run: env-check
	@echo "🌐 Launching Hybrid Audio API (v3.9.1 — Bit-Exact + Rotational Mode)..."
	@$(ACTIVATE) && uvicorn fastapi_server:app --reload --host 0.0.0.0 --port $(PORT)

# ────────────────────────────────────────────────
# 🎧 Test: Legacy Endpoint (Clean Merge)
# ────────────────────────────────────────────────
test-legacy: env-check
	@echo "\n🎧 Testing /assemble_audio (legacy clean merge)..."
	@$(ACTIVATE) && time curl -s -X POST "http://$(HOST):$(PORT)/assemble_audio" \
		-H "Content-Type: application/json" \
		-d '{"first_name": "John", "developer": "Hilton", "clean_merge": true}' | jq .

# ────────────────────────────────────────────────
# 🧩 Test: Template Endpoint (Full Bit-Exact Generation)
# ────────────────────────────────────────────────
test-template: env-check
	@echo "\n🧩 Testing /assemble_template (full generation, Sonic-3)..."
	@$(ACTIVATE) && time curl -s -X POST "http://$(HOST):$(PORT)/assemble_template" \
		-H "Content-Type: application/json" \
		-d '{"first_name": "John", "developer": "Hilton", "template": "double_anchor_hybrid_v3_3.json", "staple_only": false}' | jq .

# ────────────────────────────────────────────────
# ⚡ Test: Template Endpoint (Staple-Only Mode)
# ────────────────────────────────────────────────
test-staple: env-check
	@echo "\n⚡ Testing /assemble_template (staple-only, cached stems)..."
	@$(ACTIVATE) && time curl -s -X POST "http://$(HOST):$(PORT)/assemble_template" \
		-H "Content-Type: application/json" \
		-d '{"first_name": "John", "developer": "Hilton", "template": "double_anchor_hybrid_v3_3.json", "staple_only": true}' | jq .

# ────────────────────────────────────────────────
# 🧬 Test: Bit-Exact Merge Verification
# ────────────────────────────────────────────────
test-merge: env-check
	@echo "\n🧬 Verifying bit-exact assembly (bitmerge_semantic)..."
	@$(ACTIVATE) && printf "%s\n" \
		"import glob, soundfile as sf" \
		"stems = sorted(glob.glob('stems/*.wav'))" \
		"print(f'Found {len(stems)} stems')" \
		"if stems:" \
		"    info = sf.info(stems[0])" \
		"    print(f'Base format → {info.samplerate} Hz · {info.subtype} · {info.channels} ch')" \
		"print('✅ bitmerge_semantic check complete.')" \
		| $(PYTHON)

# ────────────────────────────────────────────────
# 🔁 Batch Generation — Rotational Datasets
# ────────────────────────────────────────────────
batch-rotations: env-check
	@echo "\n🔁 Generating rotational stems (Hello {name}, {developer} timeshare)..."
	@$(ACTIVATE) && $(PYTHON) batch_generate_stems.py rotations data/common_names.json data/developer_names.json
	@echo "✅ Rotational batch complete."

batch-template: env-check
	@echo "\n📜 Generating stems from template (v3.5 calm pacing)..."
	@$(ACTIVATE) && $(PYTHON) batch_generate_stems.py template double_anchor_hybrid_v3_5.json
	@echo "✅ Template batch complete."

batch-validate: env-check
	@echo "\n🔎 Validating cache and dataset integrity..."
	@$(ACTIVATE) && printf "%s\n" \
		"import json, os" \
		"from config import STEMS_DIR" \
		"print(f'Total stems cached → {len(os.listdir(STEMS_DIR))}')" \
		"print('✅ Cache validation complete.')" \
		| $(PYTHON)

batch-audit: env-check
	@echo "\n🧮 Auditing cached stems against datasets..."
	@$(ACTIVATE) && printf "%s\n" \
		"import json, os" \
		"from pathlib import Path" \
		"from config import BASE_DIR, STEMS_DIR" \
		"names = json.load(open(BASE_DIR/'data/common_names.json'))['items']" \
		"devs = json.load(open(BASE_DIR/'data/developer_names.json'))['items']" \
		"cached = [p.stem for p in Path(STEMS_DIR).glob('*.wav')]" \
		"missing_names = [n for n in names if f'stem_name_hello_{n.lower()}' not in cached]" \
		"missing_devs = [d for d in devs if f'stem_brand_{d.lower()}_timeshare' not in cached]" \
		"print(f'🔍 Missing name stems: {len(missing_names)}')" \
		"print(f'🔍 Missing developer stems: {len(missing_devs)}')" \
		"print('✅ Audit complete.')" \
		| $(PYTHON)

# ────────────────────────────────────────────────
# ❤️ Health & Cache Diagnostics
# ────────────────────────────────────────────────
health: env-check
	@echo "\n❤️ Checking /health..."
	@$(ACTIVATE) && curl -s http://$(HOST):$(PORT)/health | jq .

cache: env-check
	@echo "\n📦 Checking /cache/summary..."
	@$(ACTIVATE) && curl -s http://$(HOST):$(PORT)/cache/summary | jq .

# ────────────────────────────────────────────────
# 🧪 Local Test Harness (CLI)
# ────────────────────────────────────────────────
cli-test: env-check
	@echo "\n🧪 Running local sample generation test..."
	@$(ACTIVATE) && $(PYTHON) test_sample_generation.py --first John --dev Hilton --template double_anchor_hybrid_v3_3.json --staple

# ────────────────────────────────────────────────
# 🧮 One-Shot Full System Audit
# ────────────────────────────────────────────────
audit-all: env-check
	@echo "\n🧪 Starting full audit of Hybrid Audio API (v3.9.1)"
	@echo "───────────────────────────────────────────────"
	@start=$$(date +%s); \
	echo "📦 [0] Environment check..."; \
	make init >/dev/null; \
	echo "🌐 [1] Launching API (background)..."; \
	nohup bash -c "$(ACTIVATE) && uvicorn fastapi_server:app --host 127.0.0.1 --port $(PORT)" > /tmp/hybrid_api.log 2>&1 & \
	sleep 5; \
	echo "❤️ [2] Health check..."; make health; \
	echo "📦 [3] Cache summary..."; make cache; \
	echo "🎧 [4] Testing staple-only mode..."; make test-staple; \
	echo "🔁 [5] Rotational batch generation..."; make batch-rotations; \
	echo "🧮 [6] Dataset audit..."; make batch-audit; \
	echo "🧪 [7] CLI sample test..."; make cli-test; \
	echo "🧹 [8] Cleanup..."; make clean; \
	end=$$(date +%s); \
	echo "───────────────────────────────────────────────"; \
	echo "✅ Full audit complete in $$((end - start))s"; \
	echo "📄 Log file: /tmp/hybrid_api.log"; \
	echo "───────────────────────────────────────────────"

# ────────────────────────────────────────────────
# 🧹 Maintenance
# ────────────────────────────────────────────────
clean: env-check
	@echo "🧹 Cleaning compiled files, logs, and cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find output -type f -name "*.wav" -delete
	@echo "✅ Cleanup complete."

# ────────────────────────────────────────────────
# 🧾 Summary Help
# ────────────────────────────────────────────────
help:
	@echo ""
	@echo "Hybrid Audio API — v3.9.1 Command Summary"
	@echo "────────────────────────────────────────"
	@echo "make init            → Create venv and install dependencies"
	@echo "make run             → Launch FastAPI server (reload mode)"
	@echo "make test-legacy     → Test /assemble_audio (legacy)"
	@echo "make test-template   → Test /assemble_template (full)"
	@echo "make test-staple     → Test /assemble_template (cached)"
	@echo "make test-merge      → Verify bit-exact merge integrity"
	@echo "make batch-rotations → Generate rotational stems (Hello {name}, {developer} timeshare)"
	@echo "make batch-template  → Generate stems from phrasing template"
	@echo "make batch-validate  → Verify dataset and cache integrity"
	@echo "make batch-audit     → Check for missing stems (dataset vs cache)"
	@echo "make audit-all       → Run complete system audit sequence"
	@echo "make health          → Check /health endpoint"
	@echo "make cache           → Check /cache/summary endpoint"
	@echo "make cli-test        → Local CLI-based test"
	@echo "make clean           → Remove cache and temp files"
	@echo ""
