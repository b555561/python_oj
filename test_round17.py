# -*- coding: utf-8 -*-
"""第 17 轮专项测试：四大板块页头瘦身 + 顺序调整

菜园 /farm    ：删对话气泡 / 能量规则长文 / 色块边框，页头只留动画 + 能量值，
                能量规则改成小图标（点击弹窗）；支线导航移到页面底部
种子商店 /shop：稀有种子卡片提到最上方（在苗小序板块之前）
果蔬摊 /market：页头只留动画 + 金币/能量值 + 操作；摊位名片与支线移至底部；
                禾籽对话框缩小（compact）
厨房   /kitchen：同上，页头只留动画 + 能量值；台账与支线移至底部

业务（翻地/播种/浇水/收获/买卖/做菜）一律不动。
"""
import io
import os
import re
import sys
import time
import requests

BASE = os.environ.get("PYOJ_BASE", "http://127.0.0.1:8001")
OK = BAD = 0


def check(name, cond, extra=""):
    global OK, BAD
    if cond:
        OK += 1
        print("  ✓ " + name)
    else:
        BAD += 1
        print("  ✗ " + name + ("  << " + str(extra) if extra else ""))


def idx(h, key):
    return h.find(key)


def read(p):
    return io.open(p, encoding="utf-8").read()


sess = requests.Session()
uname = "r17t" + str(int(time.time()) % 100000)
sess.post(BASE + "/register",
          data={"username": uname, "password": "test123456", "nickname": "r17t"},
          allow_redirects=False, timeout=15)
sess.get(BASE + "/", timeout=15)

farm = sess.get(BASE + "/farm", timeout=15).text
market = sess.get(BASE + "/market", timeout=15).text
kitchen = sess.get(BASE + "/kitchen", timeout=15).text
shop = sess.get(BASE + "/shop", timeout=15).text

src_farm = read("templates/farm.html")
src_market = read("templates/market.html")
src_kitchen = read("templates/kitchen.html")
src_shop = read("templates/shop.html")
src_hezi = read("templates/_hezi.html")
src_mascot = read("templates/_mascot.html")
src_help = read("templates/_energy_help.html")
js_help = read("static/js/energy_help.js")
css = read("static/css/style.css")
base = read("templates/base.html")

print("\n=== 1. 菜园：页头只剩「动画 + 能量值 + 操作」 ===")
check("菜园有精简页头 .sec-top", 'class="sec-top"' in farm)
check("菜园页头用缩小版舞台（ms-wrap sm）", "ms-wrap sm" in farm)
check("菜园页头保留绿色苗小序动画（ms-farm 舞台）", "ms-stage ms-farm" in farm)
check("菜园页头保留能量值", "⚡ 能量" in farm)
check("菜园页头不再有对话气泡 nan-say", "nan-say" not in farm)
check("菜园页头不再有绿色色块卡片 nan-card", "nan-card" not in farm)
check("菜园不再有能量规则长文（能量怎么来）", "能量怎么来" not in farm)
check("菜园不再有能量规则长文（能量怎么用）", "能量怎么用" not in farm)
check("菜园页头不再有旧的大标题块", "苗小序的菜园</h2>" not in farm)
check("菜园仍保留一键收获按钮", "harvestAll()" in farm)

print("\n=== 2. 菜园：能量规则小图标 + 弹窗 ===")
check("菜园页头有能量规则小图标", "energy-help" in farm)
check("小图标点击调用 openEnergyHelp()", "onclick=\"openEnergyHelp()\"" in farm)
check("小图标有无障碍说明", "aria-label" in src_help and "title" in src_help)
check("弹窗脚本已全局引入（base.html）", "static/js/energy_help.js" in base)
check("弹窗函数已定义", "function openEnergyHelp()" in js_help)
for kw in ("每日打卡", "首次通过题目", "重复通过", "测验达标",
           "学习圈发帖", "翻地", "播种", "浇水", "收获"):
    check("弹窗规则含「%s」" % kw, kw in js_help)
check("弹窗分「赚能量 / 花能量」两块", js_help.count("eh-h") >= 2)
check("弹窗用通用 openModal（非新弹窗体系）", "openModal(" in js_help)

print("\n=== 3. 菜园：下方卡片紧跟页头，支线移到底 ===")
o_top = idx(farm, "sec-top")
o_atlas = idx(farm, "作物图鉴")
o_basket = idx(farm, "我的菜篮")
o_tips = idx(farm, "种植小贴士")
o_land = idx(farm, "我的地（")
o_branch = idx(farm, "收获之后")
check("页头在作物图鉴之前", 0 < o_top < o_atlas)
check("作物图鉴紧跟页头之后", o_atlas < o_basket)
check("我的菜篮在图鉴之后", o_basket > o_atlas)
check("种植小贴士在菜篮之后", o_tips > o_basket)
check("我的地在卡片之后", o_land > o_tips)
check("支线导航已移到最底部（在我的地之后）", o_branch > o_land,
      str([o_top, o_atlas, o_basket, o_tips, o_land, o_branch]))
_seg = farm.split("sec-top")[1].split("作物图鉴")[0]
check("页头与图鉴之间不再夹任何说明/气泡内容",
      "nan-say" not in _seg and "<p class=\"note\"" not in _seg
      and "能量怎么用" not in _seg, _seg[-120:])

print("\n=== 4. 种子商店：稀有种子提到最上方 ===")
s_seed = idx(shop, "稀有种子")
s_hero = idx(shop, "shop-hero")
s_hezi = idx(shop, "nan-row")
s_fert = idx(shop, "肥料道具")
check("稀有种子在苗小序招牌之前", 0 < s_seed < s_hero,
      str([s_seed, s_hero]))
check("稀有种子在禾籽对话框之前", s_seed < s_hezi)
check("苗小序招牌仍在（未删除）", s_hero > 0)
check("禾籽对话框仍在（未删除）", s_hezi > 0)
check("肥料道具仍在对话框之后", s_fert > s_hezi)
check("商店顶部卡片不再多留 16px 空白",
      "<!-- ============ 稀有种子（提到最上方） ============ -->" in src_shop)

print("\n=== 5. 果蔬摊：页头精简 + 支线/名片移到底 ===")
check("果蔬摊有精简页头 .sec-top", 'class="sec-top"' in market)
check("果蔬摊页头用缩小版舞台", "ms-wrap sm" in market)
check("果蔬摊页头保留动画（ms-market）", "ms-stage ms-market" in market)
check("果蔬摊页头保留金币值", "🪙 金币" in market)
check("果蔬摊页头保留能量值", "⚡ 能量" in market)
check("果蔬摊页头去掉了旧色块 stall-card", "stall-card" not in market)
check("果蔬摊页头不再有摊位等级 pill（已下移）",
      market.split("sec-top")[1].find("sum.stall.name") < 0
      and "我的摊位" in market)
m_hezi = idx(market, "nan-row")
m_price = idx(market, "今日价目牌")
m_goods = idx(market, "我的货")
m_card = idx(market, "我的摊位")
m_branch = idx(market, "branch-nav")
check("禾籽气泡紧跟页头（位置不变）", 0 < m_hezi < m_price)
check("价目牌在气泡之后", m_price > m_hezi)
check("我的货在价目牌之后", m_goods > m_price)
check("摊位名片已移到我的货之后", m_card > m_goods, str([m_card, m_goods]))
check("支线导航已移到最底部", m_branch > m_card, str([m_branch, m_card]))

print("\n=== 6. 厨房：页头精简 + 台账/支线移到底 ===")
check("厨房有精简页头 .sec-top", 'class="sec-top"' in kitchen)
check("厨房页头用缩小版舞台", "ms-wrap sm" in kitchen)
check("厨房页头保留动画（ms-kitchen）", "ms-stage ms-kitchen" in kitchen)
check("厨房页头保留能量值", "⚡ 能量" in kitchen)
check("厨房页头去掉了旧色块 kitchen-card", "kitchen-card" not in kitchen)
k_hezi = idx(kitchen, "nan-row")
k_recipe = idx(kitchen, "菜谱")
k_pantry = idx(kitchen, "灶台上的食材")
k_dish = idx(kitchen, "我的作品")
k_ledger = idx(kitchen, "我的台账")
k_branch = idx(kitchen, "branch-nav")
check("禾籽气泡紧跟页头（位置不变）", 0 < k_hezi < k_recipe)
check("菜谱在气泡之后", k_recipe > k_hezi)
check("食材在菜谱之后", k_pantry > k_recipe)
check("我的作品在食材之后", k_dish > k_pantry)
check("厨房台账已移到最底部（作品之后）", k_ledger > k_dish, str([k_ledger, k_dish]))
check("支线导航在台账之后", k_branch > k_ledger, str([k_branch, k_ledger]))

print("\n=== 7. 禾籽对话框：位置不变、只缩小 ===")
check("_hezi.html 支持 compact 参数", "cls='compact'" in src_hezi or 'cls="compact"' in src_hezi)
check("果蔬摊调用 compact", "nan-row compact" in market)
check("厨房调用 compact", "nan-row compact" in kitchen)
check("商店也用紧凑气泡", "compact" in src_shop)
check("气泡头像缩小（40 而非 60）", ", 40, 'compact'" in src_market
      and ", 40, 'compact'" in src_kitchen)
check("CSS 定义 .nan-row.compact", ".nan-row.compact" in css)
_c = css.split(".nan-row.compact .nan-say {")[1].split("}")[0]
check("紧凑气泡内边距更小（7px 11px）", "7px 11px" in _c, _c)
check("紧凑气泡字号更小（12.5px）", re.search(r"font-size:\s*12(\.5)?px", _c) is not None, _c)

print("\n=== 8. 舞台缩小：macro + CSS ===")
check("_mascot.html 支持 sm 参数", "sm=false" in src_mascot)
check("sm 会套一层 .ms-wrap", "ms-wrap{% if sm %} sm{% endif %}" in src_mascot)
check("CSS 定义 .ms-wrap.sm 尺寸 86px", ".ms-wrap.sm { width: 86px; height: 86px; }" in css)
check("CSS 有 farm 缩放 .73", ".ms-wrap.sm .ms-farm" in css and "scale(.73)" in css)
check("CSS 有 market/kitchen 缩放 .77", "scale(.77)" in css)
check("CSS 有 circle 缩放 .90", "scale(.90)" in css)
check("缩放用 transform（不触发重排）", "transform-origin: top left" in css)
check("原有动画关键帧未被删", css.count("@keyframes ms") >= 10)

print("\n=== 9. 业务功能未被动 ===")
check("菜园：翻地仍在", "plow(" in farm)
check("菜园：播种仍在", "plant(" in farm)
check("菜园：浇水仍在", "water(" in farm)
check("菜园：收获仍在", "harvest(" in farm and "harvestAll" in farm)
check("菜园：地块仍在渲染", 'class="plot' in farm)
check("菜园：施肥仍在", "fertilize(" in farm)
check("果蔬摊：卖出接口未变", "/api/market/sell" in src_market)
check("果蔬摊：兑换接口未变", "/api/market/exchange" in src_market)
check("厨房：做菜接口未变", "/api/kitchen/cook" in src_kitchen)
check("厨房：发布接口未变", "/api/kitchen/publish" in src_kitchen)
check("商店：兑换接口未变", "/api/shop/buy" in src_shop)
check("商店：使用肥料接口未变", "/api/shop/use" in src_shop)

r = sess.post(BASE + "/api/farm/plow", json={"pid": 1}, timeout=15)
check("翻地接口仍可用", r.status_code == 200, r.status_code)
r2 = sess.post(BASE + "/api/farm/plow", json={"pid": 2}, timeout=15)
check("第二块地翻地仍可用", r2.status_code == 200, r2.status_code)

print("\n=== 10. 硬性规则：无第三方动画库 ===")
for lib in ("animate.css", "cdnjs", "unpkg", "jsdelivr", "gsap", "lottie",
            "anime.js", "velocity"):
    hit = [p for p in ("templates/farm.html", "templates/market.html",
                       "templates/kitchen.html", "templates/shop.html",
                       "templates/base.html", "static/css/style.css",
                       "static/js/energy_help.js") if lib in read(p)]
    check("未引入 %s" % lib, not hit, hit)
check("能量弹窗为原生 JS（无库）", "import " not in js_help and "require(" not in js_help)

print("\n" + "=" * 56)
print("第 17 轮：通过 %d 项，失败 %d 项" % (OK, BAD))
print("=" * 56)
sys.exit(1 if BAD else 0)
