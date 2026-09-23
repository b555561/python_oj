"""厨房 —— 菜园收获的第二条出路：把菜做成菜肴，学点食品科学，再发布到学习圈换能量。

流程：
    菜篮 --(按菜谱消耗食材)--> 菜肴作品 + 一张食品科普卡
    菜肴 --(发布到学习圈「田园食光」)--> 能量（菜谱越高级给得越多）
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from . import circle, db
from .farm import CROPS

# ---------- 菜谱 ----------
# need: 需要的食材 | energy: 发布到学习圈可获得的能量 | lv: 解锁等级
RECIPES: Dict[str, Dict[str, Any]] = {
    "greens": {
        "name": "清炒小白菜", "emoji": "🥬", "lv": 1,
        "need": {"cabbage": 2}, "energy": 40,
        "desc": "最朴素的一道家常菜，火候是全部秘诀",
        "science": {"title": "叶菜为什么要大火快炒？",
                    "body": "小白菜富含维生素 C 和叶酸，而维生素 C 既怕热又溶于水。\n"
                            "加热时间越长损失越大，所以「大火快炒 1 分钟」比小火慢炖保留得更多；\n"
                            "另外要「先洗后切」，切后再洗会让断面里的水溶性维生素顺着水流走。"},
    },
    "ricebowl": {
        "name": "糙米焖饭", "emoji": "🍚", "lv": 1,
        "need": {"rice": 2}, "energy": 44,
        "desc": "留着胚芽的一碗饭，嚼起来有谷物香",
        "science": {"title": "糙米和白米的差别在哪？",
                    "body": "稻谷去掉谷壳是糙米，再磨掉胚芽和糊粉层才变成白米。\n"
                            "B 族维生素、矿物质和膳食纤维大多集中在被磨掉的那部分，\n"
                            "所以糙米营养密度远高于白米。缺点是吸水慢 —— 提前浸泡 1 小时再煮，口感会好很多。"},
    },
    "smoothie": {
        "name": "草莓奶昔", "emoji": "🥤", "lv": 2,
        "need": {"strawberry": 3}, "energy": 60,
        "desc": "甜，但不腻，打好后要尽快喝掉",
        "science": {"title": "果汁为什么要现打现喝？",
                    "body": "草莓的维生素 C 含量很高（约 60 mg/100 g，比橙子还多一点）。\n"
                            "但打碎之后细胞破碎、与空气接触面积暴增，维生素 C 会被快速氧化。\n"
                            "所以鲜榨果汁放得越久，营养损失越多 —— 尽快喝掉才是正解。"},
    },
    "tomegg": {
        "name": "番茄炒蛋", "emoji": "🍳", "lv": 2,
        "need": {"tomato": 3}, "energy": 72,
        "desc": "国民下饭菜，也是脂溶性营养的教科书",
        "science": {"title": "番茄为什么要放油炒？",
                    "body": "番茄的红色来自番茄红素，它是一种脂溶性类胡萝卜素 —— 只溶于油脂，不溶于水。\n"
                            "加一点油炒、并且把番茄煮软（破坏细胞壁），番茄红素的吸收率会比生吃高好几倍。\n"
                            "这就是「有些菜必须带油做」的科学依据。"},
    },
    "cornsoup": {
        "name": "玉米浓汤", "emoji": "🌽", "lv": 3,
        "need": {"corn": 3}, "energy": 90,
        "desc": "金黄浓稠，冷天喝一碗最舒服",
        "science": {"title": "玉米的黄色是什么？",
                    "body": "玉米的黄色主要来自叶黄素和玉米黄素，它们同样属于脂溶性类胡萝卜素。\n"
                            "研究发现这两种色素会富集在视网膜黄斑区，帮助过滤蓝光。\n"
                            "做汤时加少量油脂（比如一点奶油），能显著提高它们的吸收率。"},
    },
    "soymilk": {
        "name": "现磨豆浆", "emoji": "🥛", "lv": 4,
        "need": {"soybean": 3}, "energy": 105,
        "desc": "看起来简单，最讲究「煮透」二字",
        "science": {"title": "豆浆为什么会「假沸」？",
                    "body": "生大豆中含有胰蛋白酶抑制剂和皂苷，不彻底加热会让人恶心、腹泻。\n"
                            "麻烦的是豆浆在 80 ℃ 左右就会因皂苷产生大量泡沫，看起来像开了，其实没熟 —— 这叫「假沸」。\n"
                            "正确做法是出现泡沫后转小火继续煮 5~10 分钟，直到泡沫消失、真正沸腾。"},
    },
    "pepperdish": {
        "name": "虎皮青椒", "emoji": "🌶️", "lv": 5,
        "need": {"pepper": 3}, "energy": 130,
        "desc": "表皮起皱起泡，辣得通透",
        "science": {"title": "为什么喝水不解辣？",
                    "body": "辣不是味觉，是痛觉：辣椒素会激活口腔里的 TRPV1 受体，而这个受体本来是感受高温的。\n"
                            "辣椒素不溶于水，却溶于油脂和酒精 —— 所以喝水只会把辣味摊开，\n"
                            "含脂肪的牛奶、酸奶才是真正的解辣高手。"},
    },
    "pumpkinpie": {
        "name": "南瓜饼", "emoji": "🥮", "lv": 6,
        "need": {"pumpkin": 3}, "energy": 155,
        "desc": "外脆里糯，橙黄的颜色很有食欲",
        "science": {"title": "南瓜的颜色从哪来？",
                    "body": "南瓜的橙黄色来自 β-胡萝卜素，它在人体内可以转化成维生素 A，对视力与黏膜健康很重要。\n"
                            "β-胡萝卜素同样是脂溶性的，所以南瓜和油脂一起吃吸收更好。\n"
                            "不过油炸会大幅提高能量密度 —— 想吃得更健康，可以改成少油煎或蒸后压泥。"},
    },
    "iceslush": {
        "name": "西瓜冰沙", "emoji": "🍧", "lv": 7,
        "need": {"watermelon": 3}, "energy": 190,
        "desc": "夏天的救赎，冰晶越细口感越好",
        "science": {"title": "冰沙的口感由什么决定？",
                    "body": "西瓜 90% 以上是水，含糖量约 6%~8%，这也是它吃起来甜却不腻的原因。\n"
                            "冰沙好不好吃，关键在冰晶大小：冻结越慢，冰晶越粗，口感越像嚼碎冰；\n"
                            "糖和果肉中的可溶性固形物能抑制冰晶长大，所以糖度合适的水果打出来更细腻。"},
    },
    "grapejam": {
        "name": "葡萄果酱", "emoji": "🫙", "lv": 8,
        "need": {"grape": 3}, "energy": 230,
        "desc": "熬一罐能放很久，是最古老的保存智慧",
        "science": {"title": "果酱为什么会凝固？",
                    "body": "果酱的凝胶需要三个条件同时满足：果胶、糖、酸。\n"
                            "果胶在酸性、高糖环境下才能形成网络把水锁住；\n"
                            "葡萄本身果胶偏少，所以常要额外加果胶或柠檬汁。\n"
                            "而高糖高酸的环境本身就抑制微生物生长 —— 这就是罐头的保存原理。"},
    },
    "salad": {
        "name": "田园沙拉", "emoji": "🥗", "lv": 3,
        "need": {"cabbage": 1, "tomato": 1, "corn": 1}, "energy": 100,
        "desc": "三种颜色，一口吃到整块地",
        "science": {"title": "生吃一定更营养吗？",
                    "body": "生食确实能最大化保留热敏性维生素（比如维生素 C、叶酸），\n"
                            "但类胡萝卜素（β-胡萝卜素、番茄红素）反而在加热+油脂后吸收率更高。\n"
                            "所以没有绝对的「生吃更好」—— 生熟搭配才是正解。另外生食要注意清洗与生熟分开，避免交叉污染。"},
    },
    "stirfry": {
        "name": "时蔬小炒", "emoji": "🍛", "lv": 4,
        "need": {"tomato": 1, "pepper": 1, "cabbage": 1}, "energy": 120,
        "desc": "一锅三色，下锅顺序有讲究",
        "science": {"title": "为什么炒菜要分先后下锅？",
                    "body": "不同蔬菜的最佳熟度不一样：质地密实的根茎类需要更长时间，叶菜十几秒就够。\n"
                            "一起下锅的结果往往是「根茎还夹生、叶菜已经黄了」。\n"
                            "按「难熟的先下、易熟的后下」排队，既能兼顾口感，也减少了总加热时间，营养损失更少。"},
    },
    "hotpot": {
        "name": "丰收大烩菜", "emoji": "🍲", "lv": 5,
        "need": {"rice": 1, "soybean": 1, "pumpkin": 1, "corn": 1}, "energy": 210,
        "desc": "把整块地的收成都炖进一锅",
        "science": {"title": "为什么「谷物+豆类」是黄金搭配？",
                    "body": "人体需要 8 种必需氨基酸，而单一食物的氨基酸组成往往有短板：\n"
                            "谷类缺赖氨酸，豆类缺蛋氨酸。两者一起吃，短板互相补上，蛋白质的利用率大幅提升，\n"
                            "这叫「蛋白质互补」。米饭配豆腐、玉米配大豆，都是这个道理。"},
    },
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _lv_of(user_id: int) -> int:
    row = db.query_one("SELECT exp FROM users WHERE id=?", (user_id,))
    return db.level_of(row["exp"] if row else 0)["level"]


def pantry(user_id: int) -> Dict[str, int]:
    """菜篮里各作物还剩多少（做菜消耗的原料）。"""
    out = {}
    for r in db.query("SELECT crop, count FROM harvests WHERE user_id=?", (user_id,)):
        out[r["crop"]] = r["count"]
    return out


def recipes(user_id: int) -> List[Dict[str, Any]]:
    """菜谱卡片：带解锁状态、食材是否够、缺什么。"""
    have = pantry(user_id)
    lv = _lv_of(user_id)
    out = []
    for key, r in RECIPES.items():
        need = r["need"]
        miss = {c: n - have.get(c, 0) for c, n in need.items() if have.get(c, 0) < n}
        out.append({
            "key": key, **r,
            "locked": lv < r["lv"],
            "can": not miss,
            "miss": miss,
            "need_list": [{"crop": c, "count": n, "name": CROPS[c]["name"],
                           "emoji": CROPS[c]["emoji"], "have": have.get(c, 0)}
                          for c, n in need.items()],
        })
    return out


def cook(user_id: int, dish_key: str) -> Dict[str, Any]:
    r = RECIPES.get(dish_key)
    if not r:
        return {"ok": False, "msg": "没有这道菜谱"}
    if _lv_of(user_id) < r["lv"]:
        return {"ok": False, "msg": f"Lv.{r['lv']} 才能做{r['name']}，再升两级吧"}
    have = pantry(user_id)
    for c, n in r["need"].items():
        if have.get(c, 0) < n:
            return {"ok": False, "msg": f"{CROPS[c]['name']}不够，还差 {n - have.get(c, 0)} 份"}
    for c, n in r["need"].items():
        row = db.query_one("SELECT id FROM harvests WHERE user_id=? AND crop=?", (user_id, c))
        db.execute("UPDATE harvests SET count=count-? WHERE id=?", (n, row["id"]))
    did = db.execute(
        "INSERT INTO dishes(user_id, dish_key, name, emoji, score, energy, post_id, created_at) "
        "VALUES (?,?,?,?,?,?,0,?)",
        (user_id, dish_key, r["name"], r["emoji"], r["energy"], r["energy"], _now()))
    return {"ok": True, "msg": f"{r['emoji']} {r['name']}做好啦！发布到学习圈可换 {r['energy']} 点能量",
            "id": did, "name": r["name"], "emoji": r["emoji"], "key": dish_key,
            "energy": r["energy"], "science": r["science"]}


def my_dishes(user_id: int, limit: int = 24) -> List[Dict[str, Any]]:
    rows = db.query("SELECT * FROM dishes WHERE user_id=? ORDER BY id DESC LIMIT ?",
                    (user_id, limit))
    for d in rows:
        r = RECIPES.get(d["dish_key"], {})
        d["desc"] = r.get("desc", "")
        d["time"] = d["created_at"][5:16]
        d["published"] = bool(d["post_id"])
    return rows


def dish_by_id(dish_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    row = db.query_one("SELECT * FROM dishes WHERE id=? AND user_id=?", (dish_id, user_id))
    if not row:
        return None
    row["recipe"] = RECIPES.get(row["dish_key"], {})
    return row


def publish(user_id: int, dish_id: int, title: str = "", note: str = "") -> Dict[str, Any]:
    """把菜肴作品发布到学习圈「田园食光」，换取能量。每道菜只能发布一次。"""
    d = dish_by_id(dish_id, user_id)
    if not d:
        return {"ok": False, "msg": "找不到这道菜"}
    if d["post_id"]:
        return {"ok": False, "msg": "这道菜已经发布过啦"}
    r = d["recipe"]
    title = (title or "").strip() or f"{d['emoji']} 我的作品：{d['name']}"
    need_text = "、".join(f"{CROPS[c]['name']}×{n}" for c, n in r.get("need", {}).items())
    body = (
        f"🍽️ 作品：{d['name']}\n"
        f"🧺 用了：{need_text}\n"
        f"✨ 发布奖励：{d['energy']} 点能量\n\n"
        f"📖 做菜时学到的：\n{r.get('science', {}).get('title', '')}\n"
        f"{r.get('science', {}).get('body', '')}\n"
    )
    if (note or "").strip():
        body += f"\n💬 我想说：\n{note.strip()}\n"
    body += "\n—— 用菜园的收成做的，记录一下 🌾"
    res = circle.create_post(user_id, title, body, "田园食光")
    if not res["ok"]:
        return res
    db.execute("UPDATE dishes SET post_id=? WHERE id=?", (res["id"], dish_id))
    e = db.add_energy(user_id, d["energy"])
    return {"ok": True, "msg": f"已发布到学习圈，能量 +{d['energy']}",
            "post_id": res["id"], "energy": e, "gained": d["energy"]}


def stats(user_id: int) -> Dict[str, int]:
    n = db.query_one("SELECT COUNT(*) AS c FROM dishes WHERE user_id=?", (user_id,))["c"]
    pub = db.query_one("SELECT COUNT(*) AS c FROM dishes WHERE user_id=? AND post_id>0",
                       (user_id,))["c"]
    return {"dishes": n, "published": pub}
