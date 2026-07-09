# Wiki 原始檔(繁體中文)

這個資料夾是 GitHub Wiki 的原始 Markdown 內容,對應 `erichuang777777/GWT_perturbseq_analysis_2025.wiki.git`。

之所以放在主 repo 而非直接推到 Wiki:目前的自動化 session 對 `.wiki.git` 端點沒有推送權限(git proxy 回 403 — Wiki 不在 session 的 git 範圍內)。內容已在此完整撰寫並版本控管,可用下方一行指令發佈到真正的 Wiki。

## 頁面

| 檔案 | Wiki 頁面 | 內容 |
|---|---|---|
| `Home.md` | 首頁 / 介紹 | 平台是什麼、能力總覽、設計原則 |
| `Development-Guide.md` | 開發說明 | 給協同開發夥伴:現況、目標、快速上手、程式碼地圖、可接手的第一件事 |
| `Manual.md` | 完整手冊 | 引用文獻、數據來源、說明/開發文件索引、commit 紀錄、ASCII 架構圖 |
| `Maintenance.md` | 維護 | 環境、執行、測試、重建、快取/版本失效 |
| `Roadmap.md` | 路線圖 | Wave 1–6 已完成 + 未來方向 |
| `Plan.md` | 計劃 | 實作計劃摘要與規格來源 |
| `Tech-Debt.md` | 技術債 | code review 發現的正確性問題、descope、清理項目 |
| `_Sidebar.md` | 側邊欄 | 導覽 |

## 發佈到 GitHub Wiki

先在 GitHub 上啟用 Wiki(Repo → Settings → Features → Wikis 打勾),並在 Wiki 頁面隨意建立第一頁一次以初始化 `.wiki.git`。然後在有 GitHub 認證的機器上:

```bash
git clone https://github.com/erichuang777777/GWT_perturbseq_analysis_2025.wiki.git
cp wiki/*.md GWT_perturbseq_analysis_2025.wiki/
cd GWT_perturbseq_analysis_2025.wiki
git add -A
git commit -m "Populate wiki (zh-TW): introduction, maintenance, roadmap, plan, tech debt"
git push origin master
```

> Wiki 頁面連結用檔名(去掉 `.md`),例如 `[維護](Maintenance)`。頁面之間的相對連結已按此格式撰寫。
