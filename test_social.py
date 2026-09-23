"""端到端测试：好友邀请 / 学习小队 / 能量菜园 / 学习圈。"""
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


def reg(s, name):
    r = s.post(BASE + "/register",
               data={"username": name, "password": "test123456", "nickname": name},
               timeout=15, allow_redirects=False)
    return r


def main():
    a = "ta_" + rnd()
    b = "tb_" + rnd()
    sa, sb = requests.Session(), requests.Session()

    print("=== 1. 注册两个用户 ===")
    ra = reg(sa, a)
    rb = reg(sb, b)
    check("用户A注册", ra.status_code in (200, 302, 303), ra.status_code)
    check("用户B注册", rb.status_code in (200, 302, 303), rb.status_code)
    check("A 已登录（可访问首页）", sa.get(BASE + "/me", timeout=10).status_code == 200)

    print("\n=== 2. 邀请码与好友 ===")
    r = sa.post(BASE + "/api/invite/mine", json={}, timeout=10)
    check("获取我的邀请码", r.json().get("code") == 0, r.text[:120])
    code_a = r.json()["data"]["code"]
    check("邀请码为 8 位", len(code_a) == 8, code_a)

    r = sb.post(BASE + "/api/friend/add", json={"code": code_a}, timeout=10)
    check("B 用邀请码加 A 为好友", r.json().get("code") == 0, r.text[:120])

    r = sa.get(BASE + "/friends", timeout=10)
    check("好友页可访问", r.status_code == 200)
    check("好友页出现对方昵称", b in r.text, "未找到 " + b)

    r = sa.post(BASE + "/api/friend/add", json={"code": code_a}, timeout=10)
    check("重复添加被拒绝", r.json().get("code") != 0)

    print("\n=== 3. 邀请链接注册自动成为好友 ===")
    c = "tc_" + rnd()
    sc = requests.Session()
    r = sc.post(BASE + "/register",
                data={"username": c, "password": "test123456",
                      "nickname": c, "invite": code_a},
                timeout=15, allow_redirects=False)
    check("带邀请码注册成功", r.status_code in (200, 302, 303), r.status_code)
    r = sa.get(BASE + "/friends", timeout=10)
    check("新用户自动成为 A 的好友", c in r.text)

    print("\n=== 4. 学习小队 ===")
    r = sa.post(BASE + "/api/team/create", json={"name": "早八刷题组", "slogan": "一起冲"},
                timeout=10)
    check("创建小队", r.json().get("code") == 0, r.text[:120])
    tcode = r.json()["data"]["code"]
    tid = r.json()["data"]["id"]
    r = sb.post(BASE + "/api/team/join", json={"code": tcode}, timeout=10)
    check("B 加入小队", r.json().get("code") == 0, r.text[:120])
    r = sa.get(BASE + f"/team/{tid}", timeout=10)
    check("小队页可访问", r.status_code == 200)
    check("小队页显示成员 B", b in r.text)
    r = sa.post(BASE + "/api/team/invite", json={"pid": tid, "code": "999999"}, timeout=10)
    check("邀请非好友被拒绝", r.json().get("code") != 0)

    print("\n=== 5. 打卡与能量 ===")
    r = sa.post(BASE + "/api/checkin", json={}, timeout=10)
    check("A 打卡成功", r.json().get("code") == 0, r.text[:120])
    check("打卡发放 10 能量", r.json()["data"].get("e_gain") == 10, r.json()["data"])
    e1 = r.json()["data"]["energy"]
    r = sa.post(BASE + "/api/checkin", json={}, timeout=10)
    check("重复打卡被拒绝", r.json().get("code") != 0)

    print("\n=== 6. 菜园：翻地 → 播种 → 浇水 → 收获 ===")
    sys.path.insert(0, ".")
    from core import db
    uid = db.query_one("SELECT id FROM users WHERE username=?", (a,))["id"]
    db.execute("UPDATE users SET energy=200 WHERE id=?", (uid,))

    r = sa.get(BASE + "/farm", timeout=10)
    check("菜园页可访问", r.status_code == 200)
    check("菜园页显示苗小序形象", "nan" in r.text and "svg" in r.text)

    r = sa.post(BASE + "/api/farm/plow", json={"pid": 1}, timeout=10)
    check("1 号地翻地成功", r.json().get("code") == 0, r.text[:120])
    check("翻地扣 5 能量", r.json()["data"]["energy"] == 195, r.json()["data"])

    r = sa.post(BASE + "/api/farm/plant", json={"pid": 1, "code": "cabbage"}, timeout=10)
    check("播种小白菜", r.json().get("code") == 0, r.text[:120])

    r = sa.post(BASE + "/api/farm/water", json={"pid": 1}, timeout=10)
    check("浇水成功", r.json().get("code") == 0, r.text[:120])

    r = sa.post(BASE + "/api/farm/harvest", json={"pid": 1}, timeout=10)
    check("未成熟收获被拒", r.json().get("code") != 0)

    # 把播种时间往前挪，模拟已经长熟
    db.execute("UPDATE plots SET planted_at='2020-01-01 00:00:00' WHERE user_id=? AND slot=1",
               (uid,))
    r = sa.post(BASE + "/api/farm/harvest", json={"pid": 1}, timeout=10)
    check("成熟后收获成功", r.json().get("code") == 0, r.text[:120])
    check("收获返还能量（净 +18）", r.json()["data"]["energy"] == 195 - 8 - 10 + 18,
          r.json()["data"])

    r = sa.get(BASE + "/farm", timeout=10)
    check("菜篮里出现小白菜", "小白菜" in r.text)

    r = sa.post(BASE + "/api/farm/plow", json={"pid": 6}, timeout=10)
    check("未解锁地块不能翻", r.json().get("code") != 0)
    r = sa.post(BASE + "/api/farm/plant", json={"pid": 2, "code": "grape"}, timeout=10)
    check("等级不足不能种葡萄", r.json().get("code") != 0)

    print("\n=== 7. 学习圈 ===")
    r = sa.post(BASE + "/api/circle/post",
                json={"title": "我是怎么搞懂列表推导式的",
                      "content": "先写 for，再写 if，最后写表达式。\n多练几遍就顺了。",
                      "category": "经验分享"}, timeout=10)
    check("发帖成功", r.json().get("code") == 0, r.text[:120])
    pid = r.json()["data"]["id"]
    check("发帖奖励 5 能量", r.json()["data"].get("bonus") == 5, r.json()["data"])

    r = sa.post(BASE + "/api/circle/post", json={"title": "太短", "content": "hi"},
                timeout=10)
    check("过短内容被拒绝", r.json().get("code") != 0)

    r = sb.get(BASE + "/circle", timeout=10)
    check("学习圈页可访问", r.status_code == 200)
    check("列表出现帖子标题", "列表推导式" in r.text)

    r = sb.post(BASE + "/api/circle/like", json={"pid": pid}, timeout=10)
    check("点赞成功", r.json().get("code") == 0 and r.json()["data"]["liked"] is True,
          r.text[:120])
    r = sb.post(BASE + "/api/circle/like", json={"pid": pid}, timeout=10)
    check("再次点赞变取消", r.json()["data"]["liked"] is False)

    r = sb.post(BASE + "/api/circle/comment", json={"pid": pid, "message": "受教了！"},
                timeout=10)
    check("评论成功", r.json().get("code") == 0, r.text[:120])

    r = sa.get(BASE + f"/post/{pid}", timeout=10)
    check("帖子详情可访问", r.status_code == 200)
    check("详情显示评论", "受教了" in r.text)

    r = sb.post(BASE + "/api/circle/delete", json={"pid": pid}, timeout=10)
    check("非作者不能删帖", r.json().get("code") != 0)
    r = sa.post(BASE + "/api/circle/delete", json={"pid": pid}, timeout=10)
    check("作者可删帖", r.json().get("code") == 0, r.text[:120])

    print("\n=== 8. 催打卡提醒 ===")
    r = sb.post(BASE + "/api/nudge", json={"pid": uid}, timeout=10)
    check("A 已打卡时催打卡被拒", r.json().get("code") != 0)
    db.execute("DELETE FROM checkins WHERE user_id=?", (uid,))
    r = sb.post(BASE + "/api/nudge", json={"pid": uid}, timeout=10)
    check("未打卡时可催", r.json().get("code") == 0, r.text[:120])
    r = sa.get(BASE + "/", timeout=10)
    # 第五轮起角标类名改为卡片导航的 nc-badge（旧名 dot-badge 兼容保留）
    check("首页出现未读提醒角标", ("nc-badge" in r.text) or ("dot-badge" in r.text))

    print("\n=== 9. 清理测试数据 ===")
    names = [a, b, c]
    for n in names:
        row = db.query_one("SELECT id FROM users WHERE username=?", (n,))
        if not row:
            continue
        i = row["id"]
        for t in ["submissions", "wrongs", "favorites", "checkins", "certs",
                  "plots", "harvests", "notices", "invites", "posts"]:
            db.execute(f"DELETE FROM {t} WHERE user_id=?", (i,))
        db.execute("DELETE FROM friends WHERE user_id=? OR friend_id=?", (i, i))
        db.execute("DELETE FROM team_members WHERE user_id=?", (i,))
    for t in db.query("SELECT id FROM teams WHERE owner_id NOT IN (SELECT id FROM users)"):
        db.execute("DELETE FROM teams WHERE id=?", (t["id"],))
    for n in names:
        db.execute("DELETE FROM users WHERE username=?", (n,))
    print(f"  剩余用户 {db.query_one('SELECT COUNT(*) c FROM users')['c']} 个")

    print("\n" + "=" * 46)
    print(f"  通过 {OK} 项，失败 {FAIL} 项")
    print("=" * 46)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
