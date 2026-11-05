"""Keyword rules that put each story into one main category. First matching rule wins, so order matters:
narrow topics (security, MCP, skills, agents) come before broad ones (applications)."""

import re

CATEGORIES = ["AI Agent", "AI 應用", "技能", "MCP", "開源", "創新", "資安公佈", "其它"]
OTHER = "其它"  # no rule matched (policy, business, chips and everything else)


def words(*patterns):
    return re.compile("|".join(patterns), re.IGNORECASE)


RULES = [
    ("資安公佈", words(r"\bCVE-\d", r"\bvulnerab", r"\bsecurity (advisory|flaw|bug|patch|update)", r"\bexploit", r"\bzero[- ]day",
                   r"\bbreach", r"\bmalware", r"\bransomware", r"\bprompt injection", r"\bjailbreak", r"\bsupply[- ]chain attack",
                   r"\bbackdoor", r"\bphishing", r"\bleak(ed|s)?\b", r"\bpaths to root\b", r"\bhack(ed|ers?)\b",
                   "漏洞", "資安", "攻擊", "惡意", "外洩", "駭客", "釣魚", "後門", "勒索")),
    ("技能", words(r"\bagent skills?\b", r"\bclaude (code )?skills?\b", r"SKILL\.md", r"[-/]skills?\b", r"\bskills? (marketplace|library|registry)\b",
                 "技能包", r"Agent Skill")),
    ("MCP", words(r"\bMCP\b", r"model context protocol")),
    ("AI Agent", words(r"\bagents?\b", r"\bagentic\b", r"\bcomputer[- ]use\b", r"\bClaude Code\b", r"\bCodex\b", r"\bCursor\b",
                       r"\bautonomous\b", r"\bmulti-agent\b", "代理", "智能體", "智慧代理")),
    ("開源", words(r"\bopen[- ]source", r"\bopen[- ]weights?\b", r"\bweights are out\b", "開源")),
    ("創新", words(r"\b(GPT|Claude|Gemini|Llama|Qwen|DeepSeek|Mistral|Kimi|Grok|Phi|Gemma|Nemotron)[- ]?\d",
                   r"\bnew (AI )?model\b", r"\bmodel (release|launch)", r"\b(releases?|launch(es)?|unveils?|introduc(es|ing))\b.*\bmodel\b",
                   "新模型", "模型.*(發布|推出|釋出)", "(發布|推出|釋出).*模型")),
    ("創新", words(r"\bbreakthrough", r"\bfirst[- ]ever\b", r"\bworld'?s first\b", r"\bnovel\b", r"\brobot", r"\bhumanoid",
                 r"\bworld models?\b", r"\bquantum\b", r"\binvent", r"\bscientific discover", r"\bAI for science\b",
                 "突破", "首創", "全球首", "創新", "機器人", "量子")),
    ("創新", words(r"\bpapers?\b", r"\bresearch(ers)?\b", r"\bstudy\b", r"\bbenchmark", r"\barxiv\b", r"\bprovable\b",
                   "論文", "研究")),
    ("AI 應用", words(r"\blaunch(es|ed)?\b", r"\breleases?\b", r"\brolls? out\b", r"\bapps?\b", r"\bfeatures?\b",
                    r"\btools?\b", r"\bAPI\b", r"\bupdate", r"\bbrowser\b", r"\bCLI\b", r"\bSDK\b", r"\bhospital",
                    r"\bhealthcare\b", r"\bdoctors?\b", r"\beducation", r"\bschools?\b", r"\bfactor(y|ies)\b",
                    r"\buses AI\b", r"\busing AI\b", r"\bcustomers?\b", r"\benterprise", r"\bchatbot", r"\bassistant",
                    "推出", "功能", "工具", "上線", "更新", "應用", "導入", "醫療", "教育", "製造", "客服")),
]

# arXiv papers count as 創新; the trending lists fall back to 開源 when no narrower rule matches
FIRST_BY_SOURCE = {"arXiv": "創新"}
FALLBACK_BY_SOURCE = {"GitHub Trending": "開源", "Hugging Face Trending": "開源"}


def classify(title, summary="", source_groups=()):
    for group in source_groups:
        if group in FIRST_BY_SOURCE:
            return FIRST_BY_SOURCE[group]
    # the title decides first; the feed description only helps when the title matches nothing
    for text in (title, f"{title} {summary[:300]}"):
        for category, pattern in RULES:
            if pattern.search(text):
                if category == "AI 應用" and any(g in FALLBACK_BY_SOURCE for g in source_groups):
                    break  # a trending repo/model that only matched the broad bucket is still an open-source project
                return category
    for group in source_groups:
        if group in FALLBACK_BY_SOURCE:
            return FALLBACK_BY_SOURCE[group]
    return OTHER


# --- highlight tabs: 焦點 / 黑馬 / 潛力 --------------------------------------------------------------

HIGHLIGHTS = ["焦點", "黑馬", "潛力"]
TRENDING = {"GitHub Trending", "Hugging Face Trending"}
# big labs and big tech: their news is never a "dark horse" or an up-and-coming project
BIG = words(r"\b(openai|chatgpt|anthropic|claude|google|gemini|deepmind|meta|llama|microsoft|copilot|nvidia|apple|siri|"
            r"amazon|aws|xai|grok|mistral|deepseek|qwen|alibaba|moonshot|kimi|ibm|samsung|tesla|musk|altman|"
            r"bytedance|tencent|baidu|huawei|intel|amd|qualcomm|tsmc|meta-llama|facebook)\b")


def is_big(c):
    return bool(BIG.search(f"{c['title_original']} {c['primary_url']}"))


def pick_highlights(clusters, n=10):
    """Clusters must already be scored (sorted by score) and carry heat_norm."""
    # 必知大新聞: an official lab announcement (weight 5) or a story at least two independent sources covered
    # stories more sources picked up come first, then by score
    focus = sorted((c for c in clusters if c["weight"] == 5 or len(c["groups"]) >= 2),
                   key=lambda c: (len(c["groups"]), c["score"]), reverse=True)
    focus += [c for c in clusters if c not in focus]  # top up by score if the day is quiet
    # 受歡迎的黑馬: hot community discussion (HN) about someone other than the big players
    dark = sorted((c for c in clusters if c["heat_norm"] > 0 and not is_big(c) and not c["groups"] & TRENDING
                   and not c["title_original"].startswith("Show HN")), key=lambda c: c["heat_norm"], reverse=True)
    # 最有潛力: up-and-coming open-source projects and models (trending lists, Show HN) from outside the big players
    rising = sorted((c for c in clusters if (c["groups"] & TRENDING or c["title_original"].startswith("Show HN"))
                     and not is_big(c)), key=lambda c: c["heat_norm"], reverse=True)
    return {"焦點": focus[:n], "黑馬": dark[:n], "潛力": rising[:n]}
