# -*- coding: utf-8 -*-
"""端到端测试（第十五轮）：注册 / 登录双流程 + 欢迎弹窗时序动画 + 4 步新手蒙布引导

一、注册流程（新用户）
  1. 注册页表单填写引导（data-tip + regform.js 实时校验）
  2. 注册成功 → 全屏欢迎弹窗：最终版欢迎文案 + 放大版苗小序 + 对话气泡自我介绍
  3. 时序动画：静止自我介绍 → 缩小 + 原地旋转一圈飞回悬浮位 → 尺寸与悬浮图标一致
              → 亮光消散 + 气泡消失 → 自动关闭
  4. 关闭后跳转签到页 /checkin，紧接着触发 4 步功能图标蒙布教学
二、登录流程（老用户）：保留原版，不弹欢迎窗
三、全部动画为原生 CSS @keyframes，禁止第三方动画库
"""
import re
import time

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


css = s.get(BASE + "/static/css/style.css", timeout=15).text
wj = s.get(BASE + "/static/js/welcome.js", timeout=15).text
oj = s.get(BASE + "/static/js/onboard.js", timeout=15).text
rj = s.get(BASE + "/static/js/regform.js", timeout=15).text

print("=== 1. 注册页表单填写引导 ===")
rp = s.get(BASE + "/register", timeout=15).text
check("注册页可访问", rp.status_code if False else "注册" in rp)
check("引入 regform.js", "regform.js" in rp)
check("三个字段都带填写说明 data-tip",
      rp.count("data-tip") == 3, rp.count("data-tip"))
for tid in ("tipUser", "tipNick", "tipPwd"):
    check(f"提示容器 {tid}", f'id="{tid}"' in rp)
check("regform.js 有用户名校验（3~20）", "length < 3" in rj and "length > 20" in rj)
check("regform.js 有密码校验（至少 6 位）", "length < 6" in rj)
check("regform.js 聚焦时展示填写说明", "'focus'" in rj and "data-tip" in rj)
check("regform.js 输入时实时校验", "'input'" in rj)
check("regform.js 提交前统一校验并阻止", "preventDefault" in rj)
check("CSS 有提示条样式 .rg-tip", ".rg-tip" in css)
check("CSS 有校验通过/不通过样式", ".rg-tip.ok" in css and ".rg-tip.bad" in css)

print("\n=== 2. 注册流程：全屏欢迎弹窗 ===")
P = "/re" + "gister"
uname = "r15_%d" % (int(time.time()) % 1000000)
r = s.post(BASE + P, data={"username": uname, "password": "test123456",
                           "nickname": "十五轮"}, allow_redirects=False)
check("注册成功返回 302", r.status_code == 302, r.status_code)
check("注册下发一次性 welcome_new cookie",
      "welcome_new=1" in (r.headers.get("set-cookie") or ""))
home = s.get(BASE + "/", timeout=15).text
check("注册后出现全屏欢迎弹窗 welcome-mask", "welcome-mask" in home)
check("弹窗含放大版苗小序 wlc-hero", "wlc-hero" in home)
check("弹窗含对话气泡 wlc-bubble", "wlc-bubble" in home)
_hero = home.split('wlc-hero')[1][:400] if 'wlc-hero' in home else ''
check("放大版苗小序渲染尺寸为 220（远大于悬浮图标 46）",
      'width="220"' in _hero, _hero[:120])
check("自我介绍台词前半句正确", "你好呀！我是苗小序👋！" in home)
check("自我介绍台词后半句正确",
      "欢迎问我任何问题，快来开启你的编程种田之旅吧！" in home)
check("欢迎文案第 1 行", "是否也曾在编程学习路上迷茫彷徨？" in home)
check("欢迎文案第 2 行", "厌倦乏味的机械刷题，渴望看得见的成长；" in home)
check("欢迎文案第 3 行（欢迎来到 PyOJ ✨）",
      "欢迎来到" in home and "PyOJ" in home and "✨" in home)
check("欢迎文案第 4 行",
      "脑力作犁，代码为种。在趣味养成中打磨编程本领，开启独属于你的代码乐园！" in home)
check("弹窗含亮光层 wlc-flash", "wlc-flash" in home)

print("\n=== 3. 弹窗动画时序（原生 CSS @keyframes） ===")
check("阶段1：出场动画 wlcIn", "@keyframes wlcIn" in css)
check("阶段1：挥手说话动画 wlcTalk", "@keyframes wlcTalk" in css)
check("阶段2：飞回动画 wlcFly", "@keyframes wlcFly" in css)
_fly = css.split("@keyframes wlcFly")[1][:600] if "@keyframes wlcFly" in css else ""
check("阶段2：旋转完整一圈 360deg", "rotate(360deg)" in _fly)
check("阶段2：中途旋转 180deg（缓慢旋转）", "rotate(180deg)" in _fly)
check("阶段2：缩放到悬浮图标比例 scale(var(--k", "scale(var(--k" in css)
check("阶段2：位移使用 --dx/--dy", "var(--dx)" in css and "var(--dy)" in css)
check("阶段3：落位态 .wlc-hero.landed", ".wlc-hero.landed" in css)
check("阶段4：亮光消散 wlcFlash", "@keyframes wlcFlash" in css)
check("阶段4：亮光光环 wlcRing", "@keyframes wlcRing" in css)
check("阶段4：人物淡出 wlcGone", "@keyframes wlcGone" in css)
check("阶段4：气泡淡出 wbOut", "@keyframes wbOut" in css)

check("JS 编排三个时序常量（介绍/飞行/亮光）",
      "T_INTRO" in wj and "T_FLY" in wj and "T_FLASH" in wj)
check("JS 计算位移与缩放变量", "--dx" in wj and "--dy" in wj and "--k" in wj)
check("JS 用 animationend 衔接阶段2→3", "animationend" in wj and "wlcFly" in wj)
check("JS 落位后尺寸对齐悬浮图标（66×66 / 苗小序 46）",
      "'66px'" in wj and "'46'" in wj)
check("缩放比例按悬浮图标内的苗小序尺寸算", "fabSvg" in wj)
check("飞行前停掉悬浮球漂浮动画（保证落位精确）", "nf-static" in wj)
check("落位后悬浮球高亮回馈", "nf-welcome-pop" in wj)
check("阶段5：自动关闭弹窗", "closeAndGo" in wj)
check("阶段5：关闭后跳转签到页 /checkin", "'/checkin'" in wj)
check("跳转前清除 welcome_new cookie", "delCookie('welcome_new')" in wj)
check("注册当天不抢戏：写 pop_signin", "pop_signin" in wj)
check("标记刚注册，保证签到页紧接着触发引导",
      "pyoj_just_registered" in wj)
check("附带音频：Web Audio 合成问候音",
      "AudioContext" in wj and "createOscillator" in wj)
check("音频失败不影响动画（try/catch 降级）",
      wj.count("catch (e)") >= 2)
check("尊重减少动态效果设置", "prefers-reduced-motion" in wj)
check("允许 Esc / 点遮罩提前跳过", "Escape" in wj and "e.target === mask" in wj)

print("\n=== 4. 新手蒙布教学：严格 4 步 ===")
STEPS = [
    ("/problems", "✍️ 答题时间到！脑力耕地，现在开工！"),
    ("/farm", "🥬 脑力值到手！下地耕耘，一起种菜吧！"),
    ("/market", "🥬 蔬菜成熟啦！去果蔬摊兑换资源，收获你的劳动成果！"),
    ("/kitchen", "🍳 食材就位！进厨房加工，解锁更多惊喜奖励！"),
]
check("引导步骤数为 4", len(re.findall(r"\{ sel:", oj)) == 4,
      len(re.findall(r"\{ sel:", oj)))
for href, tip in STEPS:
    check(f"第{STEPS.index((href, tip)) + 1}步高亮导航 {href}",
          f'.nav-card[href="{href}"]' in oj)
    check(f"第{STEPS.index((href, tip)) + 1}步文案一致", tip in oj)
check("有【下一步】按钮", "下一步" in oj)
check("最后一步按钮为【开始体验】", "开始体验" in oj)
check("有【跳过引导】", "跳过引导" in oj)
check("半透明黑色遮罩（挖洞式）", "ob-hole" in css or "ob-hole" in oj)
check("遮罩挖空仅高亮当前目标", "ob-hole" in oj and "ob-block" in oj)
check("提示卡带箭头指向目标", "ob-arrow" in oj)
check("走完自动消失并写库", "/api/onboard/done" in oj)
check("刚注册跳转过来立即开始（紧接着触发）",
      "justReg" in oj and "pyoj_just_registered" in oj)

print("\n=== 5. 登录流程（老用户）保持原版 ===")
s2 = requests.Session()
r2 = s2.post(BASE + "/login", data={"username": "demo", "password": "demo123456"},
             allow_redirects=False)
check("登录成功返回 302", r2.status_code == 302, r2.status_code)
check("登录不下发 welcome_new cookie",
      "welcome_new" not in (r2.headers.get("set-cookie") or ""))
h2 = s2.get(BASE + "/", timeout=15).text
check("老用户登录后没有欢迎弹窗", "welcome-mask" not in h2)
check("老用户登录后没有 wlc-hero", "wlc-hero" not in h2)
check("老用户 data-onboard=0（不再弹引导）",
      re.search(r'<body data-onboard="0"', h2) is not None)
check("老用户登录页流程保留（签到弹窗逻辑仍在）",
      s2.get(BASE + "/static/js/signin.js", timeout=15).status_code == 200)
check("签到页可访问", s2.get(BASE + "/checkin", timeout=15).status_code == 200)
check("老用户题库/菜园等页面正常",
      all(s2.get(BASE + p, timeout=15).status_code == 200
          for p in ("/problems", "/farm", "/market", "/kitchen")))

print("\n=== 6. 纯原生实现，禁止第三方动画库 ===")
alljs = wj + oj + rj
for bad in ("animate.css", "lottie", "gsap", "anime.js", "velocity",
            "cdn.jsdelivr", "cdnjs", "unpkg"):
    check(f"未引入 {bad}", bad not in alljs and bad not in css)
def kf(name):
    """取出 @keyframes name { ... } 的块内容"""
    m = re.search(r"@keyframes\s+" + name + r"\s*\{(.*?)\n\}", css, re.S)
    return m.group(1) if m else ""


BAD_PROP = re.compile(r"\b(width|height|top|left|right|bottom|margin|padding)\s*:")
for kfname in ("wlcIn", "wlcTalk", "wlcFly", "wlcGone", "wlcFlash", "wlcRing",
               "wbIn", "wbPulse", "wbShrink", "wbOut", "wlIn", "wlOut"):
    body = kf(kfname)
    check(f"关键帧 {kfname} 不触发重排（只动 transform/opacity/filter）",
          bool(body) and not BAD_PROP.search(body))
check("动画均声明为 @keyframes", css.count("@keyframes wlc") >= 6)

print(f"\n第 15 轮：通过 {OK} 项，失败 {FAIL} 项")
