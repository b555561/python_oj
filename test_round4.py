"""端到端测试（第四轮）：轮播 Banner、种子商店、耕耘种菜大赛、新手教程、AI 演示模式。"""
import os
import random
import string
import sys
from datetime import date

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
    from core import db, farm, shop, contest, ai

    name = "r4_" + rnd()
    s = requests.Session()
    r = s.post(BASE + "/register",
               data={"username": name, "password": "test123456", "nickname": name},
               timeout=15, allow_redirects=False)
    check("注册测试用户", r.status_code in (200, 302, 303), r.status_code)
    uid = db.query_one("SELECT id FROM users WHERE username=?", (name,))["id"]
    db.add_energy(uid, 1200)

    print("\n=== 1. 顶部自动轮播 Banner ===")
    r = s.get(BASE + "/", timeout=15)
    check("首页可访问", r.status_code == 200, r.status_code)
    check("含轮播容器", 'id="banner"' in r.text and 'id="bannerTrack"' in r.text)
    check("卡片 A：耕耘种菜大赛", "耕耘种菜大赛" in r.text)
    check("卡片 A 跳转大赛页", 'href="/contest"' in r.text)
    check("卡片 B：网站使用指南", "网站使用指南" in r.text)
    check("卡片 B 跳转教程页", 'href="/guide"' in r.text)
    check("有左右切换箭头", "banner-arrow prev" in r.text and "banner-arrow next" in r.text)
    check("有轮播指示点", "banner-dot" in r.text)
    check("轮播脚本已引入", 'src="/static/js/app.js"' in r.text)
    js = s.get(BASE + "/static/js/app.js", timeout=15).text
    check("脚本含轮播逻辑", "initBanner" in js and "bannerTrack" in js
          and "setInterval" in js and "touchstart" in js)
    for path in ["/guide", "/contest", "/shop", "/farm", "/market", "/kitchen", "/circle", "/ai"]:
        rr = s.get(BASE + path, timeout=15)
        check(f"{path} 也有 Banner", rr.status_code == 200 and 'id="banner"' in rr.text,
              rr.status_code)

    print("\n=== 2. 首页菜园主视觉 + 大按钮 + 种子商店入口 ===")
    check("主视觉 hero 区块", 'class="hero"' in r.text)
    check("菜园地块缩略图", "mini-plot" in r.text)
    check("苗小序形象更大", r.text.count("<svg") >= 2)
    for txt, href in [("我的菜园", "/farm"), ("耘野果蔬摊", "/market"), ("厨房", "/kitchen")]:
        check(f"大按钮：{txt}", f'href="{href}"' in r.text and txt in r.text)
    check("新增种子商店入口", 'href="/shop"' in r.text and "种子商店" in r.text)
    check("首页可直接兑换道具", "buyItem(" in r.text)

    print("\n=== 3. 种子商店页面与兑换 ===")
    r = s.get(BASE + "/shop", timeout=15)
    check("商店页可访问", r.status_code == 200, r.status_code)
    check("卡片式布局", "item-grid" in r.text and "item-card" in r.text)
    for key in shop.ITEMS:
        check(f"含商品 {shop.ITEMS[key]['name']}", shop.ITEMS[key]["name"] in r.text)
    e_before = db.energy_of(uid)
    r = s.post(BASE + "/api/shop/buy", json={"key": "seed_rainbow", "n": 1}, timeout=15)
    check("兑换稀有种子", r.json().get("code") == 0, r.text[:160])
    check("能量被扣除", db.energy_of(uid) == e_before - 130,
          f"{e_before} -> {db.energy_of(uid)}")
    check("背包里有七彩番茄种", shop.own(uid, "seed_rainbow") == 1)
    r = s.post(BASE + "/api/shop/buy", json={"key": "seed_melon", "n": 2}, timeout=15)
    check("可一次兑换多件", r.json().get("code") == 0 and shop.own(uid, "seed_melon") == 2)
    r = s.post(BASE + "/api/shop/buy", json={"key": "not_exist"}, timeout=15)
    check("不存在的商品被拒绝", r.json().get("code") != 0)
    db.execute("UPDATE users SET energy=5 WHERE id=?", (uid,))
    r = s.post(BASE + "/api/shop/buy", json={"key": "fert_quick"}, timeout=15)
    check("能量不足时拒绝", r.json().get("code") != 0)
    db.add_energy(uid, 800)

    print("\n=== 4. 稀有种子播种 + 肥料催熟 + 加倍收获 ===")
    r = s.post(BASE + "/api/farm/plow", json={"pid": 1}, timeout=15)
    check("翻地成功", r.json().get("code") == 0, r.text[:120])
    r = s.post(BASE + "/api/farm/plant",
               json={"pid": 1, "crop": "cabbage", "seed": "seed_rainbow"}, timeout=15)
    check("用稀有种子播种", r.json().get("code") == 0, r.text[:160])
    plot = db.query_one("SELECT * FROM plots WHERE user_id=? AND slot=1", (uid,))
    check("地块挂上 rainbow buff", plot["buff"] == "rainbow", plot.get("buff"))
    check("稀有种子已消耗", shop.own(uid, "seed_rainbow") == 0)
    r = s.post(BASE + "/api/shop/buy", json={"key": "fert_ripe", "n": 1}, timeout=15)
    check("兑换催熟肥", r.json().get("code") == 0)
    r = s.post(BASE + "/api/shop/use", json={"key": "fert_ripe", "pid": 1}, timeout=15)
    check("使用催熟肥", r.json().get("code") == 0, r.text[:160])
    check("催熟肥已消耗", shop.own(uid, "fert_ripe") == 0)
    e_before = db.energy_of(uid)
    r = s.post(BASE + "/api/farm/harvest", json={"pid": 1}, timeout=15)
    check("收获成功", r.json().get("code") == 0, r.text[:160])
    check("稀有种子让收成翻倍", r.json()["data"]["gain"] == 36, r.json()["data"])
    check("能量入账", db.energy_of(uid) == e_before + 36)
    check("收获流水已记录",
          db.query_one("SELECT COUNT(*) c FROM farm_log WHERE user_id=?", (uid,))["c"] == 1)
    r = s.post(BASE + "/api/shop/use", json={"key": "fert_quick", "pid": 1}, timeout=15)
    check("空地施肥被拒绝", r.json().get("code") != 0)

    print("\n=== 5. 耕耘种菜大赛 ===")
    r = s.get(BASE + "/contest", timeout=15)
    check("大赛页可访问", r.status_code == 200, r.status_code)
    season = contest.current()
    check("页面含赛季主题", season["title"] in r.text)
    check("页面含主推作物", season["crop_name"] in r.text)
    check("页面含榜单区块", "board-row" in r.text or "还没有人报名" in r.text)
    check("页面含奖励说明", "赛季奖励" in r.text)
    r = s.post(BASE + "/api/contest/join", json={}, timeout=15)
    check("报名参赛", r.json().get("code") == 0, r.text[:160])
    check("报名记录入库", contest.joined(uid, season["key"]))
    r = s.post(BASE + "/api/contest/join", json={}, timeout=15)
    check("重复报名被拒绝", r.json().get("code") != 0)
    # 造一点战绩：今日打卡 + 主题分类通过一题
    db.execute("INSERT OR IGNORE INTO checkins(user_id, day, created_at) VALUES (?,?,?)",
               (uid, str(date.today()), "2026-01-01 08:00:00"))
    row = db.query_one("SELECT id FROM problems WHERE category=? LIMIT 1", (season["cat"],))
    if row:
        db.execute("INSERT INTO submissions(user_id, problem_id, code, status, passed, total, "
                   "created_at) VALUES (?,?,?,'accepted',1,1,?)",
                   (uid, row["id"], "# ok", date.today().strftime("%Y-%m-%d 10:00:00")))
    sc = contest.score(uid)
    check("学习分已计入", sc["learn"] > 0, sc)
    check("耕耘分已计入", sc["farm"] > 0, sc)
    check("总分为正", sc["total"] > 0, sc)
    check("成长等级已评定", bool(sc["rank_name"]), sc["rank_name"])
    r = s.get(BASE + "/contest", timeout=15)
    check("榜单出现我的名字", name in r.text)
    check("榜单显示分数", str(sc["total"]) in r.text)
    r = s.post(BASE + "/api/contest/claim", json={}, timeout=15)
    check("结算领奖", r.json().get("code") == 0, r.text[:200])
    d = r.json()["data"]
    check("奖励含能量", d["gain"] > 0, d)
    check("奖励含道具", len(d["items"]) > 0, d["items"])
    check("领奖后写入 award", contest.entry(uid, season["key"])["claimed"] == 1)
    r = s.post(BASE + "/api/contest/claim", json={}, timeout=15)
    check("重复领奖被拒绝", r.json().get("code") != 0)

    print("\n=== 6. 新手教程页 ===")
    r = s.get(BASE + "/guide", timeout=15)
    check("教程页可访问", r.status_code == 200, r.status_code)
    check("含卡片式步骤", r.text.count("guide-step") >= 8)
    for kw in ["每日打卡", "刷题", "菜园", "耘野果蔬摊", "厨房", "种子商店", "耕耘种菜大赛"]:
        check(f"教程讲到：{kw}", kw in r.text)

    print("\n=== 7. AI 预设问答演示模式（不调用接口） ===")
    check("当前处于演示模式", ai.is_demo() and not ai.get_api_key())
    check("演示模式下 AI 可用", ai.is_enabled())
    r = s.post(BASE + "/api/ai/chat",
               json={"message": "列表推导式怎么写？", "action": "chat"}, timeout=25)
    check("提问返回结果", r.json().get("code") == 0, r.text[:200])
    check("答案是预设内容", "推导式" in r.json()["data"]["text"],
          r.json()["data"]["text"][:80])
    r = s.post(BASE + "/api/ai/chat", json={"message": "菜园怎么玩？", "action": "chat"}, timeout=25)
    check("菜园问题有预设答案", r.json().get("code") == 0 and "菜园" in r.json()["data"]["text"])
    r = s.post(BASE + "/api/ai/chat", json={"message": "随便乱问一个没收录的问题xyz",
                                            "action": "chat"}, timeout=25)
    check("未收录问题给兜底提示", r.json().get("code") == 0
          and "演示模式" in r.json()["data"]["text"])
    r = s.get(BASE + "/ai", timeout=15)
    check("AI 页标注演示模式", "预设问答演示模式" in r.text)

    print("\n=== 8. 原有功能仍在 ===")
    for path, kw in [("/problems", "题库"), ("/checkin", "打卡"), ("/circle", "学习圈"),
                     ("/market", "耘野果蔬摊"), ("/kitchen", "厨房"), ("/farm", "苗小序的农场"),
                     ("/friends", "好友"), ("/quiz", "测验")]:
        rr = s.get(BASE + path, timeout=15)
        check(f"{path} 正常", rr.status_code == 200 and kw in rr.text, rr.status_code)
    r = s.post(BASE + "/api/checkin", json={}, timeout=15)
    check("打卡接口可用", r.json().get("code") in (0, 1), r.text[:120])

    print("\n=== 9. 清理 ===")
    for t in ["items", "farm_log", "contest_entries", "sales", "dishes", "harvests",
              "plots", "posts", "checkins", "submissions", "wrongs", "favorites"]:
        db.execute(f"DELETE FROM {t} WHERE user_id=?", (uid,))
    db.execute("DELETE FROM post_likes WHERE post_id NOT IN (SELECT id FROM posts)")
    db.execute("DELETE FROM post_comments WHERE post_id NOT IN (SELECT id FROM posts)")
    db.execute("DELETE FROM users WHERE id=?", (uid,))
    check("测试数据已清理",
          db.query_one("SELECT COUNT(*) c FROM users WHERE username=?", (name,))["c"] == 0)

    print(f"\n结果：通过 {OK} 项，失败 {FAIL} 项")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
