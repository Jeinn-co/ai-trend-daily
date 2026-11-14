"""Keyword rules that put each story into one main category. First matching rule wins, so order matters:
narrow topics (policy and safety, agents and dev tools) come before broad ones (business, products).
Chinese keywords are listed in Traditional and Simplified form."""

import re
from urllib.parse import urlsplit

CATEGORIES = ["Models", "Agents & Dev Tools", "Products", "Open Source", "Research", "Policy & Safety", "Business", "Other"]
OTHER = "Other"  # no rule matched


def words(*patterns):
    return re.compile("|".join(patterns), re.IGNORECASE)


RULES = [
    ("Policy & Safety", words(
        # security incidents
        r"\bCVE-\d", r"\bvulnerab", r"\bsecurity (advisory|flaw|bug|patch|update)", r"\bexploit", r"\bzero[- ]day",
        r"\bbreach", r"\bmalware", r"\bransomware", r"\bprompt injection", r"\bjailbreak", r"\bsupply[- ]chain attack",
        r"\bbackdoor", r"\bphishing", r"\bleak(ed|s)?\b", r"\bpaths to root\b", r"\bhack(ed|ers?)\b",
        # regulation, law and AI safety
        r"\bregulat", r"\blegislat", r"\blawmakers?\b", r"\bAI Act\b", r"\bSB ?\d+\b", r"\bcongress", r"\bsenat(e|or)",
        r"\bwhite house\b", r"\bexecutive order\b", r"\bexport control", r"\bdiffusion rule\b", r"\bcopyright",
        r"\blawsuit", r"\bsue[sd]?\b", r"\bcourt\b", r"\bjudge\b", r"\bFTC\b", r"\bantitrust", r"\bban(s|ned)?\b",
        r"\bsafety\b", r"\bsafeguard", r"\balignment\b", r"\bred[- ]team", r"\bharms?\b", r"\bwellbeing\b",
        r"\bevaluat(ion|ors?)\b", r"\btransparency\b", r"\bdeepfake", r"\bmisinformation\b", r"\bprivacy\b",
        "漏洞", "資安", "网络安全", "網路安全", "攻擊", "攻击", "惡意", "恶意", "外洩", "泄露", "駭客", "黑客", "釣魚", "钓鱼",
        "後門", "后门", "勒索", "監管", "监管", "法規", "法规", "法案", "立法", "版權", "版权", "訴訟", "诉讼", "起訴", "起诉",
        "出口管制", "禁令", "隱私", "隐私", "深偽", "深度伪造", "AI ?安全", "對齊", "对齐")),
    ("Agents & Dev Tools", words(
        r"\bagent skills?\b", r"\bclaude (code )?skills?\b", r"SKILL\.md", r"[-/]skills?\b", r"\bskills? (marketplace|library|registry)\b",
        r"\bMCP\b", r"model context protocol", r"\bagents?\b", r"\bagentic\b", r"\bcomputer[- ]use\b", r"\bClaude Code\b",
        r"\bCodex\b", r"\bCursor\b", r"\bWindsurf\b", r"\bvibe[- ]coding\b", r"\bcoding (assistant|tool|model)s?\b",
        r"\bautonomous\b", r"\bmulti-agent\b", r"\bIDE\b", r"\bSDK\b", r"\bCLI\b",
        "技能包", "代理", "智能體", "智能体", "智慧代理", "編程", "编程", "程式設計", "寫程式", "写代码")),
    ("Open Source", words(r"\bopen[- ]source", r"\bopen[- ]weights?\b", r"\bweights are out\b", "開源", "开源")),
    ("Models", words(
        r"\b(GPT|Claude|Gemini|Llama|Qwen|DeepSeek|Mistral|Kimi|Grok|Phi|Gemma|Nemotron|Fable|Opus|Sonnet|Haiku|GLM|MiniMax)[- ]?\d",
        r"\bnew (AI )?model\b", r"\bmodel (release|launch)", r"\b(releases?|launch(es)?|unveils?|introduc(es|ing))\b.*\bmodel\b",
        r"\bbenchmark", r"\bleaderboard\b", r"\bLLMs?\b",
        "新模型", "大模型", "模型.*(發布|发布|推出|釋出|上线|上線|開放|开放)", "(發布|发布|推出|釋出|开放|開放).*模型", "跑分", "榜單", "榜单")),
    ("Research", words(
        r"\bpapers?\b", r"\bresearch(ers)?\b", r"\bstudy\b", r"\barxiv\b", r"\bprovable\b", r"\btheorems?\b",
        r"\bmath(s|ematic)", r"\bbreakthrough", r"\bfirst[- ]ever\b", r"\bworld'?s first\b", r"\bnovel\b", r"\brobot",
        r"\bhumanoid", r"\bworld models?\b", r"\bquantum\b", r"\binvent", r"\bscien(ce|tific)", r"\bdiscover",
        "論文", "论文", "研究", "突破", "首創", "首创", "全球首", "創新", "创新", "機器人", "机器人", "具身", "量子", "科學", "科学",
        "數學", "数学", "定理")),
    ("Business", words(
        r"\braise[sd]?\b", r"\bfunding\b", r"\bseries [A-F]\b", r"\$\d[\d.,]*\s?(m|b|bn|million|billion|trillion)\b",
        r"\bvaluation", r"\bIPO\b", r"\bacqui(re|res|red|sition)", r"\bmerger", r"\bdeal\b", r"\binvest", r"\brevenue",
        r"\bearnings\b", r"\bprofit", r"\blayoffs?\b", r"\bCEO\b", r"\bsteps? down\b", r"\bresign", r"\bhires?\b",
        r"\bchips?\b", r"\bGPUs?\b", r"\bdata ?cent(er|re)s?\b", r"\bstocks?\b", r"\bshares\b", r"\bmarket cap\b",
        r"\bsubscri(be|ption)", r"\bpric(e|es|ing)\b", r"\bpartner(s|ship)?\b",
        "融資", "融资", "估值", "收購", "收购", "併購", "并购", "投資", "投资", "營收", "营收", "財報", "财报", "裁員", "裁员",
        "辭職", "辞职", "換帥", "换帅", "執行長", "首席执行官", "晶片", "芯片", "算力", "數據中心", "数据中心", "資料中心",
        "市值", "上市", "股價", "股价", "訂閱", "订阅", "合作")),
    ("Products", words(
        r"\blaunch(es|ed)?\b", r"\breleases?\b", r"\brolls? out\b", r"\bapps?\b", r"\bfeatures?\b",
        r"\btools?\b", r"\bAPI\b", r"\bupdate", r"\bbrowser\b", r"\bhospital",
        r"\bhealthcare\b", r"\bdoctors?\b", r"\beducation", r"\bschools?\b", r"\bfactor(y|ies)\b",
        r"\buses AI\b", r"\busing AI\b", r"\bcustomers?\b", r"\benterprise", r"\bchatbot", r"\bassistant",
        "推出", "發布", "发布", "功能", "工具", "上線", "上线", "更新", "應用", "应用", "導入", "导入", "醫療", "医疗",
        "教育", "製造", "制造", "客服", "助手", "手機", "手机", "眼鏡", "眼镜")),
]

# papers count as Research; the trending lists fall back to Open Source when no narrower rule matches
FIRST_BY_SOURCE = {"arXiv": "Research", "Hugging Face Papers": "Research"}
FALLBACK_BY_SOURCE = {"GitHub Trending": "Open Source", "Hugging Face Trending": "Open Source"}
BROAD = {"Business", "Products"}  # too generic to label a trending repo or model


def classify(title, summary="", source_groups=()):
    for group in source_groups:
        if group in FIRST_BY_SOURCE:
            return FIRST_BY_SOURCE[group]
    # the title decides first; the feed description only helps when the title matches nothing
    for text in (title, f"{title} {summary[:300]}"):
        for category, pattern in RULES:
            if pattern.search(text):
                if category in BROAD and any(g in FALLBACK_BY_SOURCE for g in source_groups):
                    break  # a trending repo/model that only matched a broad bucket is still an open-source project
                return category
    for group in source_groups:
        if group in FALLBACK_BY_SOURCE:
            return FALLBACK_BY_SOURCE[group]
    return OTHER


# --- highlight tabs: Headlines / Dark Horses / Rising --------------------------------------------------------------

HIGHLIGHTS = ["Headlines", "Dark Horses", "Rising"]
TRENDING = {"GitHub Trending", "Hugging Face Trending"}
PAPERS = {"Hugging Face Papers"}
PER_SITE = 2  # Headlines never fill up with one site's posts
# big labs and big tech: their news is never a "dark horse" or an up-and-coming project
BIG = words(r"\b(openai|chatgpt|anthropic|claude|google|gemini|deepmind|meta|llama|microsoft|copilot|nvidia|apple|siri|"
            r"amazon|aws|xai|grok|mistral|deepseek|qwen|alibaba|moonshot|kimi|ibm|samsung|tesla|musk|altman|"
            r"bytedance|tencent|baidu|huawei|intel|amd|qualcomm|tsmc|meta-llama|facebook)\b")


def is_big(c):
    return bool(BIG.search(f"{c['title_original']} {c['primary_url']}"))


def pick_highlights(clusters, n=10):
    """Clusters must already be scored (sorted by score) and carry heat_norm."""
    # 必知大新聞: popular stories, i.e. community heat (HN points, Readhub outlet count), a curated headline source
    # (weight 5: Techmeme) or at least two independent sources; an official post alone no longer qualifies.
    # Hottest first; trending repos and papers have their own tabs
    news = [c for c in clusters if not c["groups"] <= TRENDING | PAPERS]
    hot = sorted((c for c in news if c["heat_norm"] > 0 or c["weight"] == 5 or len(c["groups"]) >= 2),
                 key=lambda c: (min(len(c["groups"]), 5) / 5 + c["heat_norm"], c["score"]), reverse=True)
    focus, per = [], {}
    for c in hot + [c for c in news if c not in hot]:  # top up by score if the day is quiet
        site = urlsplit(c["primary_url"]).netloc.lower().removeprefix("www.")
        if per.get(site, 0) < PER_SITE:
            per[site] = per.get(site, 0) + 1
            focus.append(c)
    # 受歡迎的黑馬: hot community discussion (HN) about someone other than the big players
    dark = sorted((c for c in clusters if c["heat_norm"] > 0 and not is_big(c) and not c["groups"] & (TRENDING | PAPERS)
                   and not c["title_original"].startswith("Show HN")), key=lambda c: c["heat_norm"], reverse=True)
    # 最有潛力: up-and-coming open-source projects and models (trending lists, Show HN) from outside the big players
    rising = sorted((c for c in clusters if (c["groups"] & TRENDING or c["title_original"].startswith("Show HN"))
                     and not is_big(c)), key=lambda c: c["heat_norm"], reverse=True)
    return {"Headlines": focus[:n], "Dark Horses": dark[:n], "Rising": rising[:n]}
