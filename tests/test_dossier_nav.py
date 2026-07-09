"""Unit tests for the list->dossier deep-link seeding logic (FE-1).

``seed_dossier_session`` lets a list view open the target dossier on a specific
target via query params, without ever clobbering a user's own edit on rerun. It
is pure (dict-in/dict-out), so we test it with plain dicts -- no Streamlit runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dashboard"
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

from nav import seed_dossier_session  # noqa: E402


def test_seeds_both_from_query_params_into_empty_session():
    ss: dict = {}
    seeded_ds, seeded_target = seed_dossier_session({"target": "IL2RA", "dataset_id": "abc"}, ss)
    assert (seeded_ds, seeded_target) == ("abc", "IL2RA")
    assert ss["dossier_query"] == "IL2RA"
    assert ss["dossier_dataset"] == "abc"


def test_absent_params_seed_nothing():
    ss: dict = {}
    assert seed_dossier_session({}, ss) == (None, None)
    assert ss == {}


def test_existing_session_is_not_overwritten():
    # user already navigated to FOXP3 / another dataset; a stale query param must
    # NOT clobber it on rerun.
    ss = {"dossier_query": "FOXP3", "dossier_dataset": "user-ds"}
    seeded_ds, seeded_target = seed_dossier_session({"target": "IL2RA", "dataset_id": "abc"}, ss)
    assert (seeded_ds, seeded_target) == (None, None)
    assert ss["dossier_query"] == "FOXP3"
    assert ss["dossier_dataset"] == "user-ds"


def test_partial_params_seed_only_present_field():
    ss: dict = {}
    seeded_ds, seeded_target = seed_dossier_session({"target": "CD247"}, ss)
    assert seeded_target == "CD247"
    assert seeded_ds is None
    assert ss == {"dossier_query": "CD247"}
