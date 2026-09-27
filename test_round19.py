# -*- coding: utf-8 -*-
"""第 19 轮专项测试：果蔬摊 / 厨房页头「动画 + 禾籽介绍」并成一行

改动范围（只动排版，不动业务）：
  果蔬摊 /market ：禾籽气泡（黄色禾籽 + 介绍文案）从页头下方挪进 .sec-top，
                   与绿色苗小序动画同一行；金币 / 能量 / 帮助图标 / 一键清空菜篮
                   按钮都留在原位
  厨房   /kitchen：同上（页头只有动画 + 能量 + 帮助图标 + 气泡）
  CSS           ：新增 .nan-row.inline（可伸缩、窄屏整行落到下面）

业务（卖出 / 兑换 / 做菜 / 发布）一律不动。
"""
import io
import os
import re
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


def read(p):
    return io.open(p, encoding="utf-8").read()


def sec_top_block(src):
    """取出模板里 .sec-top 这一层的内部内容（缩进的 </div> 不算，只认顶格那个）
    注意：渲染后的 HTML 里吉祥物 SVG 宏会顶格输出 </div>，所以只能对模板源码用。"""
    if 'class="sec-top"' not in src:
        return ""
    rest = src.split('class="sec-top"', 1)[1]
    m = re.search(r"\n</div>", rest)
    return rest[:m.start()] if m else rest


def at(h, key):
    return h.find(key)


sess = requests.Session()
uname = "r19t" + str(int(time.time()) % 100000)
sess.post(BASE + "/register",
          data={"username": uname, "password": "test123456", "nickname": "r19t"},
          allow_redirects=False, timeout=15)
sess.get(BASE + "/", timeout=15)

market = sess.get(BASE + "/market", timeout=15).text
kitchen = sess.get(BASE + "/kitchen", timeout=15).text

src_market = read("templates/market.html")
src_kitchen = read("templates/kitchen.html")
css = read("static/css/style.css")

m_top = sec_top_block(src_market)      # 模板源码块（判断是否真的写进页头条里）
k_top = sec_top_block(src_kitchen)

print("\n=== 1. 禾籽气泡已并入页头条 ===")
check("果蔬摊模板调用 compact inline", "'compact inline'" in src_market)
check("厨房模板调用 compact inline", "'compact inline'" in src_kitchen)
check("果蔬摊渲染出 inline 气泡", "nan-row compact inline" in market)
check("厨房渲染出 inline 气泡", "nan-row compact inline" in kitchen)
check("果蔬摊气泡写在 .sec-top 里（与动画同一行）", "hezi_say" in m_top, m_top[:200])
check("厨房气泡写在 .sec-top 里（与动画同一行）", "hezi_say" in k_top, k_top[:200])
# 渲染后：气泡夹在页头条与下方卡片之间，说明它确实跟着页头走
check("果蔬摊：气泡紧跟页头、在行情牌之前",
      at(market, 'class="sec-top"') < at(market, "nan-row compact inline") < at(market, "grid grid-2"),
      [at(market, 'class="sec-top"'), at(market, "nan-row compact inline"), at(market, "grid grid-2")])
check("厨房：气泡紧跟页头、在菜谱卡片之前",
      at(kitchen, 'class="sec-top"') < at(kitchen, "nan-row compact inline") < at(kitchen, "菜谱"),
      [at(kitchen, 'class="sec-top"'), at(kitchen, "nan-row compact inline"), at(kitchen, "菜谱")])
check("果蔬摊整页只有一个禾籽气泡", market.count("nan-row compact") == 1,
      market.count("nan-row compact"))
check("厨房整页只有一个禾籽气泡", kitchen.count("nan-row compact") == 1,
      kitchen.count("nan-row compact"))

print("\n=== 2. 同一行内的左右顺序：动画在前，气泡在后 ===")
check("果蔬摊：动画在气泡左侧", 0 <= at(market, "ms-wrap") < at(market, "nan-row"),
      [at(market, "ms-wrap"), at(market, "nan-row")])
check("厨房：动画在气泡左侧", 0 <= at(kitchen, "ms-wrap") < at(kitchen, "nan-row"),
      [at(kitchen, "ms-wrap"), at(kitchen, "nan-row")])
check("果蔬摊：数值在气泡左侧",
      0 <= at(market, "sec-top-main") < at(market, "nan-row"),
      [at(market, "sec-top-main"), at(market, "nan-row")])
check("果蔬摊：一键清空按钮仍在气泡右侧",
      at(market, "nan-row") < at(market, "sellAll()"),
      [at(market, "nan-row"), at(market, "sellAll()")])

print("\n=== 3. CSS：.nan-row.inline ===")
check("定义了 .nan-row.inline", ".nan-row.inline" in css)
_i = css.split(".nan-row.inline {")[1].split("}")[0]
check("inline 气泡可伸缩占据剩余宽度", re.search(r"flex:\s*1\s+1\s+\d+px", _i) is not None, _i)
check("inline 气泡取消外边距（贴进页头条）", re.search(r"margin:\s*0", _i) is not None, _i)
check("inline 气泡垂直居中对齐动画", "align-items: center" in _i, _i)
check("气泡文字可收缩（min-width:0）", "min-width: 0" in css.split(".nan-row.inline .nan-say {")[1].split("}")[0])
check("窄屏整行落到下方", "order: 3" in css and "820px" in css)

print("\n=== 4. 页头其它元素没被挪走 ===")
check("果蔬摊动画仍在页头（stage sm）", "stage('market', 88, sm=true)" in m_top)
check("厨房动画仍在页头（stage sm）", "stage('kitchen', 88, sm=true)" in k_top)
check("果蔬摊金币仍在", "coin-tag" in m_top and "金币" in m_top)
check("果蔬摊能量值仍在", "energy-tag" in m_top and "能量" in m_top)
check("厨房能量值仍在", "energy-tag" in k_top and "能量" in k_top)
check("果蔬摊能量规则小图标仍在", "energy_help()" in m_top)
check("厨房能量规则小图标仍在", "energy_help()" in k_top)
check("果蔬摊一键清空菜篮按钮仍在", "sellAll()" in m_top)
check("果蔬摊动画仍是缩小版（sm）", "stage('market', 88, sm=true)" in src_market)
check("厨房动画仍是缩小版（sm）", "stage('kitchen', 88, sm=true)" in src_kitchen)

print("\n=== 5. 下方内容没被影响 ===")
check("果蔬摊行情牌仍在", "今日价目牌" in market or "price-grid" in market)
check("果蔬摊摊位名片仍靠后", market.find("branch-nav") > market.find("price-grid"))
check("厨房菜谱仍在", "recipe-grid" in kitchen or "菜谱" in kitchen)
check("厨房台账仍在", "台账" in kitchen)
check("厨房支线导航在台账之后", kitchen.find("branch-nav") > kitchen.find("台账"))

print("\n=== 6. 没有引入第三方动画库 ===")
for lib in ("animate.css", "cdnjs", "unpkg", "jsdelivr", "gsap", "lottie", "anime.js"):
    check("未引入 " + lib, lib not in src_market and lib not in src_kitchen and lib not in css)

print("\n" + "=" * 56)
print("第 19 轮：通过 %d 项，失败 %d 项" % (OK, BAD))
print("=" * 56)
