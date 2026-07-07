# 架構重構規劃:模組拆分、隔離、可安全抽換

**狀態:** 規劃(尚未實作) · **語言:** 繁體中文 · **範圍:** `src/3_DE_analysis/`(平台工具);`src/1_preprocess`、`src/6`、`src/7` 等原始分析 pipeline 為獨立關注點,可沿用同一模式但不在本次首要範圍。

**目標(使用者需求):**
1. 把整個專案模組拆小。
2. 不同模組間盡量完整隔離,確保可以安全抽換。
3. 有共用變數設定,不會「一個壞掉全部壞」。

本文件是可審閱的設計藍圖;每個主張都對應 repo 內真實檔案與實測到的耦合,不含臆測。

---

## 1. 現況診斷(實測)

| 觀察 | 證據 | 問題 |
|---|---|---|
| 扁平結構、無 package | `src/3_DE_analysis/` 有 17 個 .py、無 `__init__.py`,靠 `sys.path` + `from build_target_cards import ...` | 沒有明確分層;任何檔案都能 import 任何檔案 |
| API god-module | `target_card_api.py`(990 行)import 其他 **10** 個模組,同時是 FastAPI app + 版本常數 + 路徑常數 + 全域快取 | 單點故障;一個 router 或一個被 import 的模組出錯,整個 app 起不來 |
| 無共用 config | 找不到 `config/settings/constants` 模組;**74 處**硬編碼路徑/常數 | 改一個路徑/門檻要改很多處;易漏 |
| 常數散落 | KD floor 在 `build_target_cards.py`;版本號在 `target_card_api.py`;相關係數門檻 0.2/0.3 在 `build_target_cards`、`calibration`、`readiness_engine` **各寫一份**(code review 已記錄) | 三份門檻可各自漂移,校準報告與實際評分可能不一致 |
| 跨模組挖私有函式 | `calibration`/`readiness_engine` reach into `build_target_cards`;重複實作 `_num`≈`_to_float`、`_now`==`utc_now`、`load_overlays`==`load_druggable_overlays`(code review 已記錄) | 契約隱性、易漂移 |
| **危險的依賴方向** | `readiness_engine.py` import `external_evidence_cache`(`load_snapshot`) | 核心評分依賴脆弱的網路層 → 證據層壞了會往核心傳 |
| 好的既有隔離 | `target_card_dashboard.py` 走 HTTP(`API_BASE = os.getenv("GWT_API_BASE", ...)`)連 API | 行程邊界隔離,這個模式正確,保留 |

**現況依賴圖(誰 import 誰):**
```
target_card_api ──► build_target_cards, calibration, cre_schema, disease_translator,
                    external_evidence_cache, gene_identifier_resolver, gene_search,
                    generate_target_report, import_manager, readiness_engine
calibration      ──► build_target_cards
readiness_engine ──► build_target_cards, external_evidence_cache   ◄── 危險:核心→脆弱邊緣
gene_search      ──► gene_identifier_resolver
```

---

## 2. 設計原則:依賴方向一律「往內指」

核心保證——**價值產出的核心(建卡、評分、就緒度)不依賴任何脆弱的邊緣(網路、框架、UI)**,所以邊緣壞了核心照跑。這就是「一個壞掉不會全部壞」的結構性根據。

```
   ui ─► api ─► { core, evidence, resolve, report, upload }
                          │
                          ▼
             { data, contracts, common, config }   ← 最內層,誰都不依賴
```

- 箭頭一律往內。**外層可依賴內層,內層永不依賴外層。**
- `core` 只依賴 `contracts`/`common`/`config`/`data`;**不 import `evidence`、`api`、`ui`**。
- 沒有任何模組依賴 `api`/`ui`,所以框架或介面壞掉燒不到領域邏輯。

---

## 3. 目標套件結構(17 檔 → 分層套件)

```
src/3_DE_analysis/
  config/
    settings.py      # 路徑、目錄(data dir、cache dir、gene_lists dir);env 可覆寫
    thresholds.py    # KD floor(0.001)、min_cells、min_de、相關係數門檻(0.2/0.3)、kd_status 門檻
    versions.py      # ENGINE_VERSION、DATASET_VERSION、CARD_SCHEMA_VERSION、SIGNATURE_SET、KD_THRESHOLD_VERSION
  contracts/
    card_schema.py   # target_cards.csv 欄位契約 + validate_cards(df)
    readiness_schema.py
    evidence_schema.py  # _evidence/<gene>.json 形狀
    interfaces.py    # Protocol:CardBuilder、ReadinessEngine、EvidenceProvider、GeneResolver
  common/
    coerce.py        # _to_bool / _to_float / _as_bool 合一(消滅重複)
    timeutil.py      # utc_now(消滅 _now 重複)
    io.py            # gene-set 載入、csv 欄位正規化
    degrade.py       # 統一的「try → typed unavailable」降級包裝
  data/
    loaders.py       # 讀 suppl tables、gene lists、overlays、benchmark
  core/                       # 純領域,無網路/無框架/無 I/O(只吃 loaders 給的 DataFrame)
    cards.py         # build_cards_frame(from build_target_cards)
    kd_status.py     # _kd_status + floor(引用 config.thresholds)
    scoring.py       # _make_score、_score_cap_reasons
    readiness.py     # readiness_engine(證據改為「注入」,不再 import evidence)
    calibration.py
  resolve/
    resolver.py      # gene_identifier_resolver
    search.py        # gene_search
    cre.py           # cre_schema
  evidence/                   # 脆弱、可降級的邊緣
    external_cache.py # external_evidence_cache
    disease.py        # disease_translator
    registry.py       # provider 註冊表 + 降級包裝
  report/
    generate.py       # generate_target_report
  upload/
    import_manager.py
  api/
    app.py            # FastAPI app 組裝
    deps.py           # DI:快取 resolver、settings、evidence provider
    routers/
      build.py cards.py readiness.py calibration.py evidence.py disease.py genes.py imports.py

frontend/                        # 獨立頂層資料夾(已完成,見 §5 Phase 0.5),不在 src/3_DE_analysis 之下
  README.md           # 隔離規則:只能透過 API 的 HTTP/JSON 溝通,不 import 任何 src/3_DE_analysis 模組
  dashboard/
    target_card_dashboard.py   # streamlit(已 HTTP 隔離),含自己的 requirements.txt
```

`src/9_cell_integration/` 已是獨立目錄,沿用同原則(它本來就 backed-mode、無框架依賴)。

**為何 `frontend/` 是頂層資料夾而非 `src/3_DE_analysis/ui/`:** 前端與後端本質上是「可能用不同語言/框架、可能不同人開發、可能獨立部署」的兩個系統,只靠 HTTP/JSON 契約溝通——這比 §2 的「依賴往內」原則更進一步,是**完全的行程邊界隔離**。放在 `src/3_DE_analysis/` 底下會誤導成「這是 Python 套件的一部分」,實際上它連 import 都不能有。

---

## 4. 三個需求 → 具體機制

### 4.1 拆小
- 依「責任層」分套件(§3)。
- 把 990 行的 `target_card_api.py` 拆成 **每個資源一個 router**(build / cards / readiness / calibration / evidence / disease / genes / imports),app.py 只負責組裝。

### 4.2 完整隔離 + 可安全抽換
- **① 單一資料契約 `contracts/card_schema.py`**:目前 `CARD_SCHEMA_VERSION` 只是字串;升級成真的欄位契約 + `validate_cards(df)`。任何 scorer 只要吐出契約,下游(calibration、report、dashboard)都不必改 → 這就是「安全抽換」的地基。
- **② 介面 Protocol `contracts/interfaces.py`**:定義接縫
  ```python
  class ReadinessEngine(Protocol):
      def compute(self, cards: pd.DataFrame, *, evidence: EvidenceLookup | None = None) -> pd.DataFrame: ...
  class EvidenceProvider(Protocol):
      def for_gene(self, gene: str) -> EvidenceSnapshot: ...  # 缺席時回 unavailable,不 raise
  ```
  API 依賴 **介面**,不依賴具體模組;抽換 = 換一個實作,呼叫端不動。
- **③ registry 註冊表 `evidence/registry.py`**:evidence 來源、overlay、scorer 以名稱註冊、用 `config` 選用。抽掉/替換一個 provider 不影響其他。

### 4.3 共用設定 + 一個壞掉不全壞
- **① 單一 `config/`**:所有路徑/門檻/版本一個來源,改一處生效。消滅 74 處硬編碼與三份重複的相關係數門檻。
- **② 統一降級邊界 `common/degrade.py`**:把 evidence 已有的 `source_status:"unavailable"` 模式抽成通用包裝,套用到所有可選能力;例外轉成 typed 結果,不往上竄。
- **③ 依賴往內(§2)**:core 零脆弱依賴 → evidence/api/ui 任一壞掉都燒不到建卡與評分。
- **④ API router 惰性載入 + 各自錯誤邊界**:一個 router import 失敗或一個 provider 當掉,不拖垮整個 app;`/health` 可回報「哪個能力可用/降級」。
- **⑤ 關鍵解耦**:`core/readiness.py` 不再 import `evidence`;證據以參數注入(`compute(cards, evidence=...)`)。同時滿足可抽換 + 故障隔離。

---

## 5. 分階段遷移(增量、測試護航)

每階段結束都必須:**31 個 pytest 綠 + `py_compile` 乾淨 + commit**。全程不改行為,只搬位置與加邊界。

| 階段 | 內容 | 風險 |
|---|---|---|
| **Phase 0.5**(已完成) | 把 `target_card_dashboard.py` 從 `src/3_DE_analysis/` 搬到頂層 `frontend/dashboard/`,附獨立 `requirements.txt` + `frontend/README.md`。搬移前已實測確認零 Python import 耦合(只用 stdlib/pandas/requests/streamlit,只靠 `GWT_API_BASE` 走 HTTP),故為零風險搬移。 | 已完成,見對應 commit |
| **Phase 0** | 新增 `config/`(settings/thresholds/versions)與 `contracts/card_schema.py`;**只集中常數 + 加 validator**,不搬檔。既有模組改 import 它們。 | 低。純新增 + 改引用點 |
| **Phase 1** | 抽 `common/`(coerce/timeutil/io/degrade),合併 code review 找到的重複函式;各模組改用 common。 | 低 |
| **Phase 2** | 引入 package + `__init__.py` **re-export shim**,讓舊 `from build_target_cards import X` 仍可用;再逐檔遷移 import。同步更新 `tests/conftest.py` 的 sys.path。 | 中(動最多檔,但有 shim 過渡 + 測試逐檔驗證) |
| **Phase 3** | 在接縫放 Protocol 介面 + registry;把 `readiness`→`evidence` 的 import 改為注入。 | 中 |
| **Phase 4** | 拆 API god-module 成 routers + `deps.py`(DI);router 惰性載入 + 錯誤邊界 + `/health`。 | 中 |

**回退性:** 每階段獨立 commit,任一階段有問題可單獨 revert;Phase 2 的 shim 讓新舊 import 並存,不需一次全改。

---

## 6. 風險與取捨

- **最大動作在 Phase 2 的 import 遷移**:靠 `__init__.py` re-export shim 過渡 + 31 個測試當安全網,逐檔驗證;`conftest.py` 需同步。
- **不追求一次到位**:Protocol/registry(Phase 3)只在「真的需要抽換」的接縫放(evidence、scorer、resolver),不在每個函式都套介面,避免過度工程。
- **行為不變**:本重構是純結構調整;若任何一步改到數字或決策,即為 bug,測試會擋下(golden-file + known-answer 會抓到)。
- **與現有 PR 的關係**:建議在 PR #3 合併後、以新分支分階段進行,每個 Phase 一個小 PR,方便審閱與回退。

---

## 7. 驗收標準(重構完成的定義)

1. `core/` 內任何檔案 `grep` 不到 `import`  `evidence`/`api`/`ui`/`streamlit`/`fastapi`/`requests`。
2. 所有路徑/門檻/版本只在 `config/` 出現一次(`grep` 驗證無重複硬編碼)。
3. 停用任一 evidence provider 或讓其拋錯,`build`+`readiness`+`calibration` 仍完整跑完(故障隔離測試)。
4. 抽換一個 scorer 實作(符合 `card_schema` 契約),下游模組與測試零修改即通過。
5. 31 個既有測試全綠,並新增:契約 validator 測試、故障隔離測試、注入式 readiness 測試。
