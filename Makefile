# One-command run for the CD4 Perturb-seq target-discovery toolkit
# (docs/ux_trust_fix_plan.md Wave 2: cold-start / ops).
#
# This is the light API+web runtime, NOT the heavy scanpy/pertpy analysis
# pipeline (that stays on environment.yaml / conda). See src/3_DE_analysis/
# requirements.txt for the API's Python deps and frontend/webserver/package.json
# for the portal's npm deps.
#
# The frontend is `frontend/webserver/` (React + Vite) -- it replaced the
# Streamlit dashboard that used to live at `frontend/dashboard/`. It reads a
# static, pre-exported `public/real-dataset.json` (regenerate with
# `python3 frontend/webserver/scripts/export_real_data.py`), so `make web` does
# NOT need `make api` running. The one thing that DOES need the live API is the
# standalone upload tool at `http://127.0.0.1:8000/upload` (`make api`) -- see
# README.md "Upload your own screen (live)".

API_PORT ?= 8000
API_BASE := http://127.0.0.1:$(API_PORT)
WEB_PORT ?= 5173

.PHONY: install-api install-web install api web dev test validate-pipeline eda freeze

install-api:
	pip install -r src/3_DE_analysis/requirements.txt

install-web:
	cd frontend/webserver && npm install

install: install-api install-web

api: install-api
	uvicorn target_card_api:app --app-dir src/3_DE_analysis --port $(API_PORT)

web: install-web
	cd frontend/webserver && npm run dev -- --port $(WEB_PORT)

# Runs the API in the background and the portal's Vite dev server in the
# foreground, both under one `make dev`. The trap kills BOTH processes on
# Ctrl-C/exit -- so `make dev` never leaves an orphaned API server running
# after you stop it (the exact footgun a maintainer hits running the API by
# hand in a second terminal and forgetting about it).
dev: install
	@trap 'kill 0' EXIT INT TERM; \
	uvicorn target_card_api:app --app-dir src/3_DE_analysis --port $(API_PORT) & \
	sleep 2; \
	cd frontend/webserver && npm run dev -- --port $(WEB_PORT)

test:
	pytest

# Read-only collector that prints the live numbers docs/human_validation_protocol.md
# has a human sign off on (active dataset + column count, validate_cards results,
# raw-file row counts, dtypes, thresholds, and auto-detected open-finding lines).
# It is a collector, not a validator -- it decides nothing; tests/ + contracts/
# are the authority. Safe to run anytime; it never writes or rebuilds anything.
validate-pipeline:
	python scripts/validate_pipeline.py

# Regenerate the deterministic per-stage EDA inventory reports (raw -> frontend).
# Idempotent: on unchanged inputs it rewrites byte-identical files. See
# docs/mvp-research/pipeline/EDA_INDEX.md.
eda:
	python scripts/generate_stage_eda.py

# Release-freeze integrity check: verify every asset pinned in
# FREEZE_MANIFEST.csv still matches its frozen md5, and that the EDA reports are
# up to date. Non-zero exit on any drift/missing/stale -- this is the machine
# check behind "結果可以重現". Does NOT re-run the S3-gated heavy pipeline.
freeze:
	python scripts/freeze_pipeline.py --eda

# Whole-repo freeze + isolation guard (unified v2). Verifies every module in
# docs/structure/FREEZE_MANIFEST_UNIFIED.csv still matches its pinned
# module_blob_sha256, and that file ownership is a disjoint total partition.
# Non-zero exit on drift/contamination. See docs/structure/PHASE_MODULE_MAP.md.
validate-freeze:
	python scripts/validate_freeze_unified.py
