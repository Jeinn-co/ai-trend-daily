# 來源測試報告

最後測試：2026-11-05T07:19:55+00:00（`python scripts/check_sources.py` 產生）

## sources.yaml 內的來源

| 來源 | 類型 | URL | 結果 | 48 小時內項目數 |
|---|---|---|---|---|
| OpenAI | rss | https://openai.com/news/rss.xml | ✅ | 8 |
| Anthropic | sitemap | https://www.anthropic.com/sitemap.xml | ✅ | 0 |
| Google DeepMind | rss | https://deepmind.google/blog/rss.xml | ✅ | 1 |
| Microsoft Research | rss | https://www.microsoft.com/en-us/research/feed/ | ✅ | 1 |
| Hugging Face Blog | rss | https://huggingface.co/blog/feed.xml | ✅ | 3 |
| Mistral AI | rss | https://mistral.ai/rss.xml | ✅ | 0 |
| NVIDIA Blog | rss | https://blogs.nvidia.com/feed/ | ✅ | 1 |
| NVIDIA Developer | rss | https://developer.nvidia.com/blog/feed | ✅ | 3 |
| TechCrunch | rss | https://techcrunch.com/category/artificial-intelligence/feed/ | ✅ | 20 |
| The Verge | rss | https://www.theverge.com/rss/ai-artificial-intelligence/index.xml | ✅ | 10 |
| MIT Technology Review | rss | https://www.technologyreview.com/topic/artificial-intelligence/feed | ✅ | 3 |
| Ars Technica | rss | https://arstechnica.com/ai/feed/ | ✅ | 3 |
| Hacker News | hn | https://hn.algolia.com/api/v1/search_by_date | ✅ | 22 |
| r/MachineLearning | rss | https://www.reddit.com/r/MachineLearning/top/.rss?t=day | ✅ | 9 |
| r/LocalLLaMA | rss | https://www.reddit.com/r/LocalLLaMA/top/.rss?t=day | ❌ HTTPError: 429 Client Error: Too Many Requests for url: https://www.reddit.com/r/LocalLLaMA/top/.rss?t=day | 0 |
| arXiv cs.AI | rss | https://rss.arxiv.org/rss/cs.AI | ✅ | 25 |
| arXiv cs.CL | rss | https://rss.arxiv.org/rss/cs.CL | ✅ | 25 |
| arXiv cs.LG | rss | https://rss.arxiv.org/rss/cs.LG | ✅ | 25 |
| arXiv cs.CV | rss | https://rss.arxiv.org/rss/cs.CV | ✅ | 25 |
| GitHub Trending | github_trending | https://github.com/trending?since=daily | ✅ | 9 |
| Hugging Face Trending | hf_models | https://huggingface.co/api/models?sort=trendingScore&limit=10 | ✅ | 10 |
| iThome | rss | https://www.ithome.com.tw/rss.xml | ✅ | 1 |
| INSIDE | rss | https://www.inside.com.tw/feed/rss | ✅ | 5 |

## 測試失敗、已移除的來源

| 來源 | 測試的 URL | 原因 |
|---|---|---|
| Anthropic | https://www.anthropic.com/rss.xml、/news/rss.xml | 404，官網沒有 RSS；改用 sitemap.xml 的 /news/ 頁面 |
| Meta AI | https://ai.meta.com/blog/rss/、/blog/feed/ | 404；robots.txt 列出的 sitemap 回 403，沒有可用格式 |
| Mistral AI | https://mistral.ai/news/rss.xml | 404；改用 https://mistral.ai/rss.xml |
| VentureBeat | https://venturebeat.com/category/ai/feed/ | 連續回 429（限流），分類頁也 429 |
| 數位時代 | https://www.bnext.com.tw/rss、/categories/ai/rss | 404；sitemap 的 lastmod 全是 2012-03-19，無法判斷發布時間 |
| INSIDE AI 分類 | https://www.inside.com.tw/tag/ai/feed、/feed/tag/ai | 404；改用全站 feed/rss 加關鍵字過濾 |
| Reddit JSON API | https://www.reddit.com/r/<sub>/top.json | 403；改用 RSS，但 RSS 沒有 upvotes，Reddit 項目不計社群熱度 |

Reddit 與 VentureBeat 對雲端主機 IP 常限流；在 GitHub Actions 上失敗時只會記 log，不影響整體流程。
