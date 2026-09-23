"""端到端冒烟测试：走一遍注册 → 刷题 → 错题 → 收藏 → 打卡 → 测验 → 认证的全流程。
用法：python test_e2e.py
"""
import os
import random
import string
import sys

import requests

BASE = "http://127.0.0.1:" + os.environ.get("OJ_PORT", "8001")
FAILS = []
PASSED = 0


def check(name, cond, extra=""):
    global PASSED
    if cond:
        PASSED += 1
        print(f"  [OK] {name}")
    else:
        FAILS.append(name)
        print(f"  [!!] {name} {extra}")


def main():
    s = requests.Session()
    user = "tester_" + "".join(random.choices(string.ascii_lowercase, k=6))

    print("\n=== 1. 页面可达性（未登录） ===")
    for path in ["/", "/login", "/register", "/problems", "/problem/1", "/rank"]:
        r = s.get(BASE + path, timeout=15)
        check(f"GET {path} -> {r.status_code}", r.status_code == 200, r.text[:200])

    print("\n=== 2. 注册 ===")
    r = s.post(BASE + "/register", data={"username": user, "password": "test123456",
                                         "nickname": "测试同学"}, allow_redirects=False, timeout=15)
    check("注册返回 302", r.status_code == 302, r.status_code)
    check("注册后拿到 session cookie", "session" in s.cookies, s.cookies.get_dict())

    print("\n=== 3. 已登录页面 ===")
    for path in ["/", "/wrongs", "/favorites", "/checkin", "/quiz", "/cert",
                 "/me", "/ai", "/settings", "/problem/1"]:
        r = s.get(BASE + path, timeout=15)
        check(f"GET {path} -> {r.status_code}", r.status_code == 200,
              (r.text[:300] if r.status_code != 200 else ""))

    print("\n=== 4. 判题：错误代码 ===")
    r = s.post(BASE + "/api/submit", json={"pid": 1, "code": "def add(a,b):\n    return a-b\n"}, timeout=30)
    d = r.json()
    check("提交接口 code=0", d.get("code") == 0, d)
    res = d.get("data", {}).get("result", {})
    check("判为未通过", res.get("status") == "wrong", res.get("status"))
    check("错题动作触发", d.get("data", {}).get("action") == "wrong")

    print("\n=== 5. 判题：正确代码 ===")
    r = s.post(BASE + "/api/submit", json={"pid": 1, "code": "def add(a,b):\n    return a+b\n"}, timeout=30)
    d = r.json()
    check("提交接口 code=0", d.get("code") == 0, d)
    check("判为通过", d["data"]["result"]["status"] == "accepted", d["data"]["result"]["status"])
    check("获得经验", d["data"]["gained"] > 0, d["data"]["gained"])
    check("升级信息存在", "level" in d["data"])

    print("\n=== 6. 错题本 ===")
    r = s.get(BASE + "/wrongs", timeout=15)
    check("错题本页面正常", r.status_code == 200)
    r = s.post(BASE + "/api/submit", json={"pid": 2, "code": "def is_even(n):\n    return False\n"}, timeout=30)
    check("制造第二道错题", r.json()["data"]["action"] == "wrong")
    r = s.get(BASE + "/wrongs", timeout=15)
    check("错题本含第 2 题", "#2" in r.text or "判断奇偶" in r.text)

    print("\n=== 7. 收藏 ===")
    r = s.post(BASE + "/api/favorite", json={"pid": 3}, timeout=15)
    check("收藏成功", r.json()["data"].get("fav") is True, r.json())
    r = s.post(BASE + "/api/favorite", json={"pid": 3}, timeout=15)
    check("再次点击取消收藏", r.json()["data"].get("fav") is False)
    s.post(BASE + "/api/favorite", json={"pid": 3}, timeout=15)
    r = s.get(BASE + "/favorites", timeout=15)
    check("收藏页含该题目", "摄氏温度转华氏" in r.text)

    print("\n=== 8. 打卡 ===")
    r = s.post(BASE + "/api/checkin", json={}, timeout=15)
    check("打卡成功", r.json().get("code") == 0, r.json())
    check("打卡连续天数=1", r.json()["data"].get("streak") == 1)
    r = s.post(BASE + "/api/checkin", json={}, timeout=15)
    check("重复打卡被拒绝", r.json().get("code") == 1)

    print("\n=== 9. 限时测验 ===")
    r = s.post(BASE + "/api/quiz/start", json={"count": 5, "difficulty": "easy",
                                               "category": "", "minutes": 10}, timeout=15)
    check("创建测验", r.json().get("code") == 0, r.json())
    qid = r.json()["data"]["quiz_id"]
    r = s.get(BASE + f"/quiz/{qid}", timeout=15)
    check("测验答题页正常", r.status_code == 200)
    r = s.post(BASE + f"/api/quiz/{qid}/submit", json={"codes": {}, "seconds": 120}, timeout=60)
    check("交卷成功", r.json().get("code") == 0, r.json())
    r = s.get(BASE + f"/quiz/{qid}/result", timeout=15)
    check("成绩页正常", r.status_code == 200)

    print("\n=== 10. 超时与错误处理 ===")
    r = s.post(BASE + "/api/run", json={"pid": 6,
                                        "code": "def sum_to(n):\n    while True:\n        pass\n"}, timeout=40)
    check("死循环被超时终止", r.json()["data"]["status"] == "timeout", r.json()["data"]["status"])
    r = s.post(BASE + "/api/run", json={"pid": 6, "code": "def sum_to(n):\n    import os\n"}, timeout=30)
    check("沙箱禁用 import", r.json()["data"]["status"] == "error", r.json()["data"]["status"])
    r = s.post(BASE + "/api/run", json={"pid": 6, "code": "def sum_to(n):\n    return ("}, timeout=30)
    check("语法错误被捕获", r.json()["data"]["status"] == "error")

    print("\n=== 11. 认证与排行榜 ===")
    r = s.get(BASE + "/cert", timeout=15)
    check("认证页正常", r.status_code == 200)
    r = s.post(BASE + "/api/cert/start", json={"pid": 0, "code": "basic"}, timeout=15)
    check("未达标时拒绝考试", r.json().get("code") == 1, r.json())
    r = s.get(BASE + "/rank", timeout=15)
    check("排行榜正常", r.status_code == 200)
    check("排行榜含当前用户", "测试同学" in r.text)

    print("\n=== 11b. 认证考试全流程（造数据达标后应颁发证书） ===")
    import sys
    sys.path.insert(0, ".")
    from core import db
    uid = db.query_one("SELECT id FROM users WHERE username=?", (user,))["id"]
    db.execute("UPDATE users SET exp=300 WHERE id=?", (uid,))           # Lv.3
    for p in db.query("SELECT id FROM problems LIMIT 16"):              # 造 16 条 AC
        db.execute("INSERT INTO submissions(user_id,problem_id,code,status,passed,total,created_at)"
                   " VALUES (?,?,'<seed>','accepted',1,1,?)", (uid, p["id"], "2026-01-01 00:00:00"))
    r = s.post(BASE + "/api/cert/start", json={"pid": 0, "code": "basic"}, timeout=15)
    check("达标后允许考试", r.json().get("code") == 0, r.json())
    qid = r.json()["data"]["quiz_id"]
    sol = {}
    for it in db.query("SELECT qi.id, p.solution FROM quiz_items qi JOIN problems p "
                       "ON p.id=qi.problem_id WHERE qi.quiz_id=?", (qid,)):
        sol[str(it["id"])] = it["solution"]
    r = s.post(BASE + f"/api/quiz/{qid}/submit", json={"codes": sol, "seconds": 300}, timeout=90)
    check("认证考试交卷", r.json().get("code") == 0, r.json())
    check("考试判定通过", r.json()["data"].get("passed") == 1, r.json()["data"])
    cert_no = r.json()["data"].get("cert_no")
    check("生成证书编号", bool(cert_no), cert_no)
    if cert_no:
        r = s.get(BASE + f"/certificate/{cert_no}", timeout=15)
        check("证书页面可访问", r.status_code == 200 and cert_no in r.text)
    r = s.get(BASE + "/me", timeout=15)
    check("个人中心显示证书", cert_no in r.text if cert_no else False)

    print("\n=== 12. 苗小序预设问答演示模式（不调用接口） ===")
    r = s.post(BASE + "/api/ai/chat", json={"message": "你好", "action": "chat"}, timeout=15)
    check("演示模式下能直接作答", r.json().get("code") == 0
          and len(r.json().get("data", {}).get("text", "")) > 10, r.json())

    print("\n=== 13. 退出登录 ===")
    r = s.post(BASE + "/logout", allow_redirects=False, timeout=15)
    check("退出成功", r.status_code == 302)
    r = s.get(BASE + "/me", timeout=15)
    check("退出后 /me 跳转登录", r.status_code == 302 or "登录" in r.text)

    print("\n" + "=" * 50)
    print(f"通过 {PASSED} 项，失败 {len(FAILS)} 项")
    if FAILS:
        print("失败项：")
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("全部通过 ✅")


if __name__ == "__main__":
    main()
