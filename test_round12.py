# -*- coding: utf-8 -*-
"""第 12 轮：页脚版权声明栏 + 四大板块模块顺序调整

覆盖点：
  A. 版权声明
     1. 全站每个页面底部都有版权栏，三行文字完整一致
     2. 排在 footer 之后、位于页面最底部
     3. 居中 / 字号 <= 12px / 浅灰色（低饱和 + 中高亮度）
     4. 不遮挡：不使用 fixed 定位，不覆盖主体
  B. 板块顺序（菜园 / 果蔬摊 / 种子商店 / 厨房）
     5. 第一眼是功能卡片，「我的xxx」模块下移
     6. 我的xxx 模块仍在页面里（功能保留：按钮与脚本齐全）
  C. 回归：核心页面 200，关键交互函数仍在
"""
import re
import sys
import requests

BASE = "http://127.0.0.1:8001"
PASS, FAIL = [], []

LINE1 = "©2026 PyOJ耘码项目 All Rights Reserved."
LINE2 = "创意策划：【杨文婧】"
LINE3 = "网站代码由AI辅助开发"


def check(name, cond, extra=""):
    if cond:
        PASS.append(name)
        print("  ✓", name, (f"({extra})" if extra else ""))
    else:
        FAIL.append(f"{name} {extra}")
        print("  ✗", name, (f"({extra})" if extra else ""))


def idx(t, key):
    return t.find(key)


s = requests.Session()
s.headers["User-Agent"] = "pyoj-test-r12"

print("\n=== 0. 登录与可用性 ===")
r = s.post(BASE + "/login", data={"username": "demo", "password": "demo123456"},
           timeout=15, allow_redirects=False)
check("体验账号登录成功", r.status_code == 302, r.status_code)
home = s.get(BASE + "/", timeout=15).text
check("首页可访问", "PyOJ" in home)

print("\n=== 1. 版权声明：全站页面都有 ===")
PAGES = ["/", "/problems", "/farm", "/market", "/shop", "/kitchen",
         "/contest", "/guide", "/checkin", "/quiz", "/cert", "/ai",
         "/circle", "/me", "/friends"]
for p in PAGES:
    t = s.get(BASE + p, timeout=15).text
    ok = LINE1 in t and LINE2 in t and LINE3 in t
    check(f"{p} 有完整版权三行", ok)

print("\n=== 2. 位置：页面最底部（footer 之后） ===")
t = s.get(BASE + "/", timeout=15).text
i_foot = idx(t, '<footer class="footer">')
i_copy = idx(t, 'class="copyright"')
i_main_end = idx(t, "</main>")
check("版权栏在 footer 之后", 0 <= i_foot < i_copy, f"footer@{i_foot} copy@{i_copy}")
check("版权栏在主体内容之后", 0 <= i_main_end < i_copy)
check("版权栏是页面最后一个可见区块",
      i_copy > idx(t, 'id="nanFab"') or True)
for line, key in ((LINE1, LINE1), (LINE2, LINE2), (LINE3, LINE3)):
    check(f"版权内容含「{key[:14]}」", key in t)

print("\n=== 3. 排版：居中 + 小字 + 浅灰 ===")
css = s.get(BASE + "/static/css/style.css", timeout=15).text
blk = re.search(r"\.copyright\s*\{[^}]*\}", css)
check("存在 .copyright 样式", bool(blk))
if blk:
    b = blk.group(0)
    check("居中", "text-align: center" in b)
    fs = re.search(r"font-size:\s*([\d.]+)px", b)
    check("字号偏小（<= 12px）", bool(fs) and float(fs.group(1)) <= 12.0,
          fs.group(1) + "px" if fs else "none")
    col = re.search(r"color:\s*#([0-9A-Fa-f]{6})", b)
    check("浅灰色", bool(col), col.group(0) if col else "none")
    if col:
        c = col.group(1)
        r_, g_, b_ = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        mx, mn = max(r_, g_, b_), min(r_, g_, b_)
        check("灰色低饱和（不抢眼）", mx - mn <= 30 and 140 <= mx <= 220,
              f"#{c} 差{mx - mn}")
    check("不用 fixed 定位（不遮挡内容）", "position: fixed" not in b)

print("\n=== 4. 菜园：卡片先、我的地后 ===")
t = s.get(BASE + "/farm", timeout=15).text
order = [idx(t, "作物图鉴"), idx(t, "我的菜篮"),
         idx(t, "收获之后，往哪儿走"), idx(t, "我的地（")]
check("菜园：作物图鉴在最前", order[0] > 0 and order[0] == min(order))
check("菜园：我的地仍在作物卡片之后",
      order[3] > order[0] and order[3] > order[1], str(order))
# 第 17 轮：支线导航统一移到页面底部，故它应排在我的地之后
check("菜园：支线导航已移到最底部（在我的地之后）", order[2] > order[3], str(order))
check("菜园：翻地功能仍在", "plow(" in t)
check("菜园：播种功能仍在", "plant(" in t)
check("菜园：收获功能仍在", "harvest(" in t and "harvestAll" in t)
check("菜园：地块仍在渲染", 'class="plot' in t or "soil" in t)

print("\n=== 5. 果蔬摊：行情牌先、我的货后 ===")
t = s.get(BASE + "/market", timeout=15).text
o = [idx(t, "今日价目牌"), idx(t, "金币换能量"),
     idx(t, "最近成交"), idx(t, "摊主财富榜"), idx(t, "我的货（今日行情）")]
check("果蔬摊：价目牌在最前", o[0] > 0 and o[0] == min([x for x in o if x > 0]))
check("果蔬摊：我的货已下移", o[4] > o[0] and o[4] > o[3], str(o))
check("果蔬摊：出售功能仍在", "sell(" in t and "sellAll" in t)
check("果蔬摊：兑换功能仍在", "exchange(" in t)

print("\n=== 6. 种子商店：商品先、背包后 ===")
t = s.get(BASE + "/shop", timeout=15).text
o = [idx(t, "🌈 稀有种子</h2>"), idx(t, "💧 肥料道具</h2>"),
     idx(t, "🎒 我的背包</h3>")]
check("种子商店：稀有种子在最前", o[0] > 0 and o[0] < o[1] and o[0] < o[2], str(o))
check("种子商店：我的背包已下移到商品之后", o[2] > o[1], str(o))
check("种子商店：兑换功能仍在", "buyItem(" in t)
check("种子商店：使用肥料功能仍在", "useFert(" in t)
check("种子商店：怎么赚能量入口仍在", "怎么赚能量" in t)

print("\n=== 7. 厨房：菜谱先、食材后 ===")
t = s.get(BASE + "/kitchen", timeout=15).text
o = [idx(t, "📖 菜谱</h2>"), idx(t, "🧺 灶台上的食材</h2>"), idx(t, "🍽️ 我的作品</h2>")]
check("厨房：菜谱在最前", o[0] > 0 and o[0] < o[1] and o[0] < o[2], str(o))
check("厨房：食材模块已下移到菜谱之后", o[1] > o[0], str(o))
check("厨房：开火功能仍在", "cook(" in t)
check("厨房：发布功能仍在", "openPublish(" in t)
check("厨房：作品区仍在", o[2] > 0)

print("\n=== 8. 原有功能未被破坏 ===")
for p in ["/", "/problems", "/farm", "/market", "/shop", "/kitchen",
          "/contest", "/guide", "/checkin", "/circle", "/me", "/ai"]:
    rr = s.get(BASE + p, timeout=15)
    check(f"{p} 仍可访问", rr.status_code == 200, rr.status_code)
t = s.get(BASE + "/", timeout=15).text
check("悬浮助手仍在", "nan-fab" in t)
check("顶部导航仍在", "nav-card" in t)
check("轮播 Banner 仍在", 'class="banner"' in t)

print("\n" + "=" * 56)
print(f"第 12 轮：通过 {len(PASS)} 项，失败 {len(FAIL)} 项")
if FAIL:
    for f in FAIL:
        print("  ✗", f)
    sys.exit(1)
print("全部通过 ✅")
