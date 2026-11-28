"""Keyword rules that put each story into one of six topics most people follow about AI (see README: surveys put jobs,
everyday tools, and rules/scams/privacy at the top). First matching rule wins, so order matters: narrow topics come
before broad ones. Chinese keywords are listed in Traditional and Simplified form."""

import re
from urllib.parse import urlsplit

CATEGORIES = ["Tools & Apps", "New Models", "Work & Jobs", "Rules & Safety", "Chips & Industry", "Everyday AI", "Other"]
OTHER = "Other"  # no rule matched; not shown as a tab


def words(*patterns):
    return re.compile("|".join(patterns), re.IGNORECASE)


RULES = [
    ("Rules & Safety", words(
        # scams, privacy, deepfakes, security incidents
        r"\bscam", r"\bfraud", r"\bdeepfake", r"\bmisinformation\b", r"\bprivacy\b", r"\bsurveillance\b",
        r"\bCVE-\d", r"\bvulnerab", r"\bbreach", r"\bmalware", r"\bransomware", r"\bprompt injection", r"\bjailbreak",
        r"\bphishing", r"\bleak(ed|s)?\b", r"\bhack(ed|ers?)\b",
        # law, regulation, safety
        r"\bregulat", r"\blegislat", r"\blawmakers?\b", r"\bAI Act\b", r"\bcongress", r"\bsenat(e|or)", r"\bwhite house\b",
        r"\bexecutive order\b", r"\bexport control", r"\bcopyright", r"\blawsuit", r"\bsue[sd]?\b", r"\bcourt\b",
        r"\bjudge\b", r"\bFTC\b", r"\bantitrust", r"\bban(s|ned)?\b", r"\bsafety\b", r"\bharms?\b", r"\bchild(ren)?\b",
        r"\bteens?\b", r"\bminors?\b",
        "詐騙", "诈骗", "深偽", "深度伪造", "假訊息", "假新闻", "隱私", "隐私", "個資", "个人信息", "漏洞", "資安", "网络安全",
        "外洩", "泄露", "駭客", "黑客", "釣魚", "钓鱼", "監管", "监管", "法規", "法规", "法案", "立法", "版權", "版权",
        "訴訟", "诉讼", "起訴", "起诉", "出口管制", "禁令", "未成年", "AI ?安全")),
    ("Work & Jobs", words(
        r"\bjobs?\b", r"\blayoffs?\b", r"\blaid off\b", r"\bworkers?\b", r"\bworkforce\b", r"\bemploy(ees?|ment|ers?)\b",
        r"\bhiring\b", r"\bcareers?\b", r"\bunemploy", r"\breplace(s|d)? (humans?|workers?|jobs?)", r"\bworkplace\b",
        r"\bproductivity\b", r"\bwhite[- ]collar\b", r"\bentry[- ]level\b", r"\bgraduates?\b", r"\breskill", r"\bupskill",
        "工作(?!流)", "就業", "就业", "失業", "失业", "裁員", "裁员", "職場", "职场", "員工", "员工", "職缺", "岗位", "崗位",
        "取代", "求職", "求职", "招聘", "徵才", "薪資", "薪资", "上班族", "打工人", "生產力", "生产力")),
    ("New Models", words(
        r"\b(GPT|Claude|Gemini|Llama|Qwen|DeepSeek|Mistral|Kimi|Grok|Gemma|Fable|Opus|Sonnet|Haiku|GLM|MiniMax|Veo|Sora)[- ]?\d",
        r"\bnew (AI )?model\b", r"\bmodel (release|launch)", r"\b(releases?|launch(es)?|unveils?|introduc(es|ing))\b.*\bmodel\b",
        r"\bopen[- ]weights?\b", r"\bbenchmark", r"\bleaderboard\b",
        "新模型", "大模型", "模型.*(發布|发布|推出|釋出|上线|上線|開源|开源)", "(發布|发布|推出|釋出|開源|开源).*模型", "跑分", "榜單", "榜单")),
    ("Everyday AI", words(
        r"\bhealth", r"\bhospital", r"\bdoctors?\b", r"\bpatients?\b", r"\bmedic", r"\bdrug", r"\bcancer\b",
        r"\beducation", r"\bschools?\b", r"\bstudents?\b", r"\bteachers?\b", r"\bhomework\b",
        r"\biPhone\b", r"\bAndroid\b", r"\bSiri\b", r"\bsmartphones?\b", r"\b(smart )?glasses\b", r"\bwearables?\b",
        r"\bcars?\b", r"\bdriv(ing|erless)\b", r"\brobotaxi", r"\bhumanoid", r"\brobots?\b", r"\bshopping\b",
        r"\btravel\b", r"\bmusic\b", r"\bmovies?\b", r"\bgames?\b",
        "醫療", "医疗", "醫院", "医院", "醫生", "医生", "病人", "健康", "教育", "學校", "学校", "學生", "学生", "老師", "老师",
        "手機", "手机", "眼鏡", "眼镜", "穿戴", "汽車", "汽车", "自駕", "自动驾驶", "機器人", "机器人", "家電", "家电",
        "購物", "购物", "旅遊", "旅游", "音樂", "音乐", "電影", "电影", "遊戲", "游戏")),
    ("Chips & Industry", words(
        r"\bchips?\b", r"\bGPUs?\b", r"\bsemiconductor", r"\bNVIDIA\b", r"\bTSMC\b", r"\bFoxconn\b", r"\bdata ?cent(er|re)s?\b",
        r"\braise[sd]?\b", r"\bfunding\b", r"\bseries [A-F]\b", r"\$\d[\d.,]*\s?(m|b|bn|million|billion|trillion)\b",
        r"\bvaluation", r"\bIPO\b", r"\bacqui(re|res|red|sition)", r"\bmerger", r"\bdeal\b", r"\binvest", r"\brevenue",
        r"\bearnings\b", r"\bprofit", r"\bstocks?\b", r"\bshares\b", r"\bmarket cap\b", r"\bCEO\b", r"\bbubble\b",
        "晶片", "芯片", "半導體", "半导体", "輝達", "英伟达", "台積電", "台积电", "鴻海", "广达", "廣達", "伺服器", "服务器",
        "算力", "資料中心", "數據中心", "数据中心", "融資", "融资", "估值", "收購", "收购", "併購", "并购", "投資", "投资",
        "營收", "营收", "財報", "财报", "市值", "上市", "股價", "股价", "泡沫", "供應鏈", "供应链")),
    ("Tools & Apps", words(
        r"\bChatGPT\b", r"\bCopilot\b", r"\bGemini\b", r"\bClaude\b", r"\bPerplexity\b", r"\bNotebookLM\b", r"\bMeta AI\b",
        r"\bagents?\b", r"\bagentic\b", r"\bClaude Code\b", r"\bCodex\b", r"\bCursor\b", r"\bvibe[- ]coding\b",
        r"\blaunch(es|ed)?\b", r"\breleases?\b", r"\brolls? out\b", r"\bapps?\b", r"\bfeatures?\b", r"\btools?\b",
        r"\bupdate", r"\bbrowser\b", r"\bchatbot", r"\bassistant", r"\bsearch\b", r"\bimage gen", r"\bvideo gen",
        "推出", "發布", "发布", "功能", "工具", "上線", "上线", "更新", "應用", "应用", "助手", "智能體", "智能体", "代理",
        "聊天機器人", "聊天机器人", "生圖", "生图", "影片生成", "视频生成", "瀏覽器", "浏览器", "搜尋", "搜索")),
]


def classify(title, summary=""):
    # the title decides first; the feed description only helps when the title matches nothing
    for text in (title, f"{title} {summary[:300]}"):
        for category, pattern in RULES:
            if pattern.search(text):
                return category
    return OTHER


# --- Headlines: the one highlight tab --------------------------------------------------------------------------

PER_SITE = 2  # Headlines never fill up with one site's posts


def pick_headlines(clusters, n=10):
    """Clusters must already be scored (sorted by score) and carry heat_norm.

    Popular stories first: community heat (HN points, Readhub outlet count), a curated headline source (weight 5:
    Techmeme) or at least two independent sources. An official post alone only tops up a quiet day."""
    hot = sorted((c for c in clusters if c["heat_norm"] > 0 or c["weight"] == 5 or len(c["groups"]) >= 2),
                 key=lambda c: (min(len(c["groups"]), 5) / 5 + c["heat_norm"], c["score"]), reverse=True)
    picked, per = [], {}
    for c in hot + [c for c in clusters if c not in hot]:
        site = urlsplit(c["primary_url"]).netloc.lower().removeprefix("www.")
        if per.get(site, 0) < PER_SITE:
            per[site] = per.get(site, 0) + 1
            picked.append(c)
    return picked[:n]
