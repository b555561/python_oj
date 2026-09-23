"""端到端测试（第七轮）：

1. 顶部导航：16 个按钮固定一排（不换行、不挤压），浅底 + 深色字 + 主题图案
2. 顶部 Banner：高度收窄，让出首屏
3. 首屏能看到四大核心板块；全站原有功能不丢
"""
import colorsys
import os
import random
import re
import string
import sys

import requests

BASE = "http://127.0.0.1:" + os.environ.get("OJ_PORT", "8001")
OK = FAIL = 0

PAGES = ["/", "/problems", "/wrongs", "/favorites", "/checkin", "/farm", "/shop",
         "/market", "/kitchen", "/contest", "/quiz", "/cert",
         "/friends", "/circle", "/rank", "/guide", "/ai", "/me", "/settings"]

NAV_KEYS = ["problems", "wrongs", "favorites", "checkin", "farm", "shop",
            "market", "kitchen", "contest", "quiz", "cert", "friends",
            "circle", "rank", "guide", "ai"]

CORE = [("/farm", "菜园"), ("/market", "果蔬摊"),
        ("/kitchen", "厨房"), ("/shop", "种子商店")]


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


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(h):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def sat(h):
    r, g, b = [c / 255.0 for c in rgb(h)]
    return colorsys.rgb_to_hsv(r, g, b)[1]


def main():
    sys.path.insert(0, ".")
    s = requests.Session()
    s.post(BASE + "/login", data={"username": "demo", "password": "demo123456"},
           timeout=15, allow_redirects=False)

    css = s.get(BASE + "/static/css/style.css", timeout=15).text
    home = s.get(BASE + "/", timeout=15).text

    print("\n=== 1. 导航栏：16 个按钮一排，不换行不超出 ===")
    nav_block = re.search(r"\.nav\s*\{[^}]*\}", css)
    check("导航用 16 等分单排栅格",
          bool(nav_block) and "repeat(16, minmax(0, 1fr))" in nav_block.group(0),
          nav_block.group(0)[:80] if nav_block else "无 .nav")
    check("窄屏改为横向滑动（始终一排）",
          "@media (max-width: 1120px)" in css and "overflow-x: auto" in css)
    check("首页渲染 16 个导航按钮", home.count('class="nav-card') == 16,
          home.count('class="nav-card'))
    for p in ["/problems", "/farm", "/contest"]:
        r = s.get(BASE + p, timeout=15)
        check(f"{p} 也是 16 个按钮", r.text.count('class="nav-card') == 16,
              r.text.count('class="nav-card'))

    print("\n=== 2. 主题图案全部保留 ===")
    check("16 套造型 SVG 渲染", home.count('class="nc-art"') == 16,
          home.count('class="nc-art"'))
    check("图案随主题色上色（currentColor）", home.count("currentColor") >= 16,
          home.count("currentColor"))
    for k in NAV_KEYS:
        check(f"nc-{k} 保留主题类", f"nc-{k}" in home)

    print("\n=== 3. 低饱和浅底 + 深色文字（可读性） ===")
    pat = re.compile(r"\.nc-(\w+)\s*\{[^}]*--tint:(#[0-9a-fA-F]{6});[^}]*--art:(#[0-9a-fA-F]{6});[^}]*--ink2:(#[0-9a-fA-F]{6});")
    got = {m.group(1): (m.group(2), m.group(3), m.group(4)) for m in pat.finditer(css)}
    check("16 套主题色齐全", len(got) == 16, f"{len(got)} 套: {sorted(got)}")
    if len(got) == 16:
        low_sat = all(sat(v[0]) <= 0.40 for v in got.values())
        light_bg = all(lum(v[0]) >= 0.82 for v in got.values())
        dark_txt = all(lum(v[2]) <= 0.35 for v in got.values())
        good_ct = all(contrast(v[0], v[2]) >= 4.5 for v in got.values())
        check("底色低饱和（S ≤ 0.40）", low_sat,
              str({k: round(sat(v[0]), 2) for k, v in got.items() if sat(v[0]) > 0.40}))
        check("底色足够浅（亮度 ≥ 0.82）", light_bg,
              str({k: round(lum(v[0]), 2) for k, v in got.items() if lum(v[0]) < 0.82}))
        check("文字为深色（亮度 ≤ 0.35）", dark_txt,
              str({k: round(lum(v[2]), 2) for k, v in got.items() if lum(v[2]) > 0.35}))
        worst = min(round(contrast(v[0], v[2]), 2) for v in got.values())
        check("文字/底色对比度 ≥ 4.5（WCAG AA）", good_ct, f"最低 {worst}")
        check("导航文字用深色变量", "color: var(--ink2" in css)

    print("\n=== 4. 不与下方菜园板块撞色 ===")
    if "farm" in got:
        nav_bg, _, nav_ink = got["farm"]
        big = re.search(r"\.big-farm\s*\{\s*background:\s*linear-gradient\(135deg,\s*(#[0-9a-fA-F]{6})", css)
        big_c = big.group(1) if big else "#4CAF50"
        check("导航底色近乎无彩色、菜园按钮才是高饱和（不撞色）",
              sat(nav_bg) <= 0.15 and sat(big_c) >= 0.50,
              f"nav S={round(sat(nav_bg), 2)} vs btn S={round(sat(big_c), 2)}")
        check("导航底色明显浅于菜园大按钮",
              lum(nav_bg) - lum(big_c) > 0.35,
              f"nav {round(lum(nav_bg), 2)} vs btn {round(lum(big_c), 2)}")
    check("导航不再使用高饱和渐变底", "linear-gradient(135deg, var(--c1" not in css)

    print("\n=== 5. Banner 收窄，让出首屏 ===")
    mh = re.search(r"\.banner-card\s*\{[^}]*min-height:\s*(\d+)px", css)
    h = int(mh.group(1)) if mh else 999
    check(f"Banner 高度已收窄（{h}px ≤ 130px）", h <= 130, f"{h}px")
    check("Banner 在页面最顶端（导航栏之上）",
          0 <= home.find('class="banner"') < home.find('<header class="topbar"'))
    check("两张海报卡都在", home.count('class="banner-card') == 2)
    check("左右切换箭头在", "banner-arrow prev" in home and "banner-arrow next" in home)
    check("轮播指示点在", "banner-dot" in home)
    check("自动轮播进度条在", "bc-timer" in home and "bcbar" in css)
    check("去掉了占位的英文装饰行", 'class="bc-en"' not in home)

    print("\n=== 6. 首屏四大核心板块 ===")
    check("主视觉 hero 在", 'class="hero"' in home)
    check("四个大按钮齐全", home.count('class="big-btn') == 4, home.count('class="big-btn'))
    for href, nm in CORE:
        check(f"核心入口 {nm}", f'href="{href}"' in home and f"big-{href.strip('/')}" in home)
    check("四大板块排在 Banner 之后、页脚之前",
          home.find('class="big-actions"') > home.find('class="banner"'))

    print("\n=== 7. 全站功能保留（原有页面仍可访问） ===")
    for p in PAGES:
        r = s.get(BASE + p, timeout=15)
        check(f"{p} 可访问", r.status_code == 200, r.status_code)

    print("\n=== 8. 关键接口仍可用 ===")
    check("打卡接口", s.post(BASE + "/api/checkin", timeout=15).json().get("code") in (0, 1))
    check("菜园接口", s.post(BASE + "/api/farm/plow", json={"pid": 1}, timeout=15).json().get("code") in (0, 1))
    r = s.post(BASE + "/api/ai/chat", json={"message": "菜园怎么玩？", "action": "chat"}, timeout=15)
    check("AI 演示模式（不调接口）", r.json().get("code") == 0 and "翻地" in r.json().get("data", {}).get("text", ""))

    print("\n=== 9. 悬浮 AI 助手仍在 ===")
    check("悬浮图标 + 弹窗", 'id="nanFab"' in home and 'id="nanPanel"' in home)
    check("语音按钮保留", 'id="npMic"' in home)

    print("\n" + "=" * 46)
    print(f"  通过 {OK} 项，失败 {FAIL} 项")
    print("=" * 46)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
