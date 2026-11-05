"""Fetch items from every source in sources.yaml. One failing source never stops the run."""

import calendar
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)
UA = {"User-Agent": "Mozilla/5.0 (compatible; ai-trend-daily/1.0; +https://github.com/Jeinn-co/ai-trend-daily)"}
TIMEOUT = 20
WINDOW = timedelta(hours=48)

AI_WORDS = re.compile(
    r"(?<![A-Za-z])(AI|AGI|LLMs?|GPT[-\w.]*|RAG)(?![A-Za-z])"
    r"|artificial intelligence|machine learning|deep learning|neural|transformer|diffusion|"
    r"language model|openai|anthropic|claude|gemini|deepmind|llama|mistral|qwen|deepseek|kimi|"
    r"copilot|chatbot|agentic|inference|embedding|fine-tun|multimodal|"
    r"人工智慧|生成式|大模型|語言模型|機器學習|深度學習|神經網路|智慧代理|聊天機器人|算力",
    re.IGNORECASE,
)


def load_sources(path="sources.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["sources"]


def get(url):
    r = requests.get(url, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r


def is_ai(*texts):
    return bool(AI_WORDS.search(" ".join(t or "" for t in texts)))


def strip_html(html):
    return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)


def item(src, title, url, published, summary="", heat=None, extra_links=(), undated=False):
    return {
        "source": src["name"],
        "group": src.get("group", src["name"]),
        "weight": src["weight"],
        "title": (title or "").strip(),
        "url": url,
        "published": published,
        "summary": summary,
        "heat": heat,  # (kind, value) or None
        "extra_links": list(extra_links),  # [{name, url}] e.g. the HN discussion page
        "undated": undated,  # trending lists have no publish date; published = this run
    }


def fetch_rss(src, now):
    feed = feedparser.parse(get(src["url"]).content)
    if not feed.entries:
        raise ValueError("feed has no entries")
    out = []
    for e in feed.entries:
        t = e.get("published_parsed") or e.get("updated_parsed")
        if not t:
            continue
        published = datetime.fromtimestamp(calendar.timegm(t), timezone.utc)
        # arXiv lists replacements too; keep only new submissions
        if e.get("arxiv_announce_type", "new") not in ("new", "cross"):
            continue
        summary = strip_html(e.get("summary", ""))
        if src.get("ai_filter") and not is_ai(e.get("title"), summary):
            continue
        out.append(item(src, e.get("title"), e.get("link"), published, summary))
    return out


def fetch_sitemap(src, now):
    xml = get(src["url"]).text
    out = []
    for loc, lastmod in re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", xml):
        if not loc.startswith(src["prefix"]) or loc.rstrip("/") == src["prefix"].rstrip("/"):
            continue
        published = datetime.fromisoformat(lastmod.replace("Z", "+00:00"))
        if now - published > WINDOW:
            continue
        # sitemaps carry no title; read it from the page itself
        soup = BeautifulSoup(get(loc).text, "html.parser")
        og = soup.find("meta", property="og:title")
        title = og["content"] if og and og.get("content") else (soup.title.string if soup.title else loc)
        out.append(item(src, title, loc, published))
    return out


def fetch_hn(src, now):
    since = int((now - WINDOW).timestamp())
    params = {
        "tags": "story",
        "numericFilters": f"points>{src.get('min_points', 100)},created_at_i>{since}",
        "hitsPerPage": 200,
    }
    hits = requests.get(src["url"], params=params, headers=UA, timeout=TIMEOUT).json()["hits"]
    out = []
    for h in hits:
        if not is_ai(h.get("title")):
            continue
        discussion = f"https://news.ycombinator.com/item?id={h['objectID']}"
        published = datetime.fromtimestamp(h["created_at_i"], timezone.utc)
        out.append(item(src, h["title"], h.get("url") or discussion, published, heat=("hn", h.get("points", 0)),
                        extra_links=[{"name": "Hacker News 討論", "url": discussion}]))
    return out


def fetch_github_trending(src, now):
    soup = BeautifulSoup(get(src["url"]).text, "html.parser")
    rows = soup.select("article.Box-row")
    if not rows:
        raise ValueError("no repositories found on the trending page")
    out = []
    for row in rows:
        a = row.select_one("h2 a")
        repo = re.sub(r"\s+", "", a.get_text())
        desc_el = row.select_one("p")
        desc = desc_el.get_text(" ", strip=True) if desc_el else ""
        if not is_ai(repo, desc):
            continue
        m = re.search(r"([\d,]+) stars today", row.get_text())
        stars = int(m.group(1).replace(",", "")) if m else 0
        out.append(item(src, f"{repo}: {desc}" if desc else repo, f"https://github.com/{repo}", now, desc,
                        heat=("github", stars), undated=True))
    return out


def fetch_hf_models(src, now):
    models = get(src["url"]).json()
    return [item(src, m["id"], f"https://huggingface.co/{m['id']}", now, heat=("hf", m.get("trendingScore", 0)), undated=True)
            for m in models]


FETCHERS = {
    "rss": fetch_rss,
    "sitemap": fetch_sitemap,
    "hn": fetch_hn,
    "github_trending": fetch_github_trending,
    "hf_models": fetch_hf_models,
}


def fetch_one(src, now):
    start = time.monotonic()
    try:
        items = [i for i in FETCHERS[src["type"]](src, now) if i["url"] and i["title"] and now - i["published"] <= WINDOW]
        items.sort(key=lambda i: i["published"], reverse=True)
        items = items[: src.get("limit", 200)]
        log.info("source ok: %s (%d items, %.1fs)", src["name"], len(items), time.monotonic() - start)
        return src["name"], items, None
    except Exception as e:  # noqa: BLE001 - any source failure is logged and skipped
        log.error("source failed: %s: %s: %s", src["name"], type(e).__name__, e)
        return src["name"], [], f"{type(e).__name__}: {e}"


def fetch_all(sources, now=None):
    now = now or datetime.now(timezone.utc)
    with ThreadPoolExecutor(12) as ex:
        results = list(ex.map(lambda s: fetch_one(s, now), sources))
    items = [i for _, found, _ in results for i in found]
    failed = {name: err for name, _, err in results if err}
    return items, failed
