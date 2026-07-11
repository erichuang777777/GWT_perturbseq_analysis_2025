"""
chart_id:        A17
source image:    figure1.png
chart title:     Signed-DE application & external validation (7-panel)
language:        unknown
env name:        python
input-artifact version_ids (18):
  - 729315c2-a086-4988-a12c-ecf15a1b5ffb  (signed_ranking_v2.csv)
  - c454a7d1-11f0-49f1-94a6-f8bc692e682b  (downstream_enrichment_v2.csv)
  - be0150d9-d316-4f49-bfd7-b2fe82d0f999  (lincs_concordance.csv)
  - 51e54f43-4c6b-4579-ae43-4e6dbe1b4593  (ot_genetic_association_crosscheck.csv)
  - 8234b4b5-8eb7-42bd-8c35-184f514b90ca  (string_partner_recovery.csv)
  - 6ae01452-3790-45ed-b424-12b2fa940736  (gse318876_target_evidence.csv)
  - e2949caf-db1c-40f1-9a24-78987a7149a4  (panelB_signed_volcano.csv)
  - 6fd31e24-9ba8-4a16-bcd7-1c41076c4248  (panelC_downstream.csv)
  - 4c284560-ad3c-4d99-89df-a8dc2af5e6c0  (panelD_gwas.csv)
  - 8dfb6d94-4f08-4862-bb54-8eb29567aa53  (panelE_string.csv)
  - d6e145c8-6eac-4cb6-89b5-988966b0bb3d  (panelF_hiv.csv)
  - 33e15964-b453-4950-b624-14ea5a9a545c  (panel_a.png)
  - d2da1659-248b-4e64-8362-f99b3821c8a4  (panel_b.png)
  - 2b989956-52d4-4bf6-8ef0-c81a9b19230a  (panel_c.png)
  - d036fd0f-a8cb-413f-93c0-6e669bf4b720  (panel_d.png)
  - 11ee353b-0e45-4bc5-a31b-3dd8f7bba307  (panel_e.png)
  - 71d9a85a-dde7-4ed5-8cf3-0d6dca0ebb9f  (panel_f.png)
  - 0ba87550-bfb3-42df-aa6a-3ddcc285578f  (panel_g.png)

NOTE: This figure was COMPOSED from pre-rendered sub-panels (see input
artifacts panel_*.png above). The producing cell in the main lineage is a
bare compose_figure() call with no standalone panel-plotting logic; the
per-panel code is NOT present in this artifact's lineage. No plotting code
has been fabricated. To tweak a single panel, edit the source cell that
produced the corresponding panel_*.png input, or the compose_figure helper.
"""

# --- Raw producing cell (stub; not self-contained) ---
# [lineage] reconstruction failed validation (max_tokens) — raw producing cell below; see Execution Log for full trace
out,(W,H)=compose_figure(outline, paths, "figure1.png", letter_case="lower")
print("recomposed", W, H)

