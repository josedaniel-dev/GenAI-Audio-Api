# ════════════════════════════════════════════════════════════
# Hybrid Audio API – Makefile v5.2 (Hardened / Sonic-3 Edition)
# Author: José Daniel Soto
# Secure GNU Make — No heredocs — No mixed indentation
# ════════════════════════════════════════════════════════════

# GLOBAL SHELL SAFETY
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

PYTHON := python3
VENV := .venv
ACTIVATE := . $(VENV)/bin/activate
HOST := 127.0.0.1
PORT := 8000
CLI := $(PYTHON) CLI.py
ARGS ?=

# Validate .env early
ENV_FILE := .env

# Required for production hardening
INTERNAL_API_KEY := $(shell grep -E '^INTERNAL_API_KEY=' $(ENV_FILE) 2>/dev/null | cut -d= -f2-)

# ════════════════════════════════════════════════════════════
# SECTION 0 — ENVIRONMENT
# ════════════════════════════════════════════════════════════

check-env-file:
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "❌ ERROR: Missing .env file in project root."; \
		exit 1; \
	fi

check-prod-key:
	@if [ "$${MODE:-DEV}" = "PROD" ] && [ -z "$(INTERNAL_API_KEY)" ]; then \
		echo "❌ ERROR: INTERNAL_API_KEY required in PROD mode."; \
		exit 1; \
	fi

init-folders:
	mkdir -p stems output data logs templates routes observability

env-check: check-env-file
	@echo "🧩 Checking virtual environment..."
	@if [ ! -d "$(VENV)/bin" ]; then \
		echo "⚙️ Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
		$(ACTIVATE) && pip install --upgrade pip setuptools wheel; \
		if [ -f requirements.txt ]; then \
			$(ACTIVATE) && pip install -r requirements.txt; \
		else \
			echo "⚠️ WARNING: requirements.txt missing"; \
		fi; \
	else \
		echo "✅ Environment OK."; \
	fi

init: env-check init-folders check-prod-key
	@echo "Environment + folder structure ready."

# ════════════════════════════════════════════════════════════
# SECTION 1 — SERVER / API
# ════════════════════════════════════════════════════════════

run: check-env-file check-prod-key env-check
	@echo "🌐 Launching Hybrid Audio API (reload)…"
	@$(ACTIVATE) && uvicorn fastapi_server:app --reload --host 0.0.0.0 --port $(PORT)

run-prod: check-env-file check-prod-key env-check
	@echo "🚀 Launching Hybrid Audio API (production)…"
	@$(ACTIVATE) && uvicorn fastapi_server:app --host 0.0.0.0 --port $(PORT)

restart:
	@echo "🔁 Restarting server…"
	@pkill -f "uvicorn" || true
	@sleep 1
	@make run

# ════════════════════════════════════════════════════════════
# SECTION 2 — CLI
# ════════════════════════════════════════════════════════════

cli:
	@$(ACTIVATE) && $(CLI) $(ARGS)

cli-generate:
	@$(ACTIVATE) && $(CLI) generate $(ARGS)

cli-assemble:
	@$(ACTIVATE) && $(CLI) assemble $(ARGS)

cli-rotation:
	@$(ACTIVATE) && $(CLI) rotation $(ARGS)

cli-cache:
	@$(ACTIVATE) && $(CLI) cache $(ARGS)

cli-external:
	@$(ACTIVATE) && $(CLI) external $(ARGS)

# ════════════════════════════════════════════════════════════
# SECTION 3 — BATCH GENERATION
# ════════════════════════════════════════════════════════════

batch-rotations: env-check
	@echo "🔁 Generating rotational stems (Sonic-3)…"
	@$(ACTIVATE) && $(PYTHON) - <<'EOF'
from pathlib import Path
from batch_generate_stems import generate_rotational_stems
generate_rotational_stems(Path('data/common_names.json'), Path('data/developer_names.json'))
EOF
	@echo "✅ Rotational batch complete."

batch-template: env-check
	@echo "📜 Generating template stems…"
	@$(ACTIVATE) && $(PYTHON) - <<'EOF'
from batch_generate_stems import generate_from_template
generate_from_template('templates/double_anchor_hybrid_v3_5.json', first_name='John', developer='Hilton', max_workers=4)
EOF
	@echo "✅ Template stems ready."

batch-outputs: env-check
	@echo "🎧 Generating all outputs (may be heavy)…"
	@$(ACTIVATE) && $(PYTHON) - <<'EOF'
import json
from itertools import product
from pathlib import Path
from config import BASE_DIR
from assemble_message import assemble_pipeline

names = json.loads((BASE_DIR/'data/common_names.json').read_text())['items']
devs = json.loads((BASE_DIR/'data/developer_names.json').read_text())['items']
[(assemble_pipeline(n, d, clean_merge=True, template_name='double_anchor_hybrid_v3_5.json'))
	for n, d in product(names, devs)]
EOF
	@echo "✅ Batch outputs complete."

# ════════════════════════════════════════════════════════════
# SECTION 4 — AUDITS
# ════════════════════════════════════════════════════════════

rotation-stats: env-check
	@echo "📊 Rotational engine stats…"
	@$(ACTIVATE) && $(PYTHON) - <<'EOF'
import json
from rotational_engine import rotation_stats
print(json.dumps(rotation_stats(), indent=2, ensure_ascii=False))
EOF

# ════════════════════════════════════════════════════════════
# SECTION 5 — INTEGRATION TESTS
# ════════════════════════════════════════════════════════════

_curl = curl -fSs -H "X-Internal-API-Key: $(INTERNAL_API_KEY)"

test-template: env-check
	@echo "Testing /assemble/template…"
	@$(ACTIVATE) && $(_curl) -X POST \
		"http://$(HOST):$(PORT)/assemble/template?extended=true" \
		-H "Content-Type: application/json" \
		-d '{"first_name":"John","developer":"Hilton","template":"double_anchor_hybrid_v3_5.json","upload":false}' | jq .

test-cache-list:
	@echo "Testing /cache/list…"
	@$(ACTIVATE) && $(_curl) "http://$(HOST):$(PORT)/cache/list?extended=true" | jq .

# ════════════════════════════════════════════════════════════
# SECTION 6 — CLEANUP
# ════════════════════════════════════════════════════════════

clean:
	@echo "🧹 Cleaning…"
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find output -type f -name "*.wav" -delete
	@echo "Cleanup done."

# ════════════════════════════════════════════════════════════
# HELP
# ════════════════════════════════════════════════════════════

help:
	@echo ""
	@echo "Hybrid Audio API – Makefile v5.2 (Hardened / Sonic-3)"
	@echo "────────────────────────────────────────────────"
	@echo "make init                 → Prepare environment"
	@echo "make run                  → Start server (reload)"
	@echo "make run-prod             → Start server (PROD)"
	@echo "make cli ARGS=\"...\"     → Run CLI"
	@echo ""
	@echo "make batch-rotations      → Generate rotational stems"
	@echo "make batch-template       → Generate template stems"
	@echo ""
	@echo "make rotation-stats       → Show rotation stats"
	@echo ""
	@echo "make test-template        → Test Sonic-3 pipeline"
	@echo "make test-cache-list      → Test cache endpoint"
	@echo ""
	@echo "make clean                → Purge artifacts"
	@echo ""
