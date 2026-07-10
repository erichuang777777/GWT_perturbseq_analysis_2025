# External QA Review Intake — 2026-07-10

## 這份文件是什麼

2026-07-10 收到一份外部（Codex-style QA agent）對整個 repo 的靜態科學嚴謹性審查，涵蓋
scientific rigor、方法學設計、呈現方式。使用者指示：**另一個 agent/session 已經在處理相關修正
（`.claude/worktrees/agent-*` 有 3 個進行中的 worktree；`main` 已有 "Task A: extract full
genome-wide signed DE matrix"、"Freeze: pin all 7 pipeline stages" 等提交），這個 session 只需要
把審查內容整合、記錄下來，不重複實作**。

因此本文件是**記錄層**：保留審查的原始判斷、標註哪些是本 session 當場覆核為真、哪些已有既存
追蹤機制（避免與 `docs/human_validation_protocol.md` §9 Open Findings 或
`docs/def_followup_plan.md` 重複記錄同一件事），哪些是全新、目前無人追蹤的項目。

## 總體評分（審查原文摘要）

科學意義：高 · 方法學骨架：中高 · 復現/方法透明度：中等，仍需補強 · target-prioritization 呈現：
有價值但需避免過度詮釋 · 作為臨床/治療決策工具：不充分（repo 本身多處已聲明僅供
hypothesis-generating）。

## 逐項覆核

| # | 審查發現 | 本 session 覆核結果 | 是否已有追蹤 |
|---|---|---|---|
| 1 | Primary DE 以 `target` 為 contrast（`design_formula: '~ log10_n_cells + donor_id + target'`），guide-level heterogeneity 主要靠事後 robustness flag 補救，而非模型一級 uncertainty。建議明確分層呈現（pooled → guide-consistent → donor-consistent → knockdown-confirmed → high-confidence）。 | **verified** — `src/3_DE_analysis/DE_config_local.yaml:27` 的 formula 屬實。 | **部分已追蹤**：`docs/def_followup_plan.md` 的 `high_confidence` 定義（`replicate_pass_flag` + cross-donor/guide + cells + offtarget）已在做同方向的分層；本項的「呈現時要把 pooled signal 和 robustness-filtered signal 分開標示」是尚未落地的呈現層建議，未見於任何現有 doc。 |
| 2 | Robustness coverage 稀疏（33,983 列中僅 1,102 過 `replicate_pass_flag`），排名/呈現不該預設把 raw DE breadth 當作最終結論。 | **verified exactly** — `docs/def_followup_plan.md:20,35` 精確記載 1,102/33,983（3%）且 top-N 在嚴格穩健過濾下翻攪 74–85%。 | **已追蹤** — `def_followup_plan.md` 的 D 項就是在處理「過濾優先 vs 加權排序」這件事。本項等於是外部審查獨立確認了同一個已知問題，沒有新資訊。 |
| 3 | `DE_config_local.yaml` 的 `reduced_targets_only: true`（只跑 1,235 個過 MVP 門檻的 targets）若被誤讀為 genome-wide 結果會誤導 FDR/hit-rate 詮釋。 | **verified** — `src/3_DE_analysis/DE_config_local.yaml:36-37` 屬實：`# 只跑通过 MVP 门槛的 1,235 个标的` / `reduced_targets_only: true`。 | **未見追蹤** — 目前沒有任何 doc 明確警告「這是 demo/reduced config，不是 genome-wide config」；`_local` 後綴本身也不足以傳達這個區別給非工程背景的科學家。**建議未來補進 OF 系列（例如 OF-8）或 `data_dictionary.md`。** |
| 4 | `make_pseudobulk.py::main_merge()` 內有 hardcode 的 `/mnt/oak/users/emma/...` 路徑，弱化復現性。 | **verified** — `src/3_DE_analysis/make_pseudobulk.py:109` 屬實：`glob.glob('/mnt/oak/users/emma/data/GWT/CD4iR1_Psomagen/tmp/*DE_pseudobulk.h5ad') + glob.glob('/mnt/oak/users/emma/data/GWT/CD4iR2_Psomagen/tmp/*DE_pseudobulk.h5ad')`。 | **未見追蹤** — 這是 upstream one-time 合併腳本（不在本 repo 的 `make test`/`make validate-pipeline` 路徑上），目前沒有 open finding 涵蓋它。 |
| 5 | README quickstart 指向 legacy 資料集 `e7ecd8d5-...`（31-col），但 canonical 是 `a6bba17b-...`（39-col）。 | **verified** — `README.md:42` 目前仍指示使用者貼上 `e7ecd8d5-5463-43e3-9bf1-6e8a15d3e137`；`docs/REPRODUCIBILITY.md:139` 則以 `a6bba17b-...` 為起點資料集。兩者確實不一致。 | **已部分追蹤但未完整** — `docs/human_validation_protocol.md` OF-1（schema drift, BLOCKING）已記載 `e7ecd8d5` 是 31-col legacy、`validate_cards(strict=True)` 會失敗，並提出「是否該 retire/regenerate legacy 資料集」的問題；但 OF-1 沒有點名 **README 的 quickstart 本身正把新使用者導向這個 legacy UUID** 這個具體、可獨立修的呈現問題。**這是本次審查貢獻的新增細節，值得在 OF-1 的裁決欄位補上這一點。** |
| 6 | Perturb-seq 實驗證據 / disease-gene association / LoF burden / drug-trial 證據 / readiness call 是不同層級的 evidence type，容易被 polish 過的 dashboard 過度解讀成「target 已驗證」。 | 未逐一重新核對每個呈現位置（範圍太大），但 repo 現有文件（README「Research / hypothesis-generating use only」聲明、`docs/human_validation_protocol.md` §0 的 7-dimension 框架）方向上與此建議一致。 | **概念上已有 guardrail，但呈現層尚未強制**——沒有機制強迫每個 target card / dashboard 卡片都顯示 evidence-type 標籤。**未見具體追蹤項。** |
| 7 | 文獻合理性登記表（§7）許多列 DOI/PMID 留白，若不清楚標示會讓人以為驗證已完成。 | **設計本身正確**——`docs/human_validation_protocol.md` §0 明確定義留白 = 待人工簽核，never-fabricate 是刻意設計，非疏漏。本 session（PR #42）撰寫該表時只有 basiliximab↔IL2RA 一列是本 session 用 ClinicalTrials.gov 實查驗證，其餘刻意留白。 | **審查的疑慮是「對外部讀者的觀感」，不是文件本身的邏輯錯誤**——文件內部已誠實標示哪些是 verified、哪些待補。若要對外公開（如發表或分享給非團隊成員），才需要額外的「未完成」視覺標記；目前僅供內部/團隊使用，優先度較低。 |
| 8 | 應該在 README / reports / dashboard 一致地凸顯限制（CD4⁺ only、in vitro、CRISPRi 非 knockout、donor 數有限、transcriptomic phenotype only）。 | 部分文件已有此類聲明（README 的 hypothesis-generating 聲明、`src/9_cell_integration/README.md:114` 的 "Do not treat integrated embeddings as primary differential-expression evidence"），但確實不是每處呈現都重複這些限制。 | **未見統一的「limitations banner」追蹤項**——這是呈現一致性問題，不是單一 bug。 |
| 9 | `src/9_cell_integration` 的 state-specific 結果若被 join 回 target card，可能被當成與 pseudobulk DE 同等強的證據，即使該模組自己的 README 有警語。 | **verified** — `src/9_cell_integration/README.md:114` 確實有 "Do not treat integrated embeddings as primary differential-expression evidence."。審查的疑慮是**這個警語只存在模組自己的 README，一旦數值被 join 進 target card / dashboard，警語不會跟著走**。 | **未見追蹤**——沒有機制確認 target card 呈現層會把這條警語帶到使用者看到的畫面。 |

## 淨新增、目前無人追蹤的項目（給接手的 agent/使用者參考）

以下是本次覆核後認為**尚無任何現有 doc/OF 條目對應**、且已用真實檔案位置驗證屬實的項目，供後續
排入 `docs/human_validation_protocol.md` §9 Open Findings 或另開任務：

- `reduced_targets_only: true`（`DE_config_local.yaml:37`）需要在文件中明確區分「demo/reduced config」vs「genome-scale config」，避免結果被誤讀為 genome-wide screen。
- `make_pseudobulk.py:109` 的 hardcoded `/mnt/oak/users/emma/...` 路徑，離開作者環境即無法執行；應改讀 config。
- `README.md:42` 的 quickstart 貼上的 UUID 是 legacy（31-col, OF-1 already flags it as failing `validate_cards(strict=True)`），而非 `REPRODUCIBILITY.md` 記載的 canonical `a6bba17b-...`（39-col）——這是 OF-1 的一個可獨立處理的具體呈現面向，建議在 OF-1 的裁決欄位或另立新項時引用本文件。
- Evidence-type 標籤（screen evidence / genetic association / safety overlay / tractability precedent / readiness heuristic）目前沒有機制強制在每張 target card 呈現，仰賴讀者自行從 dashboard 文案理解。
- `src/9_cell_integration` 的「不可當 primary DE evidence」警語目前只存在該模組自己的 README，未確認是否隨資料 join 進 target card / dashboard 時一起顯示。

## 已存在、審查只是獨立再次確認（不需要新增追蹤）

- Robustness coverage 稀疏（1,102/33,983）——`docs/def_followup_plan.md` 已在處理。
- 文獻合理性登記表留白——`docs/human_validation_protocol.md` §0/§7 的設計本身就是刻意留白待人工簽核，非疏漏。

## 審查原文保留的方法學判斷框架（呈現指引，未變更任何程式碼即可採用）

**足夠支持的結論：** 某些 CRISPRi perturbations 在 primary human CD4⁺ T cells 中有明顯
transcriptomic effect；某些 target 有 condition-specific pattern；某些 regulator 與 T cell
activation/polarization/cytokine programs 有關；穿過 knockdown + donor/guide robustness + off-target
檢查後，可產生高可信度候選 target 子集；外部 human genetics/disease association/safety overlay 可
作為候選 target 的輔助 triage。

**不應過度支持的結論：** 某 target 已是 therapeutic target；某 target 在特定疾病中必然有效；
readiness score 等同臨床可行性；dashboard top rank 等同 biological truth；integrated embedding 的
state-specific signal 可取代 pseudobulk DE；reduced-target config 的結果可代表 genome-wide screen。

**建議用詞：** 傾向 "candidate" / "hypothesis" / "screen-supported regulator"，避免 "validated
target" / "actionable target" / "clinical priority"（除非另有實驗驗證）。
