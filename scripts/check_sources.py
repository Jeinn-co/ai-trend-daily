"""Test every source in sources.yaml and write sources_report.md: python scripts/check_sources.py"""

import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from pipeline.fetch import fetch_one, load_sources  # noqa: E402

# Tested on 2026-11-05 and removed from sources.yaml. Re-test before adding any of them back.
REMOVED = [
    ("Anthropic", "https://www.anthropic.com/rss.xml、/news/rss.xml", "404，官網沒有 RSS；改用 sitemap.xml 的 /news/ 頁面"),
    ("Meta AI", "https://ai.meta.com/blog/rss/、/blog/feed/", "404；robots.txt 列出的 sitemap 回 403，沒有可用格式"),
    ("Mistral AI", "https://mistral.ai/news/rss.xml", "404；改用 https://mistral.ai/rss.xml"),
    ("VentureBeat", "https://venturebeat.com/category/ai/feed/", "連續回 429（限流），分類頁也 429"),
    ("數位時代", "https://www.bnext.com.tw/rss、/categories/ai/rss", "404；sitemap 的 lastmod 全是 2012-03-19，無法判斷發布時間"),
    ("INSIDE AI 分類", "https://www.inside.com.tw/tag/ai/feed、/feed/tag/ai", "404；改用全站 feed/rss 加關鍵字過濾"),
    ("Reddit JSON API", "https://www.reddit.com/r/<sub>/top.json", "403；改用 RSS，但 RSS 沒有 upvotes，Reddit 項目不計社群熱度"),
]


def main():
    now = datetime.now(timezone.utc)
    rows = []
    for src in load_sources():
        name, items, err = fetch_one(src, now)
        rows.append(f"| {name} | {src['type']} | {src['url']} | {'❌ ' + err if err else '✅'} | {len(items)} |")
        print(rows[-1])
    removed = [f"| {n} | {u} | {why} |" for n, u, why in REMOVED]
    report = "\n".join([
        "# 來源測試報告",
        "",
        f"最後測試：{now.isoformat(timespec='seconds')}（`python scripts/check_sources.py` 產生）",
        "",
        "## sources.yaml 內的來源",
        "",
        "| 來源 | 類型 | URL | 結果 | 48 小時內項目數 |",
        "|---|---|---|---|---|",
        *rows,
        "",
        "## 測試失敗、已移除的來源",
        "",
        "| 來源 | 測試的 URL | 原因 |",
        "|---|---|---|",
        *removed,
        "",
        "Reddit 與 VentureBeat 對雲端主機 IP 常限流；在 GitHub Actions 上失敗時只會記 log，不影響整體流程。",
        "",
    ])
    with open("sources_report.md", "w", encoding="utf-8") as f:
        f.write(report)


if __name__ == "__main__":
    main()
