"""苗小序的菜园 —— 用打卡刷题攒下的能量耕地、播种、浇水、收获。

时间线：
    空地 --(耕地 -5 能量)--> 已耕 --(播种 -种子成本)--> 生长中
    --(浇水 -8 能量，每次抵 10 分钟 / 或自然时间)--> 成熟 --(收获 +能量)--> 空地
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from . import db

# ---------- 作物图鉴 ----------
# cost: 种子能量成本 | grow: 成熟所需分钟 | reward: 收获返还能量 | lv: 解锁等级
CROPS = {
    "cabbage":    {"name": "小白菜", "emoji": "🥬", "cost": 10, "grow": 15,
                   "reward": 18,  "lv": 1, "desc": "长得快，适合攒第一桶能量"},
    "rice":       {"name": "水稻",   "emoji": "🌾", "cost": 16, "grow": 40,
                   "reward": 30,  "lv": 1, "desc": "农学院的看家本领，稳稳当当"},
    "strawberry": {"name": "草莓",   "emoji": "🍓", "cost": 20, "grow": 60,
                   "reward": 38,  "lv": 2, "desc": "甜，但得有点耐心"},
    "tomato":     {"name": "番茄",   "emoji": "🍅", "cost": 24, "grow": 80,
                   "reward": 46,  "lv": 2, "desc": "菜园里的常青选手"},
    "corn":       {"name": "玉米",   "emoji": "🌽", "cost": 30, "grow": 110,
                   "reward": 58,  "lv": 3, "desc": "一根一根，金黄饱满"},
    "soybean":    {"name": "大豆",   "emoji": "🫘", "cost": 36, "grow": 140,
                   "reward": 70,  "lv": 4, "desc": "扎实耐放，回报稳定"},
    "pepper":     {"name": "辣椒",   "emoji": "🌶️", "cost": 44, "grow": 180,
                   "reward": 88,  "lv": 5, "desc": "有点冲，收益也冲"},
    "pumpkin":    {"name": "南瓜",   "emoji": "🎃", "cost": 52, "grow": 220,
                   "reward": 105, "lv": 6, "desc": "沉甸甸的一大个"},
    "watermelon": {"name": "西瓜",   "emoji": "🍉", "cost": 62, "grow": 280,
                   "reward": 130, "lv": 7, "desc": "夏天最值得等的那一个"},
    "grape":      {"name": "葡萄",   "emoji": "🍇", "cost": 75, "grow": 360,
                   "reward": 165, "lv": 8, "desc": "一串一串，压弯枝头"},
}

TOTAL_SLOTS = 6          # 菜园最多 6 块地
WATER_BOOST = 10         # 每次浇水相当于多长了 10 分钟
MAX_WATER = 12           # 单块地最多浇水次数，防止一次浇爆

# 稀有种子挂在地块上的加成（种子商店兑换所得）
BUFF_LABEL = {
    "rainbow": "🌈 收获 ×2",
    "golden":  "🌟 快熟 40%",
    "melon":   "🍉 收获 +50%",
}
BUFF_MULT = {"rainbow": 2.0, "melon": 1.5}     # 收获能量倍率
GOLDEN_FACTOR = 0.6                             # 黄金稻种：成熟时间打六折


def _now() -> datetime:
    return datetime.now()


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def slots_of(user_id: int) -> int:
    """按等级解锁地块数：Lv1→2 块，之后每 2 级 +1，最多 6 块。"""
    row = db.query_one("SELECT exp FROM users WHERE id=?", (user_id,))
    exp = row["exp"] if row else 0
    lv = db.level_of(exp)["level"]
    return min(TOTAL_SLOTS, 2 + (lv - 1) // 2)


def ensure_plots(user_id: int) -> None:
    """保证该用户有 6 条地块记录（超出的显示时再按等级屏蔽）。"""
    have = {r["slot"] for r in db.query("SELECT slot FROM plots WHERE user_id=?", (user_id,))}
    for i in range(1, TOTAL_SLOTS + 1):
        if i not in have:
            db.execute("INSERT INTO plots(user_id, slot, state) VALUES (?,?,'empty')",
                       (user_id, i))


def _grow_minutes(plot: Dict[str, Any], cfg: Dict[str, Any]) -> float:
    """这块地实际需要的成熟分钟数（含金稻种折扣）。"""
    base = cfg["grow"]
    if plot.get("buff") == "golden":
        return base * GOLDEN_FACTOR
    return base


def _progress(plot: Dict[str, Any]) -> int:
    """生长进度百分比（含浇水加成）。"""
    if plot["state"] != "growing":
        return 0
    cfg = CROPS.get(plot["crop"])
    if not cfg or not plot["planted_at"]:
        return 0
    try:
        planted = datetime.strptime(plot["planted_at"], "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return 0
    minutes = (_now() - planted).total_seconds() / 60.0
    minutes += plot["watered"] * WATER_BOOST
    return min(100, int(minutes * 100 / _grow_minutes(plot, cfg)))


def garden(user_id: int) -> List[Dict[str, Any]]:
    """返回菜园全部地块状态。"""
    ensure_plots(user_id)
    unlocked = slots_of(user_id)
    rows = db.query("SELECT * FROM plots WHERE user_id=? ORDER BY slot", (user_id,))
    out = []
    for r in rows:
        p = dict(r)
        p["locked"] = p["slot"] > unlocked
        prog = _progress(p)
        p["progress"] = prog
        p["ready"] = p["state"] == "growing" and prog >= 100
        cfg = CROPS.get(p["crop"])
        p["crop_name"] = cfg["name"] if cfg else ""
        p["crop_emoji"] = cfg["emoji"] if cfg else ""
        p["buff"] = p.get("buff") or ""
        p["buff_label"] = BUFF_LABEL.get(p["buff"], "")
        if p["state"] == "growing" and cfg:
            left = _grow_minutes(p, cfg) * (100 - prog) / 100
            p["left_text"] = _human_minutes(left)
        else:
            p["left_text"] = ""
        out.append(p)
    return out


def _human_minutes(m: float) -> str:
    m = max(0, int(round(m)))
    if m < 60:
        return f"{m} 分钟"
    h, mm = divmod(m, 60)
    if h < 24:
        return f"{h} 小时 {mm} 分"
    return f"{h // 24} 天 {h % 24} 小时"


def basket(user_id: int) -> List[Dict[str, Any]]:
    rows = db.query("SELECT crop, count FROM harvests WHERE user_id=? AND count>0 "
                    "ORDER BY count DESC", (user_id,))
    out = []
    for r in rows:
        cfg = CROPS.get(r["crop"])
        if not cfg:
            continue
        out.append({"crop": r["crop"], "count": r["count"],
                    "name": cfg["name"], "emoji": cfg["emoji"]})
    return out


def plow(user_id: int, slot: int) -> Dict[str, Any]:
    p = db.query_one("SELECT * FROM plots WHERE user_id=? AND slot=?", (user_id, slot))
    if not p or p["state"] != "empty":
        return {"ok": False, "msg": "这块地现在不能翻"}
    if slot > slots_of(user_id):
        return {"ok": False, "msg": "这块地还没解锁，继续升级吧"}
    if db.energy_of(user_id) < db.ENERGY_PLOW:
        return {"ok": False, "msg": f"能量不足，翻地需要 {db.ENERGY_PLOW} 点"}
    db.add_energy(user_id, -db.ENERGY_PLOW)
    db.execute("UPDATE plots SET state='plowed', crop='', planted_at=NULL, watered=0, "
               "buff=NULL WHERE user_id=? AND slot=?", (user_id, slot))
    return {"ok": True, "msg": "地翻好啦，选个种子种下去吧 🌱",
            "energy": db.energy_of(user_id)}


def rare_options(user_id: int) -> List[Dict[str, Any]]:
    """播种时可选的稀有种子（背包里持有的才出现）。"""
    from . import shop
    return [{"key": s["key"], "name": s["name"], "emoji": s["emoji"],
             "effect": s["effect"]}
            for s in shop.seeds(user_id) if s["own"] > 0]


def plant(user_id: int, slot: int, crop_key: str, seed_key: str = "") -> Dict[str, Any]:
    """播种。seed_key 为空表示普通种子，否则消耗一枚稀有种子挂上加成。"""
    cfg = CROPS.get(crop_key)
    if not cfg:
        return {"ok": False, "msg": "没有这种种子"}
    p = db.query_one("SELECT * FROM plots WHERE user_id=? AND slot=?", (user_id, slot))
    if not p or p["state"] != "plowed":
        return {"ok": False, "msg": "这块地还没翻好"}
    row = db.query_one("SELECT exp FROM users WHERE id=?", (user_id,))
    lv = db.level_of(row["exp"] if row else 0)["level"]
    if lv < cfg["lv"]:
        return {"ok": False, "msg": f"Lv.{cfg['lv']} 才能种{cfg['name']}，继续努力"}
    if db.energy_of(user_id) < cfg["cost"]:
        return {"ok": False, "msg": f"能量不足，{cfg['name']}种子需要 {cfg['cost']} 点"}

    buff = ""
    if seed_key:
        from . import shop
        item = shop.ITEMS.get(seed_key)
        if not item or item["kind"] != "seed":
            return {"ok": False, "msg": "这不是能种下去的种子"}
        if shop.own(user_id, seed_key) <= 0:
            return {"ok": False, "msg": f"背包里没有{item['name']}"}
        buff = item["buff"]

    db.add_energy(user_id, -cfg["cost"])
    if seed_key:
        from . import shop
        shop.consume(user_id, seed_key, 1)
    now = _fmt(_now())
    db.execute("UPDATE plots SET state='growing', crop=?, planted_at=?, watered=0, "
               "buff=? WHERE user_id=? AND slot=?",
               (crop_key, now, buff or None, user_id, slot))
    extra = f"（{BUFF_LABEL.get(buff, '')}）" if buff else ""
    return {"ok": True, "msg": f"{cfg['emoji']} {cfg['name']}种下去啦{extra}，记得浇水～",
            "energy": db.energy_of(user_id), "buff": buff}


def fertilize(user_id: int, slot: int, boost: int) -> Dict[str, Any]:
    """给正在生长的地块追肥：boost=分钟数，>=9999 表示立刻成熟。"""
    p = db.query_one("SELECT * FROM plots WHERE user_id=? AND slot=?", (user_id, slot))
    if not p or p["state"] != "growing":
        return {"ok": False, "msg": "这里没有正在生长的作物"}
    if _progress(p) >= 100:
        return {"ok": False, "msg": "已经熟啦，直接收获就行"}
    cfg = CROPS.get(p["crop"])
    if not cfg:
        return {"ok": False, "msg": "作物数据异常"}
    if boost >= 9999:
        back = _now() - timedelta(minutes=_grow_minutes(p, cfg) + 1)
        db.execute("UPDATE plots SET planted_at=? WHERE user_id=? AND slot=?",
                   (_fmt(back), user_id, slot))
        return {"ok": True, "msg": f"{cfg['emoji']}{cfg['name']}当场熟透，快收获！",
                "energy": db.energy_of(user_id)}
    times = int(round(boost / WATER_BOOST))
    if p["watered"] + times > MAX_WATER:
        return {"ok": False, "msg": "这块地肥力已经到顶啦，换个催熟肥试试"}
    db.execute("UPDATE plots SET watered=watered+? WHERE user_id=? AND slot=?",
               (times, user_id, slot))
    return {"ok": True, "msg": f"{cfg['emoji']}{cfg['name']}猛长了一截（+{boost} 分钟）",
            "energy": db.energy_of(user_id)}


def water(user_id: int, slot: int) -> Dict[str, Any]:
    p = db.query_one("SELECT * FROM plots WHERE user_id=? AND slot=?", (user_id, slot))
    if not p or p["state"] != "growing":
        return {"ok": False, "msg": "这里没有正在生长的作物"}
    if _progress(p) >= 100:
        return {"ok": False, "msg": "已经熟啦，快收获！"}
    if p["watered"] >= MAX_WATER:
        return {"ok": False, "msg": "这块地浇太多啦，会涝的"}
    if db.energy_of(user_id) < db.ENERGY_WATER:
        return {"ok": False, "msg": f"能量不足，浇水需要 {db.ENERGY_WATER} 点"}
    db.add_energy(user_id, -db.ENERGY_WATER)
    db.execute("UPDATE plots SET watered=watered+1 WHERE user_id=? AND slot=?",
               (user_id, slot))
    return {"ok": True, "msg": "浇过水啦，长势喜人 💧",
            "energy": db.energy_of(user_id)}


def harvest(user_id: int, slot: int) -> Dict[str, Any]:
    p = db.query_one("SELECT * FROM plots WHERE user_id=? AND slot=?", (user_id, slot))
    if not p or p["state"] != "growing":
        return {"ok": False, "msg": "这里没有可收获的作物"}
    if _progress(p) < 100:
        return {"ok": False, "msg": "还没熟呢，再等等～"}
    cfg = CROPS.get(p["crop"])
    if not cfg:
        return {"ok": False, "msg": "作物数据异常"}
    buff = p.get("buff") or ""
    db.execute("UPDATE plots SET state='empty', crop='', planted_at=NULL, watered=0, "
               "buff=NULL WHERE user_id=? AND slot=?", (user_id, slot))
    row = db.query_one("SELECT id FROM harvests WHERE user_id=? AND crop=?",
                       (user_id, p["crop"]))
    if row:
        db.execute("UPDATE harvests SET count=count+1 WHERE id=?", (row["id"],))
    else:
        db.execute("INSERT INTO harvests(user_id, crop, count) VALUES (?,?,1)",
                   (user_id, p["crop"]))
    gain = int(round(cfg["reward"] * BUFF_MULT.get(buff, 1.0)))
    energy = db.add_energy(user_id, gain)
    db.execute("INSERT INTO farm_log(user_id, crop, energy, created_at) VALUES (?,?,?,?)",
               (user_id, p["crop"], gain, _fmt(_now())))
    mark = f"（{BUFF_LABEL[buff]}）" if buff in BUFF_LABEL else ""
    return {"ok": True, "msg": f"收获 {cfg['emoji']} {cfg['name']}！能量 +{gain}{mark}",
            "energy": energy, "crop": cfg["name"], "emoji": cfg["emoji"],
            "gain": gain, "crop_key": p["crop"]}


def harvest_all(user_id: int) -> Dict[str, Any]:
    got, total = [], 0
    for p in garden(user_id):
        if p["ready"]:
            r = harvest(user_id, p["slot"])
            if r["ok"]:
                got.append(r["emoji"] + r["crop"])
                total += 1
    if not got:
        return {"ok": False, "msg": "还没有成熟的作物"}
    return {"ok": True, "msg": f"一次性收了 {total} 份：{' '.join(got)}",
            "energy": db.energy_of(user_id), "count": total}


def shop(user_id: int) -> List[Dict[str, Any]]:
    """种子商店：带解锁状态与是否买得起。"""
    row = db.query_one("SELECT exp, energy FROM users WHERE id=?", (user_id,))
    lv = db.level_of(row["exp"] if row else 0)["level"]
    energy = (row["energy"] or 0) if row else 0
    out = []
    for key, c in CROPS.items():
        out.append({
            "key": key, **c,
            "locked": lv < c["lv"],
            "afford": energy >= c["cost"],
        })
    return out


def ready_count(user_id: int) -> int:
    return sum(1 for p in garden(user_id) if p["ready"])
