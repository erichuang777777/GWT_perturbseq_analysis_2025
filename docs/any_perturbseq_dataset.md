# Bring your own perturb-seq dataset — end-to-end runbook

**狀態:** 使用指南 · **日期:** 2026-07-22 · **語言:** 繁中 + 英文技術詞
**目的:** 把 portal 從「一個 CD4 資料集」升級成「接納任何 perturb-seq scRNA」。四階段 P0–P3 已全部實作 + 測試,本頁是**整合操作手冊**。

---

## 你的資料在哪一層,就從哪一步進

```
原始 scRNA (.h5ad/.mtx)           →  P3 prep  →  兩張 CSV
    │                                              │
    │(已經是摘要表就跳過 P3)                          ▼
    └────────────────────────────────►  target_evidence.csv  +  signed_de.csv
                                                    │
                                     P1 上傳 /api/imports (兩種 source type)
                                                    │
                          ┌─────────────────────────┼──────────────────────────┐
                          ▼                          ▼                          ▼
                 cards + readiness         reversal / breadth /        P0 export --cards
                 (target_evidence)         ego-network (signed_de)     → 靜態 portal
```

---

## P3 — 原始 h5ad → 兩張 CSV(離線)

portal runtime 刻意不吃原始細胞(無 scanpy)。用離線工具轉檔:

```bash
python3 src/3_DE_analysis/raw_perturbseq_prep.py my_screen.h5ad \
    --out ./prep_out --target-col target --condition-col condition --control-label NTC
# → prep_out/target_evidence.csv, prep_out/signed_de.csv, prep_out/prep_manifest.json
```

- DE 核心 `pseudobulk_de` 是純 numpy/pandas/scipy(log2FC of group means + Welch t + BH-FDR)。
- **誠實 caveat**:這是快速 pseudobulk mean-difference,**不是** paper 的 donor-aware DESeq2 管線;要發表級結果請走完整 `src/1_preprocess … 3_DE_analysis`。caveat 印在終端也寫進 manifest。
- 低於 `--min-cells` 的組直接跳過,不 impute。

## P1 — 上傳兩張 CSV(bring-your-own-data)

`/upload` 或 `POST /api/imports`,兩種 source type:

| 檔 | source type | 餵給 | 必要欄 |
|---|---|---|---|
| `target_evidence.csv` | `target_evidence` | cards + readiness | `target`, `condition` |
| `signed_de.csv` | `signed_de_evidence` ⭐新 | 反轉 / 廣度 / 網路 | `target`(或 `target_gene`), `downstream_gene`, `log_fc`(或 `beta`/`coef`) |

signed 表在你自己的資料上跑三大引擎:
```bash
# 反轉:哪個 KD 反轉你的疾病 signature
curl -X POST /api/disease_reversal/from_upload \
  -d '{"import_id":"<id>","up":["G1","G2"],"down":["G3"],"min_hits":3}'
# 網路廣度 / hub
curl "/api/trans_network/from_upload/<import_id>?gene=MYGENE"
```

- reader `signed_de_io.read_signed_de_table` 容錯欄名(gene/beta/coef/padj…);無 condition → 合成 `all`;無 padj → 視為顯著(0.0),兩者都在 `notes` 揭露,不隱藏。

## P0 — 用你的 cards 烘焙靜態 portal

```bash
python3 frontend/webserver/scripts/export_real_data.py \
  --cards /path/to/your/target_cards.csv --out frontend/webserver/public/real-dataset.json --force
# 或 GWT_CARDS_CSV=... GWT_OUT_JSON=...
```
新欄位(novelty / hypothesis / knownDrugs / transNeighborhood)會一併灌入;找不到 dataset 會給清楚錯誤而非 crash。

## P2 — 非 CD4 資料集的去 CD4 化(env 覆寫,預設不變)

```bash
export GWT_PUBMED_CONTEXT="hepatocyte"          # 新穎性用你的細胞情境查文獻
export GWT_POSITIVE_CONTROLS="GENE1,GENE2"       # 你領域的陽性對照
export GWT_OFF_CONTEXT_TISSUES="Liver,Kidney"    # off-context 安全訊號排除的組織
export GWT_ENABLE_CONCEPT_MODULES=0              # 非 CD4 關閉 M01–M20 概念模組
```
查目前生效設定:`GET /api/domain_context`。這些只調**描述性/證據情境**,**不動**校準過的 readiness 決策路徑。概念模組關閉後,用**任意上傳 signature 的反轉引擎**取代固定 CD4 模組。

---

## 天生就與資料集無關(零設定)

只要是基因 symbol 就能用,換資料集不用改:PubMed novelty(情境可調)、Open Targets 藥物 / disease-drug、gnomAD/GTEx 疊加、deterministic hypothesis、QC 前置閘門、自含 HTML 報告、self-falsification 稽核。

---

## 對照:四階段實作與測試

| 階段 | 交付 | 測試 |
|---|---|---|
| P0 export 任意 dataset | `export_real_data.py` `--cards/--out` + env | 手動驗證(跑通替代 dataset 路徑) |
| P1 signed-DE 上傳 → 三引擎 | `signed_de_evidence` 型別 + `signed_de_io` + `from_upload` 端點 | `test_signed_de_upload.py` |
| P2 去 CD4 化 | `domain_context.py` + novelty 接線 + `/api/domain_context` | `test_domain_context.py` |
| P3 raw h5ad → CSV | `raw_perturbseq_prep.py`(純 DE 核心 + h5ad wrapper) | `test_raw_perturbseq_prep.py` |

**一句話**:摘要表**現在就能上傳評分**;signed 表**現在就能跑反轉/廣度/網路**;原始 h5ad **用離線 prep 一步轉檔**再走上面;非 CD4 **用四個 env 覆寫**。整條 bring-your-own-data 通了。
