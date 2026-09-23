"""耘野果蔬摊 —— 菜园收获的第一条出路：把菜卖成金币，顺便学点经营常识。

流程：
    菜篮 --(按今日行情出售)--> 金币 + 售卖流水 --> 随机一张「管理学 / 基础金融」科普卡
    金币 --(COIN_RATE 枚换 1 点)--> 能量，回到菜园继续种
"""
import hashlib
import random
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from . import db
from .farm import CROPS

# ---------- 基准价目表（金币 / 份）----------
PRICES = {
    "cabbage":    12,
    "rice":       20,
    "strawberry": 26,
    "tomato":     32,
    "corn":       40,
    "soybean":    48,
    "pepper":     60,
    "pumpkin":    72,
    "watermelon": 90,
    "grape":      115,
}

# 摊位等级（按累计收入）
STALL_LEVELS = [
    (0,     "路边小摊", "🧺"),
    (120,   "集市摊主", "🏪"),
    (400,   "果蔬铺老板", "🥕"),
    (1000,  "农产品经纪人", "📦"),
    (2500,  "田园商社社长", "🏡"),
    (6000,  "供应链掌柜", "🚚"),
]

# ---------- 出售成功后弹出的科普卡 ----------
TIPS: List[Dict[str, str]] = [
    {"tag": "金融", "title": "机会成本",
     "body": "你把这份菜卖成了金币，就放弃了把它做成菜肴再发布换能量的机会。\n"
             "「为了做这件事而放弃的最高价值」，就叫机会成本 —— 它不写在账本上，却真实存在。"},
    {"tag": "经济学", "title": "价格由供需决定",
     "body": "今天某种作物的行情涨了，多半是因为市场上货少。\n"
             "价格不是谁定的，它是供给和需求相互拉扯出来的信号：货多人少就跌，货少人多就涨。"},
    {"tag": "金融", "title": "复利",
     "body": "每天打卡攒 10 点能量看着不起眼，但连着 30 天就是 300 点，足够撬动更贵的种子。\n"
             "复利的要害在于：收益会加入本金继续产生收益，时间越长曲线越陡。"},
    {"tag": "金融", "title": "沉没成本",
     "body": "已经浇出去的那 8 点能量收不回来了。\n"
             "理性决策只看「接下来还值不值」，别被「我都投入这么多了」绑架 —— 那是沉没成本谬误。"},
    {"tag": "经济学", "title": "边际收益递减",
     "body": "同一块地浇第 10 次水的效果，远不如第 1 次。\n"
             "在技术不变的条件下，持续追加某一种投入，每一份新增投入带来的产出会越来越少。"},
    {"tag": "金融", "title": "现金流",
     "body": "摊子上堆再多货，变不了现就只是库存。\n"
             "很多生意不是不赚钱，而是死在现金流断裂上 —— 账上有利润，手里没钱。学习也一样："
             "能随时调用的知识才叫能力。"},
    {"tag": "金融", "title": "分散风险",
     "body": "别把 6 块地全种成西瓜，万一行情跌了就全赔。\n"
             "把资源分散到相关性低的项目上，可以在不牺牲太多收益的前提下显著降低波动，"
             "这是最朴素的「不要把所有鸡蛋放在一个篮子里」。"},
    {"tag": "管理学", "title": "PDCA 循环",
     "body": "计划(Plan) → 执行(Do) → 检查(Check) → 改进(Act)。\n"
             "种一茬菜、看一次行情、调一次种植结构，就是完整的一轮 PDCA。持续改进靠的不是灵感，是循环。"},
    {"tag": "管理学", "title": "二八定律",
     "body": "往往 20% 的高价值作物贡献了 80% 的收入。\n"
             "帕累托法则提醒你：先找出那关键的 20%，把好钢用在刀刃上，而不是平均用力。"},
    {"tag": "管理学", "title": "木桶效应",
     "body": "一块地产出再高，也会被你最缺的那项资源卡住 —— 能量、地块数还是时间？\n"
             "一只木桶能装多少水，取决于最短的那块板。补短板常常比拉长板更划算。"},
    {"tag": "管理学", "title": "库存周转",
     "body": "菜篮里堆着 30 个南瓜不算富有，能快速卖出去才算。\n"
             "周转率比囤货量更值得盯：同样的货一年卖 12 次，赚的钱是一年卖 1 次的很多倍。"},
    {"tag": "管理学", "title": "SMART 目标",
     "body": "「我要变强」不是目标，「本周做完 5 道列表题、打卡 7 天」才是。\n"
             "具体、可衡量、可实现、相关、有时限 —— 五个条件缺一个，执行时就会打滑。"},
    {"tag": "营销", "title": "品牌溢价",
     "body": "同样的番茄，标上「自家菜园直采」就能多卖钱。\n"
             "溢价不来自产品本身，来自信任。个人能力也是一样：稳定的交付记录，就是你的品牌。"},
    {"tag": "金融", "title": "通货膨胀",
     "body": "如果金币发得比菜多，金币就会越来越不值钱。\n"
             "货币的价值从来不来自它本身，而来自它背后能换到多少东西。"},
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _factor(crop: str, day: str = "") -> float:
    """今日行情系数 0.80~1.30，同一天同一作物固定，靠日期哈希决定。"""
    day = day or date.today().isoformat()
    h = hashlib.md5(f"{day}-{crop}".encode("utf-8")).hexdigest()
    v = int(h[:8], 16) % 1000 / 1000.0
    return round(0.80 + v * 0.50, 2)


def price_of(crop: str) -> Dict[str, Any]:
    """返回该作物今日的行情。"""
    base = PRICES.get(crop, 10)
    f = _factor(crop)
    return {"base": base, "price": max(1, int(round(base * f))),
            "factor": f, "delta": int(round((f - 1) * 100)),
            "up": f >= 1.0}


def stall_level(income: int) -> Dict[str, Any]:
    cur = STALL_LEVELS[0]
    nxt = None
    for i, (need, name, icon) in enumerate(STALL_LEVELS):
        if income >= need:
            cur = (need, name, icon)
            nxt = STALL_LEVELS[i + 1] if i + 1 < len(STALL_LEVELS) else None
    need_now = cur[0]
    next_need = nxt[0] if nxt else None
    prog = 0
    if next_need:
        prog = min(100, int((income - need_now) * 100 / (next_need - need_now)))
    return {"name": cur[1], "icon": cur[2], "next": nxt[1] if nxt else "",
            "next_need": next_need, "progress": 100 if not nxt else prog}


def stock(user_id: int) -> List[Dict[str, Any]]:
    """菜篮库存 + 今日行情，卡片直接渲染。"""
    out = []
    for b in db.query("SELECT crop, count FROM harvests WHERE user_id=? AND count>0 "
                      "ORDER BY count DESC", (user_id,)):
        cfg = CROPS.get(b["crop"])
        if not cfg:
            continue
        p = price_of(b["crop"])
        out.append({"crop": b["crop"], "count": b["count"], "name": cfg["name"],
                    "emoji": cfg["emoji"], **p,
                    "total": p["price"] * b["count"]})
    return out


def summary(user_id: int) -> Dict[str, Any]:
    row = db.query_one("SELECT COUNT(*) AS n, COALESCE(SUM(income),0) AS income, "
                       "COALESCE(SUM(count),0) AS goods FROM sales WHERE user_id=?",
                       (user_id,))
    n = row["n"] if row else 0
    income = row["income"] if row else 0
    goods = row["goods"] if row else 0
    return {"orders": n, "income": income, "goods": goods,
            "coins": db.coins_of(user_id), "stall": stall_level(income)}


def sell(user_id: int, crop: str, count: int = 1) -> Dict[str, Any]:
    cfg = CROPS.get(crop)
    if not cfg:
        return {"ok": False, "msg": "没有这种作物"}
    row = db.query_one("SELECT id, count FROM harvests WHERE user_id=? AND crop=?",
                       (user_id, crop))
    have = row["count"] if row else 0
    if have <= 0:
        return {"ok": False, "msg": f"菜篮里没有{cfg['name']}"}
    if count <= 0 or count == 9999:
        count = have
    if count > have:
        return {"ok": False, "msg": f"只有 {have} 份{cfg['name']}"}
    p = price_of(crop)
    income = p["price"] * count
    db.execute("UPDATE harvests SET count=count-? WHERE id=?", (count, row["id"]))
    db.add_coins(user_id, income)
    db.execute("INSERT INTO sales(user_id, crop, count, unit, income, created_at) "
               "VALUES (?,?,?,?,?,?)", (user_id, crop, count, p["price"], income, _now()))
    tip = dict(random.choice(TIPS))
    return {"ok": True,
            "msg": f"卖出 {cfg['emoji']}{cfg['name']} ×{count}，收入 {income} 金币",
            "income": income, "unit": p["price"], "count": count,
            "coins": db.coins_of(user_id), "name": cfg["name"], "emoji": cfg["emoji"],
            "tip": tip}


def sell_all(user_id: int) -> Dict[str, Any]:
    got, income, n = [], 0, 0
    for s in stock(user_id):
        r = sell(user_id, s["crop"], s["count"])
        if r["ok"]:
            got.append(r["emoji"] + r["name"])
            income += r["income"]
            n += r["count"]
    if not got:
        return {"ok": False, "msg": "菜篮是空的，先去菜园收点东西吧"}
    tip = dict(random.choice(TIPS))
    return {"ok": True, "msg": f"清空菜篮：卖出 {n} 份，共 {income} 金币",
            "income": income, "coins": db.coins_of(user_id), "tip": tip}


def recent_sales(user_id: int, limit: int = 8) -> List[Dict[str, Any]]:
    rows = db.query("SELECT * FROM sales WHERE user_id=? ORDER BY id DESC LIMIT ?",
                    (user_id, limit))
    for r in rows:
        cfg = CROPS.get(r["crop"], {})
        r["name"] = cfg.get("name", r["crop"])
        r["emoji"] = cfg.get("emoji", "🥬")
        r["time"] = r["created_at"][5:16]
    return rows


def wealth_board(limit: int = 10) -> List[Dict[str, Any]]:
    rows = db.query("SELECT id, nickname, coins FROM users WHERE coins > 0 "
                    "ORDER BY coins DESC LIMIT ?", (limit,))
    for i, r in enumerate(rows):
        r["rank"] = i + 1
    return rows


def exchange(user_id: int, coins: int) -> Dict[str, Any]:
    """金币换能量：COIN_RATE 枚金币换 1 点能量。"""
    coins = int(coins or 0)
    if coins <= 0:
        return {"ok": False, "msg": "请输入要兑换的金币数"}
    have = db.coins_of(user_id)
    if coins > have:
        return {"ok": False, "msg": f"只有 {have} 枚金币"}
    use = coins - (coins % db.COIN_RATE)      # 按汇率取整
    if use <= 0:
        return {"ok": False, "msg": f"至少需要 {db.COIN_RATE} 枚金币"}
    energy = use // db.COIN_RATE
    db.add_coins(user_id, -use)
    e = db.add_energy(user_id, energy)
    return {"ok": True, "msg": f"用 {use} 金币换到 {energy} 点能量",
            "coins": db.coins_of(user_id), "energy": e, "used": use, "gained": energy}
