# One-command run for the CD4 Perturb-seq target-discovery toolkit
# (docs/ux_trust_fix_plan.md Wave 2: cold-start / ops).
#
# This is the light API+webserver runtime, NOT the heavy scanpy/pertpy analysis
# pipeline (that stays on environment.yaml / conda). See src/3_DE_analysis/
# requirements.txt and frontend/webserver/package.json for what each installs.
#
# frontend/webserver/ (React + Vite) replaced the old Streamlit dashboard
# (frontend/dashboard/) -- see frontend/README.md.

API_PORT ?= 8000
API_BASE := http://127.0.0.1:$(API_PORT)

.PHONY: install-api install-webserver install api webserver webserver-build test validate-pipeline

install-api:
	pip install -r src/3_DE_analysis/requirements.txt

install-webserver:
	cd frontend/webserver && npm install

install: install-api install-webserver

api: install-api
	uvicorn target_card_api:app --app-dir src/3_DE_analysis --port $(API_PORT)

# Real data is already baked into frontend/webserver/public/real-dataset.json
# (see frontend/webserver/README.md) -- the webserver does not need the API
# running to browse real target data.
webserver: install-webserver
	cd frontend/webserver && npm run dev

webserver-build: install-webserver
	cd frontend/webserver && npm run build

test:
	pytest

# Read-only collector that prints the live numbers docs/human_validation_protocol.md
# has a human sign off on (active dataset + column count, validate_cards results,
# raw-file row counts, dtypes, thresholds, and auto-detected open-finding lines).
# It is a collector, not a validator -- it decides nothing; tests/ + contracts/
# are the authority. Safe to run anytime; it never writes or rebuilds anything.
validate-pipeline:
	python scripts/validate_pipeline.py
