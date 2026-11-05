"""URL normalisation, clustering of duplicate stories, scoring, and article text extraction."""

import hashlib
import logging
import math
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
import trafilatura
from rapidfuzz import fuzz

from .fetch import UA, WINDOW

log = logging.getLogger(__name__)
TITLE_SIMILARITY = 85  # rapidfuzz ratio, 0-100 (= 0.85)
TRACKING = re.compile(r"^(utm_|fbclid$|gclid$|mc_|ref$|ref_src$|cmpid$)")
TEXT_CHARS = 3000


def normalize_url(url):
    p = urlsplit(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(p.query) if not TRACKING.match(k)])
    host = p.netloc.lower().removeprefix("www.")
    return urlunsplit(("https", host, p.path.rstrip("/") or "/", query, ""))


def normalize_title(title):
    return re.sub(r"\s+", " ", title.lower()).strip()


def cluster(items):
    """Merge items with the same normalised URL or a title similarity above 0.85 (union-find)."""
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        parent[find(a)] = find(b)

    by_url = {}
    for i, it in enumerate(items):
        it["norm_url"] = normalize_url(it["url"])
        if it["norm_url"] in by_url:
            union(i, by_url[it["norm_url"]])
        by_url.setdefault(it["norm_url"], i)

    titles = [normalize_title(it["title"]) for it in items]
    # a few hundred titles per run, so the plain O(n²) loop takes well under a second
    for a in range(len(titles)):
        for b in range(a + 1, len(titles)):
            if fuzz.ratio(titles[a], titles[b], score_cutoff=TITLE_SIMILARITY):
                union(a, b)

    groups = {}
    for i, it in enumerate(items):
        groups.setdefault(find(i), []).append(it)
    return [make_cluster(members) for members in groups.values()]


def make_cluster(members):
    # the primary item is the one from the most trusted source, then the earliest
    members.sort(key=lambda i: (-i["weight"], i["published"]))
    primary = members[0]
    sources, seen = [], set()
    for m in members:
        for link in [{"name": m["source"], "url": m["url"]}, *m["extra_links"]]:
            key = normalize_url(link["url"])
            if key not in seen:
                seen.add(key)
                sources.append(link)
    return {
        "id": hashlib.sha1(primary["norm_url"].encode()).hexdigest()[:12],
        "title_original": primary["title"],
        "primary_url": primary["url"],
        "published": min(m["published"] for m in members),
        "sources": sources,
        "groups": {m["group"] for m in members},
        "weight": max(m["weight"] for m in members),
        "undated": all(m["undated"] for m in members),
        "heat": [m["heat"] for m in members if m["heat"]],
        "feed_summary": max((m["summary"] for m in members), key=len),
    }


def score(clusters, now):
    """0-100: source weight 30%, cross-source coverage 30%, recency 20%, community heat 20%."""
    # heat is normalised per kind (HN points, GitHub stars today, HF trending score) on a log scale
    top = {}
    for c in clusters:
        for kind, v in c["heat"]:
            top[kind] = max(top.get(kind, 0), v)
    window_h = WINDOW.total_seconds() / 3600
    for c in clusters:
        weight = c["weight"] / 5
        coverage = min(len(c["groups"]), 5) / 5
        age_h = (now - c["published"]).total_seconds() / 3600
        # trending lists carry no publish date, so they get a neutral recency instead of a perfect one
        recency = 0.5 if c["undated"] else max(0.0, 1 - age_h / window_h)
        heat = max((math.log1p(v) / math.log1p(top[k]) for k, v in c["heat"] if top.get(k)), default=0.0)
        c["score"] = round(100 * (0.3 * weight + 0.3 * coverage + 0.2 * recency + 0.2 * heat), 1)
    clusters.sort(key=lambda c: c["score"], reverse=True)
    return clusters


def extract_text(url):
    try:
        r = requests.get(url, headers=UA, timeout=20)
        r.raise_for_status()
        return (trafilatura.extract(r.text, include_comments=False, include_tables=False) or "")[:TEXT_CHARS]
    except Exception as e:  # noqa: BLE001 - a missing article falls back to the feed summary
        log.warning("text extraction failed: %s: %s", url, e)
        return ""


def attach_text(clusters):
    """Article text is kept in memory for the summariser only; it is never written to the published JSON."""
    with ThreadPoolExecutor(16) as ex:
        texts = list(ex.map(lambda c: extract_text(c["primary_url"]), clusters))
    for c, text in zip(clusters, texts):
        # fall back to the feed's own description (e.g. arXiv abstracts) when the page has no extractable text
        c["text"] = max(text, c["feed_summary"], key=len)[:TEXT_CHARS]
    return clusters
