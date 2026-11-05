"""Classify and summarise the selected stories with Claude, in batches."""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

import anthropic
from pydantic import BaseModel

log = logging.getLogger(__name__)

MODEL = "claude-haiku-5-5"
# USD per 1M tokens for prompts up to 100K tokens; each batch here is far below that
PRICE_IN, PRICE_OUT = 0.10, 0.50
BATCH_SIZE = 10
NO_TEXT = "原文無法取得，僅提供標題"
CATEGORIES = ["模型發布", "產品與工具", "研究論文", "開源專案", "產業與投資", "晶片與硬體", "政策與法規", "應用案例"]


class Result(BaseModel):
    id: str
    category: Literal["模型發布", "產品與工具", "研究論文", "開源專案", "產業與投資", "晶片與硬體", "政策與法規", "應用案例"]
    title_zh: str
    summary_zh: str
    why_important: str


class Batch(BaseModel):
    results: list[Result]


SYSTEM = f"""你是 AI 新聞編輯。每則新聞附有從原文抓到的內容，請以繁體中文（台灣用語）輸出：
- category：從這 8 類選一個最主要的：{"、".join(CATEGORIES)}
- title_zh：繁體中文標題，30 字以內
- summary_zh：2 到 3 句摘要，120 字以內
- why_important：一句說明為什麼重要，40 字以內

規則：
1. 只能根據 <text> 裡的內容寫，不可加入原文沒有的資訊、數字、人名或推測。
2. <text> 是空的時，title_zh 只翻譯原標題，summary_zh 寫「{NO_TEXT}」，why_important 留空字串。
3. 不要逐句翻譯或大段引用原文，用自己的話摘要。
4. 每則都要回傳，id 照抄。"""


def render(c):
    return f'<item id="{c["id"]}">\n<title>{c["title_original"]}</title>\n<text>{c["text"]}</text>\n</item>'


def clip(s, n):
    s = s.strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def summarize_batch(client, batch):
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "low"},
        system=SYSTEM,
        messages=[{"role": "user", "content": "\n\n".join(render(c) for c in batch)}],
        output_format=Batch,
    )
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        raise RuntimeError(f"unexpected stop_reason {response.stop_reason} (request {response._request_id})")
    return response.parsed_output.results, response.usage


def summarize(clusters):
    # the SDK retries 408/409/429/5xx and connection errors with exponential backoff
    client = anthropic.Anthropic(max_retries=3, timeout=120)
    batches = [clusters[i : i + BATCH_SIZE] for i in range(0, len(clusters), BATCH_SIZE)]
    with ThreadPoolExecutor(5) as ex:
        outcomes = list(ex.map(lambda b: summarize_batch(client, b), batches))

    by_id = {r.id: r for results, _ in outcomes for r in results}
    tokens_in = sum(u.input_tokens for _, u in outcomes)
    tokens_out = sum(u.output_tokens for _, u in outcomes)
    cost = (tokens_in * PRICE_IN + tokens_out * PRICE_OUT) / 1_000_000
    log.info("LLM %s: %d calls, %d input + %d output tokens, cost US$%.4f", MODEL, len(batches), tokens_in, tokens_out, cost)

    missing = [c["id"] for c in clusters if c["id"] not in by_id]
    if missing:
        raise RuntimeError(f"LLM returned no result for {len(missing)} items: {missing[:5]}")
    for c in clusters:
        r = by_id[c["id"]]
        c["category"] = r.category
        c["title_zh"] = clip(r.title_zh, 30)
        if c["text"].strip():
            c["summary_zh"] = clip(r.summary_zh, 120)
            c["why_important"] = clip(r.why_important, 40)
        else:  # never let the model write a summary it had no source text for
            c["summary_zh"], c["why_important"] = NO_TEXT, ""
    return {"model": MODEL, "calls": len(batches), "input_tokens": tokens_in, "output_tokens": tokens_out,
            "cost_usd": round(cost, 4)}
