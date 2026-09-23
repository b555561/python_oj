# -*- coding: utf-8 -*-
"""端到端测试（第十四轮）：页面头部「苗小序」按 URL 加载无限循环 CSS 动画
   /farm    菜园   → 耕地 ⛏️ → 浇水 🪣
   /market  果蔬摊 → 招手 👋 + 来回踱步
   /kitchen 厨房   → 切菜 🔪 → 翻炒做菜 🍳
   /circle  学习圈 → 捧书阅读（翻书 + 低头看书）
   同时校验：右下角悬浮苗小序逻辑完整保留、历史功能未回退
"""
import re
import requests

BASE = "http://127.0.0.1:8001"
s = requests.Session()
OK = FAIL = 0


def check(name, cond, extra=""):
    global OK, FAIL
    if cond:
        OK += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} {extra}")


print("=== 0. 登录与环境 ===")
s.post(BASE + "/login", data={"username": "demo", "password": "demo123456"},
       allow_redirects=False)
css = s.get(BASE + "/static/css/style.css", timeout=15).text
nj = s.get(BASE + "/static/js/nan.js", timeout=15).text
PAGES = {"/farm": "ms-farm", "/market": "ms-market",
         "/kitchen": "ms-kitchen", "/circle": "ms-circle"}
HTML = {p: s.get(BASE + p, timeout=15).text for p in PAGES}
check("四个板块页均可访问", all(HTML.values()))

print("\n=== 1. 头部舞台按页面加载 ===")
for p, mode in PAGES.items():
    t = HTML[p]
    check(f"{p} 头部有舞台 .ms-stage.{mode}", f'class="ms-stage {mode}"' in t)
    check(f"{p} 头部是苗小序形象（SVG）",
          re.search(r'class="ms-stage ' + mode + r'"[^>]*>.{0,400}?aria-label="苗小序"',
                    t, re.S) is not None)
    check(f"{p} 只加载本页动作（不含其他页面动作类）",
          sum(1 for m in PAGES.values() if f'ms-stage {m}' in t) == 1)

print("\n=== 2. 各页动作道具齐全 ===")
PROPS = {
    "ms-farm":    ["p-hoe", "p-can", "p-drop", "p-clod"],
    "ms-market":  ["p-wave", "p-basket"],
    "ms-kitchen": ["p-knife", "p-pan", "p-flame"],
    "ms-circle":  ["p-book", "p-page", "p-spark"],
}
for mode, props in PROPS.items():
    p = [k for k, v in PAGES.items() if v == mode][0]
    for pr in props:
        check(f"{p} 道具 {pr}", f'ms-prop {pr}' in HTML[p])
check("菜园含耕地/浇水道具（锄头+水桶）",
      "p-hoe" in HTML["/farm"] and "p-can" in HTML["/farm"])
check("果蔬摊含招手道具", "p-wave" in HTML["/market"])
check("厨房含切菜/翻炒道具（刀+锅）",
      "p-knife" in HTML["/kitchen"] and "p-pan" in HTML["/kitchen"])
check("学习圈含书本/翻页道具（书+纸页）",
      "p-book" in HTML["/circle"] and "p-page" in HTML["/circle"])

print("\n=== 3. CSS 舞台样式与关键帧 ===")
for mode in PAGES.values():
    check(f"CSS 有 .{mode} 尺寸与布局", f".{mode} {{" in css)
check("舞台容器 .ms-stage", ".ms-stage {" in css)
check("形象容器 .ms-body", ".ms-stage .ms-body" in css)
check("地面阴影 .ms-ground", ".ms-stage .ms-ground" in css)

KFS = {
    "菜园": ("msFarmBody", "msHoe", "msCan", "msDrop", "msClod"),
    "果蔬摊": ("msWalk", "msShadow", "msHello", "msBasket"),
    "厨房": ("msChef", "msKnife", "msPan", "msFlame"),
    "学习圈": ("msRead", "msBook", "msPage", "msSpark"),
}
for grp, kfs in KFS.items():
    for kf in kfs:
        check(f"{grp} 关键帧 @keyframes {kf}", f"@keyframes {kf}" in css)

print("\n=== 4. 无限循环（infinite） ===")
def _loop(cls_):
    return len([ln for ln in css.split("\n")
                if f".{cls_}" in ln.split("{")[0] and "infinite" in ln])

check("菜园动作无限循环", _loop("ms-farm") >= 5, _loop("ms-farm"))
check("果蔬摊动作无限循环", _loop("ms-market") >= 4, _loop("ms-market"))
check("厨房动作无限循环", _loop("ms-kitchen") >= 4, _loop("ms-kitchen"))
check("学习圈动作无限循环", _loop("ms-circle") >= 4, _loop("ms-circle"))
check("踱步用 translateX 左右往返",
      "translateX(-24px)" in css and "translateX(24px)" in css)
check("翻书用 rotateY 翻页", "rotateY" in css)
check("低头看书有 rotate 倾斜", re.search(r"@keyframes msRead \{.*rotate\(7deg\)", css, re.S) is not None)

print("\n=== 5. 纯 CSS，无外部动画库 ===")
libs = ("animate.css", "lottie", "gsap", "anime.min.js", "velocity", "aos.css")
bad = [p + ":" + l for p, t in HTML.items() for l in libs if l in t.lower()]
check("未引入任何外部动画库", not bad, bad)
check("无外链 CDN 脚本",
      not any(re.search(r'<script[^>]+src="https?://', t) for t in HTML.values()))
heavy = [b for b in re.findall(r"@keyframes (?:ms)\w+\s*\{(.*?)\n\}", css, re.S)
         if re.search(r"(?<!-)\b(width|height|top|left|margin|padding)\s*:", b)]
check("关键帧不触发重排", not heavy)

print("\n=== 6. 悬浮苗小序（右下角）完整保留 ===")
for p in PAGES:
    check(f"{p} 仍有悬浮球 nan-fab", 'id="nanFab"' in HTML[p])
check("悬浮球道具层完整", all(k in HTML["/farm"] for k in ("nf-props", "nf-act")))
check("悬浮球仍按页面切换动作（act-farm/kitchen/shop/market）",
      all(x in nj for x in ("'farm'", "'kitchen'", "'shop'", "'market'")))
check("悬浮球拖拽逻辑保留（Pointer 事件）", "pointerdown" in nj)
check("悬浮球语音输入保留",
      "SpeechRecognition" in nj or "webkitSpeechRecognition" in nj)
check("悬浮球对话面板保留", 'id="nanPanel"' in HTML["/farm"])
check("悬浮球 CSS 动作类未丢失",
      all(x in css for x in (".nan-fab.act-farm", ".nan-fab.act-kitchen",
                             ".nan-fab.act-shop", ".nan-fab.act-market")))

print("\n=== 7. 历史功能未回退 ===")
check("菜园页仍有一键收获", "harvestAll" in HTML["/farm"])
check("厨房页仍有禾籽提示（hezi_say）", "hezi_say" in s.get(BASE + "/kitchen").text
      or "别急着生吃" in HTML["/kitchen"])
check("果蔬摊页仍有禾籽提示", "收成到手" in HTML["/market"]
      or "hezi_say" in HTML["/market"])
check("菜园页文案完整（我的地）", "我的地" in HTML["/farm"])
check("厨房页文案完整（菜谱）", "菜谱" in HTML["/kitchen"])
check("果蔬摊页文案完整（价目/行情）",
      ("价目" in HTML["/market"] or "行情" in HTML["/market"]))
check("学习圈页文案完整（发一条）", "发一条" in HTML["/circle"])
check("版权栏仍在", "©2026 PyOJ耘码项目 All Rights Reserved." in HTML["/farm"])

print("\n=== 8. 尊重「减少动态效果」 ===")
# 注意：CSS 里现在有多个 reduced-motion 块（舞台 / 认证页 …），
#       必须拼接全部，不能只取 [-1]，否则新增块会把断言顶失效
_rm = "".join(css.split("@media (prefers-reduced-motion: reduce)")[1:])
check("舞台动画可被关闭", ".ms-stage .ms-body" in _rm and "animation: none" in _rm)
check("学习圈书本静态保留", ".ms-circle .p-book" in _rm)

print(f"\n{'='*46}\n结果：通过 {OK} 项，失败 {FAIL} 项\n{'='*46}")
