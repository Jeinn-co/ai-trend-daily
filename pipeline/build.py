"""One full run: fetch → cluster → score → extract → summarise → write data/latest.json + archive.

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
from .rank import attach_text, cluster, score
from .summarize import CATEGORIES, summarize

log = logging.getLogger("pipeline")
TOP_N = 100
MIN_ITEMS = 10  # refuse to publish a nearly empty page


def to_public(c):
    return {
        "id": c["id"],
        "title_zh": c["title_zh"],
        "title_original": c["title_original"],
        "summary_zh": c["summary_zh"],
        "why_important": c["why_important"],
        "category": c["category"],
        "score": c["score"],
        "published_at": c["published"].isoformat(),
        "sources": c["sources"],
        "primary_url": c["primary_url"],
    }


def write_json(path, data):
    """Write atomically so a crash mid-write never leaves a broken file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def run(out_dir="data", sources_path="sources.yaml", skip_llm=False):
    start = time.monotonic()
    now = datetime.now(timezone.utc)
    sources = load_sources(sources_path)

    items, failed = fetch_all(sources, now)
    clusters = score(cluster(items), now)
    log.info("fetched %d items from %d/%d sources → %d clusters", len(items), len(sources) - len(failed), len(sources), len(clusters))
    top = attach_text(clusters[:TOP_N])
    if len(top) < MIN_ITEMS:
        raise RuntimeError(f"only {len(top)} stories selected; keeping the previous latest.json")

    if skip_llm:  # local smoke test without an API key; never publish this output
        for c in top:
            c.update(category=CATEGORIES[0], title_zh=c["title_original"][:30], summary_zh="（本機測試，未呼叫 LLM）", why_important="")
        llm = {"skipped": True}
    else:
        llm = summarize(top)

    public = [to_public(c) for c in top]
    data = {
        "updated_at": now.isoformat(timespec="seconds"),
        "top10": public[:10],
        "all": public,
        "categories": {cat: [p for p in public if p["category"] == cat][:10] for cat in CATEGORIES},
        # every source this site draws from, for the attribution list in the footer
        "source_list": [{"name": s["name"], "url": s["url"]} for s in sources],
        "stats": {
            "fetched": len(items),
            "after_dedup": len(clusters),
            "sources_ok": len(sources) - len(failed),
            "sources_failed": len(failed),
            "failed_sources": failed,
            "llm": llm,
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
    log.info("published %d stories in %.1fs (LLM: %s)", len(public), time.monotonic() - start, llm)
    return data


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="data")
    p.add_argument("--sources", default="sources.yaml")
    p.add_argument("--skip-llm", action="store_true", help="local smoke test without calling Claude")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        run(args.out, args.sources, args.skip_llm)
    except Exception:
        log.exception("run failed; previous latest.json left untouched")
        sys.exit(1)


if __name__ == "__main__":
    main()
