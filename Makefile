# One-command run for the CD4 Perturb-seq target-discovery toolkit
# (docs/ux_trust_fix_plan.md Wave 2: cold-start / ops).
#
# This is the light API+dashboard runtime, NOT the heavy scanpy/pertpy analysis
# pipeline (that stays on environment.yaml / conda). See src/3_DE_analysis/
# requirements.txt and frontend/dashboard/requirements.txt for what each
# installs.

API_PORT ?= 8000
API_BASE := http://127.0.0.1:$(API_PORT)

.PHONY: install-api install-dashboard install api dashboard dev test

install-api:
	pip install -r src/3_DE_analysis/requirements.txt

install-dashboard:
	pip install -r frontend/dashboard/requirements.txt

install: install-api install-dashboard

api: install-api
	uvicorn target_card_api:app --app-dir src/3_DE_analysis --port $(API_PORT)

dashboard: install-dashboard
	GWT_API_BASE=$(API_BASE) streamlit run frontend/dashboard/target_card_dashboard.py

# Runs the API in the background and the dashboard in the foreground, both
# under one `make dev`. The trap kills BOTH processes on Ctrl-C/exit -- so
# `make dev` never leaves an orphaned API server running after you stop it
# (the exact footgun a maintainer hits running the API by hand in a second
# terminal and forgetting about it).
dev: install
	@trap 'kill 0' EXIT INT TERM; \
	uvicorn target_card_api:app --app-dir src/3_DE_analysis --port $(API_PORT) & \
	sleep 2; \
	GWT_API_BASE=$(API_BASE) streamlit run frontend/dashboard/target_card_dashboard.py

test:
	pytest
