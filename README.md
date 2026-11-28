# AI 趨勢日報

每 12 小時自動抓取全球 AI 新聞，經過去重、評分、分類後存成 JSON，發布成 GitHub Pages 靜態網站。每則新聞都標出來源並附原文連結。不使用 AI、不需要任何 API 金鑰。

## 第一次設定

1. 啟用 Pages：Settings → Pages → Build and deployment → Source 選 **GitHub Actions**。免費方案的 organization 只有 public repo 能用 Pages。
2. 手動跑第一次：Actions → Update AI trend data → Run workflow。之後每天 00、12 點（UTC，台北 08、20 點）自動執行。

## 本機執行

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt

.venv/bin/python scripts/run_local.py                       # 寫入 data/
.venv/bin/python scripts/run_local.py --out /tmp/trend-test  # 輸出到別的資料夾

# 重新測試所有來源，產生 sources_report.md
.venv/bin/python scripts/check_sources.py

# 離線自我檢查（去重、評分、分類規則；不連網）
.venv/bin/python tests/test_offline.py
```

## 流程

| 步驟 | 做法 |
|---|---|
| 抓取 | `sources.yaml` 列出的來源，只取 48 小時內的項目；單一來源失敗只記 log。熱度來源是 Techmeme、Hacker News（200 分以上）與 Readhub；官方部落格與主流科技媒體 RSS 用來增加跨來源報導數。中文來源有量子位、Readhub（簡體）與 iThome、INSIDE、科技新報、科技報橘、T客邦、知勢（繁體）。2026-11-29 起不收 Reddit、Hugging Face 論文與熱門模型、GitHub Trending、IT之家，只留一般人看得懂的新聞 |
| 去重與聚類 | 網址去掉 utm 等追蹤參數和結尾斜線；標題相似度 > 0.85 視為同一事件，保留所有來源連結 |
| 評分（0–100） | 來源權重 30%、跨來源報導數 30%（最多計 5 個來源）、時效 20%（48 小時線性遞減）、社群熱度 20%（HN 分數、Readhub 報導家數，分類型取對數正規化） |
| 分類 | `pipeline/classify.py` 的關鍵字規則（中文關鍵字含繁簡），依民調中一般人最關心的 AI 話題分六類，依序比對：Rules & Safety（法規與詐騙）、Work & Jobs（工作）、New Models（新模型）、Everyday AI（生活應用）、Chips & Industry（晶片與產業）、Tools & Apps（AI 工具）；先比對標題，標題沒有符合再看描述，第一個符合的勝出。都沒符合的歸 Other，不顯示成分頁，只出現在頭條與「看全部」 |
| 頭條 | Headlines（今日頭條）：有社群熱度（HN、Readhub）、出自 Techmeme，或至少兩個來源報導的新聞，依報導數加熱度排序，同一網站最多 2 則；官方發布只在新聞不足時補位。從整輪所有新聞中挑 10 則，第 1 則在頁面上放大顯示 |
| 語言 | 介面中英對照（例：Work & Jobs · 工作）；新聞標題與描述維持各來源的原文，不翻譯 |
| 簡介 | 來源 RSS 自帶的描述，截到 200 字；沒有描述的項目只顯示標題 |
| 發布 | 寫入 `data/latest.json` 和 `data/archive/YYYY-MM-DD-HH.json`（UTC），由 workflow 提交並部署 |

任何一步失敗時，程式會在寫檔前結束並回傳錯誤，`latest.json` 和已發布的網站都維持上一版。少於 10 則時也不會發布。

## 與原始規格不同的地方

- **不使用 LLM**：不抓原文、不呼叫 Claude，沒有中文標題、中文摘要與「為什麼重要」；分類改用關鍵字規則，所以 `latest.json` 每則的欄位是 `id, title, summary, category, score, published_at, sources, primary_url`；另有 `highlights.Headlines`。
- **2026-11-29 改版**：首頁封面突出首則頭條，接續三則並列呈現，手機改為單欄。搜尋、主題與過去版本集中在上方導覽，過去版本沿用該期分類。新期別採六類大眾主題，移除 Dark Horses、Rising 與工程師向來源。
- **Reddit 沒有 upvotes**：Reddit JSON API 對未登入請求回 403，只能用 RSS，因此 Reddit 項目不計社群熱度。Reddit 也常對雲端主機限流，失敗時跳過。
- **移除的來源**：Meta AI、VentureBeat、數位時代沒有可用的格式，詳見 `sources_report.md`。
- **2026-11-14 調整**：Anthropic 暫停（sitemap 的 lastmod 會在網站重新部署時全部刷新，舊文章被當成新的）；拿掉 Microsoft Research、NVIDIA Developer 與 arXiv 四個分類，論文改用 Hugging Face Papers 前一天的榜單；Hugging Face 熱門模型排除 uncensored、merge、GGUF 這類改版；GitHub Trending 只收當日 100 星以上。

## 著作權與來源標示

- 每則新聞都列出所有報導來源的名稱與連結，標題連到原文。頁尾列出全部資料來源。
- 公開的 JSON 只有原標題、來源 RSS 自帶描述的前 200 字和連結，不抓、不存文章全文。

## 檔案

```
sources.yaml              來源清單（名稱、URL、類型、權重）
sources_report.md         來源測試結果與已移除的來源
pipeline/fetch.py         各類型來源的抓取
pipeline/rank.py          去重、聚類、評分
pipeline/classify.py      關鍵字分類規則
pipeline/build.py         串起整個流程並寫檔
scripts/run_local.py      本機跑一輪
scripts/check_sources.py  測試所有來源
tests/test_offline.py     離線自我檢查
index.html                前端（原生 JS，讀 data/latest.json）
.github/workflows/update.yml  排程、提交資料、部署 Pages
```
