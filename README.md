# AI 趨勢日報

每 6 小時自動抓取全球 AI 新聞，經過去重、評分、分類後存成 JSON，發布成 GitHub Pages 靜態網站。每則新聞都標出來源並附原文連結。不使用 AI、不需要任何 API 金鑰。

## 第一次設定

1. 啟用 Pages：Settings → Pages → Build and deployment → Source 選 **GitHub Actions**。免費方案的 organization 只有 public repo 能用 Pages。
2. 手動跑第一次：Actions → Update AI trend data → Run workflow。之後每天 00、06、12、18 點（UTC）自動執行。

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
| 抓取 | `sources.yaml` 列出的來源，只取 48 小時內的項目；單一來源失敗只記 log |
| 去重與聚類 | 網址去掉 utm 等追蹤參數和結尾斜線；標題相似度 > 0.85 視為同一事件，保留所有來源連結 |
| 評分（0–100） | 來源權重 30%、跨來源報導數 30%（最多計 5 個來源）、時效 20%（48 小時線性遞減）、社群熱度 20%（HN 分數、GitHub 當日星數、HF 熱度，分類型取對數正規化） |
| 分類 | `pipeline/classify.py` 的關鍵字規則，依序比對，第一個符合的類別勝出；arXiv 固定為研究論文，GitHub／HF 熱門榜固定為開源專案；都不符合歸「其他」（只出現在綜合排名） |
| 簡介 | 來源 RSS 自帶的描述，截到 200 字；沒有描述的項目只顯示標題 |
| 發布 | 寫入 `data/latest.json` 和 `data/archive/YYYY-MM-DD-HH.json`（UTC），由 workflow 提交並部署 |

任何一步失敗時，程式會在寫檔前結束並回傳錯誤，`latest.json` 和已發布的網站都維持上一版。少於 10 則時也不會發布。

## 與原始規格不同的地方

- **不使用 LLM**：不抓原文、不呼叫 Claude，沒有中文標題、中文摘要與「為什麼重要」；分類改用關鍵字規則，所以 `latest.json` 每則的欄位是 `id, title, summary, category, score, published_at, sources, primary_url`。
- **熱門榜沒有發布時間**：GitHub Trending 與 Hugging Face trending 沒有日期，時效分數固定給 0.5。
- **Reddit 沒有 upvotes**：Reddit JSON API 對未登入請求回 403，只能用 RSS，因此 Reddit 項目不計社群熱度。Reddit 也常對雲端主機限流，失敗時跳過。
- **移除的來源**：Meta AI、VentureBeat、數位時代沒有可用的格式，詳見 `sources_report.md`。

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
