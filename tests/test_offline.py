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
assert c("Kimi K3.1 Pro model weights are out") == "Open Source"
assert c("Anything at all, even agents", source_groups={"arXiv"}) == "Research"
assert c("Critical CVE-2026-1234 in popular AI library") == "Policy & Safety"
assert c("EU lawmakers agree on AI Act changes") == "Policy & Safety"
assert c("GitHub launches an MCP server registry") == "Agents & Dev Tools"
assert c("anthropics/skills: public repository for Agent Skills", source_groups={"GitHub Trending"}) == "Agents & Dev Tools"
assert c("vercel-labs/agent-desktop: Computer use CLI for AI agents", source_groups={"GitHub Trending"}) == "Agents & Dev Tools"
assert c("someone/fast-tool: a fast tool", source_groups={"GitHub Trending"}) == "Open Source"
assert c("Google releases Gemini 4 Pro") == "Models"
assert c("阿里发布新一代大模型") == "Models"
assert c("AI startup raises $40M Series B") == "Business"
assert c("黄仁勋辞职，英伟达33年首换帅") == "Business"
assert c("Hospital rolls out AI triage assistant") == "Products"
assert c("A quiet afternoon") == classify.OTHER

base = dict(heat=[], undated=False, feed_summary="", sources=[], published=now)
cl = [
    dict(base, primary_url="https://openai.com/a", title_original="OpenAI ships GPT-6", weight=4, groups={"OpenAI"}, heat_norm=0.0, score=90),
    dict(base, primary_url="https://tiny.dev/a", title_original="Tiny startup's AI tool hits #1", weight=4, groups={"Hacker News"}, heat_norm=0.9, score=60),
    dict(base, primary_url="https://github.com/someone/rising-repo", title_original="someone/rising-repo", weight=3, groups={"GitHub Trending"}, heat_norm=0.8, score=55),
    dict(base, primary_url="https://nvidia.com/a", title_original="Nvidia news on HN", weight=4, groups={"Hacker News"}, heat_norm=1.0, score=58),
    *[dict(base, primary_url=f"https://anthropic.com/news/{i}", title_original=f"Old Anthropic post {i}", weight=4,
           groups={"Anthropic"}, heat_norm=0.0, score=80) for i in range(3)],
]
h = classify.pick_highlights(cl)
heads = [c["title_original"] for c in h["Headlines"]]
assert heads[:2] == ["Nvidia news on HN", "Tiny startup's AI tool hits #1"], heads  # popular first, official posts only top up
assert "someone/rising-repo" not in heads
assert sum(t.startswith("Old Anthropic") for t in heads) == 2, heads  # at most two per site
assert [c["title_original"] for c in h["Dark Horses"]] == ["Tiny startup's AI tool hits #1"]  # big names excluded
assert [c["title_original"] for c in h["Rising"]] == ["someone/rising-repo"]
print("ok")
