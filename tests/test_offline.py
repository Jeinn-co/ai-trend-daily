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
    it("量子位", "A study of something else", "https://qbitai.com/1", hours=47, weight=2),
]), now)
assert len(clusters) == 2, clusters
top = clusters[0]
assert len(top["sources"]) == 2 and top["score"] > clusters[1]["score"]
assert 0 <= clusters[1]["score"] <= 100


c = classify.classify
assert c("OpenAI adds memory to ChatGPT for free users") == "Tools & Apps"
assert c("Google releases Gemini 4 Pro") == "New Models"
assert c("阿里发布新一代大模型") == "New Models"
assert c("Salesforce says AI let it cut 4,000 support jobs") == "Work & Jobs"
assert c("AI 自動化工作流上線") == "Tools & Apps"  # 工作流 is a tool, not a job story
assert c("Scammers use deepfake voices to empty bank accounts") == "Rules & Safety"
assert c("EU lawmakers agree on AI Act changes") == "Rules & Safety"
assert c("台積電 AI 晶片營收創新高") == "Chips & Industry"
assert c("AI startup raises $40M Series B") == "Chips & Industry"
assert c("Hospital rolls out AI triage assistant") == "Everyday AI"
assert c("A quiet afternoon") == classify.OTHER

base = dict(heat=[], undated=False, feed_summary="", sources=[], published=now)
cl = [
    dict(base, primary_url="https://openai.com/a", title_original="OpenAI ships GPT-6", weight=4, groups={"OpenAI"}, heat_norm=0.0, score=90),
    dict(base, primary_url="https://tiny.dev/a", title_original="Tiny startup's AI tool hits #1", weight=4, groups={"Hacker News"}, heat_norm=0.9, score=60),
    dict(base, primary_url="https://nvidia.com/a", title_original="Nvidia news on HN", weight=4, groups={"Hacker News"}, heat_norm=1.0, score=58),
    *[dict(base, primary_url=f"https://anthropic.com/news/{i}", title_original=f"Old Anthropic post {i}", weight=4,
           groups={"Anthropic"}, heat_norm=0.0, score=80) for i in range(3)],
]
heads = [c["title_original"] for c in classify.pick_headlines(cl)]
assert heads[:2] == ["Nvidia news on HN", "Tiny startup's AI tool hits #1"], heads  # popular first, official posts only top up
assert sum(t.startswith("Old Anthropic") for t in heads) == 2, heads  # at most two per site
print("ok")
