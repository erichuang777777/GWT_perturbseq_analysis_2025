# PR #10 任務執行報告 — 在本 sandbox 完成的項目

**執行環境：** Claude Science sandbox（**有 allowlist 網路 + MCP 連結器**）
**日期：** 2026-07-08
**對照：** PR #10 `docs/sandbox_blocked_tasks.md`

## 關鍵前提更正

PR #10 由假設「**沙盒無對外網路**」的雲端 session 撰寫，把多數任務標為 blocked。
但**這個 sandbox 對相關 API 有 allowlist 網路存取**（實測全部 HTTP 200）：
Open Targets、gnomAD、ClinicalTrials.gov、Reactome、STRING、PubMed、AlphaFold DB。
因此 PR #10 清單上的 B/C/D/E/G 五項在此**做得到**，並已用 repo 的**真實模組函式**完成
（不是重寫，是 import `evidence/external_cache.py`、`evidence/pathway_cache.py`、
`evidence/safety_overlay.py` 直接執行，確保輸出符合 schema 契約）。

## 已完成項目

| # | 任務 | 狀態 | 產出 |
|---|---|---|---|
| B | gnomAD LOEUF/pLI | ✅ 完成 | `_overlays/gnomad_constraint_seed.csv`（8→15 基因，schema `ensembl_id,gene_symbol,loeuf,pli`，通過 `load_gnomad_constraint_overlay` 驗證）|
| C | Open Targets 全量證據 | ✅ 完成 | 15 個 `_evidence/<gene>.json`，含 tractability/genetics/safety |
| C★ | **PLCG1→Angioedema 驗證** | ✅ **坐實** | `fetch_open_targets("PLCG1")` 真實回傳 `safety_liabilities:[{event:"Angioedema"}]`，已寫入 committed 快照 |
| D | 外部證據快取（CT.gov/PubMed）| ✅ 完成 | 同上 15 個快照，literature 50 篇真實 PubMed，全部 `source_status:ok` |
| E | Reactome + STRING 機制圖 | ✅ 完成 | 15 個 `_pathway/<gene>.json`，全部 ok |
| G | AlphaFold 結構補齊 | ✅ 完成 | 10 個 broad-effect 基因 `<GENE>_AF.cif`（shortlist 15 個現全數有結構）|

## 仍無法完成（真的受限）

| # | 任務 | 卡在什麼 |
|---|---|---|
| A | 全量 cell×gene DE 重跑 | 需 Stanford OAK 1.7TB 單細胞資料 + 算力，兩者都未掛載於此 sandbox |
| F | LINCS/CMap 化合物 signature | 來源資料不在 repo、且無公開免費 API 可直接抓 |

## 生物學正確性驗證（PR #10 點名項）

- **CD3E → CD3D/CD3G/CD4/SYK**：STRING 全部命中 ✓
- **MED12 → 15 個 Mediator 複合體成員**（MED1/MED10/MED11/…）✓
- **PLCG1 → Angioedema safety liability**：坐實 ✓
- **tractability 分離**：免疫候選（CD3E 10、LAT/PLCG1 7、CD247 6）> broad-effect（多為 2-3）——
  第 N 個獨立來源印證 C7 broad-effect 隔離的正確性。
- **MED12 gnomAD LOEUF=0.095**（極度 loss-intolerant），安全窗口紅旗。

## 放回 repo 的方式（遵守 PR #10 原則）

- 每個證據/機制快照都帶 `fetched_at` + `source_version`（沿用模組既有欄位）。
- gnomAD overlay schema 對齊，**零改碼生效**（已用真實 loader 驗證 available=True）。
- gnomAD 門檻備註：抓的是 **v4**（`oe_lof_upper`）；LOEUF<0.6 為 v4 官方 loss-intolerant 門檻（非舊 v2.1.1 的 0.35）。
- 抓不到的（如某些基因無 constraint）維持 honest fallback，不虛構值。
- 全量 `.h5ad`（任務 A）不進 git——本次未執行。

## 檔案清單

- `sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv`（15 基因）
- `sources/target_tool_cache/_evidence/*.json`（15 個）
- `sources/target_tool_cache/_pathway/*.json`（15 個）
- `docs/mvp-research/visualization/structures/*_AF.cif`（新增 10 個 broad-effect 結構）
