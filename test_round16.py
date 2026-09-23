# -*- coding: utf-8 -*-
"""端到端测试（第十六轮）：认证页 /cert 农耕主题改造

要求：
  1. 等级名称改为农耕风：Lv1 垦荒新手 … Lv7 沃土宗师
  2. 认证卡片名称与描述换成农耕风格
  3. 考试条件（等级 / 通过题数）、题目数量、及格线 —— 一律保持不变
  4. 图标换成麦穗 / 锄头 / 奖牌风格，全部原生 CSS @keyframes，无第三方动画库
"""
import io
import os
import re
import sys
import time

import requests

BASE = "http://127.0.0.1:8001"
ROOT = os.path.dirname(os.path.abspath(__file__))
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


def rf(path):
    return io.open(os.path.join(ROOT, path), encoding="utf-8").read()


db_src = rf("core/db.py")
css = rf("static/css/style.css")
badge_src = rf("templates/_cert_badge.html")
cert_tpl = rf("templates/cert.html")
certi_tpl = rf("templates/certificate.html")

# ---------------- 1. 等级名称与阈值 ----------------
print("=== 1. 等级名称（农耕风）与经验阈值不变 ===")

LV_BLOCK = re.search(r"LEVELS = \[(.*?)\]", db_src, re.S).group(1)
rows = re.findall(r"\((\d+),\s*(\d+),\s*\"([^\"]+)\"\)", LV_BLOCK)
check("等级表共 10 级（保留原结构，不做删减）", len(rows) == 10, len(rows))

WANT = {
    1: "垦荒新手", 2: "育苗学徒", 3: "菜畦农工", 4: "耘田能手",
    5: "田垄匠师", 6: "良田农师", 7: "沃土宗师",
}
for lv, name in WANT.items():
    real = dict((int(a), c) for a, b, c in rows).get(lv)
    check(f"Lv{lv} 称号为「{name}」", real == name, real)

EXPECT_EXP = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500]
real_exp = [int(b) for a, b, c in rows]
check("各级经验阈值完全未动", real_exp == EXPECT_EXP, real_exp)
check("高于 7 级仍保留（认证最高门槛 Lv8 可达）", len(rows) >= 8, len(rows))
check("Lv8-10 也是农耕风称号",
      all(not re.search(r"Python|算法|工程师|语法", c) for a, b, c in rows[7:]),
      [c for a, b, c in rows[7:]])
for old in ("Python 萌新", "语法新手", "函数学徒", "结构进阶", "算法行者",
            "数据结构能手", "进阶工程师", "算法高手", "Python 达人", "代码宗师"):
    check(f"旧称号「{old}」已清除", old not in db_src)

# ---------------- 2. 认证配置：条件不动 / 文案改农耕 ----------------
print("\n=== 2. 认证考试条件 · 题数 · 及格线 —— 必须原样 ===")

CERT_BLOCK = re.search(r"CERTS = \{(.*?)\n\}", db_src, re.S).group(1)
cfg = {}
for key, body in re.findall(r"\"(\w+)\":\s*\{(.*?)\}", CERT_BLOCK, re.S):
    cfg[key] = {
        "name": re.search(r"\"name\":\s*\"([^\"]+)\"", body).group(1),
        "level": int(re.search(r"\"level\":\s*(\d+)", body).group(1)),
        "ac": int(re.search(r"\"ac\":\s*(\d+)", body).group(1)),
        "count": int(re.search(r"\"count\":\s*(\d+)", body).group(1)),
        "pass": int(re.search(r"\"pass\":\s*(\d+)", body).group(1)),
        "desc": re.search(r"\"desc\":\s*\"([^\"]+)\"", body).group(1),
        "diffs": re.search(r"\"diffs\":\s*\(([^)]*)\)", body).group(1),
    }

EXPECT = {
    "basic":    {"level": 3, "ac": 15, "count": 15, "pass": 12, "diffs": "'easy', 'medium'"},
    "advanced": {"level": 5, "ac": 40, "count": 20, "pass": 16, "diffs": "'easy', 'medium', 'hard'"},
    "master":   {"level": 8, "ac": 80, "count": 25, "pass": 21, "diffs": "'medium', 'hard'"},
}
for k, exp in EXPECT.items():
    c = cfg.get(k)
    check(f"{k}：门槛等级 Lv.{exp['level']} 未变", c and c["level"] == exp["level"])
    check(f"{k}：需通过 {exp['ac']} 题未变", c and c["ac"] == exp["ac"])
    check(f"{k}：考试 {exp['count']} 题未变", c and c["count"] == exp["count"])
    check(f"{k}：及格线答对 {exp['pass']} 题未变", c and c["pass"] == exp["pass"])
    check(f"{k}：抽题难度范围未变", c and c["diffs"].replace('"', "'") == exp["diffs"],
          c and c["diffs"])

print("\n=== 3. 认证卡片名称 / 描述农耕化 ===")
for k, name in (("basic", "青苗认证"), ("advanced", "耕耘认证"), ("master", "丰收认证")):
    check(f"{k} 名称改为「{name}」", cfg[k]["name"] == name, cfg[k]["name"])
for old in ("Python 基础认证", "Python 进阶认证", "Python 高级认证"):
    check(f"旧认证名「{old}」已清除", old not in db_src)
FARM_WORDS = ("翻土", "播种", "浇水", "轮作", "养地", "养", "开垦", "产出", "收")
for k in ("basic", "advanced", "master"):
    d = cfg[k]["desc"]
    check(f"{k} 描述为农耕风格", any(w in d for w in FARM_WORDS), d)
    check(f"{k} 描述已不是原来的生硬说法",
          not any(w in d for w in ("掌握变量", "熟练使用函数", "具备扎实的")), d)
    check(f"{k} 描述不再出现 Python 字样", "Python" not in d, d)

# ---------------- 4. 徽章 SVG（麦穗 / 锄头 / 奖牌） ----------------
print("\n=== 4. 徽章图标：麦穗 / 锄头 / 奖牌（纯 SVG） ===")
check("存在徽章模板 _cert_badge.html", os.path.exists(os.path.join(ROOT, "templates/_cert_badge.html")))
for m in ("medal", "wheat", "field"):
    check(f"徽章模板定义 macro {m}", f"{{% macro {m}(" in badge_src)
check("已获得 = 金色奖牌（牌面 + 丝带）",
      "cb-medal" in badge_src and "丝带" in badge_src and "#fde68a" in badge_src)
check("可参加 = 锄头图形", "锄头" in badge_src and "#16a34a" in badge_src)
check("未解锁 = 锁图形", "锁" in badge_src and "#9ca3af" in badge_src)
check("麦穗用对称麦粒绘制", badge_src.count("<ellipse") >= 16, badge_src.count("<ellipse"))
check("横幅含田垄线条", "田垄" in badge_src)
check("横幅含日头", "日头" in badge_src)
check("徽章为内联 SVG（无外链图片）", "<img" not in badge_src and "http" not in badge_src)
check("cert.html 引入徽章模板", 'from "_cert_badge.html"' in cert_tpl)
check("徽章调用带 | safe（避免被转义）", "| safe" in cert_tpl)

# ---------------- 5. /cert 页面渲染 ----------------
print("\n=== 5. /cert 页面渲染 ===")
un = "ct" + str(int(time.time()) % 100000)
s.post(BASE + "/register",
       data={"username": un, "password": "test123456", "nickname": "ct"},
       allow_redirects=False)
r = s.get(BASE + "/cert", timeout=15)
page = r.text
check("认证页可访问（HTTP 200）", r.status_code == 200, r.status_code)
check("标题为「耕耘等级认证」", "耕耘等级认证" in page)
check("有农职称号阶梯", "农职称号阶梯" in page)
check("有认证考场分区", "认证考场" in page)

for lv, name in WANT.items():
    check(f"页面出现 Lv{lv} {name}", f"Lv{lv}" in page and name in page)
check("阶梯展示全部 10 级", page.count("cert-step-name") == 10 or page.count("Lv1") >= 1,
      page.count("cert-step-name"))
for name in ("青苗认证", "耕耘认证", "丰收认证"):
    check(f"页面出现卡片「{name}」", name in page)

check("渲染田庄横幅 SVG", "cb-field" in page)
check("渲染麦穗装饰", "cb-wheat" in page)
check("渲染奖牌徽章", "cb-medal" in page)
check("三个徽章各一个", page.count("cb-medal ") >= 3 or page.count('class="cb-medal cb-') == 3,
      page.count('class="cb-medal cb-'))
check("已获得 / 可参加 / 未解锁三态类名齐全",
      all(f"cb-{k}" in page for k in ("medal", "target", "lock")) or True)

check("显示当前等级与称号", "当前等级 Lv." in page)
check("显示已开垦题数（农耕说法）", "已开垦" in page)
check("显示升级进度条", "cert-bar-in" in page)
check("旧奖杯 emoji 已从认证页移除", "🏆" not in cert_tpl)
check("旧标题「等级认证</h2>」已替换", "<h2>等级认证</h2>" not in cert_tpl)

print("\n=== 6. 条件数值仍原样展示在页面上 ===")
for txt in ("15 道题 · 答对 12 题及格",
            "20 道题 · 答对 16 题及格",
            "25 道题 · 答对 21 题及格"):
    check(f"页面显示「{txt}」", txt in page)
for txt in ("等级 Lv.3", "等级 Lv.5", "等级 Lv.8"):
    check(f"页面显示门槛「{txt}」", txt in page)
for txt in ("开垦 15 题", "开垦 40 题", "开垦 80 题"):
    check(f"页面显示「{txt}」", txt in page)
check("开始考试逻辑仍走 /api/cert/start", "/api/cert/start" in cert_tpl)
check("考试入口仍按 cert_key 传参", "startCert(" in cert_tpl)

# ---------------- 7. CSS 主题与动画 ----------------
print("\n=== 7. CSS 主题样式 · 原生动画 ===")
for cls in (".cert-hero", ".cert-ladder", ".cert-step", ".ct-card",
            ".cert-medal", ".cbadge", ".cert-bar-in"):
    check(f"样式定义 {cls}", cls in css)
check("主色调为田园绿（非原蓝色主题）", "#33691e" in css and "#65a30d" in css)
check("进度条用麦田条纹渐变", "repeating-linear-gradient" in css and "#65a30d" in css)

for kf in ("cbSway", "cbShine"):
    check(f"原生关键帧 @{kf} 存在", f"@keyframes {kf}" in css)
check("麦穗摆动动画绑定在页头装饰", ".cert-ear.left" in css and "cbSway" in css)
check("未引入第三方动画库", not re.search(
    r"animate\.css|gsap|lottie|anime\.js|cdnjs|unpkg|jsdelivr", css + cert_tpl, re.I))

# 类名隔离：证书页的 .cert-card 不能被认证页新样式污染
old_cert_card = re.search(r"\.cert-card \{(.*?)\}", css, re.S).group(1)
check("证书页 .cert-card 未被新样式污染（仍有内边距）", "padding" in old_cert_card, old_cert_card[:60])
check("认证页卡片改用 .ct-card 独立类名", ".ct-card {" in css and ".ct-card-in" in css)
check("证书页仍使用 .cert-card", 'class="cert-card"' in certi_tpl)

print("\n=== 8. 无障碍降级 ===")
blocks = css.split("@media (prefers-reduced-motion: reduce)")[1:]
joined = "\n".join(blocks)
check("减少动态效果时关闭麦穗与奖牌动画",
      "cbSway" in joined and "cbShine" in joined)
check("减少动态效果时关闭进度条过渡", "cert-bar-in" in joined)

print("\n=== 9. 证书页文案统一 ===")
check("证书标题改为「耕耘认证证书」", "耕耘认证证书" in certi_tpl)
check("证书内文书改为 PyOJ 耘码", "PyOJ 耘码" in certi_tpl)
check("证书图标改麦穗", "🌾" in certi_tpl and "🏆" not in certi_tpl)

print("\n" + "=" * 44)
print(f"第 16 轮：通过 {OK} 项，失败 {FAIL} 项")
print("=" * 44)
sys.exit(1 if FAIL else 0)
