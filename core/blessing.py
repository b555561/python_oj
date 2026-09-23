"""登录祝福语 / 每日签到文案生成。

纯本地文案，不调用任何外部接口。
祝福语按时段 + 星期 + 连续签到天数 + 季节组合生成，
同一天内对同一用户保持稳定（不会刷新一次变一次）。
"""
import random
from datetime import date, datetime

# ---------------- 新用户引导文案（首页导语区 / 注册欢迎弹窗共用） ----------------
NEW_USER_INTRO = (
    "你是否还在为自己是编程小白感到迷茫？"
    "是不是总觉得编程学习枯燥又难熬？"
    "看着别人拿下竞赛奖项，心中满是焦虑？"
    "担心自己的技术迟迟得不到提升？"
    "欢迎来到 PyOJ！把枯燥刷题化作一方田园菜园。"
    "刷题打卡，播种成长，在趣味养成中打磨编程本领，"
    "不必追赶他人节奏，一步步收获属于自己的实力✨"
)

# ---------------- 时段问候 ----------------
_GREET = [
    (5,  "凌晨好",  "🌙"),
    (8,  "清晨好",  "🌤️"),
    (11, "上午好",  "☀️"),
    (13, "午安",    "🍚"),
    (17, "下午好",  "🌾"),
    (19, "傍晚好",  "🌇"),
    (23, "晚上好",  "🌙"),
    (24, "夜深了",  "✨"),
]

# ---------------- 祝福语库（田园 + 学习） ----------------
_BLESS = [
    ("🌱", "愿你今天的代码像春秧一样，一行一行拔节生长。"),
    ("🌾", "今天也要给大脑浇点水，长出新叶子来。"),
    ("🍅", "跑通的那一刻，像极了第一颗番茄悄悄变红。"),
    ("🌿", "Bug 就像地里的杂草，拔掉一棵就清爽一分。"),
    ("🍃", "不急不躁，稻子成熟要一百天，你也一样值得等待。"),
    ("🧺", "一行一行写，一垄一垄种，秋天自有答案。"),
    ("✨", "愿你今天少一个 Bug，多一分笃定。"),
    ("🌻", "保持向着光的方向生长，今天的你也很棒。"),
    ("💧", "坚持就是最好的肥料，点滴都会回到你身上。"),
    ("🥕", "先把简单的事做好，复杂的自然会慢慢松土。"),
    ("🌸", "愿你的思路像藤蔓一样，顺着架子越爬越高。"),
    ("🍚", "一粥一饭当思来处不易，一题一卡皆是积累。"),
    ("🌳", "今天种下的每个知识点，将来都是一棵大树。"),
    ("🪴", "慢慢来，苗小序在菜园里等你一起长大。"),
    ("🎋", "愿你今天步步有回响，节节有惊喜。"),
    ("🌼", "把难题拆成小块，就像把菜地分成一垄一垄。"),
]

# ---------------- 星期彩蛋 ----------------
_WEEKDAY = {
    0: "新的一周开始啦，先给自己定个小目标 🎯",
    1: "周二宜深耕，把上周没啃完的题再啃一口 📘",
    2: "周三过半，稳住节奏就是胜利 🌾",
    3: "周四加油，胜利已经在田埂那头招手 🚩",
    4: "周五啦，给这周的努力收个漂亮的尾 🧺",
    5: "周末好，慢一点也没关系，菜园不会催你 🌻",
    6: "周日宜复盘，把本周收获晒一晒 ☀️",
}

# ---------------- 季节词 ----------------
def _season(d: date) -> str:
    m = d.month
    if m in (3, 4, 5):
        return "春风"
    if m in (6, 7, 8):
        return "夏雨"
    if m in (9, 10, 11):
        return "秋阳"
    return "冬藏"


def greet(now: datetime = None) -> dict:
    """按时段返回问候文案。"""
    now = now or datetime.now()
    h = now.hour
    word, emoji = _GREET[-1][1], _GREET[-1][2]
    for limit, w, e in _GREET:
        if h < limit:
            word, emoji = w, e
            break
    return {"word": word, "emoji": emoji}


def _stable_pick(pool, seed_str: str):
    """同一天内稳定选取，不会刷新一次变一次。"""
    r = random.Random(seed_str)
    return r.choice(pool)


def daily(user: dict, streak: int = 0, total: int = 0,
          checked_today: bool = False, now: datetime = None,
          nickname: str = "") -> dict:
    """生成登录签到弹窗用的整套文案。"""
    now = now or datetime.now()
    g = greet(now)
    emoji, text = _stable_pick(_BLESS, f"{now.date()}|{user.get('id', 0)}")
    tip = _WEEKDAY.get(now.weekday(), "")

    if checked_today:
        head = f"今天已经签到啦，连续 {max(streak, 1)} 天，真棒！"
    elif streak >= 3:
        head = f"已连续签到 {streak} 天，别让藤蔓断在今天 🌿"
    elif streak == 0:
        head = "今天还没签到，点亮这一格就能领能量～"
    else:
        head = f"昨日之前已连续 {streak} 天，今天续上吧 ✨"

    return {
        "date": str(now.date()),
        "greet": g["word"],
        "greet_emoji": g["emoji"],
        "name": nickname or user.get("nickname") or user.get("username") or "同学",
        "emoji": emoji,
        "bless": text,
        "tip": tip,
        "head": head,
        "season": _season(now.date()),
        "streak": streak,
        "total": total,
        "checked": checked_today,
    }
