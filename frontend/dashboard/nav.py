"""Cross-page navigation helpers for the frontend dashboard (FE-1).

Pure, Streamlit-free deep-link logic so a list view (main dashboard) can open the
target-dossier page on a specific target via ``?target=&dataset_id=`` query params
+ ``st.switch_page``. Kept out of the page files so it is unit-testable without a
Streamlit runtime (importing a page module would execute the whole page).

Frontend isolation (frontend/README.md): this module imports nothing but stdlib
typing — no backend, no HTTP, no Streamlit.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Optional, Tuple


def seed_dossier_session(
    query_params: Mapping[str, Any],
    session_state: MutableMapping[str, Any],
) -> Tuple[Optional[str], Optional[str]]:
    """Seed the dossier's ``dossier_query`` / ``dossier_dataset`` from deep-link
    query params, but ONLY when the session does not already hold that key -- so a
    user's own edit or navigation is never overwritten on rerun.

    ``query_params`` and ``session_state`` are the ``st.query_params`` /
    ``st.session_state`` proxies (both ``dict``-like), passed in so this stays
    pure and directly testable with plain dicts. Returns
    ``(dataset_id_seeded, target_seeded)`` -- either element is ``None`` when that
    field was absent from the params or the session key already existed.
    """
    target = query_params.get("target")
    dataset_id = query_params.get("dataset_id")
    seeded_target = seeded_dataset = None
    if target and "dossier_query" not in session_state:
        session_state["dossier_query"] = target
        seeded_target = target
    if dataset_id and "dossier_dataset" not in session_state:
        session_state["dossier_dataset"] = dataset_id
        seeded_dataset = dataset_id
    return seeded_dataset, seeded_target
