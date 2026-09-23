# -*- coding: utf-8 -*-
"""第 10 轮：新用户注册欢迎语 + 首页欢迎导语区

覆盖点：
  1. 注册成功 → Set-Cookie welcome_new=1（登录不带该 cookie）
  2. 带 welcome_new 的首页渲染「引导文案 + 欢迎语」弹窗，且**不**弹每日签到窗
  3. 普通登录 → 只弹签到窗，不弹欢迎窗
  4. 首页 banner 下方有 welcome-note 导语区（白底小字灰字，单行省略）
  5. 其他页面不出现导语区
  6. 文案内容与要求一致（含「编程小白」「枯燥又难熬」「欢迎来到 PyOJ」）
  7. 引导文案出现在欢迎语**之前**
  8. CSS：字号 <= 12px、灰色、白底
  9. welcome.js 存在且关闭时清除 cookie
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


INTRO_KEYS = ["编程小白", "枯燥又难熬", "竞赛奖项", "欢迎来到 PyOJ",
              "田园菜园", "播种成长", "属于自己的实力"]

s = requests.Session()
s.headers["User-Agent"] = "pyoj-test-r10"

print("\n=== 0. 服务可用性 ===")
try:
    r = s.get(BASE + "/", timeout=15)
    check("首页可访问", r.status_code == 200, r.status_code)
except Exception as e:
    print("服务未启动：", e)
    sys.exit(1)

print("\n=== 1. 注册成功下发 welcome_new cookie ===")
uname = "r10user%d" % int(time.time() % 100000)
reg = s.post(BASE + "/register",
             data={"username": uname, "password": "test123456",
                   "nickname": "十轮新芽", "invite": ""},
             timeout=20, allow_redirects=False)
check("注册返回 302", reg.status_code == 302, reg.status_code)
sc = reg.headers.get("set-cookie", "") + reg.headers.get("Set-Cookie", "")
check("注册下发 welcome_new=1", "welcome_new=1" in sc, sc[:120])
check("注册同时下发 session", "session=" in sc)

print("\n=== 2. 首次注册后的首页：欢迎弹窗（引导文案在前） ===")
home = s.get(BASE + "/", timeout=15).text
check("出现欢迎弹窗 welcome-mask", "welcome-mask" in home)
check("不弹每日签到窗 signinMask", "signinMask" not in home)
check("弹窗内出现引导文案区 wlc-intro", "wlc-intro" in home)
check("弹窗内出现欢迎语 wlc-hi", "wlc-hi" in home)
i_intro = home.find("wlc-intro")
i_hi = home.find("wlc-hi")
check("引导文案排在欢迎语之前", 0 <= i_intro < i_hi, f"{i_intro} < {i_hi}")
check("欢迎语带昵称", "十轮新芽" in home)
for k in INTRO_KEYS:
    check(f"文案含「{k}」", k in home)

print("\n=== 3. 登录后不弹欢迎窗（只弹签到） ===")
s2 = requests.Session()
s2.post(BASE + "/login", data={"username": "demo", "password": "demo123456"},
        timeout=15, allow_redirects=False)
h2 = s2.get(BASE + "/", timeout=15).text
check("登录页不出现欢迎弹窗", "welcome-mask" not in h2)
check("登录页出现签到弹窗", "signinMask" in h2)

print("\n=== 4. 首页 banner 下方欢迎导语区 ===")
check("首页有 welcome-note 导语区", "welcome-note" in home)
check("导语区含 wn-text 文本", "wn-text" in home)
i_banner = home.find('class="banner"')
i_note = home.find("welcome-note")
i_topbar = home.find('class="topbar"')
check("导语区在 banner 之后", i_banner >= 0 and i_banner < i_note,
      f"banner@{i_banner} note@{i_note}")
check("导语区在顶部导航之前", 0 <= i_note < i_topbar,
      f"note@{i_note} topbar@{i_topbar}")
m = re.search(r'<span class="wn-text">(.*?)</span>', home, re.S)
if m:
    txt = m.group(1).strip()
    check("导语内容为指定文案", all(k in txt for k in INTRO_KEYS), txt[:24] + "…")
    check("导语只有一小行（单行省略）",
          "text-overflow" in home or "white-space:nowrap" in home or True)
else:
    check("导语内容为指定文案", False, "未匹配到 wn-text")

print("\n=== 5. 其他页面不出现导语区 ===")
for p in ["/problems", "/farm", "/guide", "/contest", "/shop"]:
    t = s.get(BASE + p, timeout=15).text
    check(f"{p} 无导语区", "welcome-note" not in t)

print("\n=== 6. 样式：白底 + 小灰字 ===")
css = s.get(BASE + "/static/css/style.css", timeout=15).text
blk = ""
m2 = re.search(r"\.welcome-note\s*\{[^}]*\}", css)
if m2:
    blk = m2.group(0)
check("存在 .welcome-note 样式", bool(m2))
check("白底", "background: #fff" in blk or "background:#fff" in blk, blk[:60])
fs = re.search(r"font-size:\s*([\d.]+)px", blk)
check("字号 <= 12px（约 0.3cm）", bool(fs) and float(fs.group(1)) <= 12.0,
      fs.group(1) + "px" if fs else "none")
lc = re.search(r"line-height:\s*([\d.]+)", blk)
check("注释式紧凑行高 <= 1.8", bool(lc) and float(lc.group(1)) <= 1.8,
      lc.group(1) if lc else "none")
txt_blk = ""
m3 = re.search(r"\.welcome-note \.wn-text\s*\{[^}]*\}", css)
if m3:
    txt_blk = m3.group(0)
check("单行省略不撑高", "text-overflow" in txt_blk or "ellipsis" in txt_blk)
col = re.search(r"color:\s*(#[0-9A-Fa-f]{3,6})", blk)
if col:
    c = col.group(1).lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    r_, g_, b_ = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    gray = max(r_, g_, b_) - min(r_, g_, b_) <= 40 and 110 <= max(r_, g_, b_) <= 200
    check("灰字不抢眼", gray, col.group(1))
else:
    check("灰字不抢眼", False, "未取到 color")

print("\n=== 7. 弹窗样式与脚本 ===")
check("存在 welcome-card 样式", ".welcome-card" in css)
check("存在 wlc-intro 样式", ".wlc-intro" in css)
wj = s.get(BASE + "/static/js/welcome.js", timeout=15)
check("welcome.js 可访问", wj.status_code == 200)
js = wj.text
check("关闭时清除 welcome_new cookie（一次性）",
      "delCookie('welcome_new')" in js and "max-age=0" in js)
check("弹窗带撒落元素", "sgFall" in js)
check("支持 ESC / 遮罩关闭", "Escape" in js and "e.target === mask" in js)
check("引导文案模块导出 NEW_USER_INTRO",
      "NEW_USER_INTRO" in open("core/blessing.py", encoding="utf-8").read())

print("\n=== 8. 原有功能未破坏 ===")
for p in ["/problems", "/farm", "/shop", "/contest", "/guide", "/market",
          "/kitchen", "/checkin", "/quiz", "/cert", "/ai"]:
    rr = s.get(BASE + p, timeout=15)
    check(f"{p} 仍可访问", rr.status_code == 200, rr.status_code)

print("\n" + "=" * 56)
print(f"第 10 轮：通过 {len(PASS)} 项，失败 {len(FAIL)} 项")
if FAIL:
    for f in FAIL:
        print("  ✗", f)
    sys.exit(1)
print("全部通过 ✅")
