"""端到端测试（第五轮）：卡片式导航栏 + 全局悬浮可拖拽 AI 助手（苗小序）。"""
import os
import random
import string
import sys

import requests

BASE = "http://127.0.0.1:" + os.environ.get("OJ_PORT", "8001")
OK = FAIL = 0

PAGES = ["/login", "/guide", "/", "/problems", "/farm", "/shop", "/market",
         "/kitchen", "/contest", "/circle", "/friends", "/rank", "/ai", "/checkin"]

NAV_KEYS = ["problems", "wrongs", "favorites", "checkin", "farm", "shop",
            "market", "kitchen", "contest", "quiz", "cert", "friends",
            "circle", "rank", "guide", "ai"]


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
    from core import db

    s = requests.Session()
    name = "r5_" + rnd()
    s.post(BASE + "/register",
           data={"username": name, "password": "test123456", "nickname": name},
           timeout=15, allow_redirects=False)
    uid = db.query_one("SELECT id FROM users WHERE username=?", (name,))["id"]

    print("\n=== 1. 导航卡片：全站每个页面都有 16 个图形按钮 ===")
    for p in PAGES:
        r = s.get(BASE + p, timeout=15)
        ok = r.status_code == 200 and r.text.count('class="nav-card') == 16
        check(f"{p} 导航卡片 16 个", ok, f"{r.status_code} / {r.text.count(chr(34).join(['class=', 'nav-card'])) if r.status_code == 200 else '-'}")

    print("\n=== 2. 每个导航项都有各自的主题造型背景（SVG） ===")
    home = s.get(BASE + "/", timeout=15).text
    for k in NAV_KEYS:
        check(f"nav-{k} 主题类", f'nc-{k}' in home)
    check("16 套造型 SVG 全部渲染", home.count('class="nc-art"') == 16,
          home.count('class="nc-art"'))
    _css = s.get(BASE + "/static/css/style.css", timeout=15).text
    check("菜园卡片带绿色主题色", ".nc-farm" in _css and "--art:#3f8f47" in _css)

    print("\n=== 3. 悬浮 AI 助手：任何页面都常驻 ===")
    for p in PAGES:
        r = s.get(BASE + p, timeout=15)
        ok = ('id="nanFab"' in r.text) and ('id="nanPanel"' in r.text)
        check(f"{p} 悬浮图标 + 弹窗", ok, r.status_code)

    print("\n=== 4. 弹窗能力：输入框 / 语音 / 关闭 ===")
    r = s.get(BASE + "/", timeout=15).text
    check("有文字输入框", 'id="npText"' in r)
    check("有语音按钮", 'id="npMic"' in r)
    check("有关闭按钮", 'id="npX"' in r and 'id="npMin"' in r)
    check("有快捷提问", 'id="npQuick"' in r and "data-q=" in r)
    check("弹窗默认收起", 'id="nanPanel" hidden' in r)

    print("\n=== 5. 前端脚本：拖拽 / 语音 / 高亮 ===")
    js = s.get(BASE + "/static/js/nan.js", timeout=15).text
    check("拖拽用 pointer 事件", "pointerdown" in js and "pointermove" in js and "pointerup" in js)
    check("位置记忆 localStorage", "nanFabPos" in js and "localStorage" in js)
    check("语音识别接口", "SpeechRecognition" in js and "zh-CN" in js)
    check("导航高亮逻辑", "initNavCards" in js and "classList.add('on')" in js)
    check("内嵌 base.html", "/static/js/nan.js" in r)

    print("\n=== 6. 悬浮助手走预设问答演示模式（不调接口） ===")
    r = s.post(BASE + "/api/ai/chat", json={"message": "菜园怎么玩？", "action": "chat"}, timeout=15)
    check("演示模式直接作答", r.json().get("code") == 0, r.json())
    txt = r.json().get("data", {}).get("text", "")
    check("答案是菜园预设内容", "翻地" in txt or "播种" in txt, txt[:60])

    r = s.post(BASE + "/api/ai/chat", json={"message": "帮我讲讲耕耘种菜大赛", "action": "chat"}, timeout=15)
    txt2 = r.json().get("data", {}).get("text", "")
    check("大赛问题有答案", "大赛" in txt2 or "赛季" in txt2, txt2[:60])

    print("\n=== 7. 原有功能回归 ===")
    check("题库页可访问", s.get(BASE + "/problems", timeout=15).status_code == 200)
    check("菜园接口可用", s.post(BASE + "/api/farm/plow", json={"pid": 1}, timeout=15).json().get("code") in (0, 1))
    r = s.post(BASE + "/api/checkin", timeout=15)
    check("打卡接口可用", r.json().get("code") in (0, 1), r.json())
    check("果蔬摊页面可访问", s.get(BASE + "/market", timeout=15).status_code == 200)
    check("厨房页面可访问", s.get(BASE + "/kitchen", timeout=15).status_code == 200)
    check("学习圈页面可访问", s.get(BASE + "/circle", timeout=15).status_code == 200)
    check("大赛页面可访问", s.get(BASE + "/contest", timeout=15).status_code == 200)
    check("种子商店页面可访问", s.get(BASE + "/shop", timeout=15).status_code == 200)

    # 清理
    db.execute("DELETE FROM users WHERE username=?", (name,))
    db.execute("DELETE FROM plots WHERE user_id=?", (uid,))

    print(f"\n通过 {OK} 项，失败 {FAIL} 项")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
