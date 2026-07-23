# Ported architecture from CD4 hackathon competitors

**狀態:** 已實作 · **日期:** 2026-07-23 · **來源:** 深挖 67 個 CD4-related 競爭專案的**實際程式碼**,移植 5 個具體技術

我們 clone 並精讀了 9 個競爭者的真實原始碼(不是描述),抽出**可移植、且填補本 portal 缺口**的架構,重新實作進 portal(守本 repo 紀律:descriptive≠decision、`unknown≠0`、加法式、附測試)。

## 收斂主題

所有強工具都加了本 portal 原本沒有的三樣東西:**信心/可靠度數字**、**第一級的「拒絕/不支持」型別**、**用之前先驗證訊號**。以下 5 個 port 正是這三樣。

## 五個 port

| # | 技術 | 來源(真實程式碼) | 落點 | 測試 |
|---|---|---|---|---|
| 1 | **可靠度係數 R_dep**(confidence band + `S_t=effect×R_dep`) | G-perturb #133 `per_target_ranking.py:r_dep` | `reliability.py` + `/api/reliability/*` + export/types/DossierHeader 徽章 | `test_reliability.py` |
| 2 | **型別化 evidence-class + 守恆不變式**(entering==advanced+not_advanced+rejected+unresolved;深度誠實) | PerturbGate #155 `schemas.py`,`attrition.py` | `evidence_class.py` + `/api/readiness_audit/*` | `test_evidence_class.py` |
| 3 | **軸驗證**(對照論文已發表係數,弱軸降為 exploratory) | Validated Th1/Th2 Map #240 `discover.py:138`(gate 是散文,我們補上程式) | `axis_validator.py` + `/api/axis_validation` | `test_axis_validator.py` |
| 4 | **confound 控制工具**(covariate-matched permutation + partial-Spearman) | HumanCD4CoDEGNet #234 `disease_hubs.py:48`,`further_tests.py:24` | `controlled_enrichment.py` | `test_controlled_enrichment.py` |
| 5 | **readiness 忠實性自檢**(每個 call 從自己的紅旗 cap 重新推導、檢查一致) | CD4 Predictability Audit #261 `scorecard.py:196` | `readiness_selfcheck.py` + `/api/readiness_audit/*` | `test_readiness_selfcheck.py` |

## 關鍵設計決定

- **R_dep 用現成資料**:`crossguide_correlation` + `crossdonor_correlation_mean` 早就在每張卡上,所以信心層**零 pipeline 變更**。`unknown≠0`:未量測的相關 → `r_dep=null`;量測到的非正相關 → `0.0`(可靠地不可靠),兩者分開。
- **descriptive≠decision**:全部 5 個都是描述性 —— R_dep 是**顯示在 readiness call 旁邊的 band,絕不折進 call**;evidence-class 由 call 推導而非反向;軸驗證與自檢都不改判定。
- **自檢的 cap 表與引擎同步**:`readiness_selfcheck.RED_FLAG_CAP` 與 `core/readiness.py:_red_flags` 逐條對齊,並由 `test_readiness_selfcheck.py::test_caps_in_sync_with_readiness_engine` 用 `inspect` 守住不漂移。
- **誠實可攜性**:The Nineteen 與 CoDEGNet 沒有可重用的 API 程式碼(HPC 一次性腳本),只移植其**方法**;Bench2Biobank/G-perturb/PerturbGate/PredAudit/T-CTRL 是真的可安裝套件。

## 誠實 caveat

- 前端 R_dep 徽章要在有 canonical dataset 的環境重跑 `export_real_data.py --force` 才會亮(plumbing + types 已就位、typecheck 過)。
- 軸驗證的 `rho>=0.35 AND auroc>=0.65` 門檻是我們補的(#240 只算 metric、把 demotion 留在散文),已放進可調參數並標明。
- 未移植:Bench2Biobank 的自我假陽性框架(MHC/nearest-gene/phenome-category)是策展輸出非程式碼;SNR predictability flag 需要 control-cell variance(卡片未帶)。
