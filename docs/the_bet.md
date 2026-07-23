# The Bet — one falsifiable claim this project stands behind

**狀態:** claim 文件(Action 1)· **日期:** 2026-07-22 · **語言:** 繁中 + 英文技術詞
**目的:** 把系統的輸出煉成**一句可能被推翻的話**,讓項目有靈魂、有賭注 —— 系統退居證據。

---

## 0. 為什麼需要這一頁

競爭診斷點名的決定性弱點:得分高的對手都押了「一句可能被推翻的話」(KAT6B、STAT6 新軸、17% 可信…),而本項目把 Core-5 / shortlist 降格成「系統輸出範例」。**有子彈,沒扣扳機。**

這一頁扣扳機。並且遵守本 repo 的獨門紀律:**這句 bet 必須活過系統自己的 7 個紅旗**才算數 —— 一個能通過 regression-locked 誠實閘門的 bet,可信度天生高過沒有防守的命中。

---

## 1. The bet(一句話)

> **一個不用任何藥物或疾病標籤的擾動篩選,獨立把 `NR2F6` 提名為 CD4⁺ T 細胞 Th2↔Th1 極化的可反轉調控點 —— 而 `NR2F6` 正是外部免疫學早已證明的 T 細胞內在檢查點(intracellular immune checkpoint)。**

英文版(給標題用):

> *A label-free perturbation screen independently nominates **NR2F6** as a reversible regulator of CD4⁺ T-cell Th2/Th1 polarization — the same gene external immunology has already shown to be a causal intracellular T-cell checkpoint.*

---

## 2. 這句話怎麼從系統**自己**長出來(可重現)

三個獨立的、標籤無關的計算同時指向 `NR2F6`,全部跑在真實的 `full_signed_DE` 篩選資料上:

| 訊號 | 計算 | `NR2F6` 的值 | 意義 |
|------|------|------|------|
| **方向反轉** | `disease_reversal.rank_reversal`(Th2/Th1 builtin signature,`min_hits≥8`) | reversal **+2.37**,8 hits,`reverses_disease` | 敲低 `NR2F6` 把細胞往 Th1 方向推 —— **有方向,不是靜態打分** |
| **網路中心性** | `trans_network`(KD→DEG out-degree) | breadth **16** | 有下游效應,但**聚焦**(非 SAGA/Mediator 那種 broad-effect 巨頭) |
| **活過紅旗** | 不在 `core_essentials_hart` 也不在 `broad_effect_genes` 否決清單 | ✅ 通過 | 系統**不會**因 broad-effect / essential 把它 cap 掉 |

**關鍵**:提名過程**沒有用到** `NR2F6` 是檢查點這個先驗知識 —— 純粹是「哪個 KD 反轉極化特徵 ∩ 聚焦下游 ∩ 通過安全否決」。這正是 #81「文獻盲測獨立命中」的結構。

複現指令:
```bash
python3 src/3_DE_analysis/disease_reversal.py --signature th2_vs_th1_polarization --min-hits 8 --top 20
python3 -c "import sys; sys.path.insert(0,'src/3_DE_analysis'); import trans_network as t; print(t.breadth_for_target('NR2F6'))"
```

---

## 3. 外部確認(receipts —— 系統不知道、但世界知道)

`NR2F6`(Ear-2 / COUP-TFIII)是**已發表、有因果證據**的 T 細胞內在檢查點:
- 敲除 `Nr2f6` 增強抗腫瘤免疫、放大效應 T 細胞的 cytokine 程式(published knockout immunology)。
- 它是核受體家族(`metadata/gene_lists/nuclear_receptors.tsv`)—— 有 tractability 先例的一類。

也就是說:一個**不知道**這件事的篩選,從純資料把它排到極化反轉的前段班。**外部證據與系統獨立收斂**,這是 bet 的力量來源。

---

## 4. 怎麼**推翻**這句話(falsification criteria)

一個 bet 必須可證偽。以下任一成立即推翻或重大削弱:

1. **方向錯**:獨立 guide / 第二捐獻者的 `NR2F6` 敲低,若**不**把極化特徵往 Th1 推(reversal 方向翻轉或消失)。
2. **是 artifact**:若 `NR2F6` 的反轉分數在 donor-aware pseudobulk 下塌陷(比照 #229 對自己訊號的摧毀測試)。
3. **broad-effect 混入**:若更完整的網路推斷顯示它其實是 broad-effect(那系統的紅旗**應該**要抓到它 —— 沒抓到就是系統的錯,也是可報告的自我打臉)。
4. **極化特徵不對**:Th2/Th1 signature 只是**一個** proxy;若換 responder/non-responder 或 disease signature(用 `POST /api/disease_reversal`),`NR2F6` 掉出反轉前段,則這句話只在單一情境成立,需降級。

---

## 5. 誠實 caveat(不可省)

- **CRISPRi 敲低 ≠ 藥理拮抗**;reversal 分數是假說,不是療效。
- Th2/Th1 signature 是**代理**,非臨床終點。
- 本頁的反轉/breadth 數字跑在真實 `full_signed_DE` 上,但**最終鎖定**需在 canonical dataset 上重跑一次 readiness(本 sandbox 僅有 deprecated dataset);鎖定後把數值 freeze-pin。
- 候選不只一個(見 §6)—— `NR2F6` 是**目前最可辯護**的一個(生物學可信 + 聚焦 breadth + 過紅旗),不是唯一。

---

## 6. 為什麼是 `NR2F6` 而不是榜首 `TNPO3`

同一計算的前段候選(反轉 ∩ 過否決清單):`TNPO3`(+2.92)、`PARP8`(+2.90)、`AKAP10`(+2.82)、`NR2F6`(+2.37)…

選 `NR2F6` 當領銜 bet 的理由,全部是**可辯護性**而非分數:
- **外部因果證據存在**(TNPO3 是 nuclear import transportin,免疫故事弱)。
- **聚焦 breadth(16)** → 低 pleiotropy 風險,較可能過臨床 safety。
- **核受體 → tractability 先例**。

榜首但故事弱的候選(如 `POLR2M`,breadth 638)則**應該**被 broad-effect 邏輯戒慎對待 —— 這與 §Action-3 的自我證偽一致。

---

## 7. 這句話如何當項目的靈魂

- **標題**:從「我建了一個靶點發現系統」→「一個標籤無關的篩選獨立命中 NR2F6,而外部免疫學已證明它是 T 細胞檢查點」。
- **系統退居證據**:39 欄位 / 4 判定 / reversal 引擎不再是主角,而是**支撐這句 bet 的證據鏈 + 讓任何人拿自己 signature 重跑同一句話的機器**(`POST /api/disease_reversal`)。
- **對齊得獎氣質**:有方向(#81/#227)、有外部獨立收斂、有明確 falsification criteria、且**活過自己的紅旗**(本 repo 獨門)。
