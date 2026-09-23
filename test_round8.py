"""端到端测试（第八轮）：登录后的撒落元素 + 每日签到弹窗 + 祝福语

1. 登录后才出现签到弹窗；未登录不出现
2. 弹窗内含：吉祥物、问候语、祝福语、连续/累计天数、签到按钮
3. 撒落动画脚本与样式存在（sg-leaf / sgfall / fall()）
4. /api/blessing 返回问候 + 祝福；/api/checkin 返回祝福语
5. 关掉弹窗（cookie pop_signin=今天）后当天不再弹
6. 原有页面与功能不受影响
"""
import os
import random
import re
import string
import sys
from datetime import date

import requests

BASE = "http://127.0.0.1:" + os.environ.get("OJ_PORT", "8001")
OK = FAIL = 0
TODAY = str(date.today())

PAGES = ["/", "/problems", "/wrongs", "/favorites", "/checkin", "/farm", "/shop",
         "/market", "/kitchen", "/contest", "/quiz", "/cert",
         "/friends", "/circle", "/rank", "/guide", "/ai", "/me", "/settings"]


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

    print("\n=== 1. 未登录：不应出现签到弹窗 ===")
    guest = requests.Session()
    g = guest.get(BASE + "/", timeout=15).text
    check("游客首页无签到弹窗 DOM", "signinMask" not in g)
    check("游客首页无签到祝福语容器", 'id="sgBless"' not in g)
    check("游客访问 /api/blessing 需要登录",
          guest.get(BASE + "/api/blessing", timeout=15).status_code == 401)

    print("\n=== 2. 登录后：弹出签到弹窗 ===")
    s = requests.Session()
    s.post(BASE + "/login", data={"username": "demo", "password": "demo123456"},
           timeout=15, allow_redirects=False)
    home = s.get(BASE + "/", timeout=15).text
    check("登录后首页出现签到弹窗", 'id="signinMask"' in home)
    check("弹窗带当天日期（用于写 cookie）", f'data-today="{TODAY}"' in home)
    check("弹窗有签到按钮", 'id="sgBtn"' in home)
    check("弹窗有「今日不再提醒」", 'id="sgLater"' in home)
    check("弹窗有关闭按钮", 'id="sgX"' in home)
    check("弹窗含苗小序吉祥物 SVG",
          'class="sg-mascot"' in home and "<svg" in home.split("sg-mascot")[1][:600])
    check("弹窗含连续天数", 'id="sgStreak"' in home)
    check("弹窗含累计天数", "累计" in home)
    check("弹窗含签到奖励文案（⚡ 能量）", "⚡" in home and ("签到" in home))

    print("\n=== 3. 祝福语：问候 + 每日一句 ===")
    m = re.search(r'class="sg-greet">(.*?)</div>', home, re.S)
    greet = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    check("有问候语（含称呼）", bool(greet) and "，" in greet, greet[:40])
    tail_name = greet.split("，")[-1].replace(greet.split("，")[0], "").strip()
    check("问候语带用户称呼", len(tail_name) >= 1, greet[:40])

    bm = re.search(r'class="sg-bless"[^>]*>(.*?)</div>', home, re.S)
    bless = re.sub(r"<[^>]+>", "", bm.group(1)).strip() if bm else ""
    check("有祝福语且非空", len(bless) >= 8, bless[:40])
    check("祝福语带 emoji 装饰", bool(re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", bless)))

    hm = re.search(r'class="sg-head">(.*?)</div>', home, re.S)
    head = re.sub(r"<[^>]+>", "", hm.group(1)).strip() if hm else ""
    check("有签到状态引导语", len(head) >= 6, head[:40])

    print("\n=== 4. 撒落元素动画（脚本 + 样式） ===")
    js = s.get(BASE + "/static/js/signin.js", timeout=15).text
    css = s.get(BASE + "/static/css/style.css", timeout=15).text
    check("首页引入了 signin.js", "static/js/signin.js" in home)
    # 撒落实现已抽到 app.js 的全局 sgFall()，signin.js 通过 window.sgFall 复用
    _app = s.get(BASE + "/static/js/app.js", timeout=15).text
    _js = js + _app
    check("脚本有撒落函数 sgFall()", re.search(r"function\s+sgFall\s*\(", _app) is not None)
    check("撒落元素用田园 emoji（叶/花/穗/果）",
          all(e in _app for e in ("🍃", "🌸", "🌾", "🍅")))
    check("打开弹窗即撒落", re.search(r"fall\(\s*\d+\s*\)", js) is not None)
    check("签到成功再撒一大波", "fall(70)" in js)
    check("元素落地自动移除（不残留 DOM）", "animationend" in _app and "remove()" in _app)
    check("signin.js 复用全局 sgFall", "sgFall" in js)
    check("CSS 有撒落层 .sg-leaves", ".sg-leaves" in css)
    check("CSS 有粒子 .sg-leaf", ".sg-leaf" in css)
    check("CSS 有飘落关键帧 sgfall", "@keyframes sgfall" in css)
    check("撒落层不拦截点击", "pointer-events: none" in css.split(".sg-leaves")[1][:200])
    check("尊重 prefers-reduced-motion", "prefers-reduced-motion" in js or
          "prefers-reduced-motion" in css)
    check("弹窗层级高于悬浮 AI（不被遮挡）",
          int(re.search(r"\.signin-mask\s*\{[^}]*z-index:\s*(\d+)", css).group(1)) > 9100)

    print("\n=== 5. 接口：祝福语与打卡 ===")
    b = s.get(BASE + "/api/blessing", timeout=15).json()
    check("/api/blessing 返回成功", b.get("code") == 0, str(b)[:120])
    d = b.get("data", {})
    check("返回问候词", bool(d.get("greet")), str(d.get("greet")))
    check("返回祝福语", len(d.get("bless", "")) >= 8, str(d.get("bless"))[:40])
    check("返回 emoji", bool(d.get("emoji")))
    check("返回连续/累计天数", "streak" in d and "total" in d)
    check("返回今日是否已签到", "checked" in d)

    ck = s.post(BASE + "/api/checkin", json={}, timeout=15).json()
    check("打卡接口可用", ck.get("code") in (0, 1), ck.get("msg", ""))
    if ck.get("code") == 0:
        check("打卡返回祝福语", len(ck.get("data", {}).get("bless", "")) >= 8,
              str(ck.get("data", {}).get("bless"))[:40])
        check("打卡返回能量奖励", ck.get("data", {}).get("e_gain", 0) > 0)
    else:
        check("已打卡时给出提示", bool(ck.get("msg")), ck.get("msg"))

    print("\n=== 6. 关掉后当天不再弹 ===")
    s2 = requests.Session()
    s2.post(BASE + "/login", data={"username": "demo", "password": "demo123456"},
            timeout=15, allow_redirects=False)
    s2.cookies.set("pop_signin", TODAY, path="/")
    again = s2.get(BASE + "/", timeout=15).text
    check("写过 pop_signin 后不再弹窗", 'id="signinMask"' not in again)
    check("其它功能按钮不受影响", "/checkin" in again)

    print("\n=== 7. 原功能页面仍可访问 ===")
    for p in PAGES:
        check(f"{p} 可访问", s.get(BASE + p, timeout=15).status_code == 200)

    print("\n=== 8. 悬浮 AI 助手与导航仍在 ===")
    check("悬浮 AI 助手仍在", 'id="nanFab"' in home and 'id="nanPanel"' in home)
    check("卡片导航仍在", 'class="nav-card' in home)
    check("顶部 Banner 仍在", 'id="banner"' in home)

    print("\n" + "=" * 46)
    print(f"  通过 {OK} 项，失败 {FAIL} 项")
    print("=" * 46)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
