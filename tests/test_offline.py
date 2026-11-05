"""Offline self-check (no network): python tests/test_offline.py"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import classify, rank  # noqa: E402

now = datetime.now(timezone.utc)


def it(source, title, url, hours=1, weight=3, heat=None):
    return {"source": source, "group": source, "weight": weight, "title": title, "url": url,
            "published": now - timedelta(hours=hours), "summary": "", "heat": heat, "extra_links": [], "undated": False}


assert rank.normalize_url("https://www.a.com/x/?utm_source=t&id=1") == rank.normalize_url("http://a.com/x?id=1")

clusters = rank.score(rank.cluster([
    it("TechCrunch", "OpenAI releases GPT-6 today", "https://techcrunch.com/gpt6?utm_medium=rss", weight=4),
    it("The Verge", "OpenAI releases GPT-6 today!", "https://theverge.com/gpt6", weight=4),
    it("arXiv", "A study of something else", "https://arxiv.org/abs/1", hours=47, weight=2),
]), now)
assert len(clusters) == 2, clusters
top = clusters[0]
assert len(top["sources"]) == 2 and top["score"] > clusters[1]["score"]
assert 0 <= clusters[1]["score"] <= 100


c = classify.classify
assert c("OpenAI to acquire Pierre Computer Company, Inc.") == "產業與投資"
assert c("Kimi K3.1 Pro model weights are out") == "開源專案"
assert c("Anything at all", source_groups={"arXiv"}) == "研究論文"
assert c("Nvidia unveils new data center GPU") == "晶片與硬體"
assert c("EU lawmakers agree on AI Act changes") == "政策與法規"
assert c("Google releases Gemini 4 Pro") == "模型發布"
assert c("輝達發表新晶片") == "晶片與硬體"
assert c("A quiet afternoon") == classify.OTHER
print("ok")
