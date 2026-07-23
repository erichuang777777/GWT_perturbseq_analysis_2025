# Builder-track pitch — the same project, reframed where its strengths score

**狀態:** framing 草稿(Action 2)· **日期:** 2026-07-22 · **語言:** 繁中 + 英文技術詞
**目的:** 把同一套東西重新框成 **Builder** 提案。競爭診斷的第一硬傷是**軌道錯位** —— 最強的兩維(可重用性、產品化誠實)在 Researcher 軌道**不計分**,而 ShiftScope / Louis / Spot 這些同性質工具全報 Builder 且得獎。這一頁把武器對準會計分的靶。

---

## 1. 一句話產品定位(Builder 版)

> **CD4 Target Explorer —— 一個把任何 CD4 Perturb-seq 篩選變成「可上傳、可評分、會拒絕自己壞命中」的靶點決策系統。上傳你的 DE 表或疾病 signature,90 秒得到帶紅旗、帶方向、帶藥物連結、且附一句可測試假說的 target cards —— 而且系統會誠實告訴你它該低分的地方。**

對標:ShiftScope(新穎性排序工具,Builder 得獎)、Louis(活在 Claude 的 MCP bot)、Spot(HuggingFace 產出)。**它們賣「好用的工具」,本項目賣「好用 + 會自我否決的決策系統」。**

---

## 2. Builder 軌道看什麼,我們有什麼(逐項對位)

| Builder 評分點 | 本項目的實體 | 檔案/端點 |
|------|------|------|
| **可重用(跑他人資料)** | live CSV 上傳 → 欄位對映 → approve → merge → **真 readiness** | `GET /upload`、`/api/imports/*` |
| **可重用(跑他人 signature)** | 上傳/選 disease signature → 全靶點反轉排序 | `GET /disease-reversal`、`POST /api/disease_reversal` |
| **端到端無需 build** | 一鍵 `make dev`;portal 讀預建 JSON,API 現成 | `Makefile`、`real-dataset.json` |
| **產品化誠實** | 4 分數+7 紅旗才動判定;`unknown≠0`;safety overlay regression-locked | `core/readiness.py` |
| **會自我否決(差異化)** | 系統把自己最漂亮的 hub 命中,用自己的安全否決清單擋掉(top-50 hub 48% 被否決 vs 尾端 2%) | `GET /api/self_falsification` |
| **帶行動的輸出** | 每卡一句確定性可測試假說 + 建議驗證 | `GET /api/hypothesis/{gene}` |
| **可攜交付** | 單檔自含 HTML 報告,給不用 portal 的合作者 | `GET /api/reports/{ds}/{gene}` |
| **API-first / 可整合** | 23 個 REST router,OpenAPI `/docs`,零降級載入 | `api/app.py` |

**判讀**:Researcher 軌道只給「一個發現」計分;上面這 8 列在那裡幾乎全是 0 分。在 Builder 軌道,它們全部計分,而且「會自我否決的決策系統」是全場沒有第二個的差異點。

---

## 3. 三個 90 秒 demo(Builder 評審愛看能跑的)

1. **上傳我的 screen**:丟一個 DE CSV 進 `/upload` → 看 QC 前置閘門擋住低 cell-count → 對映 → merge → 真 readiness 判定跳出來。
2. **上傳我的疾病**:在 `/disease-reversal` 貼一組 up/down 基因 → 全靶點按「哪個 KD 反轉這個疾病」排序,附 min_hits 誠實揭露。
3. **看系統打自己臉**:打 `/api/self_falsification` → 「我最像 master-regulator 的命中(SAGA/Mediator),被我自己的安全軸擋掉 48% —— 我不推銷我的 darling」。

---

## 4. 相對 Builder 得獎者的差異化一句話

- vs **ShiftScope**(新穎性排序):我不只排序,我輸出**帶決策狀態 + 會拒絕自己**的卡片;而且新穎性只是我 40+ 欄之一(`P0-E` 已把即時 PubMed novelty 收成一個維度)。
- vs **Louis / Spot**(通用工具):我針對 CD4 決策場景做深 —— 方向反轉、網路牽連、藥物連結、可測試假說、自含報告,一條龍。
- **共同殺手鐧**:`self_falsification` —— 一個會用自己的紅旗擋掉自己最漂亮命中的工具,把「產品化誠實」升級成「可展示的自我證偽」,對齊 Louis「kills its own darling」的得獎氣質,但做成**任何人可調用的端點**。

---

## 5. 如果只能改一句提交文案

> 從:「39 欄位打分 + 4 種 readiness 判定的靶點發現系統。」
> 到:**「上傳你的篩選或疾病 signature,得到會拒絕自己壞命中的 CD4 靶點決策 —— 帶方向、帶藥物、帶可測試假說,並附一鍵自含報告。」**

前者描述架構,後者描述**使用者能做什麼 + 為什麼可信**。Builder 軌道買的是後者。

---

## 6. 與 `docs/the_bet.md` 的關係(兩條路不互斥)

- **報 Builder**:用本頁,主打工具 + 自我證偽;`the_bet.md` 的 NR2F6 當「這工具能產出這種等級發現」的 demo。
- **報 Researcher**:用 `the_bet.md`,NR2F6 當靈魂,系統退居證據;本頁的工具面當「可重現、可證偽」的支撐。

無論哪條,**先有那句 bet**(動作1)都是前提 —— 連工具都需要一個殺手級 demo 命中。
