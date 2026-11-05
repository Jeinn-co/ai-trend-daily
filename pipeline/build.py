"""One full run: fetch → cluster → score → classify → write data/latest.json + archive.

Any failure raises before anything is written, so the previous latest.json stays published.
"""

import argparse
import json
import logging
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from .fetch import fetch_all, load_sources
from .classify import CATEGORIES, HIGHLIGHTS, classify, pick_highlights
from .rank import cluster, score

log = logging.getLogger("pipeline")
TOP_N = 100
MIN_ITEMS = 10  # refuse to publish a nearly empty page
SUMMARY_CHARS = 200  # the feed's own description, shortened; full articles are never copied


def to_public(c):
    return {
        "id": c["id"],
        "title": c["title_original"],
        "summary": clip(c["feed_summary"], SUMMARY_CHARS),
        "category": c["category"],
        "score": c["score"],
        "published_at": c["published"].isoformat(),
        "sources": c["sources"],
        "primary_url": c["primary_url"],
    }


def clip(s, n):
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def write_json(path, data):
    """Write atomically so a crash mid-write never leaves a broken file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def run(out_dir="data", sources_path="sources.yaml"):
    start = time.monotonic()
    now = datetime.now(timezone.utc)
    sources = load_sources(sources_path)

    items, failed = fetch_all(sources, now)
    clusters = score(cluster(items), now)
    log.info("fetched %d items from %d/%d sources → %d clusters", len(items), len(sources) - len(failed), len(sources), len(clusters))
    top = clusters[:TOP_N]
    if len(top) < MIN_ITEMS:
        raise RuntimeError(f"only {len(top)} stories selected; keeping the previous latest.json")
    for c in clusters:
        c["category"] = classify(c["title_original"], c["feed_summary"], c["groups"])
    highlights = pick_highlights(clusters)

    public = [to_public(c) for c in top]
    data = {
        "updated_at": now.isoformat(timespec="seconds"),
        "top10": public[:10],
        "all": public,
        # Headlines / Dark Horses / Rising are picked from every story of the run, not only the top 100
        "highlights": {h: [to_public(c) for c in highlights[h]] for h in HIGHLIGHTS},
        "categories": {cat: [p for p in public if p["category"] == cat][:10] for cat in CATEGORIES},
        # every source this site draws from, for the attribution list in the footer
        "source_list": [{"name": s["name"], "url": s["url"]} for s in sources],
        "stats": {
            "fetched": len(items),
            "after_dedup": len(clusters),
            "sources_ok": len(sources) - len(failed),
            "sources_failed": len(failed),
            "failed_sources": failed,
            "duration_s": round(time.monotonic() - start, 1),
        },
    }

    out = Path(out_dir)
    name = now.strftime("%Y-%m-%d-%H")
    write_json(out / "archive" / f"{name}.json", data)
    index_path = out / "archive" / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else []
    write_json(index_path, sorted(set(index) | {name}, reverse=True))
    write_json(out / "latest.json", data)
    log.info("published %d stories in %.1fs", len(public), time.monotonic() - start)
    return data


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="data")
    p.add_argument("--sources", default="sources.yaml")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        run(args.out, args.sources)
    except Exception:
        log.exception("run failed; previous latest.json left untouched")
        sys.exit(1)


if __name__ == "__main__":
    main()
