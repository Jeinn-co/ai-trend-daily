"""Offline self-check (no network, no API key): python tests/test_offline.py"""

import os
import re
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import rank, summarize  # noqa: E402

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


class Usage:
    input_tokens, output_tokens = 1000, 500


class Response:
    stop_reason, _request_id, usage = "end_turn", "test", Usage()

    def __init__(self, ids):
        self.parsed_output = summarize.Batch(results=[
            summarize.Result(id=i, category="研究論文", title_zh="標" * 40, summary_zh="模型寫的摘要", why_important="重要")
            for i in ids])


class FakeClient:
    class messages:  # noqa: N801 - mirrors client.messages
        @staticmethod
        def parse(**kw):
            return Response(re.findall(r'<item id="([^"]+)"', kw["messages"][0]["content"]))


summarize.anthropic.Anthropic = lambda **kw: FakeClient()
items = [{"id": f"a{i}", "title_original": "t", "text": "原文" if i % 2 else ""} for i in range(23)]
stats = summarize.summarize(items)
assert stats["calls"] == 3
assert items[0]["summary_zh"] == summarize.NO_TEXT and items[0]["why_important"] == ""  # no text → no invented summary
assert items[1]["summary_zh"] == "模型寫的摘要" and len(items[1]["title_zh"]) == 30
print("ok")
