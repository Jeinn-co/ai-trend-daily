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
assert c("Kimi K3.1 Pro model weights are out") == "開源"
assert c("Anything at all, even agents", source_groups={"arXiv"}) == "創新"
assert c("Critical CVE-2026-1234 in popular AI library") == "資安公佈"
assert c("GitHub launches an MCP server registry") == "MCP"
assert c("anthropics/skills: public repository for Agent Skills", source_groups={"GitHub Trending"}) == "技能"
assert c("vercel-labs/agent-desktop: Computer use CLI for AI agents", source_groups={"GitHub Trending"}) == "AI Agent"
assert c("someone/fast-tool: a CLI tool", source_groups={"GitHub Trending"}) == "開源"
assert c("Google releases Gemini 4 Pro") == "創新"
assert c("Hospital rolls out AI triage assistant") == "AI 應用"
assert c("EU lawmakers agree on AI Act changes") == classify.OTHER

base = dict(primary_url="https://x.com/a", heat=[], undated=False, feed_summary="", sources=[], published=now)
cl = [
    dict(base, title_original="OpenAI ships GPT-6", weight=5, groups={"OpenAI"}, heat_norm=0.0, score=90),
    dict(base, title_original="Tiny startup's AI tool hits #1", weight=3, groups={"Hacker News"}, heat_norm=0.9, score=60),
    dict(base, title_original="someone/rising-repo", weight=3, groups={"GitHub Trending"}, heat_norm=0.8, score=55),
    dict(base, title_original="Nvidia news on HN", weight=3, groups={"Hacker News"}, heat_norm=1.0, score=58),
]
h = classify.pick_highlights(cl)
assert h["焦點"][0]["title_original"] == "OpenAI ships GPT-6"
assert [c["title_original"] for c in h["黑馬"]] == ["Tiny startup's AI tool hits #1"]  # big names excluded
assert [c["title_original"] for c in h["潛力"]] == ["someone/rising-repo"]
print("ok")
