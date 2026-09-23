"""种子商店 —— 用攒下的能量（积分）兑换稀有种子与肥料道具。

两类商品：
    seed 稀有种子：播种时选用，给这一茬作物挂上 buff（多收 / 快熟 / 高回报）
    fert 肥料道具：对正在生长的地块使用，立刻推进生长或直接催熟

兑换消耗能量，稀有种子在播种时扣除，肥料在菜园地块上手动使用。
"""
from datetime import datetime
from typing import Any, Dict, List

from . import db

# ---------- 商品目录 ----------
# kind: seed 稀有种子 / fert 肥料
# buff: 稀有种子对应的地块 buff 键（与 farm.py 约定一致）
ITEMS: Dict[str, Dict[str, Any]] = {
    "seed_rainbow": {
        "name": "七彩番茄种", "emoji": "🌈", "kind": "seed", "price": 130,
        "buff": "rainbow", "effect": "收获能量 ×2",
        "desc": "传说中会变色的番茄，一茬收两份的能量。",
        "tip": "种下后这一茬收获的能量直接翻倍，适合配贵的作物使用。",
    },
    "seed_golden": {
        "name": "黄金稻种", "emoji": "🌟", "kind": "seed", "price": 160,
        "buff": "golden", "effect": "生长时间 −40%",
        "desc": "农学院培育的早熟稻，别人等一天，你等半天。",
        "tip": "对玉米、西瓜这类长周期作物最划算，能省下大把等待时间。",
    },
    "seed_melon": {
        "name": "沙瓤西瓜种", "emoji": "🍉", "kind": "seed", "price": 190,
        "buff": "melon", "effect": "收获能量 +50%",
        "desc": "起沙又甜的大西瓜，收成比普通种子高出一半。",
        "tip": "稳定增益，任何作物都能用，是大赛冲榜的常规武器。",
    },
    "fert_quick": {
        "name": "速长肥", "emoji": "💧", "kind": "fert", "price": 60,
        "boost": 30, "effect": "立刻生长 +30 分钟",
        "desc": "一小袋速效肥，撒下去苗头就窜一截。",
        "tip": "等价于是 3 次浇水，但只花 60 能量，比单独浇水划算。",
    },
    "fert_super": {
        "name": "壮苗肥", "emoji": "🌿", "kind": "fert", "price": 110,
        "boost": 80, "effect": "立刻生长 +80 分钟",
        "desc": "浓缩有机肥，一根藤能顶八次浇水。",
        "tip": "睡前给长周期作物来一包，第二天早上刚好能收。",
    },
    "fert_ripe": {
        "name": "催熟肥", "emoji": "✨", "kind": "fert", "price": 150,
        "boost": 9999, "effect": "立刻成熟",
        "desc": "压箱底的宝贝，撒下去作物当场就能收。",
        "tip": "大赛最后一天冲榜、或者急着做饭缺食材时最好用。",
    },
}

KIND_LABEL = {"seed": "稀有种子", "fert": "肥料道具"}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- 库存 ----------
def own(user_id: int, item_key: str) -> int:
    row = db.query_one("SELECT count FROM items WHERE user_id=? AND item_key=?",
                       (user_id, item_key))
    return (row["count"] or 0) if row else 0


def inventory(user_id: int) -> List[Dict[str, Any]]:
    """只返回持有数量 > 0 的道具。"""
    out = []
    for r in db.query("SELECT item_key, count FROM items WHERE user_id=? AND count>0 "
                      "ORDER BY count DESC", (user_id,)):
        cfg = ITEMS.get(r["item_key"])
        if not cfg:
            continue
        out.append({"key": r["item_key"], "count": r["count"], **cfg})
    return out


def inv_map(user_id: int) -> Dict[str, int]:
    return {r["item_key"]: r["count"] for r in
            db.query("SELECT item_key, count FROM items WHERE user_id=? AND count>0",
                     (user_id,))}


def grant(user_id: int, item_key: str, n: int = 1) -> int:
    """发放道具（奖励、活动用）。返回发放后的持有数。"""
    if item_key not in ITEMS or n <= 0:
        return own(user_id, item_key)
    cur = own(user_id, item_key)
    if cur:
        db.execute("UPDATE items SET count=? WHERE user_id=? AND item_key=?",
                   (cur + n, user_id, item_key))
    else:
        db.execute("INSERT INTO items(user_id, item_key, count) VALUES (?,?,?)",
                   (user_id, item_key, n))
    return cur + n


def consume(user_id: int, item_key: str, n: int = 1) -> bool:
    """消耗道具，库存不足返回 False。"""
    if own(user_id, item_key) < n:
        return False
    db.execute("UPDATE items SET count=count-? WHERE user_id=? AND item_key=?",
               (n, user_id, item_key))
    db.execute("DELETE FROM items WHERE user_id=? AND item_key=? AND count<=0",
               (user_id, item_key))
    return True


# ---------- 商店页面数据 ----------
def catalog(user_id: int) -> List[Dict[str, Any]]:
    """全部商品 + 持有数量 + 是否买得起。"""
    row = db.query_one("SELECT energy FROM users WHERE id=?", (user_id,))
    energy = (row["energy"] or 0) if row else 0
    have = inv_map(user_id)
    out = []
    for key, c in ITEMS.items():
        out.append({"key": key, **c, "own": have.get(key, 0),
                    "afford": energy >= c["price"], "energy": energy})
    return out


def seeds(user_id: int) -> List[Dict[str, Any]]:
    """稀有种子（播种时可选）。"""
    return [i for i in catalog(user_id) if i["kind"] == "seed"]


def ferts(user_id: int) -> List[Dict[str, Any]]:
    """肥料（菜园里对地块使用）。"""
    return [i for i in catalog(user_id) if i["kind"] == "fert"]


# ---------- 兑换 / 使用 ----------
def buy(user_id: int, item_key: str, n: int = 1) -> Dict[str, Any]:
    cfg = ITEMS.get(item_key)
    if not cfg:
        return {"ok": False, "msg": "没有这件商品"}
    n = max(1, min(int(n or 1), 99))
    cost = cfg["price"] * n
    if db.energy_of(user_id) < cost:
        return {"ok": False, "msg": f"能量不够，需要 {cost} 点（当前 {db.energy_of(user_id)}）"}
    db.add_energy(user_id, -cost)
    grant(user_id, item_key, n)
    return {"ok": True, "msg": f"兑换成功：{cfg['emoji']} {cfg['name']} ×{n}",
            "cost": cost, "item": cfg["name"], "emoji": cfg["emoji"],
            "own": own(user_id, item_key), "energy": db.energy_of(user_id)}


def use(user_id: int, item_key: str, slot: int) -> Dict[str, Any]:
    """使用肥料：交给 farm 执行效果，成功后扣库存。"""
    cfg = ITEMS.get(item_key)
    if not cfg:
        return {"ok": False, "msg": "没有这件道具"}
    if cfg["kind"] != "fert":
        return {"ok": False, "msg": f"{cfg['name']}要在播种时选用，不是直接撒的"}
    if own(user_id, item_key) <= 0:
        return {"ok": False, "msg": f"背包里没有{cfg['name']}，先去种子商店兑换"}
    from . import farm                       # 延迟导入，避免与 farm 形成循环依赖
    r = farm.fertilize(user_id, slot, cfg.get("boost", 0))
    if not r["ok"]:
        return r
    consume(user_id, item_key, 1)
    r["msg"] = f"{cfg['emoji']} 用了{cfg['name']}：{r['msg']}"
    r["own"] = own(user_id, item_key)
    return r
