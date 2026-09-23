"""耕耘种菜大赛 —— 每周一季，把「刷题打卡」和「种菜收菜」拧在一起比拼。

赛季：按 ISO 周自动轮换，每季绑定一个题库分类 + 一种主推作物。
积分 = 学习分（打卡 + 本周通过题目，主题分类额外加权）
     + 耕耘分（本季收获次数与收获能量，主推作物额外加权）
     + 成长值（菜园里正在生长的作物进度）

赛季结束前可以随时报名；结算时按榜单排名发放能量与稀有种子奖励。
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from . import db
from .farm import CROPS

# ---------- 赛季主题：与题库分类一一绑定 ----------
THEMES = [
    {"cat": "基础语法", "crop": "cabbage", "title": "育苗季 · 基础语法",
     "goal": "本周完成 3 道「基础语法」题，并打卡 3 天",
     "need_problems": 3, "need_checkin": 3,
     "tip": "苗刚出土，先把变量和循环练扎实，别急着追高难度。"},
    {"cat": "字符串", "crop": "rice", "title": "插秧季 · 字符串",
     "goal": "本周完成 3 道「字符串」题，并打卡 3 天",
     "need_problems": 3, "need_checkin": 3,
     "tip": "字符串像插秧，一行一行对齐了才好数。"},
    {"cat": "列表", "crop": "tomato", "title": "搭架季 · 列表",
     "goal": "本周完成 3 道「列表」题，并打卡 4 天",
     "need_problems": 3, "need_checkin": 4,
     "tip": "列表是菜园的竹架，搭稳了后面什么都好挂。"},
    {"cat": "字典与集合", "crop": "strawberry", "title": "开花季 · 字典与集合",
     "goal": "本周完成 3 道「字典与集合」题，并打卡 4 天",
     "need_problems": 3, "need_checkin": 4,
     "tip": "键值配对就像给每垄菜插上名牌，找起来才快。"},
    {"cat": "函数与递归", "crop": "corn", "title": "抽穗季 · 函数与递归",
     "goal": "本周完成 2 道「函数与递归」题，并打卡 4 天",
     "need_problems": 2, "need_checkin": 4,
     "tip": "递归是一层层的玉米苞叶，剥到最后要见底。"},
    {"cat": "算法进阶", "crop": "watermelon", "title": "丰收季 · 算法进阶",
     "goal": "本周完成 2 道「算法进阶」题，并打卡 5 天",
     "need_problems": 2, "need_checkin": 5,
     "tip": "压轴的大西瓜，得慢慢养，急不得。"},
]

# 作物成长等级（按大赛积分）
GROWTH_RANKS = [
    (0,   "🌱 幼苗期"),
    (60,  "🌿 抽枝期"),
    (150, "🍃 展叶期"),
    (280, "🌸 开花期"),
    (450, "🍅 挂果期"),
    (700, "🏆 大丰收"),
]

# 奖励表：(名次上限, 奖项名, 能量, 道具)
REWARDS = [
    (1,  "🥇 冠军 · 金穗奖", 200, {"seed_melon": 2, "fert_super": 2}),
    (3,  "🥈 领奖台 · 银穗奖", 140, {"seed_golden": 1, "fert_super": 1}),
    (10, "🥉 十强 · 铜穗奖", 90, {"seed_rainbow": 1, "fert_quick": 2}),
]

SCORE_CHECKIN = 20      # 每打卡一天
SCORE_AC = 6            # 本周每通过一道题（任意分类）
SCORE_AC_THEME = 14     # 本周每通过一道「本季主题分类」题（额外）
SCORE_HARVEST = 8       # 每收获一次
SCORE_ENERGY = 0.12     # 每一点收获能量
SCORE_THEME_CROP = 20   # 每收获一份本季主推作物


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _season_window() -> Dict[str, Any]:
    y, w, _ = date.today().isocalendar()
    start = date.fromisocalendar(y, w, 1)          # 本周一
    end = start + timedelta(days=6)
    return {"year": y, "week": w, "start": start, "end": end}


def current() -> Dict[str, Any]:
    """当前赛季信息（主题、主推作物、任务、剩余时间）。"""
    win = _season_window()
    idx = (win["year"] * 52 + win["week"]) % len(THEMES)
    t = THEMES[idx]
    cfg = CROPS.get(t["crop"], {})
    left = (win["end"] - date.today()).days
    return {
        "key": f"{win['year']}-W{win['week']:02d}",
        "index": idx,
        "title": t["title"], "cat": t["cat"], "crop": t["crop"],
        "crop_name": cfg.get("name", ""), "crop_emoji": cfg.get("emoji", "🌱"),
        "goal": t["goal"], "tip": t["tip"],
        "need_problems": t["need_problems"], "need_checkin": t["need_checkin"],
        "start": str(win["start"]), "end": str(win["end"]),
        "days_left": max(0, left) + 1,
    }


def _since(season: Dict[str, Any]) -> str:
    return season["start"] + " 00:00:00"


# ---------- 报名 ----------
def joined(user_id: int, season_key: str = "") -> bool:
    key = season_key or current()["key"]
    return bool(db.query_one("SELECT id FROM contest_entries WHERE user_id=? AND season=?",
                             (user_id, key)))


def join(user_id: int) -> Dict[str, Any]:
    s = current()
    if joined(user_id, s["key"]):
        return {"ok": False, "msg": "这一季你已经报名啦，专心种菜就行 🌱"}
    db.execute("INSERT INTO contest_entries(user_id, season, joined_at) VALUES (?,?,?)",
               (user_id, s["key"], _now()))
    return {"ok": True, "msg": f"报名成功！本季主题：{s['title']}（主推 {s['crop_emoji']}{s['crop_name']}）",
            "season": s["key"]}


def entry(user_id: int, season_key: str = "") -> Optional[Dict[str, Any]]:
    key = season_key or current()["key"]
    return db.query_one("SELECT * FROM contest_entries WHERE user_id=? AND season=?",
                        (user_id, key))


# ---------- 计分 ----------
def _learn_score(user_id: int, season: Dict[str, Any]) -> Dict[str, int]:
    since = _since(season)
    days = db.query_one("SELECT COUNT(*) AS c FROM checkins WHERE user_id=? AND day>=?",
                        (user_id, season["start"]))
    ac = db.query_one(
        "SELECT COUNT(DISTINCT s.problem_id) AS c FROM submissions s "
        "WHERE s.user_id=? AND s.status='accepted' AND s.created_at>=?", (user_id, since))
    theme = db.query_one(
        "SELECT COUNT(DISTINCT s.problem_id) AS c FROM submissions s "
        "JOIN problems p ON p.id = s.problem_id "
        "WHERE s.user_id=? AND s.status='accepted' AND s.created_at>=? AND p.category=?",
        (user_id, since, season["cat"]))
    return {"days": days["c"] if days else 0,
            "ac": ac["c"] if ac else 0,
            "theme_ac": theme["c"] if theme else 0}


def _farm_score(user_id: int, season: Dict[str, Any]) -> Dict[str, Any]:
    since = _since(season)
    row = db.query_one("SELECT COUNT(*) AS n, COALESCE(SUM(energy),0) AS e FROM farm_log "
                       "WHERE user_id=? AND created_at>=?", (user_id, since))
    theme_row = db.query_one("SELECT COUNT(*) AS n FROM farm_log WHERE user_id=? "
                             "AND created_at>=? AND crop=?",
                             (user_id, since, season["crop"]))
    return {"harvest": row["n"] if row else 0,
            "energy": row["e"] if row else 0,
            "theme_crop": theme_row["n"] if theme_row else 0}


def _garden_value(user_id: int) -> int:
    """菜园里正在生长的作物进度总和（成熟的地块按 100 计）。"""
    from . import farm
    val = 0
    for p in farm.garden(user_id):
        if p["state"] == "growing":
            val += 100 if p["ready"] else p["progress"]
    return val


def score(user_id: int, season: Dict[str, Any] = None) -> Dict[str, Any]:
    """某用户本赛季的完整战绩。"""
    season = season or current()
    learn = _learn_score(user_id, season)
    farm_s = _farm_score(user_id, season)
    grow = _garden_value(user_id)
    learn_pt = learn["days"] * SCORE_CHECKIN + learn["ac"] * SCORE_AC \
        + learn["theme_ac"] * SCORE_AC_THEME
    farm_pt = farm_s["harvest"] * SCORE_HARVEST + int(farm_s["energy"] * SCORE_ENERGY) \
        + farm_s["theme_crop"] * SCORE_THEME_CROP
    total = learn_pt + farm_pt + grow
    return {
        "total": total, "learn": learn_pt, "farm": farm_pt, "grow": grow,
        "days": learn["days"], "ac": learn["ac"], "theme_ac": learn["theme_ac"],
        "harvest": farm_s["harvest"], "energy": farm_s["energy"],
        "theme_crop": farm_s["theme_crop"],
        "rank_name": rank_name(total),
        "goal_done": learn["days"] >= season["need_checkin"]
                     and learn["theme_ac"] >= season["need_problems"],
    }


def rank_name(total: int) -> str:
    name = GROWTH_RANKS[0][1]
    for need, n in GROWTH_RANKS:
        if total >= need:
            name = n
    return name


# ---------- 榜单 ----------
def board(limit: int = 20, season: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    season = season or current()
    rows = db.query(
        "SELECT e.user_id, e.claimed, e.award, u.nickname, u.exp "
        "FROM contest_entries e JOIN users u ON u.id = e.user_id "
        "WHERE e.season=?", (season["key"],))
    out = []
    for r in rows:
        s = score(r["user_id"], season)
        lv = db.level_of(r["exp"])
        out.append({
            "user_id": r["user_id"], "nickname": r["nickname"],
            "level": lv["level"], "lv_name": lv["name"],
            "claimed": r["claimed"], "award": r["award"],
            "crop": season["crop"], "crop_emoji": season["crop_emoji"],
            "crop_name": season["crop_name"],
            **s,
        })
    out.sort(key=lambda x: (-x["total"], x["nickname"]))
    for i, r in enumerate(out):
        r["rank"] = i + 1
        r["medal"] = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i + 1, f"{i + 1}")
    return out[:limit]


def my_rank(user_id: int, season: Dict[str, Any] = None) -> Dict[str, Any]:
    season = season or current()
    rows = board(200, season)
    for r in rows:
        if r["user_id"] == user_id:
            return {"rank": r["rank"], "total": r["total"],
                    "players": len(rows), "award": r["award"], "claimed": r["claimed"]}
    return {"rank": 0, "total": 0, "players": len(rows), "award": "", "claimed": 0}


# ---------- 领奖 ----------
def reward_of(rank: int, total: int) -> Dict[str, Any]:
    """按名次给出奖励方案。"""
    for limit, name, energy, items in REWARDS:
        if rank <= limit:
            return {"title": name, "energy": energy, "items": items}
    return {"title": "🌾 完赛奖", "energy": 20 if total > 0 else 0,
            "items": {"fert_quick": 1} if total >= 60 else {}}


def claim(user_id: int) -> Dict[str, Any]:
    """结算本赛季奖励，每季只能领一次。"""
    s = current()
    e = entry(user_id, s["key"])
    if not e:
        return {"ok": False, "msg": "你还没报名这一季，先点「报名参赛」吧"}
    if e["claimed"]:
        return {"ok": False, "msg": f"这一季的奖励已经领过啦（{e['award']}）"}
    rank = my_rank(user_id, s)
    total = rank["total"]
    rw = reward_of(rank["rank"] or 999, total)
    if rw["energy"] <= 0 and not rw["items"]:
        return {"ok": False, "msg": "还没有积分，去打卡、刷题、收一茬菜再来领奖 🌱"}
    from . import shop
    energy = db.add_energy(user_id, rw["energy"])
    got = []
    for key, n in rw["items"].items():
        shop.grant(user_id, key, n)
        got.append(f"{shop.ITEMS[key]['emoji']}{shop.ITEMS[key]['name']}×{n}")
    db.execute("UPDATE contest_entries SET claimed=1, award=? WHERE id=?",
               (rw["title"], e["id"]))
    return {"ok": True,
            "msg": f"领奖成功：{rw['title']}，能量 +{rw['energy']}"
                   + ("，道具：" + "、".join(got) if got else ""),
            "award": rw["title"], "energy": energy, "gain": rw["energy"],
            "items": got, "rank": rank["rank"], "total": total}


def overview(user_id: int) -> Dict[str, Any]:
    """大赛页面一次性拿全的数据。"""
    s = current()
    return {
        "season": s,
        "joined": joined(user_id, s["key"]),
        "entry": entry(user_id, s["key"]),
        "mine": score(user_id, s),
        "rank": my_rank(user_id, s),
        "board": board(20, s),
        "rewards": [{"range": "第 1 名", "title": REWARDS[0][1], "energy": REWARDS[0][2],
                     "items": [shop_name(k, v) for k, v in REWARDS[0][3].items()]},
                    {"range": "第 2–3 名", "title": REWARDS[1][1], "energy": REWARDS[1][2],
                     "items": [shop_name(k, v) for k, v in REWARDS[1][3].items()]},
                    {"range": "第 4–10 名", "title": REWARDS[2][1], "energy": REWARDS[2][2],
                     "items": [shop_name(k, v) for k, v in REWARDS[2][3].items()]},
                    {"range": "其余完赛", "title": "🌾 完赛奖", "energy": 20,
                     "items": ["💧速长肥×1（满 60 分）"]}],
        "ranks": GROWTH_RANKS,
    }


def shop_name(key: str, n: int) -> str:
    from . import shop
    it = shop.ITEMS.get(key)
    return f"{it['emoji']}{it['name']}×{n}" if it else f"{key}×{n}"
