# -*- coding: utf-8 -*-
"""第 11 轮：首次登录分步 Onboarding + 苗小序分板块动作动画

覆盖点：
  A. Onboarding
     1. 新注册用户 body[data-onboard="1"]；老用户为 "0"（不再弹）
     2. 走完引导 → POST /api/onboard/done → 之后恒为 "0"
     3. onboard.js：严格 4 步（题库 → 菜园 → 果蔬摊 → 厨房），文案/目标完全一致
     4. 蒙层：灰色半透明遮罩 + 只挖一个高亮洞 + 白色虚线箭头
     5. 【下一步】/【开始体验】/【跳过引导】按钮齐全
     6. 欢迎弹窗关闭事件 pyoj:welcomeClosed 驱动引导开始（不打架）
  B. 苗小序动作
     7. 悬浮球带 5 个道具（💧⛏️🌱👋🍳）
     8. nan.js 按路径切 farm / market / kitchen / 空
     9. CSS 有浇水/耕地/种菜、转圈挥手、炒菜关键帧
    10. 其余页面不加动作类（不重复动作）
  C. 回归：核心页面仍可访问
"""
import re
import sys
import time
import requests

BASE = "http://127.0.0.1:8001"
PASS, FAIL = [], []


def check(name, cond, extra=""):
    if cond:
        PASS.append(name)
        print("  ✓", name, (f"({extra})" if extra else ""))
    else:
        FAIL.append(f"{name} {extra}")
        print("  ✗", name, (f"({extra})" if extra else ""))


s = requests.Session()
s.headers["User-Agent"] = "pyoj-test-r11"

print("\n=== 0. 服务可用性 ===")
try:
    r = s.get(BASE + "/", timeout=15)
    check("首页可访问", r.status_code == 200, r.status_code)
except Exception as e:
    print("服务未启动：", e)
    sys.exit(1)

print("\n=== 1. 新用户触发 / 老用户不触发 ===")
uname = "r11u%d" % int(time.time() % 100000)
reg = s.post(BASE + "/register",
             data={"username": uname, "password": "test123456", "nickname": "十一轮"},
             timeout=20, allow_redirects=False)
check("注册成功", reg.status_code == 302, reg.status_code)
new_home = s.get(BASE + "/", timeout=15).text
m = re.search(r'<body data-onboard="(\d)"', new_home)
check("新用户 body[data-onboard=1]", bool(m) and m.group(1) == "1",
      m.group(1) if m else "NONE")

s2 = requests.Session()
s2.post(BASE + "/login", data={"username": "demo", "password": "demo123456"},
        timeout=15, allow_redirects=False)
old_home = s2.get(BASE + "/", timeout=15).text
m2 = re.search(r'<body data-onboard="(\d)"', old_home)
check("老用户 body[data-onboard=0]（不再弹引导）",
      bool(m2) and m2.group(1) == "0", m2.group(1) if m2 else "NONE")

print("\n=== 2. 引导完成接口 ===")
r = s.post(BASE + "/api/onboard/done", timeout=15)
check("/api/onboard/done 返回 200", r.status_code == 200, r.status_code)
check("接口返回 code=0", r.json().get("code") == 0, str(r.json())[:60])
after = s.get(BASE + "/", timeout=15).text
m3 = re.search(r'<body data-onboard="(\d)"', after)
check("走完后不再触发（data-onboard=0）", bool(m3) and m3.group(1) == "0",
      m3.group(1) if m3 else "NONE")
r401 = requests.post(BASE + "/api/onboard/done", timeout=15)
check("未登录调用被拒绝", r401.status_code in (401, 403, 302) or
      r401.json().get("code") != 0, r401.status_code)

print("\n=== 3. onboard.js 步骤与文案 ===")
js = s.get(BASE + "/static/js/onboard.js", timeout=15).text
check("onboard.js 可访问", len(js) > 500)
steps = [
    ('/problems', '✍️ 答题时间到！脑力耕地，现在开工！'),
    ('/farm', '🥬 脑力值到手！下地耕耘，一起种菜吧！'),
    ('/market', '🥬 蔬菜成熟啦！去果蔬摊兑换资源，收获你的劳动成果！'),
    ('/kitchen', '🍳 食材就位！进厨房加工，解锁更多惊喜奖励！'),
]
for href, tip in steps:
    check(f"步骤指向 {href}", f'.nav-card[href="{href}"]' in js)
    check(f"步骤文案 {tip[:8]}…", tip in js)
check("最后一步为【开始体验】", "开始体验" in js)
check("严格 4 步（题库 → 菜园 → 果蔬摊 → 厨房）",
      len(re.findall(r"\{ sel:", js)) == 4,
      len(re.findall(r"\{ sel:", js)))
check("有【下一步】按钮", "下一步" in js)
check("有【跳过引导】", "跳过引导" in js)
check("引导走完自动关闭 + 写库",
      "/api/onboard/done" in js and "removeChild" in js)
check("等欢迎弹窗关掉再开始", "pyoj:welcomeClosed" in js)
check("点高亮区也能前进", "clientX" in js and "go(cur + 1)" in js)

print("\n=== 4. 蒙层与箭头样式 ===")
css = s.get(BASE + "/static/css/style.css", timeout=15).text
check("存在引导层 .ob-layer", ".ob-layer" in css)
hole = re.search(r"\.ob-hole\s*\{[^}]*\}", css)
check("存在高亮洞 .ob-hole", bool(hole))
check("灰色半透明遮罩（9999px 扩散阴影）",
      bool(hole) and "9999px" in hole.group(0) and "rgba(26, 38, 28" in hole.group(0))
blk = re.search(r"\.ob-block\.full\s*\{[^}]*\}", css)
check("最后一步整屏压暗", bool(blk) and "rgba(26, 38, 28" in blk.group(0))
check("存在白色虚线箭头 .ob-arrow", ".ob-arrow" in css)
check("箭头为白色虚线（stroke #fff + dasharray）",
      "stroke=\"#fff\"" in js and "stroke-dasharray" in js)
check("箭头带箭头尖", "polygon" in js)
check("提示卡 .ob-card", ".ob-card" in css)
check("下一步按钮 .ob-next", ".ob-next" in css)
check("收尾按钮高亮 .ob-next.done", ".ob-next.done" in css)
check("引导层 z-index 高于悬浮助手(9000)",
      bool(re.search(r"\.ob-layer\s*\{[^}]*z-index:\s*9[4-9]\d\d", css)))

print("\n=== 5. 苗小序分板块动作 ===")
check("悬浮球含道具层 nf-props", "nf-props" in old_home)
for p in ("p-water", "p-hoe", "p-fert", "p-wave", "p-cook", "p-knife"):
    check(f"道具 {p} 存在", p in old_home)
check("动作文字位 nf-act", "nf-act" in old_home)

nj = s.get(BASE + "/static/js/nan.js", timeout=15).text
check("nan.js 有页面动作模式函数", "pageActMode" in nj)
check("/farm → 菜园动作", "'/farm'" in nj and "'farm'" in nj)
check("/market → 果蔬摊动作", "'/market'" in nj and "'market'" in nj)
check("/kitchen → 厨房动作", "'/kitchen'" in nj and "'kitchen'" in nj)
check("菜园三动作轮换文案（耕地/浇水/施肥）", all(x in nj for x in ("耕地", "浇水", "施肥")))
check("厨房切菜/做菜文案", "切菜" in nj and "做菜" in nj)
check("商店招手 / 果蔬摊挥手文案", "招手" in nj and "挥手" in nj)
check("/shop → 商店动作", "'/shop'" in nj and "'shop'" in nj)
check("其余页面不加动作类（不重复动作）", "return ''" in nj)

check("CSS 菜园动作类 .act-farm", ".nan-fab.act-farm" in css)
check("CSS 果蔬摊动作类 .act-market", ".nan-fab.act-market" in css)
check("CSS 厨房动作类 .act-kitchen", ".nan-fab.act-kitchen" in css)
check("CSS 种子商店动作类 .act-shop", ".nan-fab.act-shop" in css)
for kf in ("nfWater", "nfHoe", "nfFert", "nfKnife", "nanSpin", "nfWave", "nanChop", "nanStir", "nfPan"):
    check(f"关键帧 {kf}", f"@keyframes {kf}" in css)
check("菜园三动作分阶段播放（耕地/浇水/施肥）",
      all(x in css for x in ("act-farm.ph-0 .nf-prop.p-hoe",
                             "act-farm.ph-1 .nf-prop.p-water",
                             "act-farm.ph-2 .nf-prop.p-fert")))
check("厨房两动作分阶段播放（切菜/做菜）",
      all(x in css for x in ("act-kitchen.ph-0 .nf-prop.p-knife",
                             "act-kitchen.ph-1 .nf-prop.p-cook")))

print("\n=== 6. 欢迎弹窗与引导串联 ===")
wj = s.get(BASE + "/static/js/welcome.js", timeout=15).text
check("欢迎窗关闭时广播事件", "pyoj:welcomeClosed" in wj)
check("base.html 引入了 onboard.js", "static/js/onboard.js" in new_home)

print("\n=== 7. 核心页面未破坏 ===")
for p in ["/problems", "/farm", "/shop", "/contest", "/guide", "/market",
          "/kitchen", "/checkin", "/quiz", "/cert", "/ai"]:
    rr = s.get(BASE + p, timeout=15)
    check(f"{p} 仍可访问", rr.status_code == 200, rr.status_code)

print("\n" + "=" * 56)
print(f"第 11 轮：通过 {len(PASS)} 项，失败 {len(FAIL)} 项")
if FAIL:
    for f in FAIL:
        print("  ✗", f)
    sys.exit(1)
print("全部通过 ✅")
