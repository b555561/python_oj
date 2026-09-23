"""端到端测试：菜园的两条支线 —— 耘野果蔬摊（卖菜→金币→科普）与厨房（做菜→科普→发圈）。"""
import os
import random
import string
import sys

import requests

BASE = "http://127.0.0.1:" + os.environ.get("OJ_PORT", "8001")
OK = FAIL = 0


def check(name, cond, extra=""):
    global OK, FAIL
    if cond:
        OK += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}  {extra}")


def rnd(n=6):
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def main():
    sys.path.insert(0, ".")
    from core import db, market, kitchen, farm

    name = "br_" + rnd()
    s = requests.Session()
    r = s.post(BASE + "/register",
               data={"username": name, "password": "test123456", "nickname": name},
               timeout=15, allow_redirects=False)
    check("注册测试用户", r.status_code in (200, 302, 303), r.status_code)
    uid = db.query_one("SELECT id FROM users WHERE username=?", (name,))["id"]

    print("\n=== 1. 给菜篮塞满收成（造数据） ===")
    for crop, n in [("cabbage", 6), ("tomato", 5), ("rice", 4), ("corn", 3)]:
        row = db.query_one("SELECT id FROM harvests WHERE user_id=? AND crop=?", (uid, crop))
        if row:
            db.execute("UPDATE harvests SET count=? WHERE id=?", (n, row["id"]))
        else:
            db.execute("INSERT INTO harvests(user_id, crop, count) VALUES (?,?,?)",
                       (uid, crop, n))
    check("菜篮有 4 种作物", len(farm.basket(uid)) == 4, farm.basket(uid))

    print("\n=== 2. 果蔬摊页面 ===")
    r = s.get(BASE + "/market", timeout=15)
    check("果蔬摊页可访问", r.status_code == 200, r.status_code)
    check("页面含摊位标题", "耘野果蔬摊" in r.text)
    check("页面含禾籽形象", "hezi" in r.text or "禾籽" in r.text)
    check("页面是卡片布局", "goods-card" in r.text and "price-cell" in r.text)

    print("\n=== 3. 卖菜 → 金币 + 管理/金融科普 ===")
    before = db.coins_of(uid)
    r = s.post(BASE + "/api/market/sell", json={"crop": "tomato", "count": 2}, timeout=15)
    check("卖 2 份番茄", r.json().get("code") == 0, r.text[:160])
    d = r.json()["data"]
    check("金币增加", db.coins_of(uid) > before, f"{before} -> {db.coins_of(uid)}")
    check("返回科普卡", bool(d.get("tip", {}).get("title")), d.get("tip"))
    check("科普卡有分类标签", d["tip"].get("tag") in ("金融", "经济学", "管理学", "营销"),
          d["tip"].get("tag"))
    check("菜篮库存扣减", db.query_one("SELECT count FROM harvests WHERE user_id=? AND crop='tomato'",
                                      (uid,))["count"] == 3)
    check("流水已记录", db.query_one("SELECT COUNT(*) c FROM sales WHERE user_id=?", (uid,))["c"] == 1)

    r = s.post(BASE + "/api/market/sell", json={"crop": "grape", "count": 1}, timeout=15)
    check("卖没有的作物被拒绝", r.json().get("code") != 0)

    r = s.post(BASE + "/api/market/sell-all", json={}, timeout=15)
    check("一键清空菜篮", r.json().get("code") == 0, r.text[:160])
    check("菜篮已清空", len(farm.basket(uid)) == 0, farm.basket(uid))
    check("摊位有累计收入", market.summary(uid)["income"] > 0, market.summary(uid))

    print("\n=== 4. 金币换能量 ===")
    coins_before = db.coins_of(uid)
    energy_before = db.energy_of(uid)
    r = s.post(BASE + "/api/market/exchange", json={"coins": 10}, timeout=15)
    check("兑换成功", r.json().get("code") == 0, r.text[:160])
    check("金币减少", db.coins_of(uid) < coins_before)
    check("能量增加", db.energy_of(uid) > energy_before)
    r = s.post(BASE + "/api/market/exchange", json={"coins": 999999}, timeout=15)
    check("超额兑换被拒绝", r.json().get("code") != 0)

    print("\n=== 5. 厨房页面与菜谱 ===")
    for crop, n in [("cabbage", 4), ("tomato", 4), ("corn", 4)]:
        row = db.query_one("SELECT id FROM harvests WHERE user_id=? AND crop=?", (uid, crop))
        if row:
            db.execute("UPDATE harvests SET count=? WHERE id=?", (n, row["id"]))
        else:
            db.execute("INSERT INTO harvests(user_id, crop, count) VALUES (?,?,?)", (uid, crop, n))
    db.execute("UPDATE users SET exp=1000 WHERE id=?", (uid,))     # Lv.5，解锁大部分菜谱
    r = s.get(BASE + "/kitchen", timeout=15)
    check("厨房页可访问", r.status_code == 200, r.status_code)
    check("页面含菜谱卡片", "recipe" in r.text and "田园沙拉" in r.text)
    check("页面含食材库存", "pantry" in r.text)

    print("\n=== 6. 做菜 → 食品科普 ===")
    r = s.post(BASE + "/api/kitchen/cook", json={"dish": "salad"}, timeout=15)
    check("做田园沙拉", r.json().get("code") == 0, r.text[:200])
    d = r.json()["data"]
    check("返回食品科普", bool(d.get("science", {}).get("title")), d.get("science"))
    check("科普正文非空", len(d["science"].get("body", "")) > 30)
    check("消耗了食材", db.query_one("SELECT count FROM harvests WHERE user_id=? AND crop='cabbage'",
                                    (uid,))["count"] == 3)
    dish_id = d["id"]
    check("菜肴已入库", kitchen.stats(uid)["dishes"] == 1, kitchen.stats(uid))

    r = s.post(BASE + "/api/kitchen/cook", json={"dish": "grapejam"}, timeout=15)
    check("食材不够时拒绝", r.json().get("code") != 0, r.text[:120])

    print("\n=== 7. 发布到学习圈「田园食光」 ===")
    e_before = db.energy_of(uid)
    r = s.post(BASE + "/api/kitchen/publish",
               json={"pid": dish_id, "title": "我的第一道菜", "note": "收获的感觉真好"}, timeout=15)
    check("发布成功", r.json().get("code") == 0, r.text[:200])
    check("能量增加", db.energy_of(uid) > e_before, f"{e_before} -> {db.energy_of(uid)}")
    pid = r.json()["data"]["post_id"]
    r = s.get(BASE + f"/post/{pid}", timeout=15)
    check("帖子页可访问", r.status_code == 200)
    check("帖子含菜名", "田园沙拉" in r.text)
    check("帖子含我的留言", "收获的感觉真好" in r.text)

    r = s.post(BASE + "/api/kitchen/publish", json={"pid": dish_id}, timeout=15)
    check("重复发布被拒绝", r.json().get("code") != 0)

    r = s.get(BASE + "/circle?category=田园食光", timeout=15)
    check("学习圈田园食光分区有该帖", r.status_code == 200 and "我的第一道菜" in r.text)

    print("\n=== 8. 清理 ===")
    for t in ["sales", "dishes", "harvests", "plots", "posts", "checkins", "submissions"]:
        db.execute(f"DELETE FROM {t} WHERE user_id=?", (uid,))
    db.execute("DELETE FROM post_likes WHERE post_id NOT IN (SELECT id FROM posts)")
    db.execute("DELETE FROM post_comments WHERE post_id NOT IN (SELECT id FROM posts)")
    db.execute("DELETE FROM users WHERE id=?", (uid,))
    check("测试数据已清理", db.query_one("SELECT COUNT(*) c FROM users WHERE username=?",
                                         (name,))["c"] == 0)

    print(f"\n结果：通过 {OK} 项，失败 {FAIL} 项")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
