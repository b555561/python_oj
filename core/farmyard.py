"""农场 —— 自由建造的 3D 小农场。

设计原则（用户明确要求）：
  * **没有固定建造任务**：不设"必须先造 X 才能造 Y"的顺序，配件买到就能摆。
  * **没有强制升级路线**：配件只按能量定价，不跟等级挂钩（等级只影响价格折扣之外的
    传统菜地玩法），想先买牛羊还是先买栅栏，完全自己说了算。
  * **完全创作自主权**：任意格都能放、能搬、能拆，拆了还退能量对应的库存（配件回到背包）。

能量来源照旧：打卡 / 刷题 / 测验 / 认证 / 学习圈 / 卖菜 / 做菜。
"""
from typing import Any, Dict, List, Optional, Tuple

from core import db

# 地皮边长（格）—— 14×14 = 196 格，够搭一个小村庄
GRID = 14


# ============ 配件目录 ============
# cat：ground 地面 / crop 庄稼 / veg 蔬菜 / fruit 果树 / animal 动物 / build 建筑 / decor 树木装饰
# price：能量；h：方块高度（单位=格）；lift：图标再往上抬多少（单位=格）
# color：方块顶面颜色（侧面自动加深）
CATS: List[Tuple[str, str, str]] = [
    ("ground", "🟩", "地面"),
    ("crop", "🌾", "庄稼"),
    ("veg", "🥬", "蔬菜"),
    ("fruit", "🍎", "果树"),
    ("animal", "🐄", "动物"),
    ("build", "🏠", "建筑"),
    ("decor", "🌳", "树木装饰"),
]

ITEMS: List[Dict[str, Any]] = [
    # ---------- 地面 ----------
    dict(key="grass", name="草皮", cat="ground", price=2, emoji="", color="#7fc86a",
         h=0.10, lift=0, desc="最普通的青草地，打底必备"),
    dict(key="soil", name="耕地", cat="ground", price=2, emoji="", color="#b07f52",
         h=0.10, lift=0, desc="翻好的褐土，种东西都种在它上面"),
    dict(key="path", name="石板路", cat="ground", price=3, emoji="", color="#d6d1c4",
         h=0.08, lift=0, desc="灰白石板，铺一条从门口到井边的小路"),
    dict(key="sand", name="沙地", cat="ground", price=3, emoji="", color="#ecd9a4",
         h=0.08, lift=0, desc="河滩的细沙，围池塘特别搭"),
    dict(key="water", name="小溪", cat="ground", price=8, emoji="💧", color="#57b9ea",
         h=0.04, lift=0.05, desc="浅浅一条活水，鸭子最爱"),
    dict(key="pond", name="池塘", cat="ground", price=12, emoji="🫧", color="#3fa3dd",
         h=0.04, lift=0.05, desc="挖个水塘，边上种芦苇刚刚好"),

    # ---------- 庄稼 ----------
    dict(key="wheat", name="小麦", cat="crop", price=6, emoji="🌾", color="#d9b24c",
         h=0.45, lift=0.10, desc="风吹麦浪，农场的主色调"),
    dict(key="corn", name="玉米", cat="crop", price=8, emoji="🌽", color="#c9a83e",
         h=0.55, lift=0.10, desc="高高的玉米秆，适合当围栏种"),
    dict(key="sunflower", name="向日葵", cat="crop", price=10, emoji="🌻", color="#c8a33c",
         h=0.60, lift=0.10, desc="一排向日葵，整片地都亮了"),
    dict(key="sugarcane", name="甘蔗", cat="crop", price=9, emoji="🎋", color="#8fbf5a",
         h=0.65, lift=0.10, desc="顺着水边种，长得最旺"),
    dict(key="cotton", name="棉花", cat="crop", price=11, emoji="🌼", color="#dfe6c8",
         h=0.40, lift=0.10, desc="白生生一团，看着就软乎"),

    # ---------- 蔬菜 ----------
    dict(key="cabbage", name="白菜", cat="veg", price=5, emoji="🥬", color="#8ccb6b",
         h=0.30, lift=0.10, desc="好养活，新手菜园第一棵"),
    dict(key="carrot", name="胡萝卜", cat="veg", price=6, emoji="🥕", color="#b98a4f",
         h=0.28, lift=0.10, desc="兔子看见了准来偷"),
    dict(key="tomato", name="番茄", cat="veg", price=7, emoji="🍅", color="#9bd06a",
         h=0.42, lift=0.10, desc="搭架子最好看"),
    dict(key="eggplant", name="茄子", cat="veg", price=8, emoji="🍆", color="#8a6fb0",
         h=0.40, lift=0.10, desc="紫得发亮"),
    dict(key="pepper", name="辣椒", cat="veg", price=8, emoji="🌶️", color="#c46a4a",
         h=0.40, lift=0.10, desc="红红火火一小片"),
    dict(key="mushroom", name="蘑菇", cat="veg", price=10, emoji="🍄", color="#c78f6a",
         h=0.25, lift=0.10, desc="种在树荫下最合适"),
    dict(key="pumpkin", name="南瓜", cat="veg", price=12, emoji="🎃", color="#d9963c",
         h=0.35, lift=0.10, desc="秋天的主角，圆滚滚"),

    # ---------- 果树 ----------
    dict(key="apple", name="苹果树", cat="fruit", price=16, emoji="🍎", color="#8a5a3b",
         h=1.10, lift=0.30, desc="农场的招牌果树"),
    dict(key="pear", name="梨树", cat="fruit", price=16, emoji="🍐", color="#8a5a3b",
         h=1.10, lift=0.30, desc="春天一树白花"),
    dict(key="peach", name="桃树", cat="fruit", price=18, emoji="🍑", color="#8a5a3b",
         h=1.05, lift=0.30, desc="桃子熟了满院香"),
    dict(key="cherry", name="樱桃树", cat="fruit", price=20, emoji="🍒", color="#7d5238",
         h=1.15, lift=0.30, desc="红果子一簇一簇"),
    dict(key="watermelon", name="西瓜地", cat="fruit", price=12, emoji="🍉", color="#6fbf63",
         h=0.22, lift=0.10, desc="夏天往树荫下一躺"),
    dict(key="grape", name="葡萄架", cat="fruit", price=18, emoji="🍇", color="#8a6a45",
         h=0.90, lift=0.25, desc="搭成廊道，走过头顶一串串"),

    # ---------- 动物 ----------
    dict(key="chick", name="小鸡", cat="animal", price=10, emoji="🐤", color="#8fd06a",
         h=0.10, lift=0.22, desc="毛茸茸，会跟着你跑"),
    dict(key="duck", name="小鸭", cat="animal", price=12, emoji="🦆", color="#8fd06a",
         h=0.10, lift=0.22, desc="有小溪就有它"),
    dict(key="rabbit", name="小兔", cat="animal", price=14, emoji="🐇", color="#8fd06a",
         h=0.10, lift=0.22, desc="蹲在菜地边啃胡萝卜"),
    dict(key="cat", name="猫", cat="animal", price=14, emoji="🐈", color="#8fd06a",
         h=0.10, lift=0.22, desc="谷仓看粮的一把好手"),
    dict(key="dog", name="看门狗", cat="animal", price=16, emoji="🐕", color="#8fd06a",
         h=0.10, lift=0.24, desc="守着院门，谁来都先叫两声"),
    dict(key="sheep", name="绵羊", cat="animal", price=18, emoji="🐑", color="#8fd06a",
         h=0.10, lift=0.28, desc="一团云在草地上飘"),
    dict(key="pig", name="小猪", cat="animal", price=18, emoji="🐖", color="#8fd06a",
         h=0.10, lift=0.26, desc="吃饱就睡，农场吉祥物"),
    dict(key="cow", name="奶牛", cat="animal", price=22, emoji="🐄", color="#8fd06a",
         h=0.10, lift=0.32, desc="黑白花，牧场不能少"),
    dict(key="horse", name="马", cat="animal", price=26, emoji="🐴", color="#8fd06a",
         h=0.10, lift=0.34, desc="沿栅栏跑一圈特别神气"),

    # ---------- 建筑 ----------
    dict(key="fence", name="木栅栏", cat="build", price=4, emoji="🪵", color="#b98a58",
         h=0.45, lift=0.05, desc="围院子、分菜地都靠它"),
    dict(key="stonewall", name="石墙", cat="build", price=5, emoji="🧱", color="#b3ada2",
         h=0.55, lift=0.05, desc="矮矮一圈，隔开牧场"),
    dict(key="gate", name="院门", cat="build", price=8, emoji="🚪", color="#a87a4a",
         h=0.60, lift=0.10, desc="留个门，别把自己关外面"),
    dict(key="well", name="水井", cat="build", price=20, emoji="🪣", color="#a9a49a",
         h=0.70, lift=0.12, desc="院子中心挖口井"),
    dict(key="coop", name="鸡舍", cat="build", price=25, emoji="🐓", color="#c09355",
         h=0.85, lift=0.15, desc="小鸡们的家"),
    dict(key="house", name="小木屋", cat="build", price=30, emoji="🏠", color="#e6d5b8",
         h=1.30, lift=0.18, desc="农场主自己的屋子"),
    dict(key="barn", name="谷仓", cat="build", price=40, emoji="🛖", color="#c05f45",
         h=1.50, lift=0.20, desc="存粮放农具，红色最经典"),
    dict(key="windmill", name="风车", cat="build", price=45, emoji="🌀", color="#e0d7c3",
         h=1.80, lift=0.25, desc="转起来整座农场都活了"),
    dict(key="tower", name="瞭望塔", cat="build", price=35, emoji="🗼", color="#c3a878",
         h=2.00, lift=0.22, desc="站高处看自己搭的农场"),
    dict(key="bridge", name="小木桥", cat="build", price=15, emoji="🌉", color="#bb8c58",
         h=0.18, lift=0.06, desc="架在小溪上"),

    # ---------- 树木与装饰 ----------
    dict(key="oak", name="橡树", cat="decor", price=12, emoji="🌳", color="#7a5236",
         h=1.20, lift=0.30, desc="最结实的大树"),
    dict(key="pine", name="松树", cat="decor", price=12, emoji="🌲", color="#6d4c34",
         h=1.30, lift=0.30, desc="四季常青"),
    dict(key="sakura", name="樱花树", cat="decor", price=22, emoji="🌸", color="#8a5f42",
         h=1.15, lift=0.30, desc="一阵风一场花雨"),
    dict(key="bush", name="灌木丛", cat="decor", price=6, emoji="🪴", color="#6fae5c",
         h=0.35, lift=0.08, desc="填边角最好用"),
    dict(key="flower", name="花丛", cat="decor", price=7, emoji="🌷", color="#79c06a",
         h=0.22, lift=0.10, desc="门口种一排"),
    dict(key="reed", name="芦苇", cat="decor", price=6, emoji="🍂", color="#c2a86a",
         h=0.45, lift=0.10, desc="水边的标配"),
    dict(key="hay", name="干草堆", cat="decor", price=9, emoji="🟨", color="#dcc274",
         h=0.50, lift=0.05, desc="牧场边上摞一堆"),
    dict(key="rock", name="石头", cat="decor", price=3, emoji="🪨", color="#a9a49a",
         h=0.30, lift=0.05, desc="最便宜的点缀"),
    dict(key="lamp", name="路灯", cat="decor", price=10, emoji="💡", color="#8f8b83",
         h=0.95, lift=0.25, desc="天黑了农场也亮着"),
    dict(key="bench", name="长椅", cat="decor", price=12, emoji="🪑", color="#b98a58",
         h=0.30, lift=0.10, desc="坐下来看看自己的地"),
]

ITEM_MAP: Dict[str, Dict[str, Any]] = {it["key"]: it for it in ITEMS}

# 新农场开业礼：够搭一个小院子的起步量（送的是库存，不是"任务奖励"，随便怎么摆）
STARTER = [("grass", 12), ("fence", 10), ("oak", 2), ("chick", 1), ("house", 1)]


def _in_grid(x: int, y: int) -> bool:
    return 0 <= x < GRID and 0 <= y < GRID


# ============ 库存 ============
def _own(user_id: int, key: str) -> int:
    row = db.query_one("SELECT qty FROM farm_own WHERE user_id=? AND item_key=?", (user_id, key))
    return int(row["qty"]) if row else 0


def owned(user_id: int) -> Dict[str, int]:
    rows = db.query("SELECT item_key, qty FROM farm_own WHERE user_id=?", (user_id,))
    return {r["item_key"]: int(r["qty"]) for r in rows if int(r["qty"]) > 0}


def _add_own(user_id: int, key: str, delta: int) -> None:
    cur = _own(user_id, key)
    new = max(0, cur + delta)
    db.execute(
        "INSERT INTO farm_own(user_id,item_key,qty) VALUES(?,?,?) "
        "ON CONFLICT(user_id,item_key) DO UPDATE SET qty=?",
        (user_id, key, new, new))


def ensure(user_id: int) -> None:
    """第一次进农场发开业礼；已经领过（有任何记录）就不再发。"""
    if db.query_one("SELECT 1 FROM farm_own WHERE user_id=? LIMIT 1", (user_id,)):
        return
    for key, n in STARTER:
        _add_own(user_id, key, n)


# ============ 目录 / 地皮 ============
def catalog(user_id: int) -> List[Dict[str, Any]]:
    """按分类分组的配件目录，带上「已拥有」数量。没有任何门槛。"""
    own = owned(user_id)
    energy = db.energy_of(user_id)
    groups = []
    for key, icon, name in CATS:
        items = []
        for it in ITEMS:
            if it["cat"] != key:
                continue
            d = dict(it)
            d["own"] = own.get(it["key"], 0)
            d["afford"] = energy >= it["price"]
            items.append(d)
        groups.append({"key": key, "icon": icon, "name": name, "items": items})
    return groups


def board(user_id: int) -> List[Dict[str, Any]]:
    rows = db.query("SELECT x,y,item_key FROM farm_decor WHERE user_id=? ORDER BY y,x", (user_id,))
    out = []
    for r in rows:
        it = ITEM_MAP.get(r["item_key"])
        out.append({
            "x": int(r["x"]), "y": int(r["y"]), "key": r["item_key"],
            "name": it["name"] if it else r["item_key"],
            "emoji": it["emoji"] if it else "",
        })
    return out


def summary(user_id: int) -> Dict[str, int]:
    """只是给页面显示用的统计，不做任何门槛判断。"""
    rows = board(user_id)
    kinds = len({r["key"] for r in rows})
    return {"placed": len(rows), "kinds": kinds, "total": GRID * GRID,
            "own_kinds": len(owned(user_id))}


# ============ 操作：买 / 摆 / 搬 / 拆 ============
def buy(user_id: int, key: str, n: int = 1) -> Dict[str, Any]:
    it = ITEM_MAP.get(key)
    if not it:
        return {"ok": False, "msg": "没有这种配件"}
    n = max(1, min(int(n or 1), 20))
    cost = it["price"] * n
    if db.energy_of(user_id) < cost:
        return {"ok": False, "msg": f"能量不够，{it['name']}要 ⚡{cost}（现有 ⚡{db.energy_of(user_id)}）"}
    db.add_energy(user_id, -cost)
    _add_own(user_id, key, n)
    return {"ok": True, "msg": f"买好啦：{it['name']} ×{n}",
            "energy": db.energy_of(user_id), "qty": _own(user_id, key), "cost": cost}


def place(user_id: int, x: int, y: int, key: str) -> Dict[str, Any]:
    it = ITEM_MAP.get(key)
    if not it:
        return {"ok": False, "msg": "没有这种配件"}
    if not _in_grid(x, y):
        return {"ok": False, "msg": "超出地皮范围"}
    if _own(user_id, key) <= 0:
        return {"ok": False, "msg": f"背包里没有{it['name']}了，先去侧边栏买一个"}
    taken = db.query_one("SELECT 1 FROM farm_decor WHERE user_id=? AND x=? AND y=?", (user_id, x, y))
    if taken:
        return {"ok": False, "msg": "这格已经有东西了"}
    _add_own(user_id, key, -1)
    db.execute("INSERT INTO farm_decor(user_id,x,y,item_key) VALUES(?,?,?,?)",
               (user_id, x, y, key))
    return {"ok": True, "msg": f"{it['emoji']} {it['name']} 摆好啦", "qty": _own(user_id, key)}


def move(user_id: int, fx: int, fy: int, tx: int, ty: int) -> Dict[str, Any]:
    if not (_in_grid(fx, fy) and _in_grid(tx, ty)):
        return {"ok": False, "msg": "超出地皮范围"}
    if (fx, fy) == (tx, ty):
        return {"ok": True, "msg": "没挪窝", "item": None}
    src = db.query_one("SELECT item_key FROM farm_decor WHERE user_id=? AND x=? AND y=?",
                       (user_id, fx, fy))
    if not src:
        return {"ok": False, "msg": "这里本来就是空的"}
    dst = db.query_one("SELECT item_key FROM farm_decor WHERE user_id=? AND x=? AND y=?",
                       (user_id, tx, ty))
    if dst:
        # 两格都有东西 → 直接对调，不用玩家先拆一个
        db.execute("UPDATE farm_decor SET x=?, y=? WHERE user_id=? AND x=? AND y=?",
                   (-1, -1, user_id, fx, fy))
        db.execute("UPDATE farm_decor SET x=?, y=? WHERE user_id=? AND x=? AND y=?",
                   (fx, fy, user_id, tx, ty))
        db.execute("UPDATE farm_decor SET x=?, y=? WHERE user_id=? AND x=? AND y=?",
                   (tx, ty, user_id, -1, -1))
        a = ITEM_MAP.get(src["item_key"], {}).get("name", "")
        b = ITEM_MAP.get(dst["item_key"], {}).get("name", "")
        return {"ok": True, "msg": f"{a} 和 {b} 换了个位置", "swap": True}
    db.execute("UPDATE farm_decor SET x=?, y=? WHERE user_id=? AND x=? AND y=?",
               (tx, ty, user_id, fx, fy))
    name = ITEM_MAP.get(src["item_key"], {}).get("name", "")
    return {"ok": True, "msg": f"{name} 搬好了", "swap": False}


def remove(user_id: int, x: int, y: int) -> Dict[str, Any]:
    if not _in_grid(x, y):
        return {"ok": False, "msg": "超出地皮范围"}
    row = db.query_one("SELECT item_key FROM farm_decor WHERE user_id=? AND x=? AND y=?",
                       (user_id, x, y))
    if not row:
        return {"ok": False, "msg": "这里本来就是空的"}
    db.execute("DELETE FROM farm_decor WHERE user_id=? AND x=? AND y=?", (user_id, x, y))
    _add_own(user_id, row["item_key"], 1)
    it = ITEM_MAP.get(row["item_key"], {})
    return {"ok": True, "msg": f"拆掉{it.get('name','')}，收回背包",
            "qty": _own(user_id, row["item_key"])}


def clear(user_id: int) -> Dict[str, Any]:
    """整块地清空，配件全部退回背包（一键重来，不做任何惩罚）。"""
    rows = db.query("SELECT item_key FROM farm_decor WHERE user_id=?", (user_id,))
    for r in rows:
        _add_own(user_id, r["item_key"], 1)
    db.execute("DELETE FROM farm_decor WHERE user_id=?", (user_id,))
    return {"ok": True, "msg": f"地皮清空了，{len(rows)} 个配件都回到背包", "n": len(rows)}
