"""Keyword rules that put each story into one main category. First matching rule wins."""

import re

CATEGORIES = ["模型發布", "產品與工具", "研究論文", "開源專案", "產業與投資", "晶片與硬體", "政策與法規", "應用案例"]
OTHER = "其他"  # no rule matched; still listed in the overall ranking, just not in a category tab

# sources whose every item belongs to one category
BY_SOURCE = {"arXiv": "研究論文", "GitHub Trending": "開源專案", "Hugging Face Trending": "開源專案"}


def words(*patterns):
    return re.compile("|".join(patterns), re.IGNORECASE)


RULES = [
    ("政策與法規", words(r"\bregulat", r"\blaws?\b", r"\blawsuit", r"\bsues?\b", r"\bcourt\b", r"\bjudge\b", r"\bsenate\b",
                    r"\bcongress\b", r"\bpolicy\b", r"\bban(s|ned)?\b", r"\bAI Act\b", r"\bcopyright", r"\bantitrust",
                    r"\bgovernment", r"\bFTC\b", r"\bEU\b", "法規", "法案", "立法", "政策", "訴訟", "監管", "政府", "禁令")),
    ("產業與投資", words(r"\bacqui(re|res|red|sition)", r"\bfunding\b", r"\braises?\b", r"\braised\b", r"\bvaluation",
                    r"\bIPO\b", r"\binvest", r"\blayoffs?\b", r"\brevenue", r"\bbillion\b", r"\bstartup", r"\bmerger",
                    r"\bstock\b", r"\bshares\b", r"\bbudgets?\b", r"\bdebt\b", r"\$\d", r"\b(m|b|tr)illion\b", "收購", "融資", "投資", "估值", "營收", "上市", "裁員", "併購")),
    ("晶片與硬體", words(r"\bchips?\b", r"\bGPUs?\b", r"\bTPUs?\b", r"\bsemiconductor", r"\bdata ?cent(er|re)s?\b",
                    r"\baccelerator", r"\bRTX\b", r"\bfirmware\b", r"\bNvidia\b", r"\bsilicon\b", r"\bfabs?\b", r"\bHBM\b", r"\bdatacenter", "晶片", "半導體",
                    "資料中心", "算力", "伺服器", "顯示卡")),
    ("開源專案", words(r"\bopen[- ]source", r"\bopen[- ]weights?\b", r"\bweights are out\b", r"\bgithub\.com\b", "開源")),
    ("模型發布", words(r"\b(GPT|Claude|Gemini|Llama|Qwen|DeepSeek|Mistral|Kimi|Grok|Phi|Gemma)[- ]?\d",
                    r"\bnew (AI )?model\b", r"\bmodel (release|launch)", r"\b(releases?|launch(es)?|unveils?|introduc(es|ing))\b.*\bmodel\b",
                    "新模型", "模型.*(發布|推出|釋出)", "(發布|推出|釋出).*模型")),
    ("研究論文", words(r"\bpaper\b", r"\bresearch(ers)?\b", r"\bstudy\b", r"\bbenchmark", r"\barxiv\b", "論文", "研究")),
    ("產品與工具", words(r"\blaunch(es|ed)?\b", r"\breleases?\b", r"\brolls? out\b", r"\bapp\b", r"\bfeatures?\b",
                    r"\btools?\b", r"\bAPI\b", r"\bupdate", r"\bagent\b", r"\bbrowser\b", r"\bCLI\b", r"\bSDK\b",
                    "推出", "功能", "工具", "上線", "更新")),
    ("應用案例", words(r"\bhospital", r"\bhealthcare\b", r"\bdoctors?\b", r"\beducation", r"\bschools?\b", r"\bfactory",
                    r"\buses AI\b", r"\busing AI\b", r"\bcase study", "應用", "導入", "醫療", "教育", "製造")),
]


def classify(title, summary="", source_groups=()):
    for group in source_groups:
        if group in BY_SOURCE:
            return BY_SOURCE[group]
    text = f"{title} {summary[:300]}"
    for category, pattern in RULES:
        if pattern.search(text):
            return category
    return OTHER
